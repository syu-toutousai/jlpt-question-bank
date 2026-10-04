#!/usr/bin/env python3
"""Merge trynihongo-extracted answers (refs/answers_trynihongo/) into the bank.

Matching: normalized stem core (same normalizer as build_bank) with a
difflib fallback; option text matched to bank options by exact/containment/
fuzzy. Only fills questions whose `answer` is still null. Idempotent; re-run
after the extractor makes progress.

    python3 tools/apply_trynihongo.py
"""
import difflib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANSWERS = ROOT / "refs" / "answers_trynihongo"
BANK = ROOT / "past-exams"

ZHEN_LABEL = re.compile(r"问题\s*\d{1,2}\s*-\s*\d{1,2}")
PUNCT = re.compile(r"[\s\u3000()（）\[\]【】。、！？!?・…「」『』,.]")


def core(s):
    s = ZHEN_LABEL.sub("", s or "")
    return PUNCT.sub("", s)


def opt_ratio(a, b):
    return difflib.SequenceMatcher(None, core(a), core(b)).ratio()


def match_option(ans_text, options):
    """Return 1-based index in options matching ans_text, or None."""
    if not ans_text:
        return None
    for i, o in enumerate(options):
        if o == ans_text:
            return i + 1
    for i, o in enumerate(options):
        if core(o) and (core(o) in core(ans_text) or core(ans_text) in core(o)):
            return i + 1
    best, bi = 0.0, None
    for i, o in enumerate(options):
        r = opt_ratio(o, ans_text)
        if r > best:
            best, bi = r, i + 1
    return bi if best >= 0.6 else None


def main():
    updated = matched = 0
    report = []
    for af in sorted(ANSWERS.glob("*/*.json")):
        level, session = af.parent.name, af.stem
        ans = json.loads(af.read_text(encoding="utf-8"))
        solved = {core(v["stem"]): v for v in ans.values() if v.get("answer_pos")}
        if not solved:
            continue
        # bank questions of this session
        files = list((BANK / level).glob(f"{session[:4]}/{session[5:]}/**/*.json"))
        pending = []
        for f in files:
            d = json.loads(f.read_text(encoding="utf-8"))
            if d.get("answer") is None:
                pending.append((f, d))
        if not pending:
            continue
        keys = list(solved)
        tryni_qs = [v for v in ans.values() if v.get("answer_pos")]

        def opt_key(opts):
            return "|".join(sorted(core(o) for o in opts if core(o)))

        tryni_by_opts = {}
        for v in tryni_qs:
            opts = [o for _, o in (v.get("opts") or [])]
            tryni_by_opts.setdefault(opt_key(opts), v)

        def match_by_options(bank_opts):
            k = opt_key(bank_opts)
            if k in tryni_by_opts:
                return tryni_by_opts[k]
            best, bv = 0.0, None
            bset = {core(o) for o in bank_opts if core(o)}
            for v in tryni_qs:
                tset = {core(o) for _, o in (v.get("opts") or []) if core(o)}
                if not bset or not tset:
                    continue
                inter = len(bset & tset)
                jac = inter / len(bset | tset)
                if jac > best:
                    best, bv = jac, v
            return bv if best >= 0.5 else None

        sess_m = sess_u = 0
        for f, d in pending:
            c = core(d.get("question", ""))
            v = solved.get(c)
            if v is None and len(c) >= 8:
                for k in keys:
                    if len(k) >= 8 and (c in k or k in c):
                        v = solved[k]
                        break
            if v is None:
                best, bk = 0.0, None
                for k in keys:
                    r = difflib.SequenceMatcher(None, c, k).ratio()
                    if r > best:
                        best, bk = r, k
                if best >= 0.78:
                    v = solved[bk]
            if v is None:
                v = match_by_options(d.get("options", []))
            if v is None:
                continue
            idx = match_option(v.get("answer_text"), d.get("options", []))
            if idx is None:
                # option texts can be stored as (id, text) pairs in the tryni dump
                vtext = v.get("answer_text")
                if not vtext and v.get("opts"):
                    vtext = v["opts"][v["answer_pos"] - 1][1] if v.get("answer_pos") else None
                idx = match_option(vtext, d.get("options", []))
            sess_m += 1
            if idx:
                d["answer"] = idx
                d["answer_text"] = d["options"][idx - 1]
                d["answer_source"] = "trynihongo"
                d["verified"] = {"status": "tryni-api", "note": ""}
                if "trynihongo" not in d.get("sources", []):
                    d.setdefault("sources", []).append("trynihongo")
                f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
                updated += 1
                sess_u += 1
        matched += sess_m
        report.append(f"{level}/{session}: matched {sess_m}, filled {sess_u} (pending {len(pending)})")
    print("\n".join(report) if report else "no answers available yet")
    print(f"\ntotal: matched {matched}, filled {updated}")


if __name__ == "__main__":
    sys.exit(main())
