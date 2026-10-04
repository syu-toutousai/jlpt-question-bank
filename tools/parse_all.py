#!/usr/bin/env python3
"""Parse archived N2-N5 HTML pages into structured JSON under parsed/.

Each refs/YYYY-MM_<site>_<level>.html becomes parsed/YYYY-MM_<site>_<level>.json
(jlptzhen: answers + explanations; jlpt247: verbatim transcript, no answers).
Also writes manifest.json with per-session counts and answer coverage.
"""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "refs"
PARSED = ROOT / "parsed"
TOOLS = ROOT / "tools"


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


zhen = load_mod("fetch_jlptzhen", TOOLS / "fetch_jlptzhen.py")
j247 = load_mod("fetch_jlpt247", TOOLS / "fetch_jlpt247.py")


def main():
    PARSED.mkdir(exist_ok=True)
    manifest = {}
    for f in sorted(REFS.glob("*.html")):
        m = re.match(r"(\d{4}-\d{2})_(jlptzhen|jlpt247)_(n[2-5])\.html$", f.name)
        if not m:
            continue
        session, site, level = m.groups()
        out = PARSED / f"{session}_{site}_{level}.json"
        if not out.exists() or out.stat().st_mtime < f.stat().st_mtime:
            html = f.read_text(encoding="utf-8")
            qs = (zhen.parse_quiz(html) if site == "jlptzhen" else j247.parse_quiz(html))
            bundle = {
                "session": session, "site": site, "level": level,
                "count": len(qs), "questions": qs,
            }
            out.write_text(json.dumps(bundle, ensure_ascii=False, indent=1), encoding="utf-8")
        else:
            qs = json.loads(out.read_text(encoding="utf-8"))["questions"]
        rec = manifest.setdefault(f"{level}/{session}", {"level": level, "session": session, "sources": {}})
        ans = sum(1 for q in qs if q.get("answer"))
        secs = sorted({q.get("section", "?") for q in qs})
        rec["sources"][site] = {"questions": len(qs), "with_answer": ans, "sections": secs}

    (ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")

    # coverage report
    print(f"{'session':10} {'lv':3} {'zhen':>18} {'247':>12}")
    for key in sorted(manifest):
        rec = manifest[key]
        z = rec["sources"].get("jlptzhen")
        t = rec["sources"].get("jlpt247")
        zs = f"{z['questions']}Q/{z['with_answer']}A" if z else "-"
        ts = f"{t['questions']}Q" if t else "-"
        print(f"{rec['session']:10} {rec['level']:3} {zs:>18} {ts:>12}")

    tot = {"jlptzhen": 0, "jlpt247": 0}
    for rec in manifest.values():
        for site, s in rec["sources"].items():
            tot[site] += s["questions"]
    print(f"\ntotal questions: jlptzhen={tot['jlptzhen']}, jlpt247={tot['jlpt247']}")


if __name__ == "__main__":
    main()
