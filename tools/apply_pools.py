#!/usr/bin/env python3
"""Fill unanswered bank questions from jlptzhen '精品真题' random-pool pages.

Pools are downloaded to refs/pools/*.html. Each pool question carries the
site's correct-answer marker + explanation; questions are real past-exam
items. We match them to the bank by normalized stem (exact/containment/fuzzy)
or by option-set similarity, and only fill questions whose answer is null.

    python3 tools/apply_pools.py
"""
import difflib
import importlib.util
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "past-exams"
POOLS = ROOT / "refs" / "pools"

spec = importlib.util.spec_from_file_location("zhen", ROOT / "tools" / "fetch_jlptzhen.py")
zhen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zhen)

PREFIX = re.compile(r"^(?:阅读问题|問題|问题)\s*\d{1,2}\s*-\s*\d{1,2}\s*")
NUMPFX = re.compile(r"^\s*\d{1,2}\s*[)）]\s*")
PUNCT = re.compile(r"[\s\u3000()（）\[\]【】。、！？!?・…「」『』,.]")


def core(s):
    s = PREFIX.sub("", s or "")
    s = NUMPFX.sub("", s)
    return PUNCT.sub("", s)


def opt_key(opts):
    return "|".join(sorted(core(o) for o in opts if core(o)))


def main():
    entries = []
    harvest = ROOT / "refs" / "pool_questions.json"
    if harvest.exists():
        entries.extend(json.loads(harvest.read_text(encoding="utf-8")))
    for f in sorted(POOLS.glob("*.html")):
        try:
            qs = zhen.parse_quiz(f.read_text(encoding="utf-8", errors="ignore"))
        except Exception as e:
            print(f"! {f.name}: {e}")
            continue
        for q in qs:
            if q.get("answer"):
                entries.append(q)
    print(f"pool questions with answers: {len(entries)}")

    by_stem, by_opts, qlist = {}, {}, []
    for q in entries:
        c = core(q.get("stem", ""))
        if len(c) >= 6:
            by_stem.setdefault(c, q)
            qlist.append(c)
        by_opts.setdefault(opt_key(q.get("options") or []), q)

    updated = 0
    for lv_dir in sorted(BANK.glob("n[2-5]")):
        level = lv_dir.name
        for f in lv_dir.rglob("*.json"):
            d = json.loads(f.read_text(encoding="utf-8"))
            if d.get("answer") is not None:
                continue
            c = core(d.get("question", ""))
            q = by_stem.get(c)
            if q is None and len(c) >= 8:
                for k in qlist:
                    if len(k) >= 8 and (c in k or k in c):
                        q = by_stem[k]
                        break
            if q is None:
                best, bk = 0.0, None
                for k in qlist:
                    r = difflib.SequenceMatcher(None, c, k).ratio()
                    if r > best:
                        best, bk = r, k
                if best >= 0.85:
                    q = by_stem[bk]
            if q is None:
                q = by_opts.get(opt_key(d.get("options") or []))
            if q is None:
                continue
            ans_text = q.get("answer_text") or (
                q["options"][q["answer"] - 1] if q.get("options") else "")
            idx = None
            for i, o in enumerate(d.get("options") or []):
                if o == ans_text or (core(o) and core(o) in core(ans_text)):
                    idx = i + 1
                    break
            if idx is None:
                best, bi = 0.0, None
                for i, o in enumerate(d.get("options") or []):
                    r = difflib.SequenceMatcher(None, core(o), core(ans_text)).ratio()
                    if r > best:
                        best, bi = r, i + 1
                idx = bi if best >= 0.6 else None
            if idx is None:
                continue
            d["answer"] = idx
            d["answer_text"] = d["options"][idx - 1]
            d["answer_source"] = "jlptzhen-pool"
            d["verified"] = {"status": "zhen-pool", "note": ""}
            if not d.get("explanation") and q.get("explanation"):
                d["explanation"] = q["explanation"]
            for s in ("jlptzhen-pool",):
                if s not in d.get("sources", []):
                    d.setdefault("sources", []).append(s)
            f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
            updated += 1
    print(f"filled {updated} questions from pools")


if __name__ == "__main__":
    main()
