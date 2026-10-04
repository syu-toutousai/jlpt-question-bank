#!/usr/bin/env python3
"""Extract the full written paper from a saved jlpt247.com transcript page.

jlpt247 transcribes the REAL exam verbatim (watupro quiz plugin, server-side
rendered). It does NOT mark correct answers — answers are applied afterwards
from independent answer keys (see merge_keys() in tools/generate_paper.py or
tools/apply_answers.py). Output goes to refs/YYYY-MM_jlpt247.json with the same
shape as fetch_jlptzhen.py so generate_paper.py can consume either source.

Structure (per question):
  <div class='watu-question ' id='question-N'>
    <div id='questionWrap-N' class='... watupro-question-id-<dbid>'>
      <div class='question-content'><div>STEM</div>
      <div class='question-choices'>... label><span>OPT</span></label> ...

Usage:
    python3 tools/fetch_jlpt247.py refs/2024-12_jlpt247_full.html [--dump]
"""
import argparse
import html as H
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "refs"

NUM_RE = re.compile(r"\s*(\d{1,2})\s*\u3000?\s*")
OPT_RE = re.compile(r"\s*(\d)\s*\u3000?\s*")


def text(frag: str) -> str:
    frag = re.sub(r"<br\s*/?>", "\n", frag)
    frag = re.sub(r"</p>", "\n", frag)
    frag = re.sub(r"<[^>]+>", "", frag)
    frag = H.unescape(frag)
    lines = [re.sub(r"[ \t]+", " ", ln).strip(" \u3000") for ln in frag.split("\n")]
    lines = [ln for ln in lines if ln.strip()]
    return "\n".join(lines)


def parse_quiz(html: str) -> list[dict]:
    # map each question start to its most recent preceding section heading
    ids = [(m.end(), m.group(1)) for m in re.finditer(r"<h3>(問題\d+)</h3>", html)]
    questions = []
    passages = {}  # section -> [passage-container texts (in page order)]
    for m in re.finditer(r"class='watu-question ' id='question-(\d+)'", html):
        start = m.start()
        end = html.find("<!-- end questionWrap--></div>", start)
        if end == -1:
            end = html.find("</div>", html.find("questionWrap-", start) + len("questionWrap-")) or start
        part = html[start:end]
        sect = next((s for pos, s in reversed(ids) if pos <= start), "")
        stem_m = re.search(r"question-content'\s*><div>(.*?)</div>", part, re.S)
        stem = text(stem_m.group(1)) if stem_m else ""
        if not stem:
            # 問題7 renders questions with an empty stem (blank inside passage)
            pass
        num_m = NUM_RE.match(stem)
        num = int(num_m.group(1)) if num_m else None
        if num_m:
            stem = stem[num_m.end():].strip(" \u3000\n")
        opts = []
        for lab in re.findall(r"<label[^>]*class=' answer'><span>(.*?)</span></label>", part, re.S):
            t = text(lab)
            om = OPT_RE.match(t)
            opts.append(t[om.end():].strip(" \u3000") if om else t)

        if num is None:
            # a passage container: remember it for this section
            passages.setdefault(sect, []).append(stem)
            continue

        # attach the section passage(s) to the question stem (self-contained)
        passage = "\n\n".join(passages.get(sect, []))
        if passage:
            stem = (passage + "\n\n" + stem) if stem else passage
        # vocab targets: 問題1/3 word in （）, 問題4 leading token
        target = ""
        if sect in ("問題1", "問題3"):
            tg = re.search(r"（([^（）]+)）", stem)
            target = tg.group(1).strip() if tg else ""
        elif sect == "問題4":
            tok = re.match(r"([^\s\u3000]+)", stem)
            target = tok.group(1).strip() if tok else ""

        q = {
            "qid": (re.search(r"watupro-question-id-(\d+)", part).group(1)
                    if re.search(r"watupro-question-id-(\d+)", part) else "jlpt247-" + str(num)),
            "section": sect,
            "instruction": "",
            "stem_html": "",
            "stem": stem,
            "num": num,
            "target": target,
            "options": opts,
            "answer": None,
            "has_correct_marker": False,
            "explanation": "",
            "audio": [],
        }
        questions.append(q)
    return [q for q in questions if q["num"] is not None]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out")
    ap.add_argument("--dump", action="store_true")
    args = ap.parse_args()

    html = Path(args.src).read_text(encoding="utf-8")
    month_hit = re.search(r"(20\d\d)-(\d{2})", Path(args.src).name) \
        or re.search(r"(20\d\d)年(\d{1,2})月", html)
    session = f"{month_hit.group(1)}-{int(month_hit.group(2)):02d}" if month_hit else "????-??"
    qs = parse_quiz(html)
    bundle = {"session": session, "url": args.src, "quiz_id": None,
              "count": len(qs), "questions": qs}
    if args.dump:
        print(json.dumps(bundle, ensure_ascii=False, indent=2))
        return 0
    out = Path(args.out) if args.out else REFS / f"{session}_jlpt247.json"
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  parsed {len(qs)} questions from {session}")
    print(f"  wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())