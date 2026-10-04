#!/usr/bin/env python3
"""Build the N2-N5 question bank from parsed jlptzhen/jlpt247 bundles + keys.

Inputs : parsed/YYYY-MM_{jlptzhen,jlpt247}_<level>.json
         refs/answerkeys/YYYY-MM_<level>.json (optional full keys)
Outputs: past-exams/<level>/<year>/<month>/<type>/<NN>.json
         past-exams/manifest.json  (coverage + answer stats)

Answer merge strategy: jlpt247 transcripts carry no answers; jlptzhen pages
carry answers for 問題1-5 (sometimes the full paper). Answers are matched by
(section, index-within-section) between the two. Questions with no answer are
kept with answer: null so coverage stays honest.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARSED = ROOT / "parsed"
OUT = ROOT / "past-exams"
KEYS = ROOT / "refs" / "answerkeys"

SECT_RE = re.compile(r"問題\s*(\d{1,2})")
ZHEN_LABEL = re.compile(r"问题\s*(\d{1,2})\s*-\s*(\d{1,2})")


def guess_type(section: str, instruction: str, stem: str) -> str:
    t = f"{instruction or ''} {stem or ''}"
    if "読み方" in t:
        return "vocab-reading"
    if "漢字で書" in t:
        return "vocab-writing"
    if "意味が最も近い" in t:
        return "vocab-paraphrase"
    if "使い方" in t:
        return "vocab-usage"
    if "並べ替え" in t or "★" in t or "___" in t and "★" in t:
        return "grammar-composition"
    if "文章" in t:
        return "grammar-passage"
    if re.search(r"（\s*）に入れる", t) or "（　　）に入れる" in t or "に入れるのに" in t:
        return f"{section.lower()}-fill" if section else "grammar-fill"
    if section == "問題1":
        return "reading"
    return (section or "unknown").lower()


def norm_num(section):
    m = SECT_RE.search(section or "")
    return int(m.group(1)) if m else None


def core(s: str) -> str:
    """Normalize a stem for cross-source matching."""
    s = ZHEN_LABEL.sub("", s or "")
    s = re.sub(r"[\s\u3000()（）\[\]【】。、！？!?・…「」『』,.]", "", s)
    return s


def build_zhen_index(zhen):
    zmap = {}
    zlist = []
    for q in zhen["questions"] if zhen else []:
        c = core(q.get("stem", ""))
        if len(c) >= 4:
            zmap.setdefault(c, q)
            zlist.append((c, q))
    return zmap, zlist


def lookup_zhen(stem, zmap, zlist):
    c = core(stem)
    if not c:
        return None
    if c in zmap:
        return zmap[c]
    if len(c) >= 8:
        for zc, zq in zlist:
            if len(zc) >= 8 and (c in zc or zc in c):
                return zq
    return None


def main():
    OUT.mkdir(exist_ok=True)
    man = {}
    key_index = {}
    if KEYS.exists():
        for f in KEYS.glob("*.json"):
            m = re.match(r"(\d{4}-\d{2})_(n[2-5])\.json", f.name)
            if m:
                key_index[f"{m.group(2)}/{m.group(1)}"] = json.loads(f.read_text(encoding="utf-8"))

    sessions = defaultdict(dict)
    for f in sorted(PARSED.glob("*.json")):
        m = re.match(r"(\d{4}-\d{2})_(jlptzhen|jlpt247)_(n[2-5])\.json", f.name)
        if m:
            d = json.loads(f.read_text(encoding="utf-8"))
            sessions[f"{m.group(3)}/{m.group(1)}"][m.group(2)] = d

    totals = defaultdict(int)
    for key in sorted(sessions):
        level, session = key.split("/")
        year, month = session.split("-")
        srcs = sessions[key]
        zhen = srcs.get("jlptzhen")
        j247 = srcs.get("jlpt247")

        # zhen answer index: normalized stem -> question
        zmap, zlist = build_zhen_index(zhen)

        # base list
        if j247 and j247["questions"] and (not zhen or len(zhen["questions"]) < 50):
            base = [dict(q, _src="jlpt247") for q in j247["questions"]]
        elif zhen:
            base = [dict(q, _src="jlptzhen") for q in zhen["questions"]]
        elif j247:
            base = [dict(q, _src="jlpt247") for q in j247["questions"]]
        else:
            continue

        counters = defaultdict(int)
        files = []
        answered = 0
        for q in base:
            sec = norm_num(q.get("section"))
            counters[sec] += 1
            qno = counters[sec]
            ans, exp, target, ans_src = q.get("answer"), q.get("explanation", ""), q.get("target", ""), None
            if ans is None and zhen:
                zq = lookup_zhen(q.get("stem", ""), zmap, zlist)
                if zq:
                    ans, exp, target = zq.get("answer"), zq.get("explanation", ""), zq.get("target", "")
                    ans_src = "jlptzhen"
                    if not q.get("instruction"):
                        q["instruction"] = zq.get("instruction", "")
            elif ans is not None:
                ans_src = q["_src"]
            key_ans = None
            k = key_index.get(key)
            if k:
                key_ans = k.get(str(qno)) or k.get(f"{sec}-{qno}")
                if key_ans and ans is None:
                    ans, ans_src = key_ans, "answerkey"
            qtype = guess_type(q.get("section", ""), q.get("instruction", ""), q.get("stem", ""))
            stem = q.get("stem", "")
            stem = re.sub(r"^\.", "", stem).strip()
            jp_sec = f"問題{sec}" if sec else q.get("section", "")
            src_label = f"JLPT {level.upper()} {year}年{int(month)}月"
            rec = {
                "id": f"{year}-{int(month):02d}-{level}-s{(sec or 0):02d}-{qtype}-{qno:02d}",
                "level": level, "year": int(year), "month": int(month),
                "section": jp_sec, "type": qtype, "number": qno,
                "question": stem,
                "target": target or q.get("target", ""),
                "options": q.get("options", []),
                "answer": ans,
                "answer_text": q["options"][ans - 1] if isinstance(ans, int) and 0 < ans <= len(q.get("options", [])) else "",
                "explanation": exp or "",
                "source": f"{src_label} 問題{sec}({qno})" if sec else src_label,
                "sources": [s for s in (q.get("_src"),) if s] + ([ans_src] if ans_src and ans_src != q.get("_src") else []),
                "answer_source": ans_src,
                "verified": {"status": "parsed" if ans is not None else "transcript-only", "note": ""},
            }
            if ans is not None:
                answered += 1
            d = OUT / level / year / f"{int(month):02d}" / f"s{(sec or 0):02d}-{qtype}"
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{qno:02d}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            files.append(rec["id"])

        man[key] = {
            "level": level, "session": session,
            "questions": len(base), "answered": answered,
            "sources": sorted(s for s in ("jlptzhen", "jlpt247") if s in srcs),
        }
        totals[level] += len(base)
        print(f"{key}: {len(base)}Q, {answered} answered -> past-exams/{level}/{year}/{int(month):02d}/", flush=True)

    (OUT / "manifest.json").write_text(
        json.dumps({"sessions": man, "totals": dict(totals)}, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")
    print("\ntotals:", dict(totals))
    print("total questions:", sum(totals.values()),
          "answered:", sum(v["answered"] for v in man.values()))


if __name__ == "__main__":
    main()
