#!/usr/bin/env python3
"""Fetch JLPT N1 listening past-exam pages from trynihongo.
Parse the embedded quizContext JSON (question id/type/text + per-option fraction),
map section 問題N by preceding description node, extract audio URL from the
question text (fall back to the section's description audio for question pairs),
and write refs/<session>_listening_trynihongo.json in the schema consumed by
tools/generate_paper.py (section=問題N, stem=番号, options, answer 1-based).

Usage:
  python3 tools/fetch_listening.py SESSION URL
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "refs"

URL_RE = re.compile(r"https://trynihongo\.com/upload/mooddata/[0-9a-f/]+")


def fetch(url: str, dest: Path = None):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        body = r.read().decode("utf-8", "replace")
    if dest:
        dest.write_text(body, encoding="utf-8")
    return body


SECTION_RE = re.compile(r"問題\s*([1-5Ⅰ-ⅤIV])")
KANA_SECT_RE = [
    (re.compile(r"聴解\s*[（(]?([1-6])[)）]?"), lambda m: int(m.group(1))),
    (re.compile(r"聴解\s*([①-⑥])"), lambda m: "①②③④⑤⑥".index(m.group(1)) + 1),
]


SECTION_RE = re.compile(r"問題\s*([1-5Ⅰ-ⅤIV])")
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
         "Ⅰ": 1, "Ⅱ": 2, "Ⅲ": 3, "Ⅳ": 4, "Ⅴ": 5}


def section_of(text: str):
    m = SECTION_RE.search(text)
    if m:
        tok = m.group(1)
        return ("問題" + str(ROMAN[tok])) if tok in ROMAN else "問題" + tok
    for rx, conv in KANA_SECT_RE:
        m = rx.search(text)
        if m:
            return f"問題{conv(m)}"
    return None


def parse(body: str, session: str) -> list:
    m = re.search(r"var quizContext\s*=\s*(\{.*?\});\s*</script>", body, re.S)
    if not m:
        raise SystemExit("! quizContext not found — page layout changed?")
    ctx = json.loads(m.group(1))
    out = []
    cur_sect = None
    cur_audio = None
    seen = 0
    for q in ctx["questions"]:
        text = (q.get("text") or "").replace("\r", " ").replace("\u00a0", " ")
        audios = URL_RE.findall(text)
        audio = audios[0] if audios else None
        if q["type"] == "description":
            sect = section_of(text)
            if sect:
                cur_sect = sect
            if audio:
                cur_audio = audio
            continue
        if q["type"] != "multichoice":
            continue
        if cur_sect is None:
            continue
        seen += 1
        stem = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text))
        stem = re.sub(r"&nbsp;", "", stem).strip()
        stem = re.split(r"\s+https?://", stem)[0] if re.search(r"\s+https?://", stem) else stem
        stem = stem.strip() or (re.sub(r"&nbsp;", "", q["text"]) or "").strip()
        opts = [a["text"] for a in q["answers"]]
        ans = next((i + 1 for i, a in enumerate(q["answers"])
                    if str(a["fraction"]).startswith("1")), 0)
        out.append({
            "qid": str(q["id"]),
            "section": cur_sect,
            "stem": stem,
            "num": None,
            "options": opts,
            "audio": audio or cur_audio,
            "answer": ans,
            "explanation": "",
        })
    return out


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    session, url = sys.argv[1], sys.argv[2]
    body = fetch(url, dest=(REFS / f"{session}_listening_page.html"))
    qs = parse(body, session)
    missing = [q for q in qs if not q["audio"] or not q["answer"]]
    if missing:
        print(f"! {len(missing)} questions without audio/answer:",
              [q['qid'] for q in missing])
    (REFS / f"{session}_listening_trynihongo.json").write_text(
        json.dumps({"questions": qs}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")
    print(f"{session}: {len(qs)} listening questions -> "
          f"refs/{session}_listening_trynihongo.json")


if __name__ == "__main__":
    main()