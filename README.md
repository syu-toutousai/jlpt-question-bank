# jlpt-question-bank（N2-N5 本地真题库）

JLPT **N2 / N3 / N4 / N5** 过去问的本地资料库：每题存题干、选项、正解、中文解析与出处
（级别·年度·月份·問題番号），供 `wago-atlas`（和語アトラス）等课件做「大和言葉」维度的
抽取、观测与练习。

- **N1 另见**：`../jlpt-n1-question-bank/`（2010-2025 全量，已有点读站与加密 Pages）。
- 本仓库**本地优先**：先把能找到的真题页全部抓回 `refs/` 存档，再离线解析，不依赖现场翻找。

## 数据源

| 源 | 内容 | 覆盖 |
|---|---|---|
| **jlptzhen.com** | 語彙・文法 25 問/回，带站方正解＋中文解析；部分回次为全卷（~100 問） | N2 30 回・N3 28 回・N4 5 回・N5 4 回（2010-2025） |
| **jlpt247.com** | 逐题转写全卷（无答案） | N2/N3 多回、N4/N5 少数（2015-2025） |
| **trynihongo.com** | 有年份标注的 N2/N3 全卷页＋N4/N5 成套页（存档于 `refs/trynihongo/`），答案可用 `check_single_question_ajax` 逐题判定（待抽取） | N2/N3 2010-2024；N4/N5 sets |

## 现状（2026-10）

```
75 sessions = N2 30 + N3 28 + N4 9 + N5 8
3005 questions, 1911 answered（正解あり）
```

- **語彙+文法（問題1-5）**：jlptzhen 基本全覆盖，答案/解析完整；
- **読解・並べ替え・文章の文法**：jlpt247 有逐题转写，答案多数待补
  （trynihongo 存档已就位，抽答案脚本见 TODO）；
- 少数 jlpt247 "更新公告"页（0 Q）与 jlptzhen 全卷回次需单独处理。

## 目录

```
├── sessions.json          # collect.py 生成的会话×源清单
├── refs/                  # 原始 HTML 存档（jlptzhen/jlpt247 + trynihongo/）
├── parsed/                # 解析后的源 bundle（每题含 stem/options/answer/explanation）
├── past-exams/            # 题库正本：<level>/<year>/<month>/<type>/<NN>.json
│   └── manifest.json      # 覆盖与答案统计
├── manifest.json          # 各会话的源级统计
└── tools/
    ├── collect.py         # sitemap → sessions.json → refs/ 全量下载
    ├── parse_all.py       # refs/ → parsed/（+ manifest.json）
    ├── build_bank.py      # parsed/ → past-exams/（跨源合并答案）
    ├── extract_trynihongo.py  # 答案逐题判定（--shard k/n 并行；checkpoint 到 refs/answers_trynihongo/）
    ├── enrich_answer_opts.py  # 从归档 HTML 离线补选项文本
    ├── apply_trynihongo.py    # 抽取答案 → past-exams/（题干+选项双路匹配）
    ├── harvest_pools.py       # jlptzhen 随机池重复采集（每次抽样不同）
    ├── apply_pools.py         # 池题答案 → past-exams/（题干+选项匹配）
    ├── fetch_jlptzhen.py  # 单页解析器（改编自 N1 仓库）
    └── fetch_jlpt247.py   # 单页解析器（改编自 N1 仓库）
```

每题 JSON 字段（与 N1 仓库 `past-exams/` 同形，便于抽取器复用）：

```jsonc
{
  "id": "2024-07-n2-s08-grammar-composition-01",
  "level": "n2", "year": 2024, "month": 7,
  "section": "問題8", "type": "grammar-composition", "number": 1,
  "question": "…★…", "target": "",
  "options": ["…", "…", "…", "…"],
  "answer": 2, "answer_text": "わかる。",
  "explanation": "中文解析（jlptzhen）",
  "source": "JLPT N2 2024年7月 問題8(1)",
  "sources": ["jlptzhen"], "answer_source": "jlptzhen",
  "verified": {"status": "parsed", "note": ""}
}
```

`answer: null` = 有转写但正解未确定（`verified.status = "transcript-only"`）。

## 重建

```bash
python3 tools/collect.py --inventory     # 刷新会话清单（读两站 sitemap）
python3 tools/collect.py --download      # 增量抓取缺失页面（限速 1.5s）
python3 tools/parse_all.py               # 解析 refs/ → parsed/
python3 tools/build_bank.py              # 合并 → past-exams/
# 答案抽取（N2/N3 有年份的 trynihongo 页，约 6 路并行）
for k in 1 2 3 4 5 6; do python3 tools/extract_trynihongo.py --shard $k/6 --sleep 0.2 & done
python3 tools/enrich_answer_opts.py      # 离线补选项（匹配用）
python3 tools/apply_trynihongo.py        # 回填答案（可反复跑）
```

## 状态（2026-10）

- **正解率**：2570 / 3005（N2 1017/1111・N3 1162/1257・N4 223/304・N5 168/333）。
- trynihongo 抽取已覆盖 N3 2010-2024 全卷；N2 仍在后台进行（`extract_trynihongo.py --shard`）。
- N3 的 trynihongo 页只转写到読解前（约 38-39 問/回），其后読解答案需其他来源。

## TODO

1. **N4/N5 补齐**：jlptzhen/jlpt247 均无更多带年份回次；trynihongo 的 N4/N5 成套页无年份标注（可只借答案），待评估；
2. N2/N3 残余読解（N2 94・N3 95）：随机池已采尽，需公开答案键或其他来源；
3. 听力：归档音频链接与スクリプト（trynihongo listening 页）；
4. 答案键：收集公开答案汇总（現有 2023-12 N2 一份，见 `refs/answerkey_2023-12_n2.html`）。

## 版权

- JLPT 官方不公开真题；本库内容来自公开学习站点的考生回忆/整理（出处见每题 `source`）。
- **使用方针（用户判定）**：在真题或改写练习中**打乱顺序、重建为观测维度**并
  **注明出处（年份·级别）**的引用方式，不涉及版权问题；可以引用并做成练习，
  也可以把阅读里出现的语言现象做成选择题。所有引用一律保留来源标注。

## GitHub Pages（加密站点）

明文题目（`past-exams/`、`parsed/`、`refs/`）**绝不提交**，只推送加密后的 `docs/`：

```bash
python3 tools/encrypt.py          # 收集 past-exams → AES-256-GCM → docs/data.json
python3 tools/encrypt.py --show   # 查看当前站点密码（本地 docs/.secret.txt）
git add docs tools README.md AGENTS.md && git commit && git push
```

站点：`https://syu-toutousai.github.io/jlpt-question-bank/`（Pages 源＝main /docs），
打开后输入密码，浏览器内解密，支持 级别/年份/题型/关键词 过滤与自测模式。
答案回填后重新 encrypt+push 即更新。
