#!/usr/bin/env python3
"""Merge undated trynihongo checkpoint answers into refs/pool_questions.json
so apply_pools.py can match them against the bank.

Undated sessions are keyed by slug (length != 'YYYY-MM'); dated ones are
already merged session-wise by apply_trynihongo.py.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANS = ROOT / "refs" / "answers_trynihongo"
POOL = ROOT / "refs" / "pool_questions.json"


def main():
    existing = {}
    if POOL.exists():
        for q in json.loads(POOL.read_text(encoding="utf-8")):
            existing[q.get("_h")] = q
    added = 0
    for f in sorted(ANS.glob("*/*.json")):
        if len(f.stem) == 7:  # dated, handled by apply_trynihongo
            continue
        ans = json.loads(f.read_text(encoding="utf-8"))
        for v in ans.values():
            if not v.get("answer_pos") or not v.get("opts"):
                continue
            opts = [t for _, t in v["opts"]]
            stem = v.get("stem") or ""
            h = hashlib.sha1(stem.encode()).hexdigest()
            if h in existing:
                continue
            existing[h] = {
                "_h": h, "stem": stem, "options": opts,
                "answer": v["answer_pos"], "answer_text": v.get("answer_text") or "",
                "src": "trynihongo-undated",
            }
            added += 1
    POOL.write_text(json.dumps(list(existing.values()), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"merged {added} undated trynihongo answers -> {POOL} (total {len(existing)})")


if __name__ == "__main__":
    main()
