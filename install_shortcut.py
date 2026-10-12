#!/usr/bin/env python3
"""Creates a 'Local Chat' launcher with an icon. Works on Windows, macOS, Linux and WSL.
Run once from the project folder:  python install_shortcut.py
Standard library only.
"""
import os
import plistlib
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

NAME = "Local Chat"
ROOT = Path(__file__).resolve().parent
LAUNCH = ROOT / "launch.py"
ASSETS = ROOT / "assets"
PY = sys.executable


def is_wsl():
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except OSError:
        return False


def quiet(cmd):
    """Run an optional helper command; ignore it if it is not installed."""
    try:
        subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


def q(s):  # PowerShell single-quoted string
    return "'" + str(s).replace("'", "''") + "'"


def ps_script(target, args, workdir, icon):
    return f"""$sh = New-Object -ComObject WScript.Shell
foreach ($d in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))) {{
  Remove-Item (Join-Path $d 'Ollama Chat.lnk') -ErrorAction SilentlyContinue
  $s = $sh.CreateShortcut((Join-Path $d '{NAME}.lnk'))
  $s.TargetPath = {q(target)}
  $s.Arguments = {q(args)}
  $s.WorkingDirectory = {q(workdir)}
  $s.IconLocation = {q(icon)}
  $s.Save()
}}
"""


def run_ps1(script, ps="powershell", folder=None, win_path=None):
    """Write the script to a temp .ps1 and run it (avoids command-line quoting problems)."""
    if folder is None:
        fd, name = tempfile.mkstemp(suffix=".ps1")
        os.close(fd)
        path, arg = Path(name), name
    else:
        path, arg = folder / "make-shortcut.ps1", win_path
    path.write_text(script, encoding="utf-8-sig")
    try:
        subprocess.check_call([ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", arg])
    finally:
        path.unlink(missing_ok=True)


def install_windows():
    run_ps1(ps_script(PY, f'"{LAUNCH}" --pause', ROOT, ASSETS / "icon.ico"))
    print("Done. 'Local Chat' is on your Desktop and in the Start menu.")


def install_wsl():
    def ps(cmd):
        return subprocess.check_output(["powershell.exe", "-NoProfile", "-Command", cmd], text=True).strip()

    def wslpath(p, flag):
        return subprocess.check_output(["wslpath", flag, p], text=True).strip()

    distro = os.environ.get("WSL_DISTRO_NAME", "")
    local = ps("$env:LOCALAPPDATA")                      # e.g. C:\Users\me\AppData\Local
    win_dir = local + "\\LocalChat"
    folder = Path(wslpath(win_dir, "-u"))
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy(ASSETS / "icon.ico", folder / "icon.ico")  # Windows needs the icon on its own disk
    dflag = f'-d "{distro}" ' if distro else ""
    args = f'{dflag}--cd "{ROOT}" -- "{PY}" launch.py --pause'
    script = ps_script(r"C:\Windows\System32\wsl.exe", args, win_dir, win_dir + "\\icon.ico")
    run_ps1(script, "powershell.exe", folder, win_dir + "\\make-shortcut.ps1")
    print("Done. 'Local Chat' is on your Windows Desktop and Start menu (it runs inside WSL).")


def install_macos():
    app = Path.home() / "Applications" / f"{NAME}.app"
    shutil.rmtree(app, ignore_errors=True)
    (app / "Contents/MacOS").mkdir(parents=True)
    (app / "Contents/Resources").mkdir()
    shutil.copy(ASSETS / "icon.icns", app / "Contents/Resources/icon.icns")
    with open(app / "Contents/Info.plist", "wb") as f:
        plistlib.dump({"CFBundleName": NAME, "CFBundleDisplayName": NAME, "CFBundleExecutable": "launcher",
                       "CFBundleIdentifier": "io.localchat.app", "CFBundleIconFile": "icon",
                       "CFBundlePackageType": "APPL", "CFBundleVersion": "1.0"}, f)
    cmd = f"cd {shlex.quote(str(ROOT))} && {shlex.quote(PY)} launch.py --pause"
    osa = 'tell application "Terminal"\nactivate\ndo script "%s"\nend tell' % cmd.replace("\\", "\\\\").replace('"', '\\"')
    launcher = app / "Contents/MacOS/launcher"
    launcher.write_text("#!/bin/bash\nosascript -e %s\n" % shlex.quote(osa))
    launcher.chmod(0o755)
    app.touch()
    print(f"Done. Created {app}\nOpen it from Launchpad/Spotlight, or drag it to your Dock.")


# (executable, flag(s) that precede the command to run)
TERMINALS = [("gnome-terminal", ["--"]), ("ptyxis", ["--"]), ("kgx", ["-e"]), ("konsole", ["-e"]),
             ("xfce4-terminal", ["-x"]), ("mate-terminal", ["-x"]), ("tilix", ["-e"]),
             ("alacritty", ["-e"]), ("kitty", []), ("xterm", ["-e"]), ("x-terminal-emulator", ["-e"])]


def find_terminal():
    for exe, flags in TERMINALS:
        path = shutil.which(exe)
        if path:
            return path, flags
    return None, []


def install_linux():
    apps = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    (apps / "ollama-chat.desktop").unlink(missing_ok=True)  # old name
    run = f'"{PY}" "{LAUNCH}" --pause'
    term, flags = find_terminal()
    if term:  # open the terminal ourselves; more reliable than Terminal=true
        exec_line = " ".join([f'"{term}"'] + flags + [run])
        in_terminal = "false"
    else:
        exec_line, in_terminal = run, "true"
        print("WARNING: no terminal emulator found, so the shortcut may do nothing.\n"
              "Install one (Debian/Ubuntu: sudo apt install gnome-terminal) and run this again.")
    entry = apps / "local-chat.desktop"
    entry.write_text(
        "[Desktop Entry]\nType=Application\n"
        f"Name={NAME}\nComment=Private web UI for Ollama\n"
        f'Exec={exec_line}\nPath={ROOT}\nIcon={ASSETS / "icon.svg"}\n'
        f"Terminal={in_terminal}\nCategories=Utility;Development;\n")
    entry.chmod(0o755)
    try:
        desk = subprocess.check_output(["xdg-user-dir", "DESKTOP"], text=True).strip()
    except Exception:
        desk = str(Path.home() / "Desktop")
    if Path(desk).is_dir():
        copy = Path(desk) / "local-chat.desktop"
        shutil.copy(entry, copy)
        copy.chmod(0o755)
        quiet(["gio", "set", str(copy), "metadata::trusted", "true"])
    quiet(["update-desktop-database", str(apps)])
    print(f"Done. Shortcut file: {entry}")
    print("Search for 'Local Chat' in your app menu (Desktop copy: right-click > Allow Launching).")
    print(f"If clicking does nothing, test it with:  gio launch {entry}")


def main():
    for f in (LAUNCH, ASSETS / "icon.ico", ASSETS / "icon.icns", ASSETS / "icon.svg"):
        if not f.exists():
            sys.exit(f"Missing {f}. Run this from the project folder.")
    if os.name == "nt":
        install_windows()
    elif sys.platform == "darwin":
        install_macos()
    elif is_wsl():
        install_wsl()
    else:
        install_linux()


if __name__ == "__main__":
    main()
