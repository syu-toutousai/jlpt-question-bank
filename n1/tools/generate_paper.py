#!/usr/bin/env python3
"""Generate per-question plaintext JSON from a refs/ session source.

Input source, tried in order:
    1. refs/<session>_full_jlptzhen.json   (jlptzhen quiz pages, 2024-07 …)
    2. refs/<session>_jlpt247.json         (jlpt247 verbatim transcription)

writes one JSON per question to past-exams/<year>/<month>/<section>/<type>_<NN>.json.

Existing files are NEVER overwritten unless --force (files may hold manual
user edits, e.g. the Q8 stem hiragana correction) — see AGENTS.md §4.

The jlptzhen quiz pages interleave the 聴解 blocks under the same 問題1–5
headings (no "聴解" prefix); questions carrying an audio URL belong to the
listening block, the earlier ones (with num) to the written block.

Standard N1 (2010+) written paper (verified against 2024-07/2024-12):
  文字語彙  問題1 reading(1–6) 問題2 context(7–13) 問題3 paraphrase(14–19)
            問題4 usage(20–25)
  文法      問題5 choice(26–35) 問題6 composition(36–40) 問題7 passage(41–44)
  読解      問題8 short(45–48) 問題9 mid(49–56) 問題10 long(57–59)
            問題11 long(60–61) 問題12 long(62–64) 問題13 long(65–66)
  聴解      問題1 point(課題理解) … 問題5 implication(統合理解)  (local 1..N)

Usage:
    python3 tools/generate_paper.py 2024-07 [--force]
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "refs"
PAST = ROOT / "past-exams"

# (問題N, repo section, type, group size). Group sizes drive the official
# global numbering for blocks whose stems carry no number.
GROUPS = [
    ("問題1", "vocab", "reading", 6),
    ("問題2", "vocab", "context", 7),
    ("問題3", "vocab", "paraphrase", 6),
    ("問題4", "vocab", "usage", 6),
    ("問題5", "grammar", "choice", 10),
    ("問題6", "grammar", "composition", 5),
    ("問題7", "grammar", "passage", 4),
    ("問題8", "reading", "short", 4),
    ("問題9", "reading", "mid", 8),
    ("問題10", "reading", "long", 3),
    ("問題11", "reading", "long", 2),
    ("問題12", "reading", "long", 3),
    ("問題13", "reading", "long", 2),
]
SECTION_JP = {"vocab": "言語知識(文字・語彙)", "grammar": "言語知識(文法)",
              "reading": "読解", "listening": "聴解"}
LISTEN_TYPE = {1: "point", 2: "grammar", 3: "overview", 4: "detailed", 5: "implication"}
DIFFICULTY = {"問題1": "easy", "問題2": "medium", "問題3": "medium", "問題4": "medium",
              "問題5": "medium", "問題6": "medium", "問題7": "medium",
              "問題8": "hard", "問題9": "hard",
              "問題10": "medium", "問題11": "medium", "問題12": "medium", "問題13": "medium"}
TAGS_EXTRA = {"reading": ["読み方", "漢字"], "context": ["言葉の意味", "文脈規定"],
              "paraphrase": ["言い換え"], "usage": ["使い方"], "choice": ["文法選択"],
              "composition": ["並べ替え"], "passage": ["文章の文法"]}

# Known gaps inside a quiz page, filled from independent transcriptions.
# Real past-exam material, verified against the cited sources.
EXTRA = {
    ("2024-07", "問題2"): [
        {
            "num": 13,
            "stem": "登山に誘われたが、あまり経験がないので、みんなの（　　）になると思い、断った。",
            "target": "足手まとい",
            "options": ["骨折り", "足手まとい", "裏目", "および腰"],
            "answer": 2,
            "explanation": "「足手まといになる」＝他人の進行をじゃまする役目。答えは2)。",
            "notes": "jlptzhen 存档缺本题(17913缺失)，题干/选项来自 jlpt247 全文転写，答案与両答案键第7位=2 一致。",
            "extra_sources": ["https://jlpt247.com/n1-jlpt-7-2024/ (全文転写)",
                              "refs/2024-07_answerkey_diliushixian.md (問題2=2241132)",
                              "refs/2024-07_answerkey_youtibao.md (問題2=2441132)"],
        }
    ],
}

# per (session, 問題N): (status, note). status ∈ matched / partial.
VERIFY = {
    ("2024-07", "問題1"): ("matched", "数字键 第六时限=羊驼=132243"),
    ("2024-07", "問題2"): ("matched", "site Q7-12=244113=羊驼；Q8=4返上；Q13(補)=2足手まとい"),
    ("2024-07", "問題3"): ("matched", "键 323144"),
    ("2024-07", "問題4"): ("matched", "键 213314"),
    ("2024-07", "問題5"): ("matched", "site=3143413241；Q29=3 なるかどうかはともかく 已判明(jlpt247 共证)"),
    ("2024-07", "問題6"): ("matched", "键 23214"),
    ("2024-07", "問題7"): ("matched", "site=羊驼3241；Q44=1 というわけです 已判明"),
    ("2024-07", "問題8"): ("matched", "键 4323"),
    ("2024-07", "問題9"): ("partial", "Q52=3 已判明(段落明示)；Q54 jlptzhen=2 vs 羊驼=3 争议待确认"),
    ("2024-07", "問題10"): ("matched", "键 441"),
    ("2024-07", "問題11"): ("matched", "键 44"),
    ("2024-07", "問題12"): ("matched", "键 331"),
    ("2024-07", "問題13"): ("matched", "键 12"),
    # 2025-07 — keys: 一茂/uno + jlpt247 DA + aixinjp(宁波爱心,含重建句) + keedu(问题5/41) + quiz334
    ("2025-07", "問題1"): ("matched", "一茂/uno=224143；DA 逐题一致；aixinjp 字键一致"),
    ("2025-07", "問題2"): ("matched", "Q7-13=1323124；Q8=手先=3(quiz334+aixinjp；uno=4 手際 误)"),
    ("2025-07", "問題3"): ("matched", "键 344231 (uno=aixinjp=quiz334)"),
    ("2025-07", "問題4"): ("matched", "键 241314；Q20 aixinjp 标③但自引文本=选项2，取2"),
    ("2025-07", "問題5"): ("matched", "键 2143414123 (uno=aixinjp=keedu)"),
    ("2025-07", "問題6"): ("matched", "★ 2,3,2,1,4 (uno=aixinjp 重建 36-40 逐空一致)"),
    ("2025-07", "問題7"): ("matched", "键 4312；Q41=4 だけが(keedu 文本+aixinjp 标4；uno=2 文法不通)"),
    ("2025-07", "問題8"): ("matched", "键 3134 (uno=aixinjp)"),
    ("2025-07", "問題9"): ("matched", "键 22424123；Q55=2(本能,aixinjp+原文论证；uno/DA=4 系误断言)"),
    ("2025-07", "問題10"): ("matched", "键 4214 (uno=aixinjp)"),
    ("2025-07", "問題11"): ("matched", "键 44 (uno=aixinjp=DA)"),
    ("2025-07", "問題12"): ("matched", "键 113 (uno=aixinjp)"),
    ("2025-07", "問題13"): ("matched", "键 33 (uno=aixinjp)"),
    # 2024-12 — jlpt247 has no answer markers; keys: aixinjp (66题) + learnjapaneseaz (Q1-44)
    ("2024-12", "問題1"): ("matched", "键 aixinjp=learnjapaneseaz=211343"),
    ("2024-12", "問題2"): ("matched", "键 1434213；aixinjp=learnjapaneseaz Q7-12 全符；Q13 learnjapaneseaz=1(じきに,疑误) 取 aixinjp=3(とっさに)"),
    ("2024-12", "問題3"): ("matched", "键 224311 (两源一致)"),
    ("2024-12", "問題4"): ("matched", "键 244321 (两源一致)"),
    ("2024-12", "問題5"): ("matched", "键 4323141132；Q34 键自引文本=选项2(あってはならない)，键标③系笔误"),
    ("2024-12", "問題6"): ("matched", "由 aixinjp 重建句逐空推导 ★ 答案：1,4,4,1,3"),
    ("2024-12", "問題7"): ("matched", "键 3412 (两源一致)"),
    ("2024-12", "問題8"): ("matched", "aixinjp 3412；选项文本逐一匹配"),
    ("2024-12", "問題9"): ("matched", "aixinjp 42242321；选项文本逐一匹配"),
    ("2024-12", "問題10"): ("matched", "aixinjp 231；选项文本匹配"),
    ("2024-12", "問題11"): ("matched", "aixinjp 43；选项文本匹配"),
    ("2024-12", "問題12"): ("matched", "aixinjp 234；选项文本匹配"),
    ("2024-12", "問題13"): ("matched", "aixinjp 11；选项文本匹配"),
    # 2023-07 — keys: aixinjp(宁波爱心,66题+重建句) + jpnihon/renrendoc 解析(读解&39-44+问题6逐空,搜索引擎快照)
    ("2023-07", "問題1"): ("matched", "键 aixinjp=413423；renrendoc 解析 1,5 等⑥字符对照一致"),
    ("2023-07", "問題2"): ("matched", "键 2234114；renrendoc 解析 Q7-13 词义对照一致"),
    ("2023-07", "問題3"): ("matched", "键 232414；renrendoc 语义：懸念=1 やつれ=3 奮闘=2 不慮=3 没頭=4"),
    ("2023-07", "問題4"): ("matched", "键 423131；renrendoc Q21収容=2, 冴える=3, もろい=4系干扰 ③=1"),
    ("2023-07", "問題5"): ("matched", "键 4313242131；renrendoc 解析 Q26-35 语义逐一吻合"),
    ("2023-07", "問題6"): ("matched", "★ 1,3,4,2,4；renrendoc 解析 36-40 逐空(2143/其中★次序)吻合"),
    ("2023-07", "問題7"): ("matched", "键 jpnihon/renrendoc 解析=2134；aixinjp=1114 于 41/43 系笔误(逆义)，见备注"),
    ("2023-07", "問題8"): ("matched", "键 1322；jpnihon 解析 45-48 逐答一致"),
    ("2023-07", "問題9"): ("matched", "键 34423114；aixinjp 全符(jpnihon 解析 51-55 一致)；Q56 jpnihon=4 vs aixinjp=1，取4(见备注)"),
    ("2023-07", "問題10"): ("matched", "键 334；jpnihon 解析 57-59 逐答一致"),
    ("2023-07", "問題11"): ("matched", "键 31；jpnihon 选项文本 60/61 一致(aixinjp 同)"),
    ("2023-07", "問題12"): ("matched", "键 434；jpnihon 解析 62-64 一致"),
    ("2023-07", "問題13"): ("matched", "键 aixinjp=24；Q66 自引文本(水曜日以降・空き確認)吻合案内文"),
    # 2022-07 — 68题真卷(問題9=49-57×9,問題12=63-66×4,PassJapanese 分节印证)；键 aixinjp(完整重建句)
    ("2022-07", "問題1"): ("matched", "键 aixinjp=133424；新泽真题卷参考答案同(133424)"),
    ("2022-07", "問題2"): ("matched", "键 4221133；新泽参考答案同"),
    ("2022-07", "問題3"): ("matched", "键 424331；新泽参考答案同"),
    ("2022-07", "問題4"): ("matched", "键 231214；新泽参考答案同"),
    ("2022-07", "問題5"): ("matched", "键 2314123422；新泽参考答案同"),
    ("2022-07", "問題6"): ("matched", "键 41324；aixinjp 附排列 3241/2413/4231/3124/1342"),
    ("2022-07", "問題7"): ("matched", "键 3211；aixinjp 重建句(そうした保育園/ただ/入学したとたん/たくましく思えます)"),
    ("2022-07", "問題8"): ("matched", "键 3143；答案句逐一吻合 jlpt247 选项文本"),
    ("2022-07", "問題9"): ("matched", "键 331322144；答案句逐一吻合选项文本"),
    ("2022-07", "問題10"): ("matched", "键 143；答案句吻合选项文本"),
    ("2022-07", "問題11"): ("matched", "键 23；答案句吻合选项文本"),
    ("2022-07", "問題12"): ("matched", "键 4124；答案句吻合选项文本"),
    ("2022-07", "問題13"): ("matched", "键 12；答案句吻合选项文本"),
    # 2022-12 — 66题；键 aixinjp(全部题号・答案对) + 词组 cross jlptzhen(25/25 已审计)
    ("2022-12", "問題1"): ("matched", "键 aixinjp=324143；jlptzhen 25/25 与 jlpt247 转写一致(09-08审计)"),
    ("2022-12", "問題2"): ("matched", "键 1324321"),
    ("2022-12", "問題3"): ("matched", "键 421243"),
    ("2022-12", "問題4"): ("matched", "键 332412"),
    ("2022-12", "問題5"): ("matched", "键 1331423241"),
    ("2022-12", "問題6"): ("matched", "键 24213；aixinjp 附排列 4231/1342/3421/3412/4132"),
    ("2022-12", "問題7"): ("matched", "键 3421；重建句吻合选项文本"),
    ("2022-12", "問題8"): ("matched", "键 2112；答案句吻合选项文本"),
    ("2022-12", "問題9"): ("matched", "键 23241233；答案句吻合选项文本"),
    ("2022-12", "問題10"): ("matched", "键 413；答案句吻合选项文本"),
    ("2022-12", "問題11"): ("matched", "键 44；答案句吻合选项文本"),
    ("2022-12", "問題12"): ("matched", "键 342；答案句吻合选项文本"),
    ("2022-12", "問題13"): ("matched", "键 32；答案句吻合选项文本"),
    # 2021-12 — 69题真卷(問題9=49-57×9,問題10=58-61×4,問題11=62-64×3)；键 aixinjp
    ("2021-12", "問題1"): ("matched", "键 aixinjp=431231；第六时限同卷答案(回忆版)多处不符见备注，取 aixinjp"),
    ("2021-12", "問題2"): ("matched", "键 1424233"),
    ("2021-12", "問題3"): ("matched", "键 313242"),
    ("2021-12", "問題4"): ("matched", "键 314421"),
    ("2021-12", "問題5"): ("matched", "键 3243242311"),
    ("2021-12", "問題6"): ("matched", "键 14421；aixinjp 附排列 3241/1342/3142/4213/1324"),
    ("2021-12", "問題7"): ("matched", "键 1342；重建句吻合选项文本"),
    ("2021-12", "問題8"): ("matched", "键 3442；答案句吻合选项文本"),
    ("2021-12", "問題9"): ("matched", "键 433212321；Q54/55/57 与第六时限冲突,答案句逐一吻合选项文本(见备注)"),
    ("2021-12", "問題10"): ("matched", "键 1411；答案句吻合选项文本"),
    ("2021-12", "問題11"): ("matched", "键 223；答案句吻合选项文本"),
    ("2021-12", "問題12"): ("matched", "键 423；答案句吻合选项文本"),
    ("2021-12", "問題13"): ("matched", "键 22；Q69 单源(aixinjp 读原图表),选项文本系其自选句"),
    # 2020-12 — 68题；键 keymap(问题1-4 jlptzhen 文本 19+5+1, 问题5-13 前途 qiantu 文本+digit+sort);
    #   读解段 weilan(exams.weilanliuxue 21250) 逐题数字交叉一致; 转写选项 shuflle-safe(文本定位)
    ("2020-12", "問題1"): ("matched", "键 213414：jlptzhen文本=qiantu文本=weilan 全符"),
    ("2020-12", "問題2"): ("matched", "键 4221423：jlptzhen/qiantu/weilan 全符"),
    ("2020-12", "問題3"): ("matched", "键 423213：三源全符"),
    ("2020-12", "問題4"): ("matched", "键 124133：jlptzhen/qiantu 全符；Q24 weilan=4 系笔误(取 3 収容)"),
    ("2020-12", "問題5"): ("matched", "键 4344132233：qiantu文本 26-35 全符；Q32=2 対戦してくる 转写位置"),
    ("2020-12", "問題6"): ("matched", "★ 42431：qiantu 排列 2,3,1,4等×5 转写逐序一致"),
    ("2020-12", "問題7"): ("matched", "键 2123：qiantu文本 41-44 全符"),
    ("2020-12", "問題8"): ("matched", "键 2311：qiantu文本=weilan 45-48"),
    ("2020-12", "問題9"): ("matched", "键 412313132：qiantu文本=weilan 49-57 全符"),
    ("2020-12", "問題10"): ("matched", "键 242；Q58=2 约五亿年前~急增后减少又增加(文本三源核对:weilan=4/qiantu=3 位置均不合文案)"),
    ("2020-12", "問題11"): ("matched", "键 44：qiantu=weilan 61-62"),
    ("2020-12", "問題12"): ("matched", "键 4321：qiantu=weilan 63-66"),
    ("2020-12", "問題13"): ("matched", "键 33：qiantu=weilan 67-68"),
}
VERIFY_SOURCES = {
    "2024-07": ["refs/2024-07_full_jlptzhen.json (jlptzhen quiz)",
                "refs/2024-07_answerkey_diliushixian.md",
                "refs/2024-07_answerkey_youtibao.md"],
    "2025-07": ["refs/2025-07_jlpt247.json (jlpt247 全文転写)",
                "refs/2025-07_answerkey_jlpt247.html (DA N1 7/2025 答案页=vocab/填空/读解/聴解 键)",
                "refs/2025-07_answerkey_nbry.html (宁波爱心日语 aixinjp 66题 键+重建句)",
                "refs/2025-07_answerkey_keedu.html (k:edu 明好小语种 答案,0字节=抓取失败,键取自搜索快照)",
                "/tmp/unojapano_2025-07.html (一茂/uno 参考答案页)",
                "refs/2025-07_vocab_jlptzhen.json (jlptzhen 25问 quiz334,手先判明等)"],
    "2024-12": ["refs/2024-12_jlpt247.json (jlpt247 全文転写)",
                "refs/2024-12_answerkey_aixinjp.html (66题 答案+选项文本)",
                "refs/2024-12_answerkey_learnjapaneseaz.html (文字・語彙/文法官方 Q14-44 交叉)",
                "refs/2024-12_jlpt247_full.html (原始页面 已存档)"],
"2023-07": ["refs/2023-07_jlpt247.json (jlpt247 全文転写,含补录 Q42 选项)",
                 "refs/2023-07_answerkey_nbry.html (宁波爱心日语 aixinjp 66题 键+重建句)",
                 "https://jpnihon.com/5649.html (jpnihon 全题解析,仅搜索引擎快照可读)",
                 "https://www.renrendoc.com/paper/325894810.html (2023年7月N1真题及答案解析,人人文库)",
                 "https://trynihongo.com/ja/de-thi-jlpt-tu-vung-ngu-phap-doc-hieu-n1-07-2023-q1334 (逐题转写+选项文本)"],
    "2022-07": ["refs/2022-07_jlpt247.json (jlpt247 全文転写 68题,問題9=49-57×9等非标准分节)",
                "refs/2022-07_answerkey_nbry.html (宁波爱心日语 aixinjp 68题 键+重建句;読解题逐句吻合选项文本)",
                "新泽真题卷参考答案 (文字語彙+問題5 全部数字同 aixinjp,第二源)",
                "PassJapanese.jp 2022年7月N1参考答案页 (分节结构印证68题真卷)"],
    "2022-12": ["refs/2022-12_jlpt247.json (jlpt247 全文転写 66题)",
                "refs/2022-12_answerkey_nbry.html (aixinjp 66题 键+题号答案对全解析)",
                "refs/2022-12_vocab_jlptzhen.json 词组 quiz (jlptzhen 25/25 与 jlpt247 转写一致,09-08审计)",
                "第六时限同年N1答案页 (読解部分数字与 aixinjp 一致)"],
    "2021-12": ["refs/2021-12_jlpt247.json (jlpt247 全文転写 69题,問題9=49-57×9等非标准分节)",
                "refs/2021-12_answerkey_nbry.html (aixinjp 69题 键+重建句;読解题逐句吻合选项文本)",
                "第六时限同年N1答案页 (回忆版,問題1-5多处与 aixinjp 分歧,经选项文本核实取 aixinjp)"],
    "2020-12": ["refs/2020-12_trynihongo.json (trynihongo 全文転写 68题)",
                "refs/2020-12_keys.json + refs/2020-12_keyreport.txt (keymap 键:问题1-4 jlptzhen 文本为主,问题5-13 前途页 qiantu,转写位置对齐)",
                "refs/2020-12_key_xdfqiantu.html (前途 逐题答案+解析+选项文本,问题6排列 2,3,1,4等×5,答案句逐句吻合)",
                "refs/2020-12_vocab_jlptzhen.json (jlptzhen 25问 问题1-4 键+文本)",
                "refs/2020-12_key_weilan.html (蔚蓝 逐题数字键:问题1-6 与 jlptzhen/qiantu 一致,读解45-68 与 qiantu 文本全符)"],
}
FLAG_TEXT = {"(2024-07, 54)": "⚠️ 答案争议：jlptzhen=2「常に客観視…」 vs 羊驼=3「正義に結びつける」 — 待用户确认"}

# Answers for sessions whose source carries no correct-answer markers
# (jlpt247 watupro quiz has no ⭕/correct flag). Every value comes from the
# archived answer keys cited in VERIFY / guides/source-log.md:
#   aixinjp  (66 written answers, digit + option text)
#   learnjapaneseaz (文字・語彙/文法 Q1-44, independent second source)
# Composition (問題6) = option number that fills the ★ blank, derived from the
# aixinjp full-sentence reconstruction (phrases numbered identically there).
# num -> (answer digit, optional note)
ANSWER_OVERRIDES = {
    "2025-07": {
        1: 2, 2: 2, 3: 4, 4: 1, 5: 4, 6: 3,                       # 問題1 (uno/DA/aixinjp/keedu一致)
        7: 1, 8: 3, 9: 2, 10: 3, 11: 1, 12: 2, 13: 4,            # 問題2 (Q8 手先,见备注)
        14: 3, 15: 4, 16: 4, 17: 2, 18: 3, 19: 1,                # 問題3
        20: 2, 21: 4, 22: 1, 23: 3, 24: 1, 25: 4,                # 問題4 (Q20 见备注)
        26: 2, 27: 1, 28: 4, 29: 3, 30: 4, 31: 1, 32: 4, 33: 1, 34: 2, 35: 3,  # 問題5
        36: 2, 37: 3, 38: 2, 39: 1, 40: 4,                       # 問題6 並べ替え ★ (uno=aixinjp 全一致)
        41: 4, 42: 3, 43: 1, 44: 2,                               # 問題7 (Q41 仅 uno 分歧→4,见备注)
        45: 3, 46: 1, 47: 3, 48: 4,                               # 問題8
        49: 2, 50: 2, 51: 4, 52: 2, 53: 4, 54: 1, 55: 2, 56: 3,   # 問題9 (Q55=aixinjp,见备注)
        57: 4, 58: 2, 59: 1, 60: 4, 61: 4,                        # 問題10-11
        62: 1, 63: 1, 64: 3,                                      # 問題12
        65: 3, 66: 3,                                             # 問題13
    },
    "2024-12": {
        1: 2, 2: 1, 3: 1, 4: 3, 5: 4, 6: 3,                      # 問題1
        7: 1, 8: 4, 9: 3, 10: 4, 11: 2, 12: 1, 13: 3,            # 問題2 (Q13 见备注)
        14: 2, 15: 2, 16: 4, 17: 3, 18: 1, 19: 1,                # 問題3
        20: 2, 21: 4, 22: 4, 23: 3, 24: 2, 25: 1,                # 問題4
        26: 4, 27: 3, 28: 2, 29: 3, 30: 1, 31: 4, 32: 1, 33: 1, 34: 2, 35: 2,  # 問題5
        36: 1, 37: 4, 38: 4, 39: 1, 40: 3,                       # 問題6 並べ替え ★
        41: 3, 42: 4, 43: 1, 44: 2,                               # 問題7
        45: 3, 46: 4, 47: 1, 48: 2,                               # 問題8
        49: 4, 50: 2, 51: 2, 52: 4, 53: 2, 54: 3, 55: 2, 56: 1,   # 問題9
        57: 2, 58: 3, 59: 1,                                      # 問題10
        60: 4, 61: 3,                                             # 問題11
        62: 2, 63: 3, 64: 4,                                      # 問題12
        65: 1, 66: 1,                                             # 問題13
    },
    "2023-07": {
        1: 4, 2: 1, 3: 3, 4: 4, 5: 2, 6: 3,                      # 問題1
        7: 2, 8: 2, 9: 3, 10: 4, 11: 1, 12: 1, 13: 4,            # 問題2
        14: 2, 15: 3, 16: 2, 17: 3, 18: 1, 19: 4,                # 問題3
        20: 4, 21: 2, 22: 3, 23: 1, 24: 3, 25: 1,                # 問題4
        26: 4, 27: 3, 28: 1, 29: 3, 30: 2, 31: 4, 32: 2, 33: 1, 34: 3, 35: 1,  # 問題5
        36: 1, 37: 3, 38: 4, 39: 2, 40: 4,                       # 問題6 並べ替え ★
        41: 2, 42: 1, 43: 3, 44: 4,                               # 問題7 (Q41/43 取 jpnihon 解析,见备注)
        45: 1, 46: 3, 47: 2, 48: 2,                               # 問題8
        49: 3, 50: 4, 51: 4, 52: 2, 53: 3, 54: 1, 55: 1, 56: 4,   # 問題9 (Q56 取 jpnihon=4,见备注)
        57: 3, 58: 3, 59: 4,                                      # 問題10
        60: 3, 61: 1,                                             # 問題11
        62: 4, 63: 3, 64: 4,                                      # 問題12
        65: 2, 66: 4,                                             # 問題13
    },
    "2022-07": {  # 68题真卷：問題9=49-57(×9),問題12=63-66(×4),問題13=67-68
        1: 1, 2: 3, 3: 3, 4: 4, 5: 2, 6: 4,                      # 問題1 (新泽参考答案同 133424)
        7: 4, 8: 2, 9: 2, 10: 1, 11: 1, 12: 3, 13: 3,            # 問題2
        14: 4, 15: 2, 16: 4, 17: 3, 18: 3, 19: 1,                # 問題3
        20: 2, 21: 3, 22: 1, 23: 2, 24: 1, 25: 4,                # 問題4
        26: 2, 27: 3, 28: 1, 29: 4, 30: 1, 31: 2, 32: 3, 33: 4, 34: 2, 35: 2,  # 問題5
        36: 4, 37: 1, 38: 3, 39: 2, 40: 4,                       # 問題6 並べ替え ★ (排列 3241/2413/4231/3124/1342)
        41: 3, 42: 2, 43: 1, 44: 1,                               # 問題7 (自引句 そうした保育園/ただ/入学したとたん/たくましく思えます)
        45: 3, 46: 1, 47: 4, 48: 3,                               # 問題8
        49: 3, 50: 3, 51: 1, 52: 3, 53: 2, 54: 2, 55: 1, 56: 4, 57: 4,  # 問題9
        58: 1, 59: 4, 60: 3,                                      # 問題10
        61: 2, 62: 3,                                             # 問題11
        63: 4, 64: 1, 65: 2, 66: 4,                               # 問題12
        67: 1, 68: 2,                                             # 問題13
    },
    "2022-12": {
        1: 3, 2: 2, 3: 4, 4: 1, 5: 4, 6: 3,                      # 問題1 (读音:かんとく/はせい/すけて/おんけい/のぞむ/にょじつ)
        7: 1, 8: 3, 9: 2, 10: 4, 11: 3, 12: 2, 13: 1,            # 問題2
        14: 4, 15: 2, 16: 1, 17: 2, 18: 4, 19: 3,                # 問題3
        20: 3, 21: 3, 22: 2, 23: 4, 24: 1, 25: 2,                # 問題4
        26: 1, 27: 3, 28: 3, 29: 1, 30: 4, 31: 2, 32: 3, 33: 2, 34: 4, 35: 1,  # 問題5
        36: 2, 37: 4, 38: 2, 39: 1, 40: 3,                       # 問題6 並べ替え ★ (排列 4231/1342/3421/3412/4132)
        41: 3, 42: 4, 43: 2, 44: 1,                               # 問題7
        45: 2, 46: 1, 47: 1, 48: 2,                               # 問題8
        49: 2, 50: 3, 51: 2, 52: 4, 53: 1, 54: 2, 55: 3, 56: 3,   # 問題9
        57: 4, 58: 1, 59: 3,                                      # 問題10
        60: 4, 61: 4,                                             # 問題11
        62: 3, 63: 4, 64: 2,                                      # 問題12
        65: 3, 66: 2,                                             # 問題13
    },
    "2021-12": {  # 69题真卷：問題9=49-57(×9),問題10=58-61(×4),問題11=62-64(×3),問題12=65-67
        1: 4, 2: 3, 3: 1, 4: 2, 5: 3, 6: 1,                      # 問題1 (Q3 与第六时限分歧,取 aixinjp,见备注)
        7: 1, 8: 4, 9: 2, 10: 4, 11: 2, 12: 3, 13: 3,            # 問題2
        14: 3, 15: 1, 16: 3, 17: 2, 18: 4, 19: 2,                # 問題3
        20: 3, 21: 1, 22: 4, 23: 4, 24: 2, 25: 1,                # 問題4
        26: 3, 27: 2, 28: 4, 29: 3, 30: 2, 31: 4, 32: 2, 33: 3, 34: 1, 35: 1,  # 問題5
        36: 1, 37: 4, 38: 4, 39: 2, 40: 1,                       # 問題6 並べ替え ★ (排列 3241/1342/3142/4213/1324)
        41: 1, 42: 3, 43: 4, 44: 2,                               # 問題7
        45: 3, 46: 4, 47: 4, 48: 2,                               # 問題8
        49: 4, 50: 3, 51: 3, 52: 2, 53: 1, 54: 2, 55: 3, 56: 2, 57: 1,  # 問題9 (Q54/55/57 与第六时限分歧,见备注)
        58: 1, 59: 4, 60: 1, 61: 1,                               # 問題10
        62: 2, 63: 2, 64: 3,                                      # 問題11
        65: 4, 66: 2, 67: 3,                                      # 問題12
        68: 2, 69: 2,                                             # 問題13
    },
}
# Per-question notes for answers resolved from conflicting keys.
ANSWER_NOTES = {
    ("2025-07", 8): "手際(uno/DA=4) vs 手先(jlptzhen quiz334=3, 宁波爱心 aixinjp=❸ 手先が器用, 惯用句)；取 3(手先)。",
    ("2025-07", 20): "宁波爱心(2025-07_answerkey_nbry.html)标③但自引文「先方への返答を保留した」=选项2；quiz334/uno 均为2；取 2。",
    ("2025-07", 41): "uno=2(なら,文法不通) vs aixinjp=❹/keedu「それ(だけが)人との関わりではありません」；取 4(だけが)。",
    ("2025-07", 55): "uno/DA=4(高いところに興味がない,与原文「高いところは怖い…脳回路にインストール」矛盾) vs aixinjp=❷(致命的な危険を避ける本能)；取 2。",
    ("2024-12", 13): "答案键分歧：aixinjp=3(とっさに 邻文义正) vs learnjapaneseaz=1(じきに, 疑误)；取 3。",
    ("2024-12", 34): "aixinjp键写了③但自引文本「あってはならない」对应本卷选项2(ことがあってはならない)；取 2。",
    ("2024-12", 54): "aixinjp=3「消費者の反応が変わっていくことを考慮して分析するべきだ」(选项文本逐一匹配)；单源。",
    ("2024-12", 60): "aixinjp=4「上司に言われたことを行うのが仕事だと思っていること」；单源。",
    ("2023-07", 41): "aixinjp=1(小説であってもだ,自引重建句亦为1) vs jpnihon/renrendoc 解析=2(小説でもあるまい,「まさか自恋…むしろ親心」否定推理,两源独立共证)；取 2。",
    ("2023-07", 43): "aixinjp=1(否定せずにいられなくなる=自我否定,与原文「修正しない】目的」逆义) vs jpnihon/renrendoc 解析=3(否定できなくなる)；取 3。",
    ("2023-07", 56): "aixinjp=1(「多様な使い手が平等だという感覚…作るべき」) vs jpnihon 解析=4(常に使い手にとっての平等について考えなければならない)；取 4。",
    ("2022-07", 67): "問題13 Q67 aixinjp=1「9000円と10000円」(案内图 8800円等复选项)；单源但自引文本独立印証。",
    ("2022-12", 1): "問題1 键=3,2,4,1,4,3(读音:かんとく/はせい/すけて/おんけい/のぞむ/にょじつ)；以存档全键为准(早先曾按误读写成1开头)。",
    ("2021-12", 1): "aixinjp=431231；第六时限(回忆版)=433231,於Q3(目に…錯覚=さっかく)分歧,以 aixinjp 重建句为准。",
    ("2021-12", 54): "aixinjp=2 vs 第六时限=1(消费者自评问题)；选项文本&文脉核实取2。",
    ("2021-12", 55): "aixinjp=3 vs 第六时限=4；选项文本核实取3。",
    ("2021-12", 57): "aixinjp=1 vs 第六时限=3；选项文本核实取1。",
    ("2021-12", 69): "键单源 aixinjp；自选句=选项2原文「AとBを使用希望日の3か月前までに提出する。学生課で説明を受ける必要がある」(该問案内图表未随 jlpt247 转写收录,选项文本系其自读图表所得)。",
}

TRAILING_NUM_RE = re.compile(r"(?:^|\n)\s*(\d{1,2})\.\s*\S")


def section_offsets():
    off = {}
    run = 1
    for sect, _, _, size in GROUPS:
        off[sect] = run
        run += size
    return off


def find_num_from_stem(stem):
    # 読解 stems end with a line like "45. 筆者の考えに合うのはどれか。"
    m = list(TRAILING_NUM_RE.finditer(stem or ""))
    return int(m[-1].group(1)) if m else None


def build_verified(session, sect, extra_sources, num):
    status, note = VERIFY.get((session, sect), ("pending", ""))
    sources = list(VERIFY_SOURCES.get(
        session, [f"refs/{session}_full_jlptzhen.json (jlptzhen quiz)"]))
    if extra_sources:
        sources = list(extra_sources) + sources[1:]
    return {"status": status, "note": note, "sources": sources}


def emit(question, summary):
    path = PAST / str(question["year"]) / f"{question['month']:02d}" / question["section"]
    path.mkdir(parents=True, exist_ok=True)
    f = path / f"{question['type']}_{question['number']:02d}.json"
    if f.exists() and not FORCE:
        summary["skipped"] += 1
        summary["skip_list"].append(str(f.name))
        return
    f.write_text(json.dumps(question, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary["written"] += 1
    summary["files"].append(str(f.relative_to(ROOT)))


def main():
    global FORCE
    ap = argparse.ArgumentParser()
    ap.add_argument("session", help="e.g. 2024-07")
    ap.add_argument("--force", action="store_true",
                    help="overwrite existing per-question files")
    args = ap.parse_args()
    FORCE = args.force
    session = args.session
    year, month = (int(x) for x in session.split("-"))
    src_label = "full_jlptzhen"
    for label in ("full_jlptzhen", "jlpt247", "trynihongo"):
        if (REFS / f"{session}_{label}.json").exists():
            src_label = label
            break
    ref = REFS / f"{session}_{src_label}.json"
    if not ref.exists():
        print(f"! missing refs for {session} — run tools/fetch_jlptzhen.py / fetch_jlpt247.py / fetch_trynihongo.py first")
        sys.exit(1)
    from_trynihongo = src_label == "trynihongo"
    legacy_keys = {}
    keys_path = REFS / f"{session}_keys.json"
    if from_trynihongo:
        if not keys_path.exists():
            print(f"! {session} has no refs/{session}_keys.json — run tools/keymap.py {session} first")
            sys.exit(1)
        legacy_keys = json.load(open(keys_path, encoding="utf-8"))
    refs_tag = ref.name
    data = json.load(open(ref, encoding="utf-8"))
    listen_ref = REFS / f"{session}_listening_trynihongo.json"
    if listen_ref.exists():
        extra = json.load(open(listen_ref, encoding="utf-8"))
        data = dict(data)
        data["questions"] = list(data.get("questions", [])) + list(extra["questions"])
    off = section_offsets()
    listen_sects = {f"問題{i}" for i in LISTEN_TYPE}
    summary = {"written": 0, "skipped": 0, "files": [], "skip_list": [], "warns": []}
    idx = {"written": 0, "listening": 0}
    cur_sect = None

    for q in data["questions"]:
        sect = q["section"]
        g = next((g for g in GROUPS if g[0] == sect), None)
        if g is None:
            summary["warns"].append(f"unknown section {sect!r} (qid {q['qid']})")
            continue
        if sect != cur_sect:
            cur_sect = sect
            idx = {"written": 0, "listening": 0}
        sname, rsec, rtype, _ = g
        is_listen = bool(q["audio"])

        if is_listen and sname in listen_sects:
            idx["listening"] += 1
            num = idx["listening"]
            ltype = LISTEN_TYPE[int(sname[-1])]
            question = {
                "id": f"{session}-listening-{ltype}-{num:02d}",
                "year": year, "month": month, "section": "listening", "type": ltype,
                "number": num, "question": q["stem"], "audio": q["audio"],
                "options": list(q["options"]), "answer": str(q["answer"]),
                "explanation": q.get("explanation", "").strip(),
                "difficulty": "medium", "tags": ["聴解"],
                "source": f"JLPT N1 {year}年{month}月 聴解 問題{sname[-1]}({num})",
                "notes": "站方解析已含完整听力脚本(见 explanation)与音频 URL；听写转写另议。",
                "verified": {"status": "structural-unverified",
                             "note": "答案标记为站点自带，尚未独立核验",
                             "sources": [f"refs/{session}_full_jlptzhen.json"]},
            }
            emit(question, summary)
            continue

        # written block
        idx["written"] += 1
        pos = idx["written"]
        if from_trynihongo:
            num = int(q["num"])
        else:
            num = q["num"] if q["num"] is not None else find_num_from_stem(q["stem"])
        if not from_trynihongo:
            if num is None:
                num = off[sname] + pos - 1
            else:
                expected = off[sname] + pos - 1
                if num != expected:
                    summary["warns"].append(
                        f"{sname} qid{q['qid']}: site num={num}, expected {expected} (official numbering "
                        f"assumes complete groups; verify against the paper)")
        target = q.get("target") or ""
        opts = list(q["options"])
        stem = re.sub(r"^[．.。]\s*", "", (q["stem"] or "").strip())
        if rtype == "usage" and target in (".", "。") and stem:
            target = stem

        # resolve the answer digit (jlpt247 / trynihongo carry no correct marker)
        answer = q["answer"]
        note = ""
        if from_trynihongo:
            k = legacy_keys.get(str(num))
            if k is None:
                summary["warns"].append(f"{sname} Q{num}: 无答案来源，跳过写入")
                continue
            answer = int(k["ans"])
            note = f"[{k['source']}] {k.get('note','')}".rstrip()
            an = ANSWER_NOTES.get((session, num), "")
            if an:
                note = (note + " " if note else "") + an
        if answer in (None, ""):
            ao = ANSWER_OVERRIDES.get(session, {}).get(num)
            if ao is None:
                summary["warns"].append(f"{sname} Q{num}: 无答案来源，跳过写入")
                continue
            if isinstance(ao, tuple):
                answer, extra_note = ao
                note = (extra_note + " " if extra_note else "") + (ANSWER_NOTES.get((session, num), "") or "")
            else:
                answer = ao
                note = ANSWER_NOTES.get((session, num), "")
        answer = int(answer)

        notes = FLAG_TEXT.get(f"({session}, {num})", "")
        if note:
            notes = (notes + " " if notes else "") + note
        tags = ([target] if target else ([opts[answer - 1]] if opts else [])) \
            + TAGS_EXTRA.get(rtype, [])
        question = {
            "id": f"{session}-{rsec}-{rtype}-{num:02d}",
            "year": year, "month": month, "section": rsec, "type": rtype,
            "number": num, "question": stem, "target": target,
            "options": opts, "answer": str(answer),
            "explanation": (q.get("explanation") or "").strip(),
            "difficulty": DIFFICULTY[sname], "tags": tags,
            "source": f"JLPT N1 {year}年{month}月 {SECTION_JP[rsec]} {sname}({num})",
            "notes": notes,
            "verified": build_verified(session, sname, [], num),
        }
        emit(question, summary)

    for extra in EXTRA.get((session, "問題2"), []):
        num = extra["num"]
        question = {
            "id": f"{session}-vocab-context-{num:02d}", "year": year, "month": month,
            "section": "vocab", "type": "context", "number": num,
            "question": extra["stem"], "target": extra["target"],
            "options": extra["options"], "answer": str(extra["answer"]),
            "explanation": extra["explanation"], "difficulty": "medium",
            "tags": [extra["target"], "言葉の意味", "文脈規定"],
            "source": f"JLPT N1 {year}年{month}月 言語知識(文字・語彙) 問題2({num})",
            "notes": extra["notes"],
            "verified": build_verified(session, "問題2", extra["extra_sources"], num),
        }
        emit(question, summary)

    print(f"[{session}] source={refs_tag} — wrote {summary['written']} new file(s), "
          f"{summary['skipped']} skipped (exist, kept)")
    for f in summary["files"]:
        print("  +", f)
    for f in summary["skip_list"]:
        print("  =", f)
    for w in summary["warns"]:
        print("  !", w)


if __name__ == "__main__":
    main()