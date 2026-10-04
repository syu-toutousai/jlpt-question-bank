#!/usr/bin/env python3
"""Extract correct answers from trynihongo full-paper pages via its check API.

Adapted from jlpt-n1-question-bank/tools/trynihongo_api.py. Works off the
locally archived pages in refs/trynihongo/, binds a session token from the
live page, then POSTs each option to check_single_question_ajax until the
server marks one correct.

Sessions are parsed from the page slug (only dated N2/N3 pages).
Output: refs/answers_trynihongo/<level>/<session>.json
    {qid: {"box":N, "answer_pos":k, "answer_text":..., "nopts":..., "stem":...}}

Usage:
    python3 tools/extract_trynihongo.py --list
    python3 tools/extract_trynihongo.py --only n2-2023-07
    python3 tools/extract_trynihongo.py --all --sleep 0.4
"""
import argparse
import json
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRY_DIR = ROOT / "refs" / "trynihongo"
OUT_DIR = ROOT / "refs" / "answers_trynihongo"
TMP = Path("/tmp/opencode")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122 Safari/537.36"

MONTHS = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
          "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
          "december": 12}


def parse_session(slug):
    """Return (level, session) for dated N2/N3 pages, else None."""
    m = re.search(r"-n([23])[a-z-]*?-(?:test-)?(january|february|march|april|may|june|july|august|september|october|november|december)-(\d{4})", slug)
    if m:
        return f"n{m.group(1)}", f"{m.group(3)}-{MONTHS[m.group(2)]:02d}"
    m = re.search(r"-n([23])[a-z-]*?-(\d{1,2})-(\d{4})", slug)
    if m:
        return f"n{m.group(1)}", f"{m.group(3)}-{int(m.group(2)):02d}"
    m = re.search(r"-n([23])(\d{1,2})-(\d{4})", slug)   # n312-2024
    if m:
        return f"n{m.group(1)}", f"{m.group(3)}-{int(m.group(2)):02d}"
    return None


def list_pages():
    out = []
    for f in sorted(TRY_DIR.glob("*.html")):
        slug = f.stem
        sess = parse_session(slug)
        if sess:
            out.append((sess[0], sess[1], slug, f))
    return out


def parse_boxes(html):
    real = []
    for mobj in re.finditer(r'id="question-(\d+)"', html):
        seg = html[mobj.end():mobj.end() + 30000]
        j = seg.find('<div class="q-icons-bottom"')
        body = seg[:j] if j > 0 else seg
        if "custom-option" not in body:
            continue
        qid = re.search(r'data-question-id="(\d+)"', body)
        stem_m = re.search(r'question-text[^>]*>(.*?)</div>', body, re.S)
        stem = re.sub(r"<[^>]+>", "", stem_m.group(1)).strip() if stem_m else ""
        opts = []
        for lbl in re.finditer(r'<label class="custom-option[^"]*"(.*?)</label>', body, re.S):
            inner = lbl.group(1)
            aid = re.search(r'data-answer-id="(\d+)"', inner)
            m = re.search(r'answer-text[^>]*>(.*?)</div>', inner, re.S)
            txt = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
            if aid:
                opts.append((int(aid.group(1)), txt))
        if opts:
            real.append({"box": int(mobj.group(1)), "qid": int(qid.group(1)) if qid else None,
                         "stem": stem, "opts": opts})
    return real


def bind(url, ck, bf, timeout=40):
    subprocess.run(["curl", "-s", "-L", "-c", ck, "-A", UA, "-b", ck, "-o", bf, url],
                   capture_output=True, timeout=timeout)
    b = bf.read_text(encoding="utf-8", errors="ignore") if bf.exists() else ""
    m = re.search(r"token:\s*'([^']+)'", b)
    return m.group(1) if m else None


def check(ck, tok, qid, aid, timeout=25):
    r = subprocess.run(
        ["curl", "-s", "-b", ck, "-c", ck, "-A", UA,
         "-H", "X-Requested-With: XMLHttpRequest",
         "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
         "--data", f"_token={tok}&question_id={qid}&answer_id={aid}&selected_fraction=1",
         "https://trynihongo.com/quiz/check_single_question_ajax"],
        capture_output=True, timeout=timeout)
    try:
        return json.loads(r.stdout.decode("utf-8", "ignore"))
    except Exception:
        return {"raw": r.stdout.decode("utf-8", "ignore")[:80]}


def extract(level, session, slug, html_file, sleep=0.4, limit=None, start=1, log=print):
    html = html_file.read_text(encoding="utf-8", errors="ignore")
    boxes = parse_boxes(html)
    url = f"https://trynihongo.com/en/{slug}"
    out_dir = OUT_DIR / level
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{session}.json"
    out = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    log(f"[{level}/{session}] boxes={len(boxes)} url={url}")
    ck = TMP / f"tk_try_{level}_{session}.txt"
    bf = TMP / f"tb_try_{level}_{session}.html"
    tok = None
    done = 0
    for i, bx in enumerate(boxes, start=1):
        if i < start:
            continue
        if limit and done >= limit:
            break
        key = str(i)
        if out.get(key, {}).get("answer_pos") is not None:
            continue
        if not tok:
            tok = bind(url, ck, bf)
            if not tok:
                log("  [!] token bind failed")
                break
        got = None
        for round_ in range(6):
            for idx, (aid, txt) in enumerate(bx["opts"], start=1):
                r = check(ck, tok, bx["qid"], aid)
                d = r.get("data", {})
                if d.get("is_correct") is True:
                    got = (idx, aid, txt)
                    break
                if d.get("is_correct") is False:
                    time.sleep(sleep)
                else:
                    time.sleep(8)
                    tok = bind(url, ck, bf)
                    break
            if got:
                break
        out[key] = {"box": bx["box"], "qid": bx["qid"], "stem": bx["stem"],
                    "answer_pos": got[0] if got else None,
                    "answer_text": got[2] if got else None,
                    "nopts": len(bx["opts"]), "src": "tryni-api"}
        done += 1
        if done % 10 == 0 or got is None:
            log(f"  Q{i}: {'OK ' + str(got[0]) if got else 'MISS'}")
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    solved = sum(1 for v in out.values() if v.get("answer_pos"))
    log(f"[{level}/{session}] solved {solved}/{len(out)} (extracted now: {done})")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--only", help="level-YYYY-MM, e.g. n2-2023-07")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--sleep", type=float, default=0.4)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--shard", help="k/n: process only targets where index %% n == k-1")
    args = ap.parse_args()

    pages = list_pages()
    if args.list:
        for lv, sess, slug, f in pages:
            print(f"{lv}-{sess}  {slug}")
        print(f"total dated pages: {len(pages)}")
        return
    targets = []
    for idx, (lv, sess, slug, f) in enumerate(pages):
        if args.only and args.only not in (f"{lv}-{sess}", sess):
            continue
        if args.shard:
            k, n = (int(x) for x in args.shard.split("/"))
            if idx % n != k - 1:
                continue
        if args.all or args.only or args.shard:
            targets.append((lv, sess, slug, f))
    if not targets:
        print("no target — use --list / --only / --all")
        return
    for lv, sess, slug, f in targets:
        extract(lv, sess, slug, f, sleep=args.sleep, limit=args.limit, start=args.start)


if __name__ == "__main__":
    main()
