#!/usr/bin/env python3
import os
import platform
import subprocess
import sys
import urllib.request
import urllib.error

PLATFORM = 'darwin'
USER_DATA_DIR = '/Users/chajinhyeog/tmp/chrome-debug'
CHROME_EXE = ''

CHROME_FLAGS = [
    "--remote-debugging-port=9222",
    "--remote-debugging-address=127.0.0.1",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-blink-features=AutomationControlled",
    "--disable-features=AutomationControlled",
    "--excludeSwitches=enable-automation",
]


def debug_port_alive() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=1):
            return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def launch() -> None:
    user_data_arg = f"--user-data-dir={USER_DATA_DIR}"

    if PLATFORM == "darwin":
        subprocess.run(
            ["open", "-na", "Google Chrome", "--args", *CHROME_FLAGS, user_data_arg],
            check=True,
        )
    elif PLATFORM in ("windows", "linux"):
        if not CHROME_EXE:
            print(f"chrome executable not configured for {PLATFORM}", file=sys.stderr)
            sys.exit(1)
        kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if PLATFORM == "windows":
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            kwargs["creationflags"] = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True
        subprocess.Popen([CHROME_EXE, *CHROME_FLAGS, user_data_arg], **kwargs)
    else:
        print(f"Unsupported platform: {PLATFORM}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    if debug_port_alive():
        print("Chrome debug already running on port 9222")
        return
    launch()
    print("Chrome launched with debug port 9222")
    print(f"User data dir: {USER_DATA_DIR}")


if __name__ == "__main__":
    main()
