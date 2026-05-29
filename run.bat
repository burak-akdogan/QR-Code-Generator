@echo off
pip install -r requirements.txt -q 2>nul
start "" pythonw main.py
