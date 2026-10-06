# jlpt-question-bank（JLPT N1–N5 本地真题库）

JLPT **N1 / N2 / N3 / N4 / N5** 过去问的本地资料库：每题存题干、选项、正解、中文解析与出处
（级别·年度·月份·問題番号），供 `wago-atlas`（和語アトラス）、`japanese-learning`
（koou / karada 课件）等做维度抽取、观测与练习。

- **唯一线上入口**：<https://syu-toutousai.github.io/jlpt-question-bank/>
  （AES-256-GCM 密码门；N1–N5 合并单站，级别 Tab＋年份/题型/关键词筛选＋自测模式）
- 旧 N1 站 <https://syu-toutousai.github.io/jlpt-n1-question-bank/> 已改为**跳转卡**，
  原 `vocab-words*.html` 深链以跳转页保留（指向新站同页）。
- **规模**：5751 題（N1 2746・N2 1111・N3 1257・N4 304・N5 333），正解 5362，收录 2010–2025。
- 本仓库**本地优先**：先把能找到的真题页全部抓回 `refs/` 存档，再离线解析，不依赖现场翻找。

> 沿革：N1 部分原为独立仓库 `jlpt-n1-question-bank`；2026-10 以 `git subtree`
> 方式**全历史并入本仓库 `n1/`**，两库合并为一个题库 repo（一个 Pages 入口）。

## 目录

```
├── past-exams/            # N2–N5 题库正本：<level>/<year>/<month>/<type>/<NN>.json【本地・gitignore】
├── parsed/                # N2–N5 解析后的源 bundle【本地】
├── refs/                  # N2–N5 原始 HTML 存档【本地】
├── sessions.json          # collect.py 生成的会话×源清单
├── manifest.json          # 各会话的源级统计
├── n1/                    # N1 子树（原 jlpt-n1-question-bank，历史完整并入）
│   ├── past-exams/<year>/<month>/<category>/*.json    # N1 正本【本地】
│   ├── question-bank/{by-type,by-year,by-theme}/      # N1 按题型/年份/主题整理副本【本地】
│   ├── analysis/  guides/  tools/  local/  data/      # 分析・指南・工具（tracked）
│   └── refs/                                          # N1 原始档【本地】
├── docs/                  # 唯一 Pages：合并加密站（index.html + data.json + index-meta.json）
│   └── vocab-words*.html  # N1 公开学习材料 27 页（免密，词条卡直链目标）
└── tools/
    ├── encrypt.py         # 合并加密：N2–N5 + N1 → docs/data.json（AAD=jlpt-qb）
    ├── proofread.py       # N1＋N2–N5 全库校对（BANKS 指向 past-exams 与 n1/past-exams）
    └── ...（N2–N5 抓取/解析/答案回填工具，见下）
```

每题 JSON 字段（两子树同形，便于抽取器共用）：

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
N1 的 `answer` 为字符串（`"3"`/`"C"`），N2–N5 为 1-based 整数——合并站前端两者皆可解析。

## Pages（合并加密站）

```bash
python3 tools/encrypt.py          # 收集 N2–N5 + N1 → AES-256-GCM → docs/data.json + index-meta.json
python3 tools/encrypt.py --show   # 查看当前站点密码（本地 docs/.secret.txt）
git add docs tools README.md AGENTS.md && git commit && git push
```

站内：一个密码门 → 级别 Tab（N1–N5）＋年份/题型/筛选＋自测模式；N1 2024 年题目可
直达 `vocab-words*.html` 词条材料。明文题目绝不提交，只推送 `docs/`。

## N1（n1/ 子树）

- 源：N1 2010-07〜2025-07 全量 2746 題（語彙・文法・読解・聴解），用户录入＋比照校对，
  `source` 注明年份·月份·問題番号；解析/抓取工具见 `n1/tools/`。
- 正本 `n1/past-exams/<year>/<month>/<category>/*.json`；`n1/question-bank/` 为
  by-type / by-year / by-theme 整理视图（与正本同 id，加密时自动去重）。
- 本地全量透明版（不加密）开发服务器：`n1/tools/serve.py`（仅绑 127.0.0.1）。

## N2–N5 数据源

| 源 | 内容 | 覆盖 |
|---|---|---|
| **jlptzhen.com** | 語彙・文法 25 問/回，带站方正解＋中文解析；部分回次为全卷（~100 問） | N2 30 回・N3 28 回・N4 5 回・N5 4 回（2010-2025） |
| **jlpt247.com** | 逐题转写全卷（无答案） | N2/N3 多回、N4/N5 少数（2015-2025） |
| **trynihongo.com** | 有年份标注的 N2/N3 全卷页＋N4/N5 成套页（存档于 `refs/trynihongo/`），答案可用 `check_single_question_ajax` 逐题判定 | N2/N3 2010-2024；N4/N5 sets |

## N2–N5 重建

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

- **合并后规模**：5751 題（N1 2746・N2 1111・N3 1257・N4 304・N5 333），正解 5362。
- N2–N5 正解率：2616 / 3005（N2 1017/1111・N3 1162/1257・N4 225/304・N5 212/333）；
  trynihongo 抽取已覆盖 N3 2010-2024 全卷，N2 仍在后台进行。
- N3 的 trynihongo 页只转写到読解前（约 38-39 問/回），其后読解答案需其他来源。

## TODO

1. **N4/N5 补齐**：jlptzhen/jlpt247 均无更多带年份回次；trynihongo 的 N4/N5 成套页无年份标注（可只借答案），待评估；
2. N2/N3 残余読解（N2 94・N3 95）：随机池已采尽，需公开答案键或其他来源；
3. 听力：归档音频链接与スクリプト（trynihongo listening 页）；
4. 答案键：收集公开答案汇总（現有 2023-12 N2 一份，见 `refs/answerkey_2023-12_n2.html`）。

## 校对（proofread）

```bash
python3 tools/proofread.py --bank all          # 只扫描出报告（N1＋N2–N5）
python3 tools/proofread.py --bank all --apply  # 应用高精度自动修正
```

覆盖兼容汉字、站方题号标注、汉字间空格、简体/旧字→日本新字体、大つ/大や行→小写、
已知混淆对、半角括号归一、开头句点等；不确定的一律只报告不改。结果见
[`PROOFREAD.md`](./PROOFREAD.md)（含残留待人工复核清单）。

⚠️ `past-exams/` 是从 `parsed/` 生成的：若重跑 `build_bank.py`，请随后重跑
`proofread.py --apply`，否则修正会被覆盖。

## 出典索引・傾向分析（免密页）

- 免密页：<https://syu-toutousai.github.io/jlpt-question-bank/trends.html>
  （N1 読解原文出典索引・傾向統計・2026-12 模拟押题第一版；真题正文不入此页）
- 生成：

  ```bash
  python3 tools/extract_sources.py   # 読解出典行＋填空/用法 metadata → analysis/source-traces.json
  python3 tools/clean_sources.py     # 確証ある転写誤記のみ補正（raw/evidence 保存）；要確認ラベル
  python3 tools/trace_sources.py     # 未詳の特徴句逆引き（Yahoo 実 Chrome；候補は要確認）
  python3 tools/build_trends.py      # → docs/trends.html（模擬押题 第二版 13 問）
  ```

- 逆引きの現実：N1 読解は広告・書籍からの**改変**が多く、精确短语检索では同定 0/65（工具は保存）。
  今後は解説本・予備校の出典一覧との照合に切替。転写補正は確証分のみ（例：内藤廣・吉田脩二・
  池上彰『〈わかりやすさ〉の勉強法』）で、未確証は「要確認」を維持。

- 出典三层：**読解**＝题面明示的「（〜による）」行（明示 289 / 未詳 369，未詳靠逆引き检索逐步补全）；
  **填空**（問題2・5・7）与**用法**（問題4）＝作成文（不追外典；用法只统计 target 語 125 語的复现）。
- 模拟题全部自写并标注「模擬」；绝不冒充真题。

## 版权

- JLPT 官方不公开真题；本库内容来自公开学习站点的考生回忆/整理（出处见每题 `source`）。
- **使用方针（用户判定）**：在真题或改写练习中**打乱顺序、重建为观测维度**并
  **注明出处（年份·级别）**的引用方式，不涉及版权问题；可以引用并做成练习，
  也可以把阅读里出现的语言现象做成选择题。所有引用一律保留来源标注。
