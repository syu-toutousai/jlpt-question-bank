# AGENTS.md — Working Rules for Agents in This Repository

This file defines how agents must behave when working in this repository.
Follow these rules strictly; they override generic behavior.

## 1. Long-term Mission (超长线任务)

- This repo runs from **now until the user passes JLPT N1** (target: the December exam of the current year, and beyond if needed).
- Treat content as **permanently accumulating**: every session may add to `past-exams/`, `question-bank/`, `analysis/`, `guides/`, etc.
- Never delete or rewrite existing content without asking unless the user explicitly requests it.
- Prefer appendable, evolvable structures (JSON per question) so later sessions can merge/rebuild indexes.

## 2. Content Ownership (用户手动录入)

- The **user manually inputs question content** (stem, options, answer, passages, notes) — anything that can be hand-entered.
- **Do NOT fabricate, guess, or auto-generate real past-exam question content.**
- When the user asks you to "add a question" without providing the content, do not invent one. Instead:
  - Ask for the content, OR
  - Wait for the user to input it.
- You MAY create documentation, templates, analysis, statistics, and tooling on your own initiative.

## 3. Active Fact-Checking Against Web Sources (积极校对)

Whenever the user has entered content (a question, answer key, passage, etc.), you **must actively verify it** against internet resources. This is not optional.

### Required practice

- **Always cross-check**:
  - Original question wording (真题原文)
  - Correct answer (答案是否正确)
  - Source attribution: exam year/month and question number (出处：年份·月份·题号)
  - Explanation correctness (解析准确性)
- Use web search / web fetch to find the source exam text or widely accepted answer keys.
- **Do not assume** the user's manual entry is correct; discrepancies are common due to memory or transcription typos.

### When checked

| Type of content | Verification expectation |
|----------------|--------------------------|
| A question the user just told you to store | Check against websources. Report matches. |
| An answer the user claims is correct | Verify against answer keys. Flag disputes. |
| A passage/audio transcript | Spot-check key sentences, kanji readings. Flag uncertainty. |
| A month of accumulated questions (bulk commit) | At least spot-check a representative sample; list reviewed/flagged items. |

### How to report

- Be explicit about what you verified and what you could not. Use a short report after storing:
  - ✅ verified — matched an online source (cite the source/URL).
  - ⚠️ unclear/cannot confirm — keep user's entry as-is, ask them to double-check.
  - ❌ mismatch found — show the discrepancy, correct the entry **only if you have a reliable source**; otherwise ask the user first.

### Tools to use

- `websearch` / `felo_search`: find original exam PDFs, answer keys, forums (e.g. Reddit, 沪江, Kakusare, JLPT past-exam archives).
- `webfetch`: fetch a concrete source page to confirm exact wording.
- Note: JLPT does not officially publish past exams. Sources are typically scans of the real test shared by test-takers, study sites, or reputable prep materials. Prefer **multiple independent confirmations** for a mismatch before changing the user's entry.

### Archiving sources (本地存档)

Whenever a useful copyrighted source is found (exam PDF, answer-key scan, etc.):

1. Save the file into **`refs/`** (gitignored, **never pushed**), name it
   `YYYY-MM_科目_来源.ext` (e.g. `2024-12_vocab_hujiang.pdf`).
2. Append one row to **`guides/source-log.md`** with: date, scope, source URL,
   verification verdict, and the refs/ filename. (This file is safe to push.)
3. If a link later dies, keep the row and mark the URL 「失效」.

## 4. Git/Commits

- Commit only when the user explicitly asks.
- When committing, keep messages focused: e.g. `Add 2024年12月 vocab questions`, `Fix answer key: 2021-12 grammar Q3 (C -> B)`.
- Review changes before committing; never commit secrets or unrelated files.

## 5. GitHub Pages & Encryption (加密部署)

The Pages site (https://syu-toutousai.github.io/jlpt-n1-question-bank/) is the
only public face of this repo, and it is **password-protected via client-side
AES-256-GCM encryption** (copyright reasons). Follow these rules strictly:

### Do NOT push plaintext question content, EVER

- Plaintext question JSONs under `past-exams/`, `question-bank/` are
  **gitignored on purpose**. They must **never** be committed or pushed.
- The only pushable content is the encrypted site under `docs/` plus
  tooling/documentation (`tools/`, README, templates, `.gitkeep`s,
  non-sensitive metadata without question text).
- Verify with `git status` / `git ls-files` that no `*.json` under
  `past-exams/` or `question-bank/` is staged before any push.

### Regenerate the encrypted site after content changes

As soon as the user has entered/verified any question content, regenerate:

```bash
python3 tools/encrypt.py          # re-encrypts into docs/ (reuses stored password)
git add docs/ && git commit && git push   # push only encrypted artifacts
```

- `docs/.secret.txt` holds the password locally and is gitignored — never push it.
- Password lives only with the user; to change it:
  `python3 tools/encrypt.py --password 'NEW_PASSWORD'`.

### Verification notes

- After each encrypt run, round-trip can be re-verified in Node (WebCrypto,
  same API as browser): decrypt `docs/data.json` with the password and confirm
  the expected questions/answers come back; confirm a wrong password is rejected.
- `data.json` contains ciphertext only; `index-meta.json` contains only
  non-sensitive counts (total / years / sections) for the landing header.

## 6. Default Structure Conventions

- One JSON file per question (see `question-bank/template.json`).
- `past-exams/<year>/<section>/` — original entries by year.
- `question-bank/by-type/<section>-<type>/` — copies/references by type (use `tools/organize.py add` to auto-maintain both).
- `analysis/` — trend statistics, error analysis, score estimates.
- `guides/` — study plan for December exam, follow-up notes.

## 7. JLPT 卷面结构与语料红线（必读・每次会话）

> 防止「自动生成伪真题」。全文与事故档案：`/home/naruto/scratch/japanese-learning/JLPT_EXAM_STRUCTURE.md`

**真题卷里的文本不全是正文**——还有故意写错的干扰项、选项片段、出题说明。按题型区分：

| 問題 | 题干 | 选项 | 语料 |
|---|---|---|---|
| 問題1 読み方 | 含目标词句子 | 读音 | 题干句 ✅ |
| 問題2 文脈規定 | 挖空句 | 词 | 题干句 ✅ |
| 問題3 言い換え | 目标句 | 近义短语 | 题干句 ✅ |
| 問題4 用法 | 仅目标词 | 四句（1正3误） | **仅正解正确；误用错项严禁入语料** ❌ |
| 問題5 文法形式 | 挖空句 | 形式 | 题干句 ✅ |
| 問題6 並べ替え | ★片段 | 片段 | ❌ |
| 問題7 文章の文法 | 篇章+编号空 | 片段 | 仅篇章正文 ✅ |
| 問題8–13 読解 | 篇章正文 | 设问+选项句 | 正文 ✅；设问/选项 ❌ |
| 聴解 | 脚本 | 编号/图/短句 | 选项 ❌ |

**红线（硬性）**：
1. 只收完整句（以 `。！？` 结尾）；片段、`(注N)` 行、编号、释义行不收。
2. **禁止扫描选项**——选项从不是正文；問題4 错项是故意误用。
3. 出题装置文字（「〜を一つ選びなさい」等）禁入。
4. 読解设问/选项句禁入；挖空/★/编号所在句子禁入。
5. 转写错字走校对流程修源（如 `ものの。→ものの、`），不得在课件层将错就错。

**已知事故**：N1 2022-07 問題4(20)「結末」误用句「細い枝の結末に…咲いている」曾生成 N5 级「〜ている」挖空题——故选项扫描已全面废除。
