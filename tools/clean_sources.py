#!/usr/bin/env python3
"""出典行の転写清掃 —— 確証のある誤記だけを修正し、証拠を残す（候補は断定しない）。

- 入力/出力: analysis/source-traces.json（passages[].source）
- 各修正は EXACT / REGEX の二種。適用時 raw を保存し corrected=true, evidence を付す。
- 未確証の怪しい行は corrected せず suspicious=true + note（要確認）。

流儀: 「補正」と「候補」を区別する。検索で書誌一致が取れたものだけ corrected。
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACES = ROOT / "analysis" / "source-traces.json"

# 確証済み（書誌一致：Amazon/版元/文春 等を確認）
EXACT = {
    "司司馬遼太郎『風塵抄』":
        ("司馬遼太郎『風塵抄』", "衍字「司」を除去（司馬遼太郎の『風塵抄』）"),
    "佐藤可士和『加藤可士和の超整理術』":
        ("佐藤可士和『佐藤可士和の超整理術』", "本文転写の誤り（著者名の混入）"),
    "竹内薫・荒野健彦「透明人間」の作り方 』":
        ("竹内薫・荒野健彦『「透明人間」の作り方』", "括弧の崩れを補正（書名は入れ子引用）"),
    "内藤広『建築のはじまりに向かって』":
        ("内藤廣『建築のはじまりに向かって』", "「広」→正字「廣」（Amazon・王国社書誌）"),
    "吉田忙 「ヒトとサ正のあいだーー精神はいつ生まれたのか」":
        ("吉田脩二『精神はいつ生まれたのか ヒトとサルのあいだ』",
         "OCR 崩れを書誌で補正（Amazon・文春 books）"),
    "池上彰『の勉強法』":
        ("池上彰『〈わかりやすさ〉の勉強法』（講談社現代新書）",
         "欠落タイトルを書誌で補正（講談社・Amazon）"),
    "成毛真『大人げない大人になれ!』":
        ("成毛眞『大人げない大人になれ!』", "「真」→正字「眞」（著者表記）"),
    "植村八渺三省堂日取得":
        ("植村八潮（三省堂）…（OCR 崩れ・書名要確認）",
         "著者名を「植村八潮」に補正（専修大学教授・Amazon 著者ページ）。書名は復元不能"),
}
REGEX = [
    (r"グローバル・ヒスとリー", "グローバル・ヒストリー", "誤字（ヒスとリー→ヒストリー）"),
    (r"\s+(?=『)|(?<=』)\s+(?=[（(])", "", "書名括弧前後の余分な空白を除去"),
    (r"\s{2,}", " ", "連続空白を正規化"),
]

# 未確証のまま「要確認」ラベルを付ける条件
SUSPICIOUS = [
    (r"^.{1,2}『", "著者名が短すぎる（姓氏欠落の可能性）"),
    (r"取得", "取得日時の転写崩れの可能性"),
    (r"[ぁ-ん]{4,}日取得", "OCR 崩れ"),
]


def main():
    data = json.loads(TRACES.read_text(encoding="utf-8"))
    fixed = 0
    for p in data["passages"]:
        src = p["source"]
        p.setdefault("raw", src)
        for a, (b, ev) in EXACT.items():
            if src == a:
                p["source"], p["corrected"], p["evidence"] = b, True, ev
                fixed += 1
                src = b
                break
        for pat, rep, ev in REGEX:
            if re.search(pat, src):
                new = re.sub(pat, rep, src)
                if new != src:
                    p["raw"] = p.get("raw") or src
                    p["source"] = new
                    p["corrected"] = True
                    p.setdefault("evidence", ev)
                    src = new
        for pat, note in SUSPICIOUS:
            if re.search(pat, src):
                p.setdefault("suspicious", True)
                p.setdefault("suspicious_note", note)
    TRACES.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    sus = sum(1 for p in data["passages"] if p.get("suspicious"))
    print(f"cleaned: corrected {fixed} / suspicious {sus} / total {len(data['passages'])}")


if __name__ == "__main__":
    main()
