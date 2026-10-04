#!/usr/bin/env python3
"""Enrich refs/answers_trynihongo/*.json with the option texts parsed from the
archived trynihongo HTML (offline; no requests). Needed for option-set matching.
"""
import json
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("ex", ROOT / "tools" / "extract_trynihongo.py")
ex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ex)


def main():
    n = 0
    for level, session, slug, f in ex.list_pages():
        ans_path = ROOT / "refs" / "answers_trynihongo" / level / f"{session}.json"
        if not ans_path.exists():
            continue
        ans = json.loads(ans_path.read_text(encoding="utf-8"))
        boxes = ex.parse_boxes(f.read_text(encoding="utf-8", errors="ignore"))
        for i, bx in enumerate(boxes, start=1):
            if str(i) in ans:
                ans[str(i)]["opts"] = [[aid, txt] for aid, txt in bx["opts"]]
        ans_path.write_text(json.dumps(ans, ensure_ascii=False, indent=1), encoding="utf-8")
        n += 1
        print(f"{level}/{session}: {len(boxes)} boxes")
    print(f"enriched {n} session files")


if __name__ == "__main__":
    main()
