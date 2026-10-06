#!/usr/bin/env python3
"""N1 出典索引 —— 読解原文出处（题面内『…による』行）＋ 填空/用法 metadata。

読解・填空・用法の「出処」三層：
  1. 読解（問題8-13）: 本文末尾の出典行（例: むのたけじ『希望は絶望のど真ん中に』による）を抽出。
     明示がなければ source=null（未詳）。原文の同定は analysis/source-traces.json に集約。
  2. 填空（問題2 文脈規定・問題5 文法形式・問題7 文章の文法）: 出典行は原則なし＝作成文。
  3. 用法（問題4）: 語の正誤用法＝作成文。target（見出し語）を統計用に記録。

出力: analysis/source-traces.json（metadata のみ・本文テキストは含めない）
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "n1" / "past-exams"
OUT = ROOT / "analysis" / "source-traces.json"

SRC_PAT = re.compile(r"[（(]([^（()）]*(?:による|より|著|編|訳)[^（()）]*)[）)]")


def clean_source(s: str) -> str:
    s = s.strip()
    s = re.sub(r"(による|より)$", "", s).strip()
    s = re.sub(r"\s+", " ", s)
    return s


def main():
    rows = []
    for f in sorted(BANK.rglob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict) or not d.get("id"):
            continue
        q = d.get("question") or ""
        m = SRC_PAT.findall(q)
        src = clean_source(m[-1]) if m else None
        rows.append({
            "id": d["id"], "year": d.get("year"), "month": d.get("month"),
            "section": d.get("section"), "type": d.get("type"),
            "number": d.get("number"), "target": d.get("target") or "",
            "source": src,
        })

    reading = [r for r in rows if r["section"] == "reading"]
    with_src = [r for r in reading if r["source"]]
    # group passages by (year, month, source) — same source line = same passage
    groups = defaultdict(list)
    for r in with_src:
        groups[(r["year"], r["month"], r["source"])].append(r["id"])
    passages = [{"year": k[0], "month": k[1], "source": k[2], "ids": sorted(v)}
                for k, v in sorted(groups.items())]
    passages.sort(key=lambda p: (-p["year"], -p["month"], p["ids"][0]))

    # 未詳 reading passages: group by (y,m,type base number without question number)
    unknown = [r for r in reading if not r["source"]]
    unk_groups = defaultdict(list)
    for r in unknown:
        base = re.sub(r"-\d+$", "", r["id"])
        unk_groups[(r["year"], r["month"], base)].append(r["id"])
    unknown_passages = [{"year": k[0], "month": k[1], "guess_base": k[2], "ids": sorted(v)}
                        for k, v in sorted(unk_groups.items())]

    # 用法 target 统计（問題4）
    usage = [r for r in rows if r["section"] == "vocab" and r["type"] == "usage"]
    usage_counter = Counter(r["target"] for r in usage if r["target"])
    usage_repeats = {w: c for w, c in usage_counter.items() if c > 1}
    usage_years = defaultdict(list)
    for r in usage:
        if r["target"]:
            usage_years[r["target"]].append(f"{r['year']}-{r['month']:02d}")

    # 問題2 文脈規定 target 统计
    context = [r for r in rows if r["section"] == "vocab" and r["type"] == "context"]
    context_counter = Counter(r["target"] for r in context if r["target"])
    context_repeats = {w: c for w, c in context_counter.items() if c > 1}

    by_type = Counter(f"{r['section']}-{r['type']}" for r in rows if r["section"])

    out = {
        "meta": {
            "scope": "JLPT N1 2010-07 ～ 2025-07",
            "total": len(rows),
            "reading_total": len(reading),
            "reading_with_source": len(with_src),
            "reading_unknown": len(unknown),
            "usage_total": len(usage),
            "context_total": len(context),
        },
        "passages": passages,
        "unknown_passages": unknown_passages,
        "usage_targets": [{"word": w, "years": sorted(usage_years[w])}
                          for w, _ in usage_counter.most_common()],
        "usage_repeats": usage_repeats,
        "context_repeats": context_repeats,
        "by_type": dict(by_type),
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  reading {len(reading)}: explicit {len(with_src)} / unknown {len(unknown)}")
    print(f"  passages(sourced) {len(passages)} / unknown groups {len(unknown_passages)}")
    print(f"  usage targets {len(usage_counter)}（repeats {len(usage_repeats)}）"
          f" / context repeats {len(context_repeats)}")
    top_authors = Counter()
    for p in passages:
        m = re.match(r"(.+?)『", p["source"])
        if m:
            top_authors[m.group(1).strip()] += len(p["ids"])
    for a, c in top_authors.most_common(10):
        print(f"    {a}: {c} 問")


if __name__ == "__main__":
    main()
