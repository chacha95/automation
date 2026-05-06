#!/usr/bin/env python3
"""Search Naver mail, open each hit, summarize bodies grouped by date.

Attaches to Chrome on CDP port 9222. Reuses existing mail tab if open.
"""
from __future__ import annotations

import argparse
import random
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright

CDP_URL = "http://localhost:9222"
MAIL_URL = "https://mail.naver.com/v2/folders/0/all"
READ_URL = "https://mail.naver.com/v2/read/-1/{mid}"

SEARCH_INPUT_SELECTORS = [
    'input[placeholder*="검색"]',
    'input[type="search"]',
    'input.search_input',
    'input#searchInput',
    'input[name="query"]',
    'input[aria-label*="검색"]',
]

DATE_RE = re.compile(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2}).*?(오전|오후)?\s*(\d{1,2}):(\d{2})")

JITTER_MIN = 2.0
JITTER_MAX = 10.0


def jitter(label: str = "") -> None:
    secs = random.uniform(JITTER_MIN, JITTER_MAX)
    print(f"  ⏳ wait {secs:.1f}s {label}".rstrip(), file=sys.stderr)
    time.sleep(secs)


def find_mail_page(browser):
    for ctx in browser.contexts:
        for p in ctx.pages:
            try:
                if "mail.naver.com" in p.url:
                    return p
            except Exception:
                continue
    return None


def first_visible(page: Page, selectors: list[str], timeout_ms: int = 20000):
    per = max(1500, timeout_ms // len(selectors))
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=per)
            return loc
        except PWTimeout:
            continue
    return None


def goto_mail_search(page: Page, keyword: str) -> None:
    page.bring_to_front()
    needs_nav = ("mail.naver.com" not in page.url) or ("/folders/" not in page.url)
    if needs_nav:
        jitter("(before nav to mail folder)")
        try:
            page.goto(MAIL_URL, wait_until="domcontentloaded", timeout=20000)
        except PWTimeout:
            pass
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except PWTimeout:
        pass

    if "nid.naver.com" in page.url or "login" in page.url.lower():
        raise RuntimeError("Naver not logged in. Log in first.")

    jitter("(before search input)")
    search = first_visible(page, SEARCH_INPUT_SELECTORS, timeout_ms=20000)
    if search is None:
        raise RuntimeError("Search input not found.")
    search.click()
    search.fill("")
    search.type(keyword, delay=30)
    search.press("Enter")
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except PWTimeout:
        pass
    page.wait_for_timeout(1200)


def collect_mail_ids(page: Page, limit: int) -> list[str]:
    page.wait_for_selector("li.mail_item", timeout=15000)
    ids = page.evaluate("""() => {
        const out = [];
        for (const li of document.querySelectorAll('li.mail_item')) {
          const m = (li.className.match(/mail-(\\d+)/) || [])[1];
          if (m) out.push(m);
        }
        return out;
    }""")
    seen = set()
    uniq = []
    for x in ids:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq[:limit]


def parse_datetime(text: str) -> tuple[str, str]:
    """Return (date_key 'YYYY-MM-DD', time 'HH:MM') from view header."""
    m = DATE_RE.search(text)
    if not m:
        return ("unknown", "")
    y, mo, d, ampm, h, mi = m.groups()
    h = int(h)
    if ampm == "오후" and h < 12:
        h += 12
    elif ampm == "오전" and h == 12:
        h = 0
    try:
        dt = datetime(int(y), int(mo), int(d), h, int(mi))
        return (dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M"))
    except ValueError:
        return ("unknown", "")


def squash_lines(text: str, max_lines: int = 5, max_chars: int = 280) -> str:
    lines = []
    for raw in text.splitlines():
        ln = re.sub(r"\s+", " ", raw).strip()
        if not ln:
            continue
        if ln in {"인쇄", "번역", "새 창으로 메일 보기"}:
            continue
        lines.append(ln)
        if len(lines) >= max_lines:
            break
    out = " / ".join(lines)
    if len(out) > max_chars:
        out = out[: max_chars - 1] + "…"
    return out


def read_mail(page: Page, mid: str) -> dict:
    prev_sig = page.evaluate(
        "() => (document.querySelector('.mail_view')?.innerText || '').slice(0, 200)"
    ) or ""
    page.goto(READ_URL.format(mid=mid), wait_until="domcontentloaded", timeout=20000)
    try:
        page.wait_for_function(
            "({mid, prev}) => location.pathname.endsWith('/' + mid) && "
            "(() => { const v = document.querySelector('.mail_view'); "
            "if (!v) return false; "
            "const t = (v.innerText || '').slice(0, 200); "
            "return t.length > 30 && t !== prev; })()",
            arg={"mid": mid, "prev": prev_sig},
            timeout=15000,
        )
    except PWTimeout:
        pass
    page.wait_for_timeout(200)

    data = page.evaluate("""() => {
        const get = (sel) => {
          const el = document.querySelector(sel);
          return el ? el.innerText : '';
        };
        return {
          header: get('.mail_view'),
          body: get('.mail_view_contents'),
        };
    }""")

    header = data.get("header", "") or ""
    body = data.get("body", "") or ""

    subject = ""
    sender = ""
    lines = [l.strip() for l in header.splitlines() if l.strip()]
    for i, ln in enumerate(lines):
        if not subject and ln == "메일 제목" and i + 1 < len(lines):
            subject = lines[i + 1]
        if not sender and ln == "보낸사람" and i + 1 < len(lines):
            sender = lines[i + 1]
        if subject and sender:
            break

    date_key, time_str = parse_datetime(header)
    summary = squash_lines(body)

    return {
        "id": mid,
        "subject": subject,
        "sender": sender,
        "date": date_key,
        "time": time_str,
        "summary": summary,
    }


def run(keyword: str, limit: int) -> int:
    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(CDP_URL)
        page = find_mail_page(browser)
        if page is None:
            ctx = browser.contexts[0] if browser.contexts else browser.new_context()
            page = ctx.new_page()

        goto_mail_search(page, keyword)
        mids = collect_mail_ids(page, limit)
        if not mids:
            print("No results.", file=sys.stderr)
            return 1

        print(f"Keyword: {keyword} | Reading {len(mids)} mail(s)...", file=sys.stderr)
        rows = []
        for i, mid in enumerate(mids, 1):
            jitter(f"(before mail {i}/{len(mids)})")
            print(f"  [{i}/{len(mids)}] mail-{mid}", file=sys.stderr)
            try:
                rows.append(read_mail(page, mid))
            except Exception as e:
                print(f"    skip {mid}: {e}", file=sys.stderr)

        groups: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            groups[r["date"]].append(r)

        out_path = write_markdown(keyword, rows, groups)
        print(f"\nMarkdown written: {out_path}", file=sys.stderr)
        return 0


def write_markdown(keyword: str, rows: list[dict], groups: dict[str, list[dict]]) -> Path:
    out_dir = Path(__file__).resolve().parent.parent / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_kw = re.sub(r"[^\w\-]+", "_", keyword)
    out_path = out_dir / f"naver_mail_{safe_kw}_{ts}.md"

    lines: list[str] = []
    lines.append(f"# 네이버 메일 검색 요약: `{keyword}`")
    lines.append("")
    lines.append(f"- 생성: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 메일 수: {len(rows)}")
    lines.append(f"- 날짜 그룹: {len(groups)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for date in sorted(groups, reverse=True):
        items = sorted(groups[date], key=lambda x: x["time"], reverse=True)
        lines.append(f"## {date} ({len(items)})")
        lines.append("")
        for r in items:
            subject = r["subject"] or "(제목 없음)"
            sender = r["sender"] or "(발신자 없음)"
            time_str = r["time"] or "--:--"
            mail_id = r["id"]
            summary = r["summary"] or "(본문 없음)"
            lines.append(f"### [{time_str}] {subject}")
            lines.append("")
            lines.append(f"- **From:** {sender}")
            lines.append(f"- **Mail ID:** `{mail_id}`")
            lines.append(f"- **Link:** https://mail.naver.com/v2/read/-1/{mail_id}")
            lines.append("")
            lines.append("> " + summary.replace("\n", " "))
            lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keyword", nargs="?", default="넥슨")
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()
    sys.exit(run(args.keyword, args.limit))


if __name__ == "__main__":
    main()
