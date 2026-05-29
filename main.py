"""
QR Code Generator  –  Modern UI
Requires: customtkinter, Pillow, qrcode[pil]
"""

from __future__ import annotations

import io
import os
import subprocess
import tempfile

import customtkinter as ctk
from tkinter import colorchooser, filedialog, messagebox
from PIL import Image, ImageTk
import qrcode

# ── Global defaults ───────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

EC_LEVELS: dict[str, int] = {
    "Low  (7% recovery)":      qrcode.constants.ERROR_CORRECT_L,
    "Medium (15% recovery)":   qrcode.constants.ERROR_CORRECT_M,
    "Quartile (25% recovery)": qrcode.constants.ERROR_CORRECT_Q,
    "High (30% recovery)":     qrcode.constants.ERROR_CORRECT_H,
}

COLOR_PRESETS = [
    ("#000000", "#FFFFFF", "Classic"),
    ("#1565C0", "#E3F2FD", "Ocean"),
    ("#1B5E20", "#E8F5E9", "Forest"),
    ("#6A1B9A", "#F3E5F5", "Violet"),
    ("#B71C1C", "#FFEBEE", "Ruby"),
    ("#E65100", "#FFF3E0", "Sunset"),
]

# ── Utility ───────────────────────────────────────────────────────────────────

def _contrast(hex_c: str) -> str:
    """Return a legible text color (white or dark) for a given background."""
    r, g, b = int(hex_c[1:3], 16), int(hex_c[3:5], 16), int(hex_c[5:7], 16)
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "white" if lum < 0.55 else "#111111"


# ── Main Application ──────────────────────────────────────────────────────────

class QRApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("QR Code Generator")
        self.geometry("1100x720")
        self.minsize(900, 580)

        self.qr_image: Image.Image | None = None
        self.fg_color: str = "#000000"
        self.bg_color: str = "#FFFFFF"
        self._debounce_id = None

        self._build_ui()
        self.after(150, self._generate)   # auto-render on startup

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_content()

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self) -> None:
        # Outer container: 3 rows — header (top), content (fills), footer (bottom)
        sb = ctk.CTkFrame(self, width=315, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_columnconfigure(0, weight=1)
        sb.grid_rowconfigure(1, weight=1)   # content row expands

        # ── Header (always visible at top) ────────────────────────────────
        hdr = ctk.CTkFrame(sb, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=16, pady=(22, 12), sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr, text="QR Code Generator",
            font=ctk.CTkFont(size=19, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        btn_style = dict(
            width=32, height=32, corner_radius=8,
            fg_color="transparent",
            text_color=("gray40", "gray70"),
            hover_color=("gray82", "gray26"),
            border_width=1,
            border_color=("gray78", "gray32"),
            font=ctk.CTkFont(size=14),
        )

        self._mode_btn = ctk.CTkButton(
            hdr, text="☀", **btn_style, command=self._toggle_mode
        )
        self._mode_btn.grid(row=0, column=1)

        ctk.CTkButton(
            hdr, text="ℹ", **btn_style, command=self._show_about
        ).grid(row=0, column=2, padx=(6, 0))

        # ── Scrollable content area (invisible scrollbar) ─────────────────
        sc = ctk.CTkScrollableFrame(
            sb, corner_radius=0, fg_color=("gray86", "gray17"),
            scrollbar_fg_color=("gray86", "gray17"),
            scrollbar_button_color=("gray86", "gray17"),
            scrollbar_button_hover_color=("gray86", "gray17"),
        )
        sc.grid(row=1, column=0, sticky="nsew")
        sc.grid_columnconfigure(0, weight=1)

        self._section(sc, "📝  Content", 0)

        self._text = ctk.CTkTextbox(
            sc, height=90, corner_radius=10, font=ctk.CTkFont(size=13))
        self._text.grid(row=1, column=0, padx=14, pady=(4, 0), sticky="ew")
        self._text.insert("0.0", "https://example.com")
        self._text.bind("<KeyRelease>", self._on_key)

        self._char_lbl = ctk.CTkLabel(
            sc, text="19 characters",
            font=ctk.CTkFont(size=10), text_color=("gray55", "gray55"), anchor="e"
        )
        self._char_lbl.grid(row=2, column=0, padx=14, sticky="e")

        # ── Error Correction ───────────────────────────────────────────────
        self._hdiv(sc, 3)
        self._section(sc, "🛡  Error Correction", 4)

        self._ec_var = ctk.StringVar(value="High (30% recovery)")
        ctk.CTkOptionMenu(
            sc, variable=self._ec_var, values=list(EC_LEVELS.keys()),
            corner_radius=8, command=lambda _: self._generate()
        ).grid(row=5, column=0, padx=14, pady=(4, 0), sticky="ew")

        # ── Export Size ────────────────────────────────────────────────────
        self._hdiv(sc, 6)
        self._section(sc, "📐  Export Size", 7)

        self._size_var = ctk.IntVar(value=512)
        sz = ctk.CTkFrame(sc, fg_color="transparent")
        sz.grid(row=8, column=0, padx=14, pady=(4, 0), sticky="ew")
        sz.grid_columnconfigure(0, weight=1)

        ctk.CTkSlider(
            sz, from_=128, to=2048, variable=self._size_var,
            number_of_steps=60, command=self._on_size
        ).grid(row=0, column=0, sticky="ew")

        self._size_lbl = ctk.CTkLabel(
            sz, text="512 px", width=62, anchor="e",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self._size_lbl.grid(row=0, column=1, padx=(6, 0))

        # ── Colors ─────────────────────────────────────────────────────────
        self._hdiv(sc, 9)
        self._section(sc, "🎨  Colors", 10)

        clr = ctk.CTkFrame(sc, fg_color="transparent")
        clr.grid(row=11, column=0, padx=14, pady=(4, 0), sticky="ew")
        clr.grid_columnconfigure((0, 1), weight=1)

        fg_frame = ctk.CTkFrame(clr, fg_color="transparent")
        fg_frame.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkLabel(fg_frame, text="Foreground", font=ctk.CTkFont(size=11),
                     text_color="gray").pack(anchor="w", pady=(0, 2))
        self._fg_btn = ctk.CTkButton(
            fg_frame, text="#000000", height=38, corner_radius=8,
            fg_color="#1a1a1a", text_color="white", command=self._pick_fg
        )
        self._fg_btn.pack(fill="x")

        bg_frame = ctk.CTkFrame(clr, fg_color="transparent")
        bg_frame.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        ctk.CTkLabel(bg_frame, text="Background", font=ctk.CTkFont(size=11),
                     text_color="gray").pack(anchor="w", pady=(0, 2))
        self._bg_btn = ctk.CTkButton(
            bg_frame, text="#FFFFFF", height=38, corner_radius=8,
            fg_color="#e8e8e8", text_color="#333333", command=self._pick_bg
        )
        self._bg_btn.pack(fill="x")

        # ── Presets ────────────────────────────────────────────────────────
        self._hdiv(sc, 12)
        self._section(sc, "✨  Quick Presets", 13)

        pre = ctk.CTkFrame(sc, fg_color="transparent")
        pre.grid(row=14, column=0, padx=14, pady=(4, 16), sticky="ew")
        for c in range(3):
            pre.grid_columnconfigure(c, weight=1)

        for i, (fg, bg, name) in enumerate(COLOR_PRESETS):
            ctk.CTkButton(
                pre, text=name, height=32, corner_radius=8,
                fg_color=fg, text_color=_contrast(fg), hover_color=fg,
                font=ctk.CTkFont(size=11),
                command=lambda f=fg, b=bg: self._apply_preset(f, b)
            ).grid(row=i // 3, column=i % 3, padx=3, pady=3, sticky="ew")

        # ── Generate Button (always visible at bottom) ────────────────────
        footer = ctk.CTkFrame(sb, fg_color="transparent")
        footer.grid(row=2, column=0, padx=14, pady=(8, 16), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        self._gen_btn = ctk.CTkButton(
            footer, text="⚡  Generate QR Code", height=50, corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold"), command=self._generate
        )
        self._gen_btn.grid(row=0, column=0, sticky="ew")

    # ── Right Content Panel ───────────────────────────────────────────────────

    def _build_content(self) -> None:
        right = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # Preview card
        card = ctk.CTkFrame(right, corner_radius=16)
        card.grid(row=0, column=0, padx=22, pady=22, sticky="nsew")
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text="Preview",
            font=ctk.CTkFont(size=13), text_color=("gray50", "gray55")
        ).grid(row=0, column=0, padx=18, pady=(16, 0), sticky="w")

        self._preview = ctk.CTkLabel(card, text="")
        self._preview.grid(row=1, column=0, sticky="nsew")

        self._status = ctk.CTkLabel(
            card, text="Ready — enter content and hit Generate",
            font=ctk.CTkFont(size=11), text_color=("gray50", "gray60")
        )
        self._status.grid(row=2, column=0, padx=18, pady=(4, 16))

        # Action buttons
        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.grid(row=1, column=0, padx=22, pady=(0, 22), sticky="ew")
        for c in range(4):
            actions.grid_columnconfigure(c, weight=1)

        # Primary: Save PNG
        ctk.CTkButton(
            actions, text="💾  Save PNG", height=44, corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._save("PNG")
        ).grid(row=0, column=0, padx=4, sticky="ew")

        # Secondary buttons
        for col, (label, cmd) in enumerate([
            ("🖼  Save JPG",    lambda: self._save("JPEG")),
            ("📋  Copy",        self._copy),
            ("🔄  Reset",       self._reset),
        ], start=1):
            ctk.CTkButton(
                actions, text=label, height=44, corner_radius=10,
                font=ctk.CTkFont(size=13),
                fg_color=("gray80", "gray28"),
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray38"),
                command=cmd
            ).grid(row=0, column=col, padx=4, sticky="ew")

    # ── UI Helpers ────────────────────────────────────────────────────────────

    def _hdiv(self, parent, row: int) -> None:
        ctk.CTkFrame(parent, height=1, fg_color=("gray80", "gray28")).grid(
            row=row, column=0, padx=10, pady=12, sticky="ew")

    def _section(self, parent, text: str, row: int) -> None:
        ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
        ).grid(row=row, column=0, padx=14, sticky="ew")

    # ── Event Handlers ────────────────────────────────────────────────────────

    def _show_about(self) -> None:
        win = ctk.CTkToplevel(self)
        win.title("About")
        win.geometry("340x220")
        win.resizable(False, False)
        win.grab_set()
        win.lift()

        ctk.CTkLabel(
            win, text="QR Code Generator",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(30, 6))

        ctk.CTkLabel(
            win, text="Version 1.0",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray60")
        ).pack(pady=(0, 16))

        ctk.CTkFrame(win, height=1, fg_color=("gray80", "gray30")).pack(
            fill="x", padx=30, pady=(0, 16))

        ctk.CTkLabel(
            win, text="Developed by  Burak Akdogan",
            font=ctk.CTkFont(size=13)
        ).pack()

        ctk.CTkButton(
            win, text="Close", width=100, corner_radius=8,
            command=win.destroy
        ).pack(pady=(20, 0))

    def _toggle_mode(self) -> None:
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("Light")
            self._mode_btn.configure(text="🌙")
        else:
            ctk.set_appearance_mode("Dark")
            self._mode_btn.configure(text="☀")

    def _on_key(self, _event=None) -> None:
        n = len(self._text.get("0.0", "end").strip())
        self._char_lbl.configure(text=f"{n} character{'s' if n != 1 else ''}")
        self._schedule(600)

    def _on_size(self, val: float) -> None:
        self._size_lbl.configure(text=f"{int(val)} px")
        self._schedule(400)

    def _schedule(self, delay_ms: int) -> None:
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(delay_ms, self._generate)

    def _pick_fg(self) -> None:
        c = colorchooser.askcolor(color=self.fg_color, title="Choose Foreground Color")
        if c[1]:
            self.fg_color = c[1]
            self._fg_btn.configure(
                fg_color=c[1], text=c[1].upper(), text_color=_contrast(c[1]))
            self._generate()

    def _pick_bg(self) -> None:
        c = colorchooser.askcolor(color=self.bg_color, title="Choose Background Color")
        if c[1]:
            self.bg_color = c[1]
            self._bg_btn.configure(
                fg_color=c[1], text=c[1].upper(), text_color=_contrast(c[1]))
            self._generate()

    def _apply_preset(self, fg: str, bg: str) -> None:
        self.fg_color, self.bg_color = fg, bg
        self._fg_btn.configure(fg_color=fg, text=fg.upper(), text_color=_contrast(fg))
        self._bg_btn.configure(fg_color=bg, text=bg.upper(), text_color=_contrast(bg))
        self._generate()

    # ── Core Logic ────────────────────────────────────────────────────────────

    def _generate(self) -> None:
        text = self._text.get("0.0", "end").strip()
        if not text:
            self._status.configure(
                text="⚠  Enter some content above", text_color="orange")
            return

        try:
            self._status.configure(
                text="⏳  Generating…", text_color=("gray50", "gray60"))
            self.update_idletasks()

            qr = qrcode.QRCode(
                error_correction=EC_LEVELS[self._ec_var.get()],
                box_size=10, border=4
            )
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(
                fill_color=self.fg_color, back_color=self.bg_color
            ).convert("RGBA")

            # Store full-resolution image for export
            export_px = int(self._size_var.get())
            self.qr_image = img.resize((export_px, export_px), Image.LANCZOS)

            # Preview: fit inside the right panel dynamically
            panel_w = max(self.winfo_width() - 390, 260)
            panel_h = max(self.winfo_height() - 130, 260)
            preview_px = min(panel_w, panel_h, 520)
            preview = img.resize((preview_px, preview_px), Image.LANCZOS)
            photo = ImageTk.PhotoImage(preview)
            self._preview.configure(image=photo, text="")
            self._preview.image = photo   # keep reference

            self._status.configure(
                text=(
                    f"✓  QR version {qr.version}"
                    f"  •  Export: {export_px}×{export_px} px"
                    f"  •  {len(text)} chars"
                ),
                text_color=("gray45", "gray62")
            )

        except Exception as exc:
            self._status.configure(text=f"✗  {exc}", text_color="#E53935")

    def _save(self, fmt: str) -> None:
        if not self.qr_image:
            messagebox.showwarning("Nothing to save", "Generate a QR code first.")
            return
        ext = "jpg" if fmt == "JPEG" else "png"
        path = filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=[(f"{fmt} Image", f"*.{ext}"), ("All Files", "*.*")],
            initialfile=f"qrcode.{ext}",
            title=f"Save QR Code as {fmt}"
        )
        if path:
            out = self.qr_image.convert("RGB") if fmt == "JPEG" else self.qr_image
            out.save(path, fmt)
            self._status.configure(
                text=f"✓  Saved → {os.path.basename(path)}", text_color="green")

    def _copy(self) -> None:
        if not self.qr_image:
            messagebox.showwarning("Nothing to copy", "Generate a QR code first.")
            return
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                path = tmp.name
            self.qr_image.save(path, "PNG")

            ps = (
                "Add-Type -AssemblyName System.Windows.Forms;"
                "Add-Type -AssemblyName System.Drawing;"
                f'[System.Windows.Forms.Clipboard]::SetImage('
                f'[System.Drawing.Image]::FromFile("{path}"));'
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                capture_output=True, timeout=10
            )
            if result.returncode == 0:
                self._status.configure(text="✓  Copied to clipboard!", text_color="green")
            else:
                raise RuntimeError(result.stderr.decode().strip())
        except Exception as exc:
            messagebox.showerror(
                "Copy Failed",
                f"Could not copy to clipboard:\n{exc}\n\nUse Save PNG instead."
            )

    def _reset(self) -> None:
        self._text.delete("0.0", "end")
        self._text.insert("0.0", "https://example.com")
        self._ec_var.set("High (30% recovery)")
        self._size_var.set(512)
        self._size_lbl.configure(text="512 px")
        self._char_lbl.configure(text="19 characters")
        self._apply_preset("#000000", "#FFFFFF")


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QRApp()
    app.mainloop()
