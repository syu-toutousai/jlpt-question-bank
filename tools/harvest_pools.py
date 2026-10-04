#!/usr/bin/env python3
"""Harvest jlptzhen random-pool pages: each request samples fresh questions.
Accumulate unique (stem-hash) questions with answers into refs/pool_questions.json.

    python3 tools/harvest_pools.py --reps 30 [--only reading|grammar|all]
"""
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POOL_LIST = Path("/tmp/opencode/zhen_pools.txt")
OUT = ROOT / "refs" / "pool_questions.json"
TMP = Path("/tmp/opencode")
UA = "Mozilla/5.0 (X11; Linux x86_64)"

spec = importlib.util.spec_from_file_location("zhen", ROOT / "tools" / "fetch_jlptzhen.py")
zhen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zhen)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--only", default="all", choices=["all", "reading", "grammar"])
    ap.add_argument("--sleep", type=float, default=0.8)
    ap.add_argument("--urls", default=str(POOL_LIST))
    args = ap.parse_args()

    urls = [u.strip() for u in Path(args.urls).read_text(encoding="utf-8").splitlines() if u.strip()]
    if args.only == "reading":
        urls = [u for u in urls if "阅读" in u or re.search(r"问题(09|10|11|12|13)", u)]
    elif args.only == "grammar":
        urls = [u for u in urls if "阅读" not in u and "听力" not in u]

    by_hash = {}
    if OUT.exists():
        for q in json.loads(OUT.read_text(encoding="utf-8")):
            by_hash[q["_h"]] = q
    print(f"start: {len(by_hash)} unique pool questions, {len(urls)} urls x {args.reps} reps")

    for ui, url in enumerate(urls, 1):
        gained_before = len(by_hash)
        for r in range(1, args.reps + 1):
            f = TMP / "pool_fetch.html"
            subprocess.run(["curl", "-s", "--max-time", "40", "-A", UA, "-L", url, "-o", str(f)], timeout=60)
            try:
                qs = zhen.parse_quiz(f.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                qs = []
            for q in qs:
                if not q.get("answer"):
                    continue
                h = hashlib.sha1((q.get("stem") or "").encode()).hexdigest()
                if h not in by_hash:
                    q["_h"] = h
                    by_hash[h] = q
            time.sleep(args.sleep)
            if r % 5 == 0:
                OUT.write_text(json.dumps(list(by_hash.values()), ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"  [{ui}/{len(urls)}] rep {r}: {len(by_hash)} unique (+{len(by_hash)-gained_before})", flush=True)
        OUT.write_text(json.dumps(list(by_hash.values()), ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{ui}/{len(urls)}] done url: {len(by_hash)} unique total", flush=True)
    print(f"FINISHED: {len(by_hash)} unique questions -> {OUT}")


if __name__ == "__main__":
    main()
