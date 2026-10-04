#!/usr/bin/env python3
"""
jlptzhen.com JLPT paper extractor.

Fetches a jlptzhen quiz page (or reads a local saved copy) and parses every
question into structured JSON, including the site's own correct-answer marker
and its Chinese explanation.  Writes the result to `refs/YYYY-MM_full_jlptzhen.json`
(plaintext, gitignored — never pushed).

Quiz-maker renders the whole paper server-side: each question is a
`<div class='step' data-question-id='...'>` containing:
  - .ays-quiz-category-description-box : section heading (問題1, 問題2, ...)
  - .ays_quiz_question                  : stem (passage repeated per step,
                                          blanks as 【N】, underlined word in <u>)
  - .ays-quiz-answers/.ays-field        : 3-4 options with a hidden
                                          `ays_answer_correct[]` input (value='1' = correct)
  - .ays_questtion_explanation          : explanation (Chinese)

Usage:
    python3 tools/fetch_jlptzhen.py https://www.jlptzhen.com/.../         # fetch + parse
    python3 tools/fetch_jlptzhen.py refs/2024-07_jlptzhen_full.html       # parse saved copy
    python3 tools/fetch_jlptzhen.py refs/2024-07_jlptzhen_full.html --dump  # pretty-print
"""

import argparse
import base64
import html as H
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "refs"


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def scrape_quiz_id(html: str) -> int | None:
    m = re.search(r"aysQuizOptions\[['\"](\d+)['\"]\]", html)
    m = m or re.search(r"data-question-id='(\d+)'", html)
    return int(m.group(1)) if m else None


def clean_text(frag: str) -> str:
    """HTML fragment -> plain text, preserving line structure."""
    frag = re.sub(r"<br\s*/?>", "\n", frag)
    frag = re.sub(r"</p>", "\n", frag)
    frag = re.sub(r"<[^>]+>", "", frag)
    frag = H.unescape(frag)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in frag.split("\n")]
    return "\n".join(ln for ln in lines if ln).strip()


def clean_options(label: str) -> str:
    """'1) 1) ふはい' -> 'ふはい'  (strip repeated 'N)' prefixes)."""
    s = clean_text(label)
    s = re.sub(r"^\s*(?:\(\d\)|\d[)．.])\s*", "", s).strip()
    s = re.sub(r"^\s*\d[)．.]\s*", "", s).strip()
    return s


def parse_quiz(html: str) -> list[dict]:
    questions = []
    steps = re.split(r"<div class='step\s*'", html)
    for part in steps[1:]:
        qid = re.search(r"data-question-id='(\d+)'", part)
        if not qid:
            continue
        q = {"qid": qid.group(1)}

        head = re.search(
            r"ays-quiz-category-description-box\s*['\"]?[^>]*>(.*?)</div>", part, re.S
        )
        if head:
            txt = clean_text(head.group(1))
            m = re.match(r"(問題\d+)\s*\u00a0?(.*)", txt, re.S)
            q["section"] = m.group(1) if m else ""
            q["instruction"] = m.group(2).strip() if m else txt

        stem = re.search(
            r"class='ays_quiz_question'[^>]*>(.*?)(?=<div class='ays-quiz-answers)",
            part, re.S,
        )
        root = re.search(
            r"class='ays_quiz_question'[^>]*>(.*?)(?=<div class='ays-quiz-answers)",
            part, re.S,
        )
        raw_stem = (root or stem).group(1) if (root or stem) else ""
        audios = sorted(set(re.findall(r"https://[^'\"]+\.mp3", raw_stem)))
        q["audio"] = audios
        stem_pkg = re.sub(r"<audio[^>]*>.*?</audio>", "", raw_stem, flags=re.S)
        q["stem_html"] = stem_pkg.strip()
        q["stem"] = clean_text(stem_pkg)
        m = re.search(r"^\s*(\d{1,2})[.．、](?=\s|\u3000)", q["stem"])
        q["num"] = int(m.group(1)) if m else None
        if q["num"]:
            q["stem"] = re.sub(r"^\s*\d{1,2}[.．、]\s*", "", q["stem"], count=1)
        target = re.search(r"<u[^>]*>(.*?)</u>", stem_pkg, re.S)
        if target:
            q["target"] = clean_text(target.group(1))

        fields = []
        ans_box = re.search(
            r"ays-quiz-answers[^>]*>(.*?)(?=<div class='ays_buttons_div')", part, re.S
        )
        if ans_box:
            for fbody in re.split(r"<div class='ays-field[^']*'>", ans_box.group(1))[1:]:
                fbody = fbody.split("</div>", 1)[0]
                fields.append(fbody)
        options, answers = [], []
        for body in fields:
            hit = re.search(r"ays_answer_correct\[\]' value='(\d)'", body)
            answers.append(hit.group(1) == "1" if hit else False)
            lab = re.search(r"<label[^>]*>(.*?)</label>", body, re.S)
            options.append(clean_options(lab.group(1)) if lab else "")
        q["options"] = options
        q["answer"] = None
        for i, c in enumerate(answers):
            if c:
                q["answer"] = i + 1
                break
        q["has_correct_marker"] = any(answers)

        expl = re.search(
            r"ays_questtion_explanation[^>]*>(.*?)</div>\s*</div>\s*</div>", part, re.S
        )
        q["explanation"] = clean_text(expl.group(1)) if expl else ""

        questions.append(q)
    return questions


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src", help="quiz URL or local html file")
    ap.add_argument("--out", help="refs/ output filename (default auto)")
    ap.add_argument("--dump", action="store_true", help="pretty-print parsed questions")
    args = ap.parse_args()

    if args.src.startswith("http"):
        html = fetch(args.src)
        url = args.src
        month_hit = re.search(r"(20\d\d)年(\d{1,2})月", url)
    else:
        html = Path(args.src).read_text(encoding="utf-8")
        url = ""
        month_hit = re.search(r"(20\d\d)-(\d{2})", Path(args.src).name)

    quiz_id = scrape_quiz_id(html)
    qs = parse_quiz(html)
    if not qs:
        print("No questions parsed. Is this a jlptzhen quiz page?", file=sys.stderr)
        return 1

    if month_hit:
        session = f"{month_hit.group(1)}-{int(month_hit.group(2)):02d}"
    else:
        session = "????-??"

    bundle = {
        "session": session,
        "url": url or args.src,
        "quiz_id": quiz_id,
        "count": len(qs),
        "questions": qs,
    }

    if args.dump:
        print(json.dumps(bundle, ensure_ascii=False, indent=2))
        return 0

    out = args.out or f"{session}_full_jlptzhen.json"
    out_path = REFS / out if not Path(out).is_absolute() else Path(out)
    out_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  parsed {len(qs)} questions from {session} (quiz_id={quiz_id})")
    print(f"  wrote {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())