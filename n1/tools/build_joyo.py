#!/usr/bin/env python3
"""Build data/joyo-kanji-2136.json — machine-readable 常用漢字表 base.

Sources (all archived under refs/, see guides/source-log.md):
  1. 文化庁「常用漢字表の音訓索引」HTML (refs/joyo_kanji_sakuin_bunkacho.html, Shift_JIS)
     → 2136 字種・音訓・例・備考（平成22年11月30日内閣告示 常用漢字表 本表）
  2. 文部科学省「小学校学習指導要領（平成29年告示）」別表 学年別漢字配当表
     (refs/joyo_gakunenbetsu_haitou_fragment-db.html) → 学年 1–6（[7] = 小学校以外＝中学）
  3. Unicode UCD: kTotalStrokes (Unihan_IRGSources.txt) → 総画数
  4. Unicode UCD 8.0: kRSKangXi (Unihan_RadicalStrokeCounts.txt) → 部首番号 → 部首名

Output schema (core 10 fields + 2 provenance helpers):
  char         常用漢字表 字種（本表の字体）
  unicode      U+XXXX
  radical      部首名; radical_no 部首番号（康熙214部首）
  strokes      総画数
  grade        学年（1–6=小学校, 7=中学校）※常用漢字表には非掲載・配当表由来
  onyomi       音読み（片仮名, 表順で全件）
  kunyomi      訓読み（平仮名・送り仮名付き, 全件）
  on_ex        音読み 例（読みと位置対応、例のない読みは ""）
  kun_ex       訓読み 例
  notes        備考（文化庁 本表 備考欄 原文）
  old_form     旧字体／異体字（本表の（）内、なければ null）

Usage:
    python3 tools/build_joyo.py            # (re)build data/joyo-kanji-2136.json
    python3 tools/build_joyo.py --check    # validate the existing output only
"""
import argparse
import html as _html
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "refs"
OUT = ROOT / "data" / "joyo-kanji-2136.json"

SAKUIN_HTML = REFS / "joyo_kanji_sakuin_bunkacho.html"      # Shift_JIS
HAITOU_HTML = REFS / "joyo_gakunenbetsu_haitou_fragment-db.html"
UNIHAN_TOTAL = REFS / "unihan" / "Unihan_IRGSources.txt"    # latest UCD (15.x)
UNIHAN_RS = REFS / "unihan8" / "Unihan_RadicalStrokeCounts.txt"  # UCD 8.0 (kRSKangXi)

# 康熙214部首：番号 → 日本語表記（辞書での常用形）。部首は総画数の抽出に使うのは番号のみ。
KANGXI = """一 丨 丶 丿 乙 亅 二 亠 人 儿 入 八 冂 冖 冫 几 凵 刀 力 勹 匕 匚 匸 十 卜 卩 厂 厶 又
口 囗 土 士 夂 夊 夕 大 女 子 宀 寸 小 尢 尸 屮 山 巛 工 己 巾 干 幺 广 廴 廾 弋 弓 彐 彡 彳
心 戈 戸 手 支 攴 文 斗 斤 方 无 日 曰 月 木 欠 止 歹 殳 毋 比 毛 氏 气 水 火 爪 父 爻 爿 片 牙
牛 犬 玄 玉 瓜 瓦 甘 生 用 田 疋 疒 癶 白 皮 皿 目 矛 矢 石 示 禸 禾 穴 立 竹 米 糸 缶 网 羊 羽
老 而 耒 耳 聿 肉 臣 自 至 臼 舌 舛 舟 艮 色 艸 虍 虫 血 行 衣 西 見 角 言 谷 豆 豕 豸 貝 赤 走
足 身 車 辛 辰 辵 邑 酉 釆 里 金 長 門 阜 隶 隹 雨 青 非 面 革 韋 韭 音 頁 風 飛 食 首 香 馬 骨
高 髟 鬥 鬯 鬲 鬼 魚 鳥 鹵 鹿 麥 麻 黃 黍 黑 黹 黽 鼎 鼓 鼠 鼻 齊 齒 龍 龜 龠""".split()
assert len(KANGXI) == 214, len(KANGXI)


# 例欄が読み数より多い稀な行：印刷表ではその読みに属する行へ合流される。
# （表の見方10：〔副〕〔接〕はその音訓の例。「極めて〔副〕」は「きわめる」の例。）
# この対応だけは機械的に決められないので原文を確認し人手で固定する。
EXAMPLE_PATCHES = {
    "極": ["極める，極め付き，極めて〔副〕", "極まる，極まり", "極み"],
}
PATCH_REASON = {
    "極": "きわめるの例「極めて〔副〕」が独立行に分かれている（表の見方10参照）",
}


def esc(s):
    return _html.unescape(re.sub(r"<[^>]+>", "", s))


def parse_sakuin(text):
    """文化庁 音訓索引: rows of (char, old_form, onyomi, on_ex, kunyomi, kun_ex, notes)."""
    start = text.find('<th bgcolor="#cc9999">漢字</th>')
    if start < 0:
        raise SystemExit("! 音訓索引 header not found")
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", text[start:], re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(tds) != 4:
            continue
        # --- 字種（font size=7）+ 旧字体（（）内） ---
        m = re.search(r'<font size="7">(.*?)</font>', tds[0], re.S)
        char = esc(m.group(1)).strip() if m else ""
        old_form = None
        rest = esc(tds[0]).strip()
        om = re.search(r"[（(]([^（()）]+)[)）]", rest)
        if om:
            old_form = om.group(1).strip()
        if not char:
            continue
        assert len(char) == 1, (char, rest)
        # --- 音訓・例：<br> が行、全角空白 が行内の区切り ---
        r_rdg = [t for t in re.split(r"<br\s*/?>", tds[1]) if esc(t).strip()]
        r_ex = [t for t in re.split(r"<br\s*/?>", tds[2]) if esc(t).strip()]
        readings = [x for line in r_rdg for x in re.split(r"[\s\u3000]+", esc(line)) if x]
        # 例：原本は読み行に対応するが、一部（都道府県専用訓・文脈〔副〕等）で非対称
        examples = [esc(x) for line in r_ex for x in re.split(r"[\s\u3000]+", esc(line)) if x]
        examples = align(readings, examples)
        # 片仮名=音、平仮名=訓（表の見方7：音は片仮名で示す）
        onyomi, on_ex = [], []
        kunyomi, kun_ex = [], []
        for rdg, ex in zip(readings, examples):
            if re.fullmatch(r"[ァ-ヶー・ヽヾ]+", rdg) and not re.search(r"[ぁ-ゖ]", rdg):
                onyomi.append(rdg); on_ex.append(ex)
            else:
                kunyomi.append(rdg); kun_ex.append(ex)
        notes = esc(tds[3]).strip()
        if char in EXAMPLE_PATCHES:
            kun_ex = EXAMPLE_PATCHES[char]
        rows.append({"char": char, "old_form": old_form,
                     "onyomi": onyomi, "on_ex": on_ex,
                     "kunyomi": kunyomi, "kun_ex": kun_ex,
                     "notes": notes})
    return rows


def align(readings, examples):
    """位置対応づけ：例のない読みには "" を、読みより多くの例行は末尾の読みに合流させる。"""
    out = []
    ei = 0
    for _r in readings:
        if ei < len(examples):
            out.append(examples[ei]); ei += 1
        else:
            out.append("")
    while ei < len(examples):
        out[-1] = "，".join(x for x in (out[-1], examples[ei]) if x)
        ei += 1
    return out


def parse_grade(text):
    """学年別漢字配当表(fragment-database HTML): {char: grade(1-6)}."""
    grades = {}
    order = {"小学1年生": 1, "小学2年生": 2, "小学3年生": 3,
             "小学4年生": 4, "小学5年生": 5, "小学6年生": 6}
    for key, g in order.items():
        m = re.search(re.escape(key) + r"（\d+字）】\s*(.*?)(?:<h|【)", text, re.S)
        if not m:
            m = re.search(re.escape(key) + r"（\d+字）】\s*(.+)", text, re.S)
        chs = re.findall(r"[\u4e00-\u9fff\U00020000-\U0002ffff]", m.group(1)) if m else []
        for c in chs:
            grades.setdefault(c, g)
    return grades


def load_unihan_total():
    tot = {}
    for line in open(UNIHAN_TOTAL, encoding="utf-8"):
        p = line.strip().split("\t")
        if len(p) >= 3 and p[1] == "kTotalStrokes":
            first = p[2].split()[0]
            if first.isdigit():
                tot[p[0]] = int(first)
    return tot


def load_unihan_radical():
    rs = {}
    for line in open(UNIHAN_RS, encoding="utf-8"):
        p = line.strip().split("\t")
        if len(p) >= 3 and p[1] == "kRSKangXi":
            rs[p[0]] = p[2].split()[0]
    return rs


def build():
    text = open(SAKUIN_HTML, encoding="shift_jis", errors="replace").read()
    rows = parse_sakuin(text)
    if len(rows) != 2136:
        raise SystemExit(f"! expected 2136 rows, got {len(rows)}")
    grade = parse_grade(open(HAITOU_HTML, encoding="utf-8", errors="replace").read())
    total = load_unihan_total()
    radical = load_unihan_radical()

    errors = []
    chars = set()
    jy = 0
    out = []
    for r in rows:
        c = r["char"]
        if c in chars:
            errors.append(f"duplicate char {c}")
        chars.add(c)
        jy += 1
        cp = "U+%X" % ord(c)
        grad = grade.get(c, 7)
        # 部首
        kv = radical.get(cp)
        if not kv:
            errors.append(f"{c}: no kRSKangXi")
            rad_no, rad_name = None, ""
        else:
            rad_no = int(kv.split(".")[0])
            rad_name = KANGXI[rad_no - 1] if 1 <= rad_no <= 214 else ""
        strokes = total.get(cp)
        if strokes is None:
            errors.append(f"{c}: no kTotalStrokes")
        # 音訓 4つ表示上限（学習カード用）は表示層の都合：底表は全読みを保持
        entry = {
            "char": c,
            "unicode": cp,
            "radical": rad_name,
            "radical_no": rad_no,
            "strokes": strokes,
            "grade": grad,
            "onyomi": r["onyomi"],
            "kunyomi": r["kunyomi"],
            "on_ex": r["on_ex"],
            "kun_ex": r["kun_ex"],
            "notes": r["notes"],
            "old_form": r["old_form"],
        }
        out.append(entry)

    # --- validation ---
    stats = {
        "total": len(out),
        "unique": len(chars),
        "with_old_form": sum(1 for e in out if e["old_form"]),
        "with_notes": sum(1 for e in out if e["notes"]),
        "onyomi": sum(len(e["onyomi"]) for e in out),
        "kunyomi": sum(len(e["kunyomi"]) for e in out),
        "grade_1_6": sum(1 for e in out if e["grade"] <= 6),
        "grade_7": sum(1 for e in out if e["grade"] == 7),
        "max_readings": max(len(e["onyomi"]) + len(e["kunyomi"]) for e in out),
    }
    # 教育漢字1026は全て2136に含まれる（配当表との交差）
    edu = set(grade)
    joyo = set(chars)
    if not edu <= joyo:
        errors.extend(f"grade char not in joyo: {c}" for c in sorted(edu - joyo))
    stats["grade_chars_total"] = len(edu)
    # 読み形式validation
    for e in out:
        for rdg in e["onyomi"]:
            if not re.fullmatch(r"[ァ-ヶー・ヽヾ]+", rdg) or re.search(r"[ぁ-ゖ]", rdg):
                errors.append(f"{e['char']}: odd onyomi {rdg!r}")
        for rdg in e["kunyomi"]:
            if not re.fullmatch(r"[ぁ-ゖゝゞー・]+", rdg):
                errors.append(f"{e['char']}: odd kunyomi {rdg!r}")
    # 例の対応行数
    for e in out:
        if len(e["onyomi"]) != len(e["on_ex"]) or len(e["kunyomi"]) != len(e["kun_ex"]):
            errors.append(f"{e['char']}: example alignment mismatch")
    if errors:
        print(f"! {len(errors)} validation error(s):")
        for x in errors[:40]:
            print("   ", x)
        raise SystemExit(1)

    meta = {
        "title": "常用漢字表 基礎データ（コア10フィールド）",
        "version": "2024.09.b1",
        "generator": "tools/build_joyo.py",
        "chars": len(out),
        "grades": {"1-6": "小学校（学年別漢字配当表）", "7": "中学校（小学校以外）"},
        "reading_cap": "表示層では読み最大4/種（学習カード用）。本データは表の全読みを保持。",
        "sources": {
            "kanji": "文化庁 常用漢字表（平成22年11月30日内閣告示）本表 - 音訓索引",
            "grade": "文部科学省 小学校学習指導要領（平成29年告示）別表 学年別漢字配当表（1026字）",
            "strokes": "Unicode UCD Unihan kTotalStrokes",
            "radical": "Unicode UCD 8.0 Unihan kRSKangXi（康熙214部首）",
        },
        "caveats": [
            "部首は康熙部首（Unihan kRSKangXi）基準。日本・漢検での部首と一部相違の可能性。",
            "画数はUnicode UCD kTotalStrokes（国際基準）。日本の辞書の画数（以=5画など）と約175字で異なる。",
            "音訓索引ページは印刷表の「1字下げ（特別なもの・用法の狭い音訓）」区別を保持していない。",
            "例は音訓索引の例欄原文。都道府県専用音訓など例のない読みは空欄（\"\"）。",
        ],
        "order": "常用漢字表 本表（字音五十音順、音のない字は字訓による）掲載順",
    }
    return {"meta": meta, "characters": out}, stats, errors


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="validate existing output only")
    args = ap.parse_args()
    if args.check:
        d = json.load(open(OUT, encoding="utf-8"))
        n = len(d["characters"])
        u = len({e["char"] for e in d["characters"]})
        print(f"CHECK {OUT}: {n} entries, unique chars {u}")
        if n != 2136 or u != 2136:
            raise SystemExit(1)
        print("  sample:", {k: v for k, v in d["characters"][0].items() if k != "on_ex"})
        return
    doc, stats, errors = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"WROTE {OUT}")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()