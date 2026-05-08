#!/usr/bin/env python3
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEBUG_PROFILE_DIR = Path.home() / "tmp" / "chrome-debug"
PROFILE_IGNORE = shutil.ignore_patterns(
    "Cache",
    "Code Cache",
    "GPUCache",
    "ShaderCache",
    "Service Worker",
    "Singleton*",
    "*.lock",
    "lockfile",
    "CrashpadMetrics*",
    "Crashpad",
)

CHROME_FLAGS = [
    "--remote-debugging-port=9222",
    "--remote-debugging-address=127.0.0.1",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-blink-features=AutomationControlled",
    "--disable-features=AutomationControlled",
    "--excludeSwitches=enable-automation",
]


def detect_windows() -> tuple[str, str]:
    user_data_dir = ""
    chrome_exe = ""

    data_candidates = []
    if localappdata := os.environ.get("LOCALAPPDATA"):
        data_candidates.append(Path(localappdata) / "Google" / "Chrome" / "User Data")
    if userprofile := os.environ.get("USERPROFILE"):
        data_candidates.append(
            Path(userprofile) / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
        )
    win_user = os.environ.get("USERNAME") or os.environ.get("USER")
    if win_user:
        data_candidates.append(
            Path(f"C:/Users/{win_user}/AppData/Local/Google/Chrome/User Data")
        )

    for c in data_candidates:
        if c.is_dir():
            user_data_dir = str(c)
            break

    exe_candidates = [
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
    ]
    if localappdata := os.environ.get("LOCALAPPDATA"):
        exe_candidates.append(
            Path(localappdata) / "Google" / "Chrome" / "Application" / "chrome.exe"
        )
    if pf_x86 := os.environ.get("ProgramFiles(x86)"):
        exe_candidates.append(
            Path(pf_x86) / "Google" / "Chrome" / "Application" / "chrome.exe"
        )
    if pf := os.environ.get("PROGRAMFILES"):
        exe_candidates.append(
            Path(pf) / "Google" / "Chrome" / "Application" / "chrome.exe"
        )

    for c in exe_candidates:
        if c.is_file():
            chrome_exe = str(c)
            break

    return user_data_dir, chrome_exe


def detect_linux() -> tuple[str, str]:
    user_data_dir = ""
    home = Path.home()
    for c in (home / ".config" / "google-chrome", home / ".config" / "chromium"):
        if c.is_dir():
            user_data_dir = str(c)
            break
    chrome_exe = shutil.which("google-chrome") or shutil.which("chromium") or ""
    return user_data_dir, chrome_exe


def detect() -> tuple[str, str, str]:
    system = platform.system()
    if system == "Darwin":
        return (
            "darwin",
            str(Path.home() / "Library" / "Application Support" / "Google" / "Chrome"),
            "",
        )
    if system == "Windows":
        ud, exe = detect_windows()
        return "windows", ud, exe
    if system == "Linux":
        ud, exe = detect_linux()
        return "linux", ud, exe
    print(f"Unsupported OS: {system}", file=sys.stderr)
    sys.exit(1)


def clone_profile(src: Path) -> Path:
    dest = DEBUG_PROFILE_DIR
    if dest.exists():
        print(f"Debug profile exists, reusing: {dest}")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Cloning profile {src} -> {dest}")
    shutil.copytree(src, dest, ignore=PROFILE_IGNORE, symlinks=True)
    return dest


def debug_port_alive() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=1):
            return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def launch(plat: str, user_data_dir: str, chrome_exe: str) -> None:
    user_data_arg = f"--user-data-dir={user_data_dir}"

    if plat == "darwin":
        subprocess.run(
            ["open", "-na", "Google Chrome", "--args", *CHROME_FLAGS, user_data_arg],
            check=True,
        )
        return

    if plat in ("windows", "linux"):
        if not chrome_exe:
            print(f"chrome executable not configured for {plat}", file=sys.stderr)
            sys.exit(1)
        kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if plat == "windows":
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            kwargs["creationflags"] = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True
        subprocess.Popen([chrome_exe, *CHROME_FLAGS, user_data_arg], **kwargs)
        return

    print(f"Unsupported platform: {plat}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    plat, user_data_dir, chrome_exe = detect()

    if not user_data_dir or not Path(user_data_dir).is_dir():
        print(f"Chrome user data directory not found on {plat}", file=sys.stderr)
        sys.exit(1)

    if plat != "darwin" and not chrome_exe:
        print(f"chrome executable not found on {plat}", file=sys.stderr)
        sys.exit(1)

    debug_dir = clone_profile(Path(user_data_dir))

    print(f"Platform: {plat}")
    print(f"Source profile: {user_data_dir}")
    print(f"Debug profile: {debug_dir}")
    if chrome_exe:
        print(f"Chrome exe: {chrome_exe}")

    if debug_port_alive():
        print("Chrome debug already running on port 9222")
        return

    launch(plat, str(debug_dir), chrome_exe)
    print("Chrome launched with debug port 9222")


if __name__ == "__main__":
    main()
