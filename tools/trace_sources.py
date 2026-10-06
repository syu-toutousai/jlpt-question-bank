#!/usr/bin/env python3
"""特徴句逆引き —— 未詳読解の原文候補を Yahoo! JAPAN 検索で同定（候補・要確認）。

- 入力: analysis/source-traces.json（unknown_passages）＋ n1/past-exams（特徴句抽出）
- 検索: 実 Chrome (Playwright) で Yahoo! JAPAN。1 グループ = 1 検索（pacing 2.5–4s）。
- 出力: 同ファイルに candidate / evidence / confidence="candidate" を追記。
  あわせて著者名の転写異常（2 文字以下・OCR 崩れ）に候補著者を付ける（author_candidate）。

⚠️ 候補は機械提案。断定せず「要確認」ラベルを維持する（本プロジェクトの流儀）。
    python3 tools/trace_sources.py            # 全未詳グループ
    python3 tools/trace_sources.py --limit 10 # 试验
"""
import argparse
import json
import random
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TRACES = ROOT / "analysis" / "source-traces.json"
BANK = ROOT / "n1" / "past-exams"

BAD = re.compile(r"（注|\(注|中略|選びなさい|最もよい|問い|設問|★|（　）|\[\d")


def load_bank():
    by_id = {}
    for f in BANK.rglob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d, dict) and d.get("id"):
            by_id[d["id"]] = d
    return by_id


BANK_BY_ID = load_bank()


def pick_phrase(qid):
    d = BANK_BY_ID.get(qid)
    if not d:
        return ""
    text = (d.get("question") or "").replace("\n", " ")
    cands = []
    for s in re.split(r"(?<=[。！？])", text):
        s = s.strip()
        if 24 <= len(s) <= 90 and not BAD.search(s):
            cands.append(s)
    if not cands:
        return ""
    # 最も長い文（情報量が多い）から 30 字を切り出す
    s = max(cands, key=len)
    return s[:30]


def search(pg, phrase):
    import urllib.parse
    q = '"' + phrase + '"'
    pg.goto("https://search.yahoo.co.jp/search?p=" + urllib.parse.quote(q), timeout=30000)
    pg.wait_for_timeout(2200)
    data = pg.eval_on_selector_all(
        "li a, div.sw-Card a, h3 a",
        "els=>els.map(e=>({t:e.textContent.trim(),s:(e.closest('li,div')||{}).textContent||''}))")
    texts = []
    for d in data:
        t = (d.get("t") or "").strip()
        if t:
            texts.append(t[:160])
        s = (d.get("s") or "").strip()
        if s and s != t:
            texts.append(s[:260])
    return texts


def overlap_ok(text, phrase):
    """证据校验：结果文本与短语至少有 12 字连续重叠，才承认『』候选。"""
    n = len(phrase)
    for L in range(min(n, 24), 11, -1):
        for i in range(0, n - L + 1):
            if phrase[i:i + L] in text:
                return True
    return False


def extract_candidates(texts, phrase):
    books = []
    for t in texts:
        if not overlap_ok(t, phrase):
            continue
        for m in re.findall(r"『([^』]{3,40})』", t):
            if m not in books:
                books.append(m)
    return books[:3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    data = json.loads(TRACES.read_text(encoding="utf-8"))
    groups = data["unknown_passages"]
    if args.limit:
        groups = groups[:args.limit]
    # 旧実行の弱い候補をリセット（precision 優先）
    for g in groups:
        for k in ("candidate_source", "candidate_books", "phrase", "evidence"):
            g.pop(k, None)
        if g.get("confidence") in ("candidate", "none", "error"):
            g.pop("confidence", None)

    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        ctx = b.new_context(locale="ja-JP")
        pg = ctx.new_page()
        done = 0
        for g in groups:
            if g.get("candidate"):
                continue
            phrase = pick_phrase(g["ids"][0])
            if not phrase:
                g["candidate"] = ""
                g["confidence"] = "none"
                continue
            try:
                texts = search(pg, phrase)
                cands = extract_candidates(texts, phrase)
                g["phrase"] = phrase
                g["candidate_source"] = cands[0] if cands else ""
                if cands:
                    ev = next((t for t in texts if overlap_ok(t, phrase) and "『" in t), "")
                    g["evidence"] = ev[:200]
                g["candidate_books"] = cands
                g["confidence"] = "candidate" if cands else "none"
            except Exception as e:
                g["confidence"] = "error"
                g["error"] = str(e)[:80]
            done += 1
            print(f"  [{done}/{len(groups)}] {g['year']}-{g['month']:02d} {g['guess_base']}: "
                  f"{g.get('candidate_source','') or '—'}")
            time.sleep(2.5 + random.random() * 1.5)
        b.close()

    TRACES.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    got = sum(1 for g in data["unknown_passages"] if g.get("candidate_source"))
    print(f"done: {done} searched, {got}/{len(data['unknown_passages'])} with candidates")
    print("⚠️ 候補は要確認（machine-suggested）。")


if __name__ == "__main__":
    main()
