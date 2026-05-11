"""
Cross-platform build script for EV Simulator.

Produces a single-file, double-clickable executable for the host OS:
  Windows -> dist/EV_Simulator.exe       (Application icon embedded)
  Linux   -> dist/EV_Simulator           (executable bit set; pinned icon
                                          via the bundled .desktop launcher)

Usage:
    python build.py                # build for the current OS
    python build.py --clean        # remove build/ and dist/ first
    python build.py --no-upx       # disable UPX compression
    python build.py --console      # show a console window (debugging)

PyInstaller is installed on demand if missing.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT       = Path(__file__).resolve().parent
APP_NAME   = "EV_Simulator"
ENTRY      = "main.py"
ICON       = ROOT / "assets" / "image.ico"
ASSETS_DIR = ROOT / "assets"


def log(msg: str) -> None:
    print(f"[build] {msg}", flush=True)


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        log("PyInstaller not found, installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def clean() -> None:
    for d in ("build", "dist"):
        p = ROOT / d
        if p.exists():
            log(f"removing {p}")
            shutil.rmtree(p, ignore_errors=True)
    spec_file = ROOT / f"{APP_NAME}.spec"
    if spec_file.exists():
        spec_file.unlink()


def add_data_arg(src: Path, dest: str) -> str:
    """PyInstaller --add-data uses ';' on Windows and ':' elsewhere."""
    sep = ";" if os.name == "nt" else ":"
    return f"{src}{sep}{dest}"


def build(console: bool, use_upx: bool) -> Path:
    if not (ROOT / ENTRY).exists():
        raise SystemExit(f"entry script not found: {ENTRY}")
    if not ICON.exists():
        raise SystemExit(f"icon not found: {ICON}")

    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name", APP_NAME,
        "--icon", str(ICON),
        "--add-data", add_data_arg(ASSETS_DIR, "assets"),
    ]
    args += ["--console"] if console else ["--windowed"]
    if not use_upx:
        args.append("--noupx")
    args.append(str(ROOT / ENTRY))

    log("running: " + " ".join(args))
    subprocess.check_call(args, cwd=ROOT)

    exe_name = f"{APP_NAME}.exe" if os.name == "nt" else APP_NAME
    out = ROOT / "dist" / exe_name
    if not out.exists():
        raise SystemExit(f"PyInstaller did not produce {out}")

    if os.name != "nt":
        out.chmod(out.stat().st_mode | 0o111)  # ensure executable bit

    return out


def write_linux_desktop_file(exe: Path) -> Path:
    """Create a .desktop launcher so the icon shows up in file managers."""
    desktop = ROOT / "dist" / f"{APP_NAME}.desktop"
    icon_dst = ROOT / "dist" / ICON.name
    shutil.copy2(ICON, icon_dst)
    contents = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name=EV Simulator\n"
        f"Exec={exe}\n"
        f"Icon={icon_dst}\n"
        "Terminal=false\n"
        "Categories=Utility;\n"
    )
    desktop.write_text(contents, encoding="utf-8")
    desktop.chmod(desktop.stat().st_mode | 0o111)
    return desktop


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EV Simulator binary.")
    parser.add_argument("--clean", action="store_true", help="remove build/ and dist/ first")
    parser.add_argument("--no-upx", action="store_true", help="disable UPX compression")
    parser.add_argument("--console", action="store_true", help="keep a console window (debug)")
    args = parser.parse_args()

    log(f"host: {platform.system()} {platform.release()} ({platform.machine()})")
    log(f"python: {sys.version.split()[0]}")

    if args.clean:
        clean()

    ensure_pyinstaller()
    exe = build(console=args.console, use_upx=not args.no_upx)
    log(f"built: {exe}")

    if os.name != "nt":
        desktop = write_linux_desktop_file(exe)
        log(f"desktop launcher: {desktop}")
        log("Tip: double-click the .desktop file, or copy it to ~/.local/share/applications/")
    else:
        log("Done. Double-click dist\\EV_Simulator.exe to launch.")


if __name__ == "__main__":
    main()
