#!/usr/bin/env python3
"""Rule-based proofreader for the JLPT question banks (N1 + N2-N5).

Scans question/target/options (NOT the Chinese explanation) for transcription
errors: compatibility ideographs, halfwidth kana, stray spaces, big-tsu/small-
kana confusions, known OCR confusion pairs, simplified-only characters,
unbalanced brackets, duplicated particles, etc.

    python3 tools/proofread.py --bank all            # report only
    python3 tools/proofread.py --bank all --apply    # apply high-precision fixes
"""
import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

BANKS = {
    "n1": Path("/home/naruto/scratch/jlpt-question-bank/n1/past-exams"),
    "n2n5": Path("/home/naruto/scratch/jlpt-question-bank/past-exams"),
}

CJK = r"\u3005\u3006\u303b\u3041-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"

BIG_TSU = {
    "しまつた": "しまった", "しまつて": "しまって",
    "真つ先": "真っ先", "真つ直": "真っ直",
    "いつしよ": "いっしょ", "いつぱい": "いっぱい",
    "ちよつと": "ちょっと", "ずつと": "ずっと", "もつと": "もっと",
    "きつと": "きっと", "まつたく": "まったく", "はつきり": "はっきり",
    "しつかり": "しっかり", "すつかり": "すっかり", "びつくり": "びっくり",
    "がつかり": "がっかり", "ゆつくり": "ゆっくり", "さつぱり": "さっぱり",
    "やつぱり": "やっぱり", "けつこう": "けっこう", "たつぷり": "たっぷり",
    "じつくり": "じっくり", "ばつたり": "ばったり", "うつかり": "うっかり",
    "こつそり": "こっそり", "ぐつすり": "ぐっすり", "につこり": "にっこり",
    "さつそく": "さっそく", "ひつそり": "ひっそり",
}
BIG_KANA = {
    "じやない": "じゃない", "じやあ": "じゃあ", "じやなく": "じゃなく",
    "しやべる": "しゃべる", "しやれ": "しゃれ", "じやま": "じゃま",
    "しゆみ": "しゅみ", "しゆくだい": "しゅくだい",
    "じゆうぶん": "じゅうぶん", "じようだん": "じょうだん",
    "ちようど": "ちょうど", "りよこう": "りょこう", "しやしん": "しゃしん",
}
CONFUSIONS = {
    "進字": "進学", "面側を見": "面倒を見", "面側": "面倒",
    "目分は": "自分は", "目分の": "自分の", "目分": "自分",
    "少さな": "小さな", "思つのす": "思うのです",
    "五成児": "五歳児", "就字前": "就学前", "低齢児": "低年齢児",
    "おこなつて": "おこなって", "おこなつた": "おこなった",
    "たづねる": "たずねる",
    # 残留审校中确认的段落级错字（唯一串，精确替换）
    "四月中にになると": "四月中になると",
    "そっちのけでで読了": "そっちのけで読了",
    "駐車場をを作る": "駐車場を作る",
    "文庫本するとき": "文庫本にするとき",
    "図図書館": "図書館",
    "依頼頼し": "依頼し",
    "熱帯雤林": "熱帯雨林",
    "書绾": "書館",
    "粗互利用": "相互利用",
    "賃出": "貸出",
    "ー度に": "一度に",
    "5忤": "5件",
    "全額利用を負担": "全額利用者負担",
    "旅行する紹介": "発行する紹介",
    "押やられ": "押しやられ",
    "申しどける": "押しのける",
    "育ちににくい": "育ちにくい",
    "だけででなく": "だけでなく",
    "ためにに関心": "ために関心",
}
# 逐字 opencc 映射：仅取人工确认的「简体/旧字体 → 日本新字体」安全对
CURATED = {
    "问": "問", "题": "題", "阅": "閲", "读": "読", "壳": "殻", "每": "毎",
    "觀": "観", "專": "専", "雜": "雑", "语": "語", "网": "網", "别": "別",
    "气": "気", "异": "異", "晝": "昼", "讓": "譲", "增": "増", "帶": "帯",
    "带": "帯", "满": "満", "盜": "盗", "报": "報", "俭": "倹", "处": "処",
    "步": "歩", "现": "現", "亞": "亜", "賴": "頼", "连": "連",
    "确": "確", "龄": "齢", "收": "収", "擊": "撃", "歷": "歴", "惡": "悪",
    "恶": "悪", "溫": "温", "辭": "辞", "緖": "緒", "录": "録", "变": "変",
    "应": "応", "聽": "聴", "內": "内", "薰": "薫", "效": "効", "值": "値",
    "赁": "賃", "賣": "売", "兩": "両", "揭": "掲", "來": "来", "歲": "歳",
    "顶": "頂", "污": "汚", "穩": "穏", "廣": "広", "晚": "晩", "眞": "真",
    "戾": "戻", "嚙": "噛", "攪": "撹", "勳": "勲",
}
# 需人工复核、不自动转换：猪 筑 丑 查 叶 庄 惠 龍 澤 栖 填 兑 橱 萝 绾 挚 焘 贰 鸾 办
PAIRS = [("（", "）"), ("(", ")"), ("「", "」"), ("『", "』"), ("【", "】")]
DUP_PARTICLES = ["をを"]  # にに/でで/がが 会被「までです・けがが・でできる」等误报，改为人工审校
LABEL_RE = re.compile(r"^(?:阅读问题|問題|问题)\s*\d{1,2}\s*-\s*\d{1,2}\s*")


def norm_char(ch):
    o = ord(ch)
    if 0x2E80 <= o <= 0x2FDF or 0xF900 <= o <= 0xFAFF:
        return unicodedata.normalize("NFKC", ch)
    return ch


def scan_text(text):
    """Return (findings, auto_fixed_text|None). findings: (rule, detail, auto_applied)."""
    findings = []
    if not text:
        return findings, None
    t = text
    auto = None

    def apply(rule, detail, new):
        nonlocal t, auto
        applied = new != t
        findings.append((rule, detail, applied))
        if applied:
            t = new
            auto = t

    def flag(rule, detail):
        findings.append((rule, detail, False))

    fixed = "".join(norm_char(c) for c in t)
    if fixed != t:
        apply("compat-ideograph", "兼容汉字/部首字符→标准汉字", fixed)
    m = LABEL_RE.match(t)
    if m:
        apply("site-label", f"去除题号标注「{m.group(0).strip()}」", t[m.end():])
    fixed = re.sub(rf"(?<=[{CJK}]) (?=[{CJK}])", "", t)
    if fixed != t:
        apply("space-between-cjk", "汉字间多余空格", fixed)
    for bad, good in list(BIG_TSU.items()) + list(BIG_KANA.items()):
        if bad in t:
            apply("kana-size", f"{bad}→{good}", t.replace(bad, good))
    for bad, good in CONFUSIONS.items():
        if bad in t:
            apply("known-confusion", f"{bad}→{good}", t.replace(bad, good))
    hits = sorted({c for c in t if c in CURATED})
    if hits:
        fixed = "".join(CURATED.get(c, c) for c in t)
        apply("simplified-char", "简体/旧字: " + "".join(hits) + " → " + "".join(CURATED[c] for c in hits), fixed)
    hw = sorted({c for c in t if 0xFF66 <= ord(c) <= 0xFF9D})
    if hw:
        flag("halfwidth-kana", "半角片假名: " + "".join(hw))
    rare = sorted({c for c in t if 0x20000 <= ord(c) <= 0x3FFFF})
    if rare:
        flag("rare-cjk", "Ext-B+ 生僻字: " + "".join(rare))
    for d in DUP_PARTICLES:
        if d in t:
            flag("dup-particle", d)
    if re.match(r"^\s*[.．]\S", t):
        apply("leading-dot", "题干开头多余句点", t.lstrip(" .．"))
    for bad in ("。。", "、、", "，，", "．．"):
        if bad in t:
            flag("dup-punct", bad)
    # 半角/全角括号混用且合并计数平衡 → 统一为全角（先于配对检查）
    if ("（" in t or "）" in t) and ("(" in t or ")" in t):
        if t.count("（") + t.count("(") == t.count("）") + t.count(")"):
            fixed = t.replace("(", "（").replace(")", "）")
            if fixed != t:
                apply("halfwidth-paren", "半角括号→全角", fixed)
    for o, c in PAIRS:
        if t.count(o) != t.count(c):
            flag("bracket", f"{o}{c} 不配对 ({t.count(o)}/{t.count(c)})")
    return findings, auto


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", choices=["n1", "n2n5", "all"], default="all")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json", help="write full report JSON")
    ap.add_argument("--min-level", default="")
    args = ap.parse_args()

    banks = ["n1", "n2n5"] if args.bank == "all" else [args.bank]
    report, rule_counts = [], Counter()
    changed_files = 0
    for bank in banks:
        for f in sorted(BANKS[bank].glob("**/*.json")):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            findings = []
            changed = False
            for field in ("question", "target"):
                val = d.get(field)
                if not isinstance(val, str):
                    continue
                res, fixed = scan_text(val)
                for rule, detail, applied in res:
                    rule_counts[rule] += 1
                    findings.append({"field": field, "rule": rule, "detail": detail, "applied": applied})
                if args.apply and fixed is not None and fixed != val:
                    d[field] = fixed
                    changed = True
            if isinstance(d.get("options"), list):
                for i, o in enumerate(d["options"]):
                    if not isinstance(o, str):
                        continue
                    res, fixed = scan_text(o)
                    for rule, detail, applied in res:
                        rule_counts[rule] += 1
                        findings.append({"field": f"options[{i}]", "rule": rule, "detail": detail, "applied": applied})
                    if args.apply and fixed is not None and fixed != o:
                        d["options"][i] = fixed
                        changed = True
            if findings:
                report.append({"bank": bank, "file": str(f.relative_to(BANKS[bank].parent)),
                               "id": d.get("id", f.stem), "findings": findings})
            if args.apply and changed:
                note = d.get("notes") or ""
                marker = "[auto-proofread 2026-10-05]"
                if marker not in note:
                    d["notes"] = (note + " " + marker).strip()
                f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
                changed_files += 1

    print("== rule counts ==")
    for r, n in rule_counts.most_common():
        print(f"  {r:18} {n}")
    print(f"files with findings: {len(report)}" + (f", changed: {changed_files}" if args.apply else ""))
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print("wrote", args.json)
    seen = set()
    for rec in report:
        for fi in rec["findings"]:
            key = fi["rule"] + ("*" if fi["applied"] else "")
            if key in seen:
                continue
            seen.add(key)
            print(f"  e.g. [{fi['rule']}] {rec['id']} {fi['field']}: {fi['detail']}")


if __name__ == "__main__":
    main()
