#!/usr/bin/env python3
"""Bulk-fetch jlptzhen N1 文字語彙 quizzes for every year-month (2010-07..2025-12).

jlptzhen.com hosts a 25-question 文字語彙 quiz per N1 session (all years, both
months; 2020-07 cancelled). Each question carries the site's correct-answer
marker + Chinese explanation. Save raw HTML to refs/<s>_jlptzhen_vocab.html and
parsed JSON to refs/<s>_vocab_jlptzhen.json (gitignored, never pushed).

Usage: python3 tools/fetch_jlptzhen_allvocab.py            # fetch missing only
       python3 tools/fetch_jlptzhen_allvocab.py --all      # refetch everything
"""
import json, re, sys, time, urllib.request
from pathlib import Path
from fetch_jlptzhen import parse_quiz  # reuse the paper parser

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "refs"
URL_BASE = "https://www.jlptzhen.com/n1%e7%9c%9f%e9%a2%98%e5%9c%a8%e7%ba%bf%e5%81%9a{year}%e5%b9%b4{month}%e6%9c%88%e6%97%a5%e6%9c%ac%e8%af%ad%e8%83%bd%e5%8a%9b%e8%af%95%e9%aa%8c/"

def sessions():
    out = []
    for y in range(2010, 2026):
        for m in ("07", "12"):
            if (y == 2020 and m == "07"):   # exam cancelled worldwide
                continue
            out.append(f"{y}-{m}")
    return out

def fetch(url):
    for i in range(8):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            time.sleep(5 + i * 5)
    raise RuntimeError(f"unreachable: {url}")

def main():
    refetch = "--all" in sys.argv
    summary = []
    for s in sessions():
        y, m = s.split("-")
        raw_path = REFS / f"{s}_jlptzhen_vocab.html"
        if raw_path.exists() and not refetch:
            html = raw_path.read_text(encoding="utf-8")
        else:
            try:
                html = fetch(URL_BASE.format(year=y, month=m))
            except RuntimeError as e:
                print(f"{s}: FAIL {e}")
                summary.append((s, 0, "FAIL"))
                continue
            raw_path.write_text(html, encoding="utf-8")
        qs = parse_quiz(html)
        n = len(qs)
        ok = all(q.get("answer") not in (None, "") for q in qs)
        qi = re.search(r"aysQuizOptions\[['\"](\d+)", html)
        meta = {"session": s, "quiz_id": qi.group(1) if qi else None, "questions": qs}
        json.dump(meta, open(REFS / f"{s}_vocab_jlptzhen.json", "w"), ensure_ascii=False, indent=1)
        summary.append((s, n, "full?" if ok else "ANS-GAP"))
    for s, n, tag in summary:
        print(f"{s}: {n} questions {tag}")

if __name__ == "__main__":
    main()
