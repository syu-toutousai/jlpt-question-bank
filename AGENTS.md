# AGENTS.md — jlpt-question-bank（N2-N5）作业守则

本仓库为 **JLPT N2-N5 本地真题资料库**，供课件（如 `wago-atlas`）做维度抽取与练习。
规则从 `../jlpt-n1-question-bank/AGENTS.md` 精简而来。

## 1. 数据原则

- **不伪造**：题干、选项、正解只能来自抓取/人工录入并核对，绝不臆造。
- **必注出处**：每题保留 `source`（级别·年份·月份·問題番号）与 `sources`（哪个源）。
- **答案未定就留空**：`answer: null` + `verified.status="transcript-only"`，不要猜。
- **增量**：抓取以 `refs/` 存档为事实源；解析产物 `parsed/`、`past-exams/` 可随时重建。

## 2. 文件约定

- `refs/` 存原始 HTML（体积大，允许本地保留；如需公开再评估）。
- `past-exams/<level>/<year>/<month>/<type>/<NN>.json` 为题库正本，id 形如
  `YYYY-MM-<level>-<type>-NN`；追加/修正只改对应 JSON。
- 中文解析来自 jlptzhen 站点，保留原样并在 `answer_source` 标注。

## 3. 引用与版权（用户判定，照此执行）

- 在真题或练习中**打乱顺序、重建为观测维度**并**注明出处（年份·级别）**的引用，
  **不涉及版权问题**；可以引用、可以做成练习；把读解中的语言现象改造成选择题也可以。
- 仍须保留 `source` 出处标注，不声称原创。

## 4. 命令

```bash
python3 tools/collect.py --inventory   # 刷新会话清单
python3 tools/collect.py --download    # 抓取缺失页（限速）
python3 tools/parse_all.py             # refs → parsed
python3 tools/build_bank.py            # parsed → past-exams
```

## 5. Git

- 仅当用户明确要求时 commit / push。
- 提交信息走既有风格：`Add N2 2015-07, N3 2016-12 …`、`Fix answer …`。
