# QR Code Generator

A modern, lightweight desktop QR code generator built with Python and CustomTkinter. Supports custom colors, presets, error correction levels, and exports to PNG/JPG — all in a clean dark/light UI.

---

## Screenshot

> Run the app and generate your first QR code to see it in action.
<img width="1100" height="749" alt="image" src="https://github.com/user-attachments/assets/aa907266-b85e-4bdd-9dac-3703dc8e3a0d" />


---

## Features

- **Instant preview** — QR code renders automatically as you type
- **Custom colors** — Pick any foreground and background color
- **Quick presets** — Classic, Ocean, Forest, Violet, Ruby, Sunset
- **Error correction** — Low (7%) · Medium (15%) · Quartile (25%) · High (30%)
- **Export size control** — 128 px to 2048 px via slider
- **Save as PNG or JPG**
- **Copy to clipboard** — One click, no save needed
- **Dark / Light mode** toggle
- **Responsive sidebar** — Generate button always visible, content scrolls invisibly

---

## Requirements

- Windows 10 / 11
- Python 3.11+
- pip packages (installed automatically by `run.bat`):
  - `customtkinter >= 5.2.2`
  - `Pillow >= 10.0.0`
  - `qrcode[pil] >= 7.4.2`

---

## Quick Start

### Option 1 — Run from source (double-click)

```
run.bat
```

Installs dependencies silently, then launches the app. No console window.

### Option 2 — Run manually

```bash
pip install -r requirements.txt
python main.py
```

---

## Build a Standalone .EXE

To create a single `.exe` you can share with anyone (no Python needed on their PC):

```
build.bat
```

The output will be at:

```
dist\QR Code Generator.exe
```

> Build takes 1–2 minutes. Requires an internet connection on first run to install PyInstaller.

---

## Project Structure

```
QR-Code-Generator/
├── main.py            # Application source code
├── requirements.txt   # Python dependencies
├── run.bat            # One-click launcher (no console)
├── build.bat          # Builds a standalone .exe via PyInstaller
├── .gitignore         # Excludes build artifacts from git
└── LICENSE            # MIT License
```

---

## How It Works

1. Enter any text or URL in the **Content** box
2. Choose **Error Correction** level (higher = more damage resistant)
3. Set the **Export Size** with the slider
4. Pick **Colors** manually or use a **Quick Preset**
5. Hit **⚡ Generate QR Code** — or it auto-generates as you type
6. **Save PNG / JPG** or **Copy** to clipboard

---

## License

MIT License — see [LICENSE](LICENSE) for details.  
© 2026 Burak Akdogan
