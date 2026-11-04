# 크롤링 스타터킷

Aside에서 웹페이지를 열어 목록을 읽고, 필요한 항목을 CSV나 JSON으로 정리하는 스킬이에요. 자바스크립트로 표시되는 목록, 페이지 이동, 더 보기 버튼도 처리할 수 있어요.

## 설치

1. 에이전트를 실행하는 컴퓨터에 [Aside](https://aside.com/download)를 설치하고 열어 주세요. [Aside의 개발자 설정 안내](https://docs.aside.com/help/developers#install-the-cli)에 따라 CLI를 설치한 뒤, 같은 터미널에서 `aside --version`이 실행되는지 확인해 주세요.
2. Python 3과 Git이 있는 터미널에서 실행해 주세요.

   ```sh
   git clone https://github.com/chacha95/automation && cd automation && python3 scripts/setup.py
   ```

   이미 저장소를 내려받았다면 그 폴더에서 `git pull --ff-only` 후 `python3 scripts/setup.py`를 다시 실행해 주세요. 설치는 Codex의 `~/.agents/skills/crawling-starter`와 Claude Code의 `~/.claude/skills/crawling-starter`에 같은 스킬을 복사해요. 이후 새 에이전트 세션을 열어 주세요.

## 첫 실행

> crawling-starter 스킬을 써서 https://quotes.toscrape.com/js/ 첫 페이지의 명언, 저자, 태그를 quotes.csv로 저장해 줘.

명언 10개가 나오면 실제로 수집할 사이트 주소, 필요한 항목, 수집 범위를 알려 주세요. 로그인이나 본인 확인이 필요한 사이트는 Aside에서 직접 진행해 주세요. 설치와 동작은 macOS에서 확인했어요.
