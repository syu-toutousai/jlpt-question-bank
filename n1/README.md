# JLPT N1 Question Bank (日本語能力試験 N1 問題集)

Comprehensive question bank for JLPT N1 exam preparation, with past exam questions organized by type, year, and theme.

## Mission (repo定位)

这是一个**超长线任务 repo**：

1. **时间跨度**：从现在开始，持续到今年 12 月的 JLPT N1 考试，甚至更久 —— 直到用户通过 N1 考试为止。repo 内容随时间滚动积累。
2. **内容来源**：用户自行手动录入内容（仅限可手工输入的内容，如题干、选项、答案、解析、笔记等）。Agent 不替他编造真题内容。
3. **质量保障**：Agent 应积极与互联网资源比照校对，审阅用户录入的内容 —— 核对真题原文、答案对错、出处年份/题号、解析准确性等，并将校对结果反馈给用户。

## Exam Structure (試験構成)

### 言語知識（文字・語彙・文法）・読解 - 110分 （2024年7月版式）

#### 文字・語彙
| 問題 | 題型 | 数量 |
|------|------|------|
| 問題1 | 読み方（漢字） | 6題 |
| 問題2 | 文脈規定（語彙） | 7題 |
| 問題3 | 言い換え・類義（語彙） | 6題 |
| 問題4 | 用法（語彙） | 6題 |

#### 文法
| 問題 | 題型 | 数量 |
|------|------|------|
| 問題5 | 文法形式選択 | 10題 |
| 問題6 | 並べ替え | 5題 |
| 問題7 | 文章文法 | 4題 |

#### 読解
| 問題 | 題型 | 数量 |
|------|------|------|
| 問題8 | 短文読解（4篇） | 4題 |
| 問題9 | 中文読解（4篇） | 8題 |
| 問題10 | 長文読解 | 3題 |
| 問題11 | 統合理解（複数文比較） | 2題 |
| 問題12 | 主張理解（長文） | 3題 |
| 問題13 | 情報検索 | 2題 |

### 聴解 (Listening) - 60分
| 問題 | 題型 | 數量 |
|------|------|------|
| 問題1 | 課題理解 | 6題 |
| 問題2 | 要点理解 | 7題 |
| 問題3 | 概要理解 | 3題 |
| 問題4 | 即時応答 | 12題 |
| 問題5 | 統合理解 | 4題 |

## Repository Structure

```
jlpt-n1-question-bank/
├── past-exams/          # 按年份整理的真题（用户手动录入，Agent 校对）【明文·仅本地】
│   ├── 2010/           # 2010年7月・12月
│   ├── 2012/           # 2012年7月・12月
│   ├── ...
│   └── 2025/           # 2025年7月
├── question-bank/       # 按題型分類的題庫【明文·仅本地】
│   ├── by-type/         # 縱向整理（按題型）
│   │   ├── vocab-reading/
│   │   ├── vocab-context/
│   │   ├── vocab-paraphrase/
│   │   ├── vocab-usage/
│   │   ├── grammar-usage/
│   │   ├── grammar-choice/
│   │   ├── grammar-composition/
│   │   ├── reading-short/
│   │   ├── reading-mid/
│   │   ├── reading-long/
│   │   ├── listening-point/
│   │   ├── listening-grammar/
│   │   ├── listening-overview/
│   │   ├── listening-detailed/
│   │   └── listening-implication/
│   ├── by-year/          # 橫向整理（按年份）
│   └── by-theme/         # 按主題分類（語法・詞彙等）
├── docs/                 # 加密后的 Pages 站点（唯一可推送内容）
│   ├── index.html       # 密码门 + 题库阅读站（WebCrypto AES-GCM 解密）
│   ├── data.json        # 题目密文（AES-256-GCM，PBKDF2-SHA256 310000 次派生）
│   └── index-meta.json  # 非敏感统计（收录年份/题数）
├── analysis/             # 分析與統計
├── guides/               # 備考指南
└── tools/                # 工具腳本
```

## Usage

### 按題型練習 (Vertical Practice)
```bash
# 練習所有年份的「語彙・文脈規定」題
ls question-bank/by-type/vocab-context/
```

### 按年份練習 (Horizontal Practice)
```bash
# 練習2024年的所有題目
ls past-exams/2024/
```

### 按主題練習 (Theme-based Practice)
```bash
# 練習所有「語法」相關題目
ls question-bank/by-theme/grammar/
```

## GitHub Pages (加密展示)

站点：https://syu-toutousai.github.io/jlpt-n1-question-bank/

**版权保护方案**（客户端 AES 加密）：
- 明文题目 JSON **仅存本地**（已被 `.gitignore` 忽略，永不入库）
- `python3 tools/encrypt.py` 将所有题目打包并 AES-256-GCM 加密（密钥由密码经 PBKDF2-SHA256 派生），写入 `docs/data.json`
- 浏览器端无需任何服务：`docs/index.html` 输入密码后在 WebCrypto 中解密渲染
- 无密码者只能看到密文，无法读取题目原文（版权内容真实不可读）

**访问密码**：`docs/.secret.txt`（本地文件，已在 `.gitignore` 中，不入库）
每次录入新题后进行两个步骤：

```bash
git add past-exams/  question-bank/   # 明文仅在本地版本库管理（可选）
python3 tools/encrypt.py              # 重新加密，更新 docs/
git add docs/
git commit && git push                # 只推送加密后的 docs/
```

> ⚠️ 明文 JSON 被 `.gitignore` 排除，不会进入 GitHub 仓库。若确需把明文题目纳入版本管理，请使用本地 git 分支或外部备份，绝不可推送到公共仓库。

## Local Dev Server (本地全量透明版)

本地起一个不加密的、全量体现本 repo 的 web 前端（题库练习 / 统计 / 仓库浏览）：

```bash
python3 tools/serve.py --port 8123     # 端口占用则自动顺延
# 打开 http://127.0.0.1:8123/
```

- 仅绑定 `127.0.0.1`；数据直接读取本地明文 JSON（`/api/questions`），与 Pages 加密版同源
- 仓库浏览视图可预览 `analysis/` `guides/` `refs/` 等全部文本文件
- 停服：`kill` 进程或前台 Ctrl+C

## File Format (JSON)

Each question is stored in JSON format:
```json
{
  "id": "2024-12-vocab-01",
  "year": 2024,
  "month": 12,
  "section": "vocab",
  "type": "context",
  "number": 1,
  "question": "問題文...",
  "options": ["A", "B", "C", "D"],
  "answer": "C",
  "explanation": "解説...",
  "difficulty": "medium",
  "tags": ["副詞", "曖昧表現"]
}
```

## Contributing

1. Fork this repository
2. Create a feature branch
3. Submit a pull request

## License

MIT
