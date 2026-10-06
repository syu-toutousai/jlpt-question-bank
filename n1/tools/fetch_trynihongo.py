#!/usr/bin/env python3
"""Download & parse a trynihongo.com full written test page into a transcript.

trynihongo mirrors the official JLPT written paper (文字・語彙/文法/読解) as an
online quiz: one page per session, Japanese question text + options, but NO
correct-answer markers (answers come from independent keys). Sections 問題1..13,
reading passages live in unnumbered description boxes that precede their
questions. Output shape matches fetch_jlpt247.py / fetch_jlptzhen.py so
generate_paper.py can consume it.

Usage:
    python3 tools/fetch_trynihongo.py <url-or-htmlfile> [--out refs/YYYY-MM_trynihongo.json]
    python3 tools/fetch_trynihongo.py --harvest   # download the 28 known session pages
"""
import argparse
import html as H
import json
import os
import re
import subprocess
import sys
import time
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "refs"

# (session, url) for every written-test page in the trynihongo sitemap
PAGES = [
    ("2010-07", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-7-2010-q724"),
    ("2010-12", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-12-2010-q725"),
    ("2011-07", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-7-2011-q726"),
    ("2011-12", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-12-2011-q727"),
    ("2012-07", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-7-2012-q728"),
    ("2012-12", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-12-2012-q729"),
    ("2013-07", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-7-2013-q730"),
    ("2013-12", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-12-2013-q731"),
    ("2014-07", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-7-2014-q732"),
    ("2014-12", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-12-2014-q733"),
    ("2015-07", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-7-2015-q734"),
    ("2015-12", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-12-2015-q735"),
    ("2016-07", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-7-2016-q736"),
    ("2016-12", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-12-2016-q737"),
    ("2017-07", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-7-2017-q738"),
    ("2017-12", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-12-2017-q739"),
    ("2018-07", "https://trynihongo.com/jlpt-vocabulary-grammar-reading-comprehension-test-n1-7-2018-q740"),
    ("2018-12", "https://trynihongo.com/jlpt-vocabulary-grammar-reading-comprehension-test-n1-12-2018-q741"),
    ("2019-07", "https://trynihongo.com/jlpt-vocabulary-grammar-reading-comprehension-test-n1-7-2019-q742"),
    ("2019-12", "https://trynihongo.com/jlpt-vocabulary-grammar-reading-comprehension-test-n1-12-2019-q743"),
    ("2020-12", "https://trynihongo.com/jlpt-vocabulary-grammar-reading-comprehension-test-n1-12-2020-q1221"),
    ("2021-07", "https://trynihongo.com/jlpt-vocabulary-grammar-reading-comprehension-n1-7-2021-q1228"),
    ("2021-12", "https://trynihongo.com/jlpt-vocabulary-grammar-reading-comprehension-test-n1-12-2021-q1311"),
    ("2022-07", "https://trynihongo.com/jlpt-vocabulary-grammar-reading-comprehension-test-n1-7-2022-q1318"),
    ("2022-12", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-12-2022-q1332"),
    ("2023-07", "https://trynihongo.com/jlpt-vocabulary-grammar-reading-comprehension-test-n1-07-2023-q1334"),
    ("2024-07", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-07-2024-q1353"),
    ("2024-12", "https://trynihongo.com/jlpt-test-vocabulary-grammar-reading-comprehension-n1-12-2024-q1355"),
]

SECT_RE = re.compile(r"(?:問題|問[题題])\s*(\d{1,2})")
SECT_FULL = re.compile(r"^(?:問題|問[题題])\s*([①-⑳]|\d{1,2})")
NUM_RE = re.compile(r"\s*(\d{1,2})\s*$")
CIRCLE = {chr(0x2460 + i - 1): i for i in range(1, 21)}  # ①..⑳


def _clean(frag: str) -> str:
    frag = re.sub(r"<br\s*/?>", "\n", frag)
    frag = re.sub(r"</p>", "\n", frag)
    frag = re.sub(r"<[^>]+>", "", frag)
    frag = H.unescape(frag)
    lines = [re.sub(r"[ \t\u3000]+", " ", ln).strip(" \u3000") for ln in frag.split("\n")]
    lines = [ln for ln in lines if ln.strip()]
    return "\n".join(lines)


class BoxParser(HTMLParser):
    """Split the page into its question-box divs (each a top-level box)."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.in_box = False
        self.box = ""
        self.boxes = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div" and "question-box" in a.get("class", ""):
            self.in_box = True
            self.depth = 1
            self.box = "<qb>"
            return
        if self.in_box:
            cls = a.get("class", "")
            if tag == "div":
                self.depth += 1
                self.box += "<d c=%r>" % cls
            else:
                self.box += "<t c=%r>" % cls

    def handle_endtag(self, tag):
        if not self.in_box:
            return
        if tag == "div":
            self.depth -= 1
            self.box += "</d>"
            if self.depth == 0:
                self.boxes.append(self.box)
                self.in_box = False
                self.box = ""
        else:
            self.box += "</t>"

    def handle_data(self, data):
        if self.in_box:
            self.box += data


def _extract_options(box: str) -> list[str]:
    return [_clean(m.group(1)) for m in re.finditer(r"<t c=['\"]answer-text[^'\"]*['\"]>(.*?)</t>", box, re.S)]


def _target_for(sect: str, stem_text: str) -> str:
    target = ""
    if sect in ("問題1", "問題3"):
        tg = re.search(r"（([^（）]+)）", stem_text)
        if not tg:
            first = (stem_text.split("\n")[0] if stem_text else "")
            m = re.match(r"^([\u4e00-\u9fff]+)", first.strip())
            target = m.group(1) if m else ""
        else:
            target = tg.group(1).strip()
    elif sect == "問題4":
        first = (stem_text.split("\n")[0] if stem_text else "")
        m = re.match(r"^([\u4e00-\u9fff]+)", first.strip())
        target = m.group(1) if m else ""
    return target


def _mk(num: int, sect: str, stem_text: str, options: list[str]) -> dict:
    return {
        "qid": "tn-" + str(num),
        "section": sect,
        "instruction": "",
        "stem_html": "",
        "stem": stem_text,
        "num": num,
        "target": _target_for(sect, stem_text),
        "options": options,
        "answer": None,
        "has_correct_marker": False,
        "explanation": "",
        "audio": [],
    }


def parse_old(html: str, boxes: list[str]) -> list[dict]:
    """Pages through 2017-07: desktop nav (class question-target) numbers the
    question boxes; section headers carry 問題N text; reading passages live in
    unnumbered description boxes."""
    labels = []
    i_nav = html.find('question-target">')
    if i_nav != -1:
        seg = html[i_nav:i_nav + 200000]
        for m in re.finditer(r'question-link[^>]*data-value="(\d+)"', seg):
            labels.append(int(m.group(1)))

    questions = []
    cur_sect = ""
    cur_passage = ""
    qn = 0
    for box in boxes:
        has_opts = "custom-option" in box
        box_text = _clean(box)

        if not has_opts:
            # section header or reading passage (unnumbered description box)
            first_line = next((ln.strip() for ln in box_text.split("\n") if ln.strip()), "")
            m = SECT_RE.match(first_line)
            if m:
                cur_sect = "問題%d" % int(m.group(1))
                cur_passage = ""
            elif cur_sect.startswith("問題"):
                txt = box_text.strip()
                if len(txt) >= 8:
                    cur_passage = txt
            continue

        # a numbered question; label comes from the nav order
        if qn >= len(labels):
            break
        num = labels[qn]
        qn += 1

        # stem = box text up to the first option label
        stem = re.split(r"<t c='custom-option", box)[0]
        stem_text = _clean(stem).strip()
        stem_text = re.sub(r"\nQ\s*\d+\s*$", "", stem_text)
        stem_text = re.sub(r"^\d+\s*\n", "", stem_text)

        options = _extract_options(box)
        if not options:
            continue

        lines = stem_text.split("\n")
        if lines and re.search(r"^\s*問題\s*\d+\s*", lines[0]):
            lines[0] = re.sub(r"^\s*問題\s*\d+\s*", "", lines[0])
        stem_text = "\n".join(lines).strip()

        if cur_passage:
            stem_text = cur_passage + "\n\n" + stem_text

        questions.append(_mk(num, cur_sect, stem_text, options))
    return questions


def parse_new(html: str, boxes: list[str]) -> list[dict]:
    """Pages from 2017-12 on: each box carries its own question-number span;
    sections are delimited by info-description boxes starting 問題①..; reading
    passages are inline description boxes (or inside section headers)."""
    questions = []
    cur_sect = ""
    cur_passage = ""
    for box in boxes:
        has_opts = "custom-option" in box
        m_info = re.search(r"<d c=['\"][^'\"]*info-description[^'\"]*['\"]>(.*?)</d>", box, re.S)

        if not has_opts or m_info:
            box_text = _clean(m_info.group(1) if m_info else box)
            txt = box_text.strip()
            mc = SECT_FULL.match(txt)
            if mc:
                dg = mc.group(1)
                n = CIRCLE.get(dg)
                if n is None:
                    n = int(dg)
                cur_sect = "問題%d" % n
                cur_passage = ""
                remainder = re.sub(r"^(?:問題|問[题題])\s*(?:[①-⑳]|\d{1,2})\s*", "", txt)
                remainder = re.sub(r"^[＿\s—-]*", "", remainder)
                if len(remainder) >= 40:
                    cur_passage = remainder
            elif cur_sect.startswith("問題"):
                if len(txt) >= 8:
                    cur_passage = txt
            continue

        # numbered question: number in the .question-number span
        m_num = re.search(r"question-number[^>]*>\s*(\d+)", box)
        if not m_num:
            continue
        num = int(m_num.group(1))

        m_text = re.search(r"<d c=['\"][^'\"]*question-text[^'\"]*['\"]>(.*?)</d>", box, re.S)
        stem_text = _clean(m_text.group(1)).strip() if m_text else ""
        options = _extract_options(box)
        if not options:
            continue

        if cur_passage:
            stem_text = cur_passage + "\n\n" + stem_text
        questions.append(_mk(num, cur_sect, stem_text, options))
    return questions


def parse_quiz(html: str) -> list[dict]:
    bp = BoxParser()
    bp.feed(html)
    boxes = bp.boxes
    if re.search(r"問題\s*[①-⑳]", html) and html.count("question-number") >= 10:
        return parse_new(html, boxes)
    return parse_old(html, boxes)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?", help="url or saved trynihongo html file")
    ap.add_argument("--out")
    ap.add_argument("--harvest", action="store_true", help="download all session pages")
    args = ap.parse_args()

    if args.harvest:
        ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        for session, url in PAGES:
            out = REFS / f"{session}_trynihongo.html"
            if out.exists() and out.stat().st_size > 50000:
                print(f"  skip {session} (already saved)")
                continue
            print(f"  fetch {session} ...", flush=True)
            r = subprocess.run(["curl", "-s", "-L", "-m", "60", "-A", ua, url, "-o", str(out)], capture_output=True)
            if not out.exists() or out.stat().st_size < 50000:
                print(f"  ! failed {session} size={out.stat().st_size if out.exists() else 0}")
            time.sleep(0.5)
        return 0

    src = args.src
    url = None
    if src.startswith("http"):
        url = src
        tmp = REFS / "tmp_trynihongo.html"
        subprocess.run(["curl", "-s", "-L", "-m", "60", "-A", "Mozilla/5.0", src, "-o", str(tmp)], check=True)
        src = str(tmp)
        session = None
    else:
        session = None

    html_text = Path(src).read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"(20\d\d)[-/\s](\d{1,2})", html_text[:4000]) or re.search(r"(20\d\d)[-/\s](\d{1,2})", Path(src).name)
    if session is None and m:
        session = "%s-%02d" % (m.group(1), int(m.group(2)))

    qs = parse_quiz(html_text)
    bundle = {"session": session or "????-??", "url": url or Path(src).name,
              "quiz_id": None, "count": len(qs), "source": "trynihongo", "questions": qs}
    print("  parsed %d questions (%s)" % (len(qs), bundle["session"]))
    if args.out:
        out = Path(args.out)
    else:
        out = REFS / f"{bundle['session']}_trynihongo.json"
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print("  wrote %s" % out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())