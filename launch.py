#!/usr/bin/env python3
"""Cross-platform launcher for Local Chat (Windows, macOS, Linux, WSL). Standard library only.

Creates a virtual environment on first run, installs dependencies, starts Ollama if it
is not running, opens your browser and runs app.py.   Usage: python launch.py
"""
import hashlib
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import venv
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
IS_WIN = os.name == "nt"
PY = VENV / ("Scripts/python.exe" if IS_WIN else "bin/python")
PORT = int(os.environ.get("PORT", 3000))
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
NULL = subprocess.DEVNULL


def is_wsl():
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except OSError:
        return False


def finish(code=0):
    if "--pause" in sys.argv:  # used by desktop shortcuts so the window stays readable
        input("\nPress Enter to close...")
    sys.exit(code)


def ensure_env():
    if sys.version_info < (3, 8):
        print("Python 3.8 or newer is required.")
        finish(1)
    if not PY.exists():
        print("First run: creating virtual environment...")
        try:
            venv.create(VENV, with_pip=True)
        except Exception as e:
            shutil.rmtree(VENV, ignore_errors=True)
            print(f"Could not create the virtual environment: {e}")
            print("Debian/Ubuntu/WSL: sudo apt install python3-venv")
            finish(1)
    req = ROOT / "requirements.txt"
    stamp = VENV / ".req-hash"
    digest = hashlib.sha256(req.read_bytes()).hexdigest()
    if not stamp.exists() or stamp.read_text() != digest:
        print("Installing dependencies...")
        if subprocess.call([str(PY), "-m", "pip", "install", "-q", "-r", str(req)]):
            print("Dependency install failed (check your internet connection).")
            finish(1)
        stamp.write_text(digest)


def ollama_up():
    try:
        urllib.request.urlopen(OLLAMA, timeout=1)
        return True
    except Exception:
        return False


def ensure_ollama():
    if ollama_up():
        return
    local = urlparse(OLLAMA).hostname in ("localhost", "127.0.0.1", "::1")
    exe = shutil.which("ollama")
    if local and exe:
        print("Starting Ollama...")
        kw = {"creationflags": 0x08000000} if IS_WIN else {"start_new_session": True}
        subprocess.Popen([exe, "serve"], stdout=NULL, stderr=NULL, **kw)
        for _ in range(16):
            if ollama_up():
                return
            time.sleep(0.5)
    print(f"Note: Ollama is not reachable at {OLLAMA}.")
    print("Install it from https://ollama.com and run 'ollama serve', or set OLLAMA_URL.")


def open_when_ready(url):
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", PORT), 0.3).close()
            break
        except OSError:
            time.sleep(0.25)
    else:
        return
    if is_wsl():  # open the Windows browser from inside WSL
        for cmd in (["wslview", url], ["explorer.exe", url],
                    ["powershell.exe", "-NoProfile", "-Command", "Start-Process", url]):
            if shutil.which(cmd[0]):
                subprocess.Popen(cmd, stdout=NULL, stderr=NULL)
                return
    webbrowser.open(url)


def main():
    ensure_env()
    ensure_ollama()
    url = f"http://localhost:{PORT}"
    threading.Thread(target=open_when_ready, args=(url,), daemon=True).start()
    proc = subprocess.Popen([str(PY), "app.py"], cwd=ROOT)
    try:
        code = proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()
        code = 0
    print("\nServer stopped.")
    finish(code)


if __name__ == "__main__":
    main()
