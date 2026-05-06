#!/usr/bin/env python3
"""Attach to Chrome on port 9222, search Naver mail for a keyword, print hits."""
from __future__ import annotations

import sys
from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright

CDP_URL = "http://localhost:9222"
MAIL_URL = "https://mail.naver.com/v2/folders/0/all"
KEYWORD = "넥슨"

SEARCH_INPUT_SELECTORS = [
    'input[placeholder*="검색"]',
    'input[type="search"]',
    'input.search_input',
    'input#searchInput',
    'input[name="query"]',
    'input[aria-label*="검색"]',
]

ROW_SELECTORS = [
    'ul.mail_list li',
    'li.mail_item',
    'div[role="listitem"]',
    'tr.mail_item',
    'ol li[data-mail-sn]',
]


def find_mail_page(browser) -> Page | None:
    for ctx in browser.contexts:
        for p in ctx.pages:
            try:
                if "mail.naver.com" in p.url:
                    return p
            except Exception:
                continue
    return None


def first_visible(page: Page, selectors: list[str], timeout_ms: int = 15000):
    deadline = page.context._impl_obj  # noqa: just to keep import use
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout_ms // len(selectors))
            return loc
        except PWTimeout:
            continue
    return None


SKIP_LABELS = {
    "보낸 사람", "메일 제목", "메일 본문 미리보기 열기", "받는 사람",
    "메일 본문", "첨부파일 있음", "중요", "별표 표시", "선택",
}


def _clean(line: str) -> str:
    return line.strip().strip("[]").strip()


def extract_results(page: Page) -> list[dict]:
    rows = None
    for sel in ROW_SELECTORS:
        loc = page.locator(sel)
        if loc.count() > 0:
            rows = loc
            break
    if rows is None:
        return []

    results: list[dict] = []
    n = min(rows.count(), 50)
    for i in range(n):
        row = rows.nth(i)
        try:
            text = row.inner_text(timeout=2000).strip()
        except Exception:
            continue
        if not text:
            continue
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        sender = subject = folder = date = ""
        for j, ln in enumerate(lines):
            if ln == "보낸 사람" and j + 1 < len(lines):
                sender = lines[j + 1]
            elif ln == "메일 제목" and j + 1 < len(lines):
                subject = lines[j + 1]
            elif ln.startswith("[") and ln.endswith("]") and not folder:
                folder = _clean(ln)

        for ln in reversed(lines):
            if any(ch.isdigit() for ch in ln) and (":" in ln or "." in ln or "-" in ln):
                if ln not in SKIP_LABELS and len(ln) <= 20:
                    date = ln
                    break

        if not (sender or subject):
            continue

        results.append({
            "index": i + 1,
            "sender": sender,
            "subject": subject,
            "folder": folder,
            "date": date,
        })
    return results


def run() -> int:
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(CDP_URL)
        page = find_mail_page(browser)
        if page is None:
            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
            page = ctx.new_page()

        page.bring_to_front()
        if "mail.naver.com" not in page.url:
            try:
                page.goto(MAIL_URL, wait_until="domcontentloaded", timeout=20000)
            except PWTimeout:
                pass

        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except PWTimeout:
            pass

        if "nid.naver.com" in page.url or "login" in page.url.lower():
            print("Not logged in. Log into Naver in this Chrome first.", file=sys.stderr)
            return 2

        search = first_visible(page, SEARCH_INPUT_SELECTORS, timeout_ms=20000)
        if search is None:
            print("Search input not found. Naver may have changed selectors.", file=sys.stderr)
            page.screenshot(path="/tmp/naver_mail_debug.png", full_page=True)
            return 3

        search.click()
        search.fill("")
        search.type(KEYWORD, delay=30)
        search.press("Enter")

        try:
            page.wait_for_load_state("networkidle", timeout=20000)
        except PWTimeout:
            pass
        page.wait_for_timeout(1500)

        results = extract_results(page)
        print(f"URL: {page.url}")
        print(f"Keyword: {KEYWORD}")
        print(f"Hits: {len(results)}")
        print("-" * 60)
        for r in results:
            print(f"[{r['index']:>2}] {r['date']:<16} | {r['folder']:<10} | "
                  f"{r['sender']:<20} | {r['subject']}")

        return 0 if results else 1


if __name__ == "__main__":
    sys.exit(run())
