#!/usr/bin/env python3
"""Check Aside CLI and install the crawling skill for Codex and Claude Code."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_NAME = "crawling-starter"
SKILL_FILE = Path(__file__).resolve().parents[1] / SKILL_NAME / "SKILL.md"
ASIDE_SETUP_URL = "https://docs.aside.com/help/developers#install-the-cli"
READY = "CRAWLING_STARTER_READY"


def check_aside() -> None:
    aside = shutil.which("aside")
    if aside is None:
        raise RuntimeError(f"Aside CLI를 설치하고 터미널을 다시 열어 주세요. {ASIDE_SETUP_URL}")

    result = subprocess.run(
        [aside, "repl", f'if (typeof openTab === "function") console.log("{READY}");'],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode or READY not in result.stdout.splitlines():
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Aside 앱을 열고 다시 실행해 주세요. {detail}".rstrip())


def install_skill() -> None:
    home = Path.home()
    for skills_dir in (home / ".agents" / "skills", home / ".claude" / "skills"):
        destination = skills_dir / SKILL_NAME / SKILL_FILE.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent) as staging_dir:
            staged_file = Path(staging_dir) / SKILL_FILE.name
            shutil.copyfile(SKILL_FILE, staged_file)
            staged_file.replace(destination)
        print(f"설치 완료 · {destination}")


def main() -> int:
    try:
        check_aside()
        install_skill()
    except subprocess.TimeoutExpired:
        print("Aside CLI 연결 시간이 초과됐어요. Aside 앱을 열고 다시 실행해 주세요.", file=sys.stderr)
        return 1
    except (OSError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    print("새 Codex 또는 Claude Code 세션에서 crawling-starter 스킬을 사용해 주세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
