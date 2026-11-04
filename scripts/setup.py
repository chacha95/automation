#!/usr/bin/env python3
"""Install the crawling skill and report whether Aside is ready."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_NAME = "crawling-starter"
SKILL_FILE = Path(__file__).resolve().parents[1] / SKILL_NAME / "SKILL.md"
ASIDE_DOWNLOAD_URL = "https://aside.com/download"
ASIDE_SETUP_URL = "https://docs.aside.com/help/developers#install-the-cli"
READY = "CRAWLING_STARTER_READY"


def check_aside() -> None:
    aside = shutil.which("aside") or shutil.which(str(Path.home() / ".local/bin/aside"))
    if aside is None:
        raise RuntimeError(
            f"Aside를 설치하고 앱에서 로그인해 주세요. {ASIDE_DOWNLOAD_URL}\n"
            f"앱을 열었으면 개발자 설정에서 Aside CLI를 설치해 주세요. {ASIDE_SETUP_URL}"
        )

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
        install_skill()
    except OSError as error:
        print(f"스킬을 설치할 수 없어요. {error}", file=sys.stderr)
        return 1

    try:
        check_aside()
    except subprocess.TimeoutExpired:
        print("Aside CLI 연결 시간이 초과됐어요. Aside 앱을 열고 연결을 확인해 주세요.", file=sys.stderr)
    except (OSError, RuntimeError) as error:
        print(f"크롤링을 시작하려면 Aside 설정이 필요해요. {error}", file=sys.stderr)
    else:
        print("Aside CLI 연결을 확인했어요.")

    print('새 Codex 또는 Claude Code 세션에서 "crawling-starter 스킬 설정을 도와줘"라고 입력해 주세요.')
    return 0


if __name__ == "__main__":
    sys.exit(main())
