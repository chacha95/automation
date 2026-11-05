# 크롤링 스타터킷

Aside에서 웹페이지를 열어 목록을 읽고, 필요한 항목을 CSV나 JSON으로 정리하는 스킬이에요. 자바스크립트로 표시되는 목록, 페이지 이동, 더 보기 버튼도 처리할 수 있어요.

## 설치

1. Python 3과 Git이 있는 터미널에서 스킬을 설치해 주세요.

   ```sh
   git clone https://github.com/chacha95/automation && cd automation && python3 scripts/setup.py
   ```

   이미 저장소를 내려받았다면 그 폴더에서 `git pull --ff-only` 후 `python3 scripts/setup.py`를 다시 실행해 주세요. 스킬은 Codex의 `~/.agents/skills/crawling-starter`와 Claude Code의 `~/.claude/skills/crawling-starter`에 설치돼요.

2. 새 Codex 또는 Claude Code 세션에서 **“crawling-starter 스킬 설정을 도와줘”**라고 입력해 주세요. 에이전트가 Aside CLI 연결 상태를 확인하고 첫 크롤링까지 안내해요.
3. Aside가 처음이라면 [Aside 앱을 설치](https://aside.com/download)하고 앱에서 로그인해 주세요. 앱의 [개발자 설정](https://docs.aside.com/help/developers#install-the-cli)에서 CLI도 설치해 주세요. 터미널에서 설치하고 싶다면 에이전트에게 Aside CLI 설치를 요청할 수 있어요.

## 첫 실행

Aside 앱을 설치하고 로그인한 뒤 실행 상태로 두세요. 이후 작업 요청은 평소 쓰던 Codex 또는 Claude Code에서 계속할 수 있어요. 에이전트가 Aside CLI로 브라우저를 사용해요.

> crawling-starter 스킬을 써서 https://quotes.toscrape.com/js/ 첫 페이지의 명언, 저자, 태그를 quotes.csv로 저장해 줘.

명언 10개가 나오면 실제로 수집할 사이트 주소, 필요한 항목, 수집 범위를 알려 주세요. 로그인이나 본인 확인이 필요한 사이트는 Aside에서 직접 진행해 주세요. 설치와 동작은 macOS에서 확인했어요.
