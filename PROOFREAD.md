# 题库校对报告（2026-10-05）

对 **N1（2746 题）＋ N2-N5（3006 题）** 共 5752 个题目文件做规则化校对。
扫描字段：`question` / `target` / `options`（不含中文解析）。工具：`tools/proofread.py`。

## 自动修正（已应用）

| 规则 | 处数 | 说明 |
|---|---|---|
| compat-ideograph | 1950 |
| site-label | 1304 |
| space-between-cjk | 454 |
| halfwidth-paren | 213 |
| simplified-char | 143 |
| leading-dot | 72 |
| known-confusion | 32 |
| kana-size | 31 |

- **compat-ideograph**：兼容汉字/部首字符（⽇・⼈・⾒…）→ 标准汉字（N1 转写来源）
- **site-label**：去除站方题号标注「问题01-01」等 1304 处
- **space-between-cjk**：汉字/假名之间的多余 ASCII 空格
- **simplified-char**：简体/旧字体 → 日本新字体（逐字精选表，避免误伤 体・国・学・雇 等）
- **kana-size**：大つ・大や行 → 小写（しまつた→しまった 等 31 处）
- **known-confusion**：段落级确证错字（進字→進学・育ちににくい→育ちにくい・そっちのけでで→そっちのけで 等）
- **halfwidth-paren**：半角括号与全角混用且合并计数平衡 → 统一全角
- **leading-dot**：题干开头多余句点

## 残留待人工复核（未自动改，避免误伤）

| 类别 | 件数 | 说明 |
|---|---|---|
| bracket 「」『』（） | 335 | 引号/括号不配对：多为长篇读解转写时漏闭合，或引语跨段；需按上下文补 |
| dup-punct 。。、、 | 8 | 多为文体（「。。。」「、、」有意使用，2012-07 読解正文即在讨论标点） |

### 残留明细

| 库 | 题目 ID | 字段 | 规则 | 详情 |
|---|---|---|---|---|
| n1 | 2010-07-grammar-composition-37 | question | bracket | 「」 不配对 (2/1) |
| n1 | 2010-07-reading-short-47 | question | bracket | 『』 不配对 (0/1) |
| n1 | 2010-07-vocab-usage-21 | options[2] | bracket | 「」 不配对 (1/0) |
| n1 | 2010-12-grammar-choice-30 | question | bracket | 「」 不配对 (0/1) |
| n1 | 2010-12-reading-long-66 | question | bracket | 「」 不配对 (9/10) |
| n1 | 2011-07-grammar-choice-34 | question | bracket | 「」 不配对 (2/1) |
| n1 | 2011-07-reading-long-63 | question | bracket | （） 不配对 (9/8) |
| n1 | 2011-07-reading-long-63 | question | bracket | 「」 不配对 (3/2) |
| n1 | 2011-07-reading-long-64 | question | bracket | （） 不配对 (9/8) |
| n1 | 2011-07-reading-long-64 | question | bracket | 「」 不配对 (3/2) |
| n1 | 2011-07-reading-mid-56 | question | bracket | 「」 不配对 (9/10) |
| n1 | 2011-07-reading-mid-56 | question | bracket | 『』 不配对 (1/0) |
| n1 | 2011-07-reading-mid-57 | question | bracket | 「」 不配对 (10/11) |
| n1 | 2011-07-reading-mid-57 | question | bracket | 『』 不配对 (1/0) |
| n1 | 2011-07-reading-mid-58 | question | bracket | 「」 不配对 (10/11) |
| n1 | 2011-07-reading-mid-58 | question | bracket | 『』 不配对 (1/0) |
| n1 | 2011-12-reading-short-47 | question | bracket | 「」 不配对 (0/1) |
| n1 | 2011-12-reading-short-48 | question | bracket | 『』 不配对 (1/0) |
| n1 | 2012-07-grammar-choice-27 | question | bracket | 「」 不配对 (1/0) |
| n1 | 2012-07-reading-mid-56 | question | dup-punct | 、、 |
| n1 | 2012-07-reading-mid-57 | question | dup-punct | 、、 |
| n1 | 2012-07-reading-mid-58 | question | dup-punct | 、、 |
| n1 | 2012-12-grammar-choice-33 | question | bracket | 「」 不配对 (2/1) |
| n1 | 2012-12-grammar-passage-41 | question | bracket | （） 不配对 (8/9) |
| n1 | 2012-12-grammar-passage-42 | question | bracket | （） 不配对 (8/9) |
| n1 | 2012-12-grammar-passage-43 | question | bracket | （） 不配对 (8/9) |
| n1 | 2012-12-grammar-passage-44 | question | bracket | （） 不配对 (8/9) |
| n1 | 2012-12-grammar-passage-45 | question | bracket | （） 不配对 (8/9) |
| n1 | 2012-12-reading-long-59 | question | bracket | 「」 不配对 (12/13) |
| n1 | 2012-12-reading-long-59 | question | bracket | 『』 不配对 (1/0) |
| n1 | 2012-12-reading-long-60 | question | bracket | 「」 不配对 (12/13) |
| n1 | 2012-12-reading-long-60 | question | bracket | 『』 不配对 (1/0) |
| n1 | 2012-12-reading-long-61 | question | bracket | 「」 不配对 (11/12) |
| n1 | 2012-12-reading-long-61 | question | bracket | 『』 不配对 (1/0) |
| n1 | 2012-12-reading-long-62 | question | bracket | 「」 不配对 (11/12) |
| n1 | 2012-12-reading-long-62 | question | bracket | 『』 不配对 (1/0) |
| n1 | 2012-12-reading-long-63 | question | bracket | （） 不配对 (6/7) |
| n1 | 2012-12-reading-long-64 | question | bracket | （） 不配对 (6/7) |
| n1 | 2013-12-grammar-choice-34 | question | bracket | 「」 不配对 (2/1) |
| n1 | 2013-12-reading-long-65 | question | bracket | 「」 不配对 (8/9) |
| n1 | 2013-12-reading-long-66 | question | bracket | 「」 不配对 (7/8) |
| n1 | 2013-12-reading-long-67 | question | bracket | 「」 不配对 (7/8) |
| n1 | 2013-12-reading-long-68 | question | bracket | 「」 不配对 (7/8) |
| n1 | 2014-07-reading-long-69 | question | bracket | () 不配对 (4/8) |
| n1 | 2014-07-reading-long-70 | question | bracket | () 不配对 (4/8) |
| n1 | 2015-07-reading-long-69 | question | bracket | （） 不配对 (7/11) |
| n1 | 2015-07-reading-long-70 | question | bracket | （） 不配对 (5/10) |
| n1 | 2015-12-grammar-choice-30 | question | bracket | () 不配对 (0/1) |
| n1 | 2015-12-reading-mid-56 | question | bracket | () 不配对 (1/0) |
| n1 | 2015-12-reading-mid-57 | question | bracket | () 不配对 (1/0) |
| n1 | 2015-12-reading-mid-58 | question | bracket | () 不配对 (1/0) |
| n1 | 2016-07-grammar-passage-41 | question | bracket | 「」 不配对 (5/6) |
| n1 | 2016-07-grammar-passage-41 | question | bracket | 『』 不配对 (1/0) |
| n1 | 2016-07-grammar-passage-42 | question | bracket | 「」 不配对 (5/6) |
| n1 | 2016-07-grammar-passage-42 | question | bracket | 『』 不配对 (1/0) |
| n1 | 2016-07-grammar-passage-43 | question | bracket | 「」 不配对 (5/6) |
| n1 | 2016-07-grammar-passage-43 | question | bracket | 『』 不配对 (1/0) |
| n1 | 2016-07-grammar-passage-44 | question | bracket | 「」 不配对 (5/6) |
| n1 | 2016-07-grammar-passage-44 | question | bracket | 『』 不配对 (1/0) |
| n1 | 2016-07-grammar-passage-45 | question | bracket | 「」 不配对 (5/6) |
| n1 | 2016-07-grammar-passage-45 | question | bracket | 『』 不配对 (1/0) |
| n1 | 2016-07-reading-long-69 | question | bracket | () 不配对 (8/13) |
| n1 | 2016-07-reading-long-70 | question | bracket | () 不配对 (9/14) |
| n1 | 2018-07-reading-short-46 | question | bracket | 「」 不配对 (4/3) |
| n1 | 2018-12-reading-long-69 | options[1] | bracket | 「」 不配对 (0/1) |
| n1 | 2018-12-reading-long-70 | question | bracket | 「」 不配对 (1/0) |
| n1 | 2019-12-reading-mid-56 | options[2] | bracket | 「」 不配对 (0/1) |
| n1 | 2020-12-grammar-passage-41 | question | bracket | 「」 不配对 (2/3) |
| n1 | 2020-12-grammar-passage-42 | question | bracket | 「」 不配对 (2/3) |
| n1 | 2020-12-grammar-passage-43 | question | bracket | 「」 不配对 (2/3) |
| n1 | 2020-12-grammar-passage-44 | question | bracket | 「」 不配对 (2/3) |
| n1 | 2020-12-reading-long-67 | question | bracket | （） 不配对 (7/8) |
| n1 | 2020-12-reading-long-68 | question | bracket | （） 不配对 (7/8) |
| n1 | 2021-12-grammar-passage-41 | question | bracket | 「」 不配对 (4/5) |
| n1 | 2021-12-grammar-passage-42 | question | bracket | 「」 不配对 (4/5) |
| n1 | 2021-12-grammar-passage-43 | question | bracket | 「」 不配对 (4/5) |
| n1 | 2021-12-grammar-passage-44 | question | bracket | 「」 不配对 (4/5) |
| n1 | 2021-12-reading-mid-49 | question | bracket | （） 不配对 (3/4) |
| n1 | 2021-12-reading-mid-50 | question | bracket | （） 不配对 (3/4) |
| n1 | 2021-12-reading-mid-51 | question | bracket | （） 不配对 (3/4) |
| n1 | 2021-12-reading-mid-52 | question | bracket | （） 不配对 (11/10) |
| n1 | 2021-12-reading-mid-52 | question | bracket | () 不配对 (2/4) |
| n1 | 2021-12-reading-mid-53 | question | bracket | （） 不配对 (11/10) |
| n1 | 2021-12-reading-mid-53 | question | bracket | () 不配对 (2/4) |
| n1 | 2021-12-reading-mid-54 | question | bracket | （） 不配对 (11/10) |
| n1 | 2021-12-reading-mid-54 | question | bracket | () 不配对 (2/4) |
| n1 | 2021-12-reading-mid-55 | question | bracket | （） 不配对 (17/16) |
| n1 | 2021-12-reading-mid-55 | question | bracket | () 不配对 (3/5) |
| n1 | 2021-12-reading-mid-56 | question | bracket | （） 不配对 (17/16) |
| n1 | 2021-12-reading-mid-56 | question | bracket | () 不配对 (3/5) |
| n1 | 2021-12-reading-mid-57 | question | bracket | （） 不配对 (17/16) |
| n1 | 2021-12-reading-mid-57 | question | bracket | () 不配对 (3/5) |
| n1 | 2021-12-reading-short-48 | question | bracket | （） 不配对 (1/2) |
| n1 | 2022-07-grammar-passage-41 | question | dup-punct | 。。 |
| n1 | 2022-07-grammar-passage-42 | question | dup-punct | 。。 |
| n1 | 2022-07-grammar-passage-43 | question | dup-punct | 。。 |
| n1 | 2022-07-grammar-passage-44 | question | dup-punct | 。。 |
| n1 | 2022-07-vocab-paraphrase-14 | question | bracket | () 不配对 (1/0) |
| n1 | 2022-12-grammar-choice-33 | question | bracket | 「」 不配对 (0/1) |
| n1 | 2022-12-reading-long-62 | question | bracket | 「」 不配对 (8/7) |
| n1 | 2022-12-reading-long-63 | question | bracket | 「」 不配对 (8/7) |
| n1 | 2022-12-reading-long-64 | question | bracket | 「」 不配对 (8/7) |
| n1 | 2024-07-grammar-composition-37 | question | bracket | 「」 不配对 (1/0) |
| n1 | 2024-07-reading-long-60 | question | bracket | 「」 不配对 (8/7) |
| n1 | 2024-07-reading-long-61 | question | bracket | 「」 不配对 (8/7) |
| n1 | 2024-07-reading-short-46 | question | bracket | （） 不配对 (1/2) |
| n1 | 2024-12-reading-short-48 | question | bracket | 「」 不配对 (7/6) |
| n2n5 | 2017-12-n2-s00-unknown-33 | question | bracket | （） 不配对 (1/2) |
| n2n5 | 2019-07-n2-s00-unknown-32 | question | bracket | 「」 不配对 (2/1) |
| n2n5 | 2019-07-n2-s00-unknown-35 | question | bracket | 「」 不配对 (3/2) |
| n2n5 | 2019-07-n2-s00-unknown-41 | question | bracket | 「」 不配对 (2/1) |
| n2n5 | 2023-07-n2-s04-問題4-01 | target | bracket | （） 不配对 (1/0) |
| n2n5 | 2023-07-n2-s04-問題4-02 | target | bracket | （） 不配对 (1/0) |
| n2n5 | 2023-07-n2-s04-問題4-03 | target | bracket | （） 不配对 (1/0) |
| n2n5 | 2023-07-n2-s04-問題4-04 | target | bracket | （） 不配对 (1/0) |
| n2n5 | 2023-07-n2-s04-問題4-06 | target | bracket | （） 不配对 (1/0) |
| n2n5 | 2023-07-n2-s04-問題4-fill-07 | target | bracket | （） 不配对 (1/0) |
| n2n5 | 2024-07-n2-s09-grammar-passage-01 | question | bracket | 「」 不配对 (1/0) |
| n2n5 | 2024-07-n2-s09-grammar-passage-02 | question | bracket | 「」 不配对 (1/0) |
| n2n5 | 2024-07-n2-s09-grammar-passage-03 | question | bracket | 「」 不配对 (1/0) |
| n2n5 | 2024-07-n2-s09-grammar-passage-04 | question | bracket | 「」 不配对 (1/0) |
| n2n5 | 2024-12-n2-s04-問題4-02 | target | bracket | （） 不配对 (1/0) |
| n2n5 | 2024-12-n2-s04-問題4-07 | target | bracket | （） 不配对 (1/0) |
| n2n5 | 2024-12-n2-s04-問題4-fill-01 | target | bracket | （） 不配对 (1/0) |
| n2n5 | 2024-12-n2-s04-問題4-fill-03 | target | bracket | （） 不配对 (1/0) |
| n2n5 | 2024-12-n2-s04-問題4-fill-04 | target | bracket | （） 不配对 (1/0) |
| n2n5 | 2024-12-n2-s04-問題4-fill-05 | target | bracket | （） 不配对 (1/0) |
| n2n5 | 2024-12-n2-s04-問題4-fill-06 | target | bracket | （） 不配对 (1/0) |
| n2n5 | 2024-12-n2-s10-grammar-passage-05 | question | bracket | 「」 不配对 (9/8) |
| n2n5 | 2017-07-n3-s00-grammar-composition-50 | question | bracket | 「」 不配对 (2/1) |
| n2n5 | 2018-07-n3-s00-unknown-43 | question | bracket | 「」 不配对 (2/1) |
| n2n5 | 2018-07-n3-s00-unknown-47 | question | bracket | 「」 不配对 (2/1) |
| n2n5 | 2018-12-n3-s00-grammar-composition-53 | question | bracket | 「」 不配对 (1/0) |
| n2n5 | 2018-12-n3-s00-unknown-41 | question | bracket | 「」 不配对 (2/1) |
| n2n5 | 2018-12-n3-s00-unknown-43 | question | bracket | 「」 不配对 (3/1) |
| n2n5 | 2020-12-n3-s00-unknown-46 | question | bracket | 「」 不配对 (3/2) |
| n2n5 | 2021-12-n3-s01-reading-04 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s01-vocab-reading-01 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s01-vocab-reading-02 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s01-vocab-reading-03 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s01-vocab-reading-05 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s01-vocab-reading-06 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s01-vocab-reading-07 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s02-vocab-reading-01 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s02-vocab-writing-02 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s02-vocab-writing-03 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s02-vocab-writing-04 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s02-vocab-writing-05 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s02-vocab-writing-06 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s03-vocab-writing-01 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s03-問題3-fill-02 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s03-問題3-fill-03 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s03-問題3-fill-04 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s03-問題3-fill-05 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s03-問題3-fill-06 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s03-問題3-fill-07 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s03-問題3-fill-08 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s03-問題3-fill-09 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s03-問題3-fill-10 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s03-問題3-fill-11 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s04-問題4-02 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s04-問題4-02 | target | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s04-問題4-03 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s04-問題4-03 | target | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s04-問題4-04 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s04-問題4-04 | target | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s04-問題4-05 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s04-問題4-05 | target | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s04-問題4-06 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2021-12-n3-s04-問題4-06 | target | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s04-問題4-fill-01 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s04-問題4-fill-01 | target | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s05-問題5-01 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s05-問題5-02 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s05-問題5-03 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s05-問題5-04 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s05-問題5-05 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s06-問題6-01 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s06-問題6-02 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s06-問題6-03 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s06-問題6-04 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s06-問題6-05 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s06-問題6-06 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s06-問題6-07 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s06-問題6-08 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s06-問題6-09 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s06-問題6-10 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s06-問題6-11 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s06-問題6-12 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s06-問題6-13 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s07-grammar-composition-01 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s07-grammar-composition-02 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s07-grammar-composition-03 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s07-grammar-composition-04 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s07-grammar-composition-05 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s08-問題8-01 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s08-問題8-02 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s08-問題8-03 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2021-12-n3-s08-問題8-04 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s01-reading-01 | question | dup-punct | 。。 |
| n2n5 | 2022-12-n3-s01-reading-01 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s01-reading-02 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s01-reading-03 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s01-reading-04 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s01-reading-05 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s01-reading-06 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s01-reading-07 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s01-reading-08 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s02-問題2-01 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s02-問題2-02 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s02-問題2-03 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s02-問題2-04 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s02-問題2-05 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s02-問題2-06 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s03-問題3-01 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s03-問題3-02 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s03-問題3-03 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s03-問題3-04 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s03-問題3-05 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s03-問題3-06 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s03-問題3-07 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s03-問題3-08 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s03-問題3-09 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s03-問題3-10 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s03-問題3-11 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s04-問題4-01 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s04-問題4-01 | target | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s04-問題4-02 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s04-問題4-02 | target | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s04-問題4-03 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s04-問題4-03 | target | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s04-問題4-04 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s04-問題4-04 | target | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s04-問題4-05 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s04-問題4-05 | target | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s05-問題5-01 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s05-問題5-02 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s05-問題5-03 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s05-問題5-04 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s05-問題5-05 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s06-問題6-01 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s06-問題6-02 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s06-問題6-03 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s06-問題6-04 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s06-問題6-05 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s06-問題6-06 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s06-問題6-07 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s06-問題6-08 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s06-問題6-08 | question | bracket | 「」 不配对 (2/1) |
| n2n5 | 2022-12-n3-s06-問題6-09 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s06-問題6-10 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s06-問題6-11 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s06-問題6-12 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s06-問題6-13 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2022-12-n3-s07-grammar-composition-01 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s07-grammar-composition-02 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s07-grammar-composition-03 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s07-grammar-composition-04 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s07-grammar-composition-05 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2022-12-n3-s08-問題8-01 | question | bracket | () 不配对 (4/5) |
| n2n5 | 2022-12-n3-s08-問題8-02 | question | bracket | () 不配对 (4/5) |
| n2n5 | 2022-12-n3-s08-問題8-03 | question | bracket | () 不配对 (4/5) |
| n2n5 | 2022-12-n3-s08-問題8-04 | question | bracket | () 不配对 (4/5) |
| n2n5 | 2023-07-n3-s06-問題6-11 | question | bracket | 「」 不配对 (2/1) |
| n2n5 | 2024-07-n3-s01-vocab-reading-01 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s01-vocab-reading-02 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s01-vocab-reading-03 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s01-vocab-reading-04 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s01-vocab-reading-05 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s01-vocab-reading-06 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s01-vocab-reading-07 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s01-vocab-reading-08 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s01-問題1-fill-09 | question | bracket | （） 不配对 (0/1) |
| n2n5 | 2024-07-n3-s01-問題1-fill-10 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s01-問題1-fill-11 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s01-問題1-fill-12 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s01-問題1-fill-13 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s01-問題1-fill-14 | question | bracket | () 不配对 (2/3) |
| n2n5 | 2024-07-n3-s01-問題1-fill-15 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s01-問題1-fill-16 | question | bracket | () 不配对 (2/3) |
| n2n5 | 2024-07-n3-s01-問題1-fill-17 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s01-問題1-fill-18 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s01-問題1-fill-18 | question | bracket | 「」 不配对 (1/2) |
| n2n5 | 2024-07-n3-s01-問題1-fill-19 | question | bracket | () 不配对 (2/3) |
| n2n5 | 2024-07-n3-s01-問題1-fill-20 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s01-問題1-fill-21 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s02-grammar-composition-07 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s02-grammar-composition-08 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s02-grammar-composition-09 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s02-grammar-composition-10 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s02-grammar-composition-11 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s02-grammar-composition-11 | question | bracket | 「」 不配对 (3/2) |
| n2n5 | 2024-07-n3-s02-vocab-writing-01 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s02-vocab-writing-02 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s02-vocab-writing-03 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s02-vocab-writing-04 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s02-vocab-writing-05 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s02-vocab-writing-06 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s03-問題3-fill-01 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s03-問題3-fill-02 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s03-問題3-fill-03 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s03-問題3-fill-04 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s03-問題3-fill-05 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s03-問題3-fill-06 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s03-問題3-fill-07 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s03-問題3-fill-08 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s03-問題3-fill-09 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s03-問題3-fill-10 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s04-grammar-passage-06 | question | bracket | () 不配对 (2/3) |
| n2n5 | 2024-07-n3-s04-grammar-passage-06 | options[1] | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s04-grammar-passage-06 | options[3] | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s04-grammar-passage-07 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s04-grammar-passage-08 | question | bracket | () 不配对 (5/6) |
| n2n5 | 2024-07-n3-s04-grammar-passage-09 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s04-vocab-paraphrase-01 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s04-vocab-paraphrase-02 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s04-vocab-paraphrase-03 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s04-vocab-paraphrase-04 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s04-vocab-paraphrase-05 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s05-grammar-passage-06 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s05-grammar-passage-07 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s05-grammar-passage-08 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s05-grammar-passage-09 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s05-grammar-passage-10 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s05-grammar-passage-11 | question | bracket | () 不配对 (1/2) |
| n2n5 | 2024-07-n3-s05-vocab-usage-01 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s05-vocab-usage-02 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s05-vocab-usage-02 | options[1] | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s05-vocab-usage-03 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s05-vocab-usage-04 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s05-vocab-usage-05 | question | bracket | () 不配对 (0/1) |
| n2n5 | 2024-07-n3-s06-grammar-passage-01 | question | bracket | () 不配对 (2/3) |
| n2n5 | 2024-07-n3-s06-grammar-passage-02 | question | bracket | () 不配对 (2/3) |
| n2n5 | 2024-07-n3-s06-grammar-passage-03 | question | bracket | () 不配对 (2/3) |
| n2n5 | 2024-07-n3-s06-grammar-passage-04 | question | bracket | () 不配对 (2/3) |
| n2n5 | 2024-07-n3-s07-問題7-01 | question | bracket | () 不配对 (6/7) |
| n2n5 | 2024-07-n3-s07-問題7-02 | question | bracket | () 不配对 (7/8) |
| n2n5 | 2024-07-n3-s07-問題7-02 | options[0] | bracket | () 不配对 (0/2) |
| n2n5 | 2024-07-n3-s07-問題7-02 | options[1] | bracket | () 不配对 (0/2) |
| n2n5 | 2017-07-n5-s00-unknown-39 | question | bracket | 「」 不配对 (2/1) |
| n2n5 | 2017-07-n5-s00-unknown-44 | question | bracket | （） 不配对 (2/1) |
| n2n5 | 2017-07-n5-s00-unknown-49 | question | bracket | 「」 不配对 (2/0) |
| n2n5 | 2017-07-n5-s00-unknown-50 | question | bracket | 「」 不配对 (3/2) |
