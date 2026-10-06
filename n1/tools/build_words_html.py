#!/usr/bin/env python3
"""Build docs/vocab-words[-SESSION].html — standalone study page from analysis markdown.

Multiple analysis files map to exam 区分 (問題1…問題13・聴解). Each material
file is rendered inside a <section class="bunrui" id="sec-<sid>"> and appears
in the top navigation; 区分 without a material show up as disabled chips.

Usage:
    python3 tools/build_words_html.py --session 2024-07
    python3 tools/build_words_html.py --session 2024-12
    python3 tools/build_words_html.py --all          # build both sessions
"""
import base64
import glob
import hashlib
import json
import os
import re
from functools import lru_cache
from pathlib import Path

# Cards whose MOJi-Dictionary spelling differs from the card heading word
# (card word → MOJi query spelling, used to locate the word-pron TTS file).
CARD_QUERY = {"および腰": "及び腰"}

# Extra card anchor ids: a stem-surface form that differs from the dictionary-form
# heading word gets its own id so index.html deep links (#w-…) still resolve.
# Multiple ids are space-separated (browsers resolve fragment to any token).
CARD_ID_ALIAS = {"侮る": ["侮って"]}

MOJI_WORD_AUDIO = os.path.expanduser("~/moji_audio")
EXAMPLE_MAP_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "data", "moji_example_map.json")
EDGE_TTS_DIR = os.path.expanduser("~/edge_tts_examples")

# All exam 区分, in exam order. sids are stable anchors.
BUNRUI = [
    ("q1", "問題1 読み方"),
    ("q2", "問題2 文脈規定"),
    ("q3", "問題3 言い換え"),
    ("q4", "問題4 使い方"),
    ("q5", "問題5 文法選択"),
    ("q6", "問題6 並べ替え"),
    ("q7", "問題7 文章の文法"),
    ("q8", "問題8 短文読解"),
    ("q9", "問題9 中文読解"),
    ("q10", "問題10 長文読解A"),
    ("q11", "問題11 統合理解"),
    ("q12", "問題12 情報検索"),
    ("q13", "問題13 長文読解B"),
    ("toki", "聴解"),
]

# ---- auto-config: derive a session's page from analysis/*.md + bank data ----
AUTO_LABELS = {
    "vocab-reading-words": ("q1", "問題1 読み方", "漢字語の読み"),
    "vocab-context-words": ("q2", "問題2 文脈規定", "語を正しく判断"),
    "paraphrase": ("q3", "問題3 言い換え", "同義表現"),
    "usage": ("q4", "問題4 使い方", "文を作る"),
    "grammar-choice": ("q5", "問題5 文法選択", "文型"),
    "composition": ("q6", "問題6 並べ替え", "並べ替え"),
    "grammar-passage": ("q7", "問題7 文章の文法", "空欄文型"),
    "reading-short": ("q8", "問題8 短文読解", "短文読解"),
    "reading-mid": ("q9", "問題9 中文読解", "中文読解"),
    "reading-long": ("q10", "問題10 長文読解A", "長文読解A"),
    "reading-long-b": ("q13", "問題13 長文読解B", "長文読解B"),
    "listening": ("toki", "聴解", "聴解 全問題"),
}
AUTO_SID_SRC = {
    "q3": ("vocab", ("paraphrase",)),
    "q4": ("vocab", ("usage",)),
    "q5": ("grammar", ("choice",)),
    "q6": ("grammar", ("composition",)),
    "q7": ("grammar", ("passage",)),
    "q8": ("reading", ("short",)),
    "q9": ("reading", ("mid",)),
    "q10": ("reading", ("long",)),
}


def _bank_min_num(session, subdir, types):
    y, m = session.split("-")
    nums = []
    for f in glob.glob(str(ROOT / "past-exams" / y / m / subdir / "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except OSError:
            continue
        if d.get("type") in types:
            try:
                nums.append(int(d.get("number") or 0))
            except ValueError:
                pass
    return min(nums) if nums else 1


def _bank_qdata(session, subdir, types):
    y, m = session.split("-")
    out = {}
    for f in glob.glob(str(ROOT / "past-exams" / y / m / subdir / "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except OSError:
            continue
        if d.get("type") not in types:
            continue
        try:
            num = int(d.get("number") or 0)
        except ValueError:
            continue
        tgt = (d.get("target") or "").strip()
        ans = None
        try:
            opts = d.get("options") or []
            ans = opts[int(d["answer"]) - 1]
        except (KeyError, ValueError, IndexError):
            pass
        out[num] = (tgt or ans or "").strip()
    return out


def auto_cfg(session):
    y, m = session.split("-")
    materials = []
    answers = {}
    for f in sorted(glob.glob(str(ANALYSIS / f"{session}-*.md"))):
        base = Path(f).name[len(session) + 1:-3]
        lab = AUTO_LABELS.get(base)
        if not lab:
            continue
        sid, label, sub = lab
        if sid == "toki":
            qfirst = 1
        elif sid in AUTO_SID_SRC:
            qfirst = _bank_min_num(session, *AUTO_SID_SRC[sid])
        else:
            qfirst = 1
        materials.append({"file": Path(f).name, "sid": sid, "qfirst": qfirst,
                          "label": label, "sub": sub})
        if sid in AUTO_SID_SRC:
            answers[sid] = {k: v for k, v in _bank_qdata(
                session, *AUTO_SID_SRC[sid]).items() if v}
    return {"title": f"{y}年{int(m)}月 JLPT N1 語注・例句集",
            "sub": "語彙・文法・読解・聴解の語注（MOJi辞書）＋ Nadeshiko 动漫日剧真实台词",
            "materials": materials, "answers": answers}


def session_cfg(sid):
    return SESSIONS[sid] if sid in SESSIONS else auto_cfg(sid)


def all_sessions():
    out = set(SESSIONS)
    for f in glob.glob(str(ANALYSIS / "[0-9][0-9][0-9][0-9]-[0-9][0-9]-*.md")):
        out.add(Path(f).name[:7])
    return sorted(out)


# ---- per-session configuration (manually curated for flagship sessions) ----
SESSIONS = {
    "2024-07": {
        "title": "2024年7月 JLPT N1 語注・例句集",
        "sub": "語彙 Q1–25 ＋ 文法 Q26–44 ＋ 読解 Q45–66 ＋ 聴解 全30 ・ MOJi辞書 读音/释义/例句 ＋ Nadeshiko 动漫日剧真实台词",
        "materials": [
            {"file": "2024-07-vocab-reading-words.md", "sid": "q1", "qfirst": 1,
             "label": "問題1 読み方", "sub": "Q1–6 読み方 ・ 漢字語の読み"},
            {"file": "2024-07-vocab-context-words.md", "sid": "q2", "qfirst": 7,
             "label": "問題2 文脈規定", "sub": "Q7–13 文脈規定 ・ 語を正しく判断"},
            {"file": "2024-07-paraphrase.md", "sid": "q3", "qfirst": 14,
             "label": "問題3 言い換え", "sub": "Q14–19 言い換え ・ 同義表現"},
            {"file": "2024-07-usage.md", "sid": "q4", "qfirst": 20,
             "label": "問題4 使い方", "sub": "Q20–25 使い方 ・ 文を作る"},
            {"file": "2024-07-grammar-choice.md", "sid": "q5", "qfirst": 26,
             "label": "問題5 文法選択", "sub": "Q26–35 文法選択 ・ 文型"},
            {"file": "2024-07-composition.md", "sid": "q6", "qfirst": 36,
             "label": "問題6 並べ替え", "sub": "Q36–40 並べ替え"},
            {"file": "2024-07-grammar-passage.md", "sid": "q7", "qfirst": 41,
             "label": "問題7 文章の文法", "sub": "Q41–44 記述問題・空欄文型"},
            {"file": "2024-07-reading-short.md", "sid": "q8", "qfirst": 45,
             "label": "問題8 短文読解", "sub": "Q45–48 短文読解"},
            {"file": "2024-07-reading-mid.md", "sid": "q9", "qfirst": 49,
             "label": "問題9 中文読解", "sub": "Q49–56 中文読解"},
            {"file": "2024-07-reading-long.md", "sid": "q10", "qfirst": 57,
             "label": "問題10 長文読解A", "sub": "Q57–66 長文読解"},
            {"file": "2024-07-listening.md", "sid": "toki", "qfirst": 1,
             "label": "聴解", "sub": "全30問 ・ 原文抜粋＋語注"},
        ],
        "answers": {
            "q1": {1: "腐敗", 2: "粗い", 3: "粘膜", 4: "寿命", 5: "戒める", 6: "誓約書"},
            "q2": {7: "根底", 8: "返上", 9: "取り次ぐ", 10: "交錯", 11: "難航", 12: "がやがや", 13: "足手まとい"},
            "q3": {14: "任せる", 15: "爽やかな", 16: "用意する", 17: "雑な", 18: "下を向いて", 19: "ダメージ"},
            "q4": {20: "風潮", 21: "もたらす", 22: "撤回", 23: "補填", 24: "コンスタント", 25: "ずばり"},
        },
    },
    "2024-12": {
        "title": "2024年12月 JLPT N1 語注・例句集",
        "sub": "語彙 Q1–25 ＋ 文法 Q26–44 ＋ 読解 Q45–66 ＋ 聴解 全30 ・ MOJi辞書 读音/释义/例句 ＋ Nadeshiko 动漫日剧真实台词",
        "materials": [
            {"file": "2024-12-vocab-reading-words.md", "sid": "q1", "qfirst": 1,
             "label": "問題1 読み方", "sub": "Q1–6 読み方 ・ 漢字語の読み"},
            {"file": "2024-12-vocab-context-words.md", "sid": "q2", "qfirst": 7,
             "label": "問題2 文脈規定", "sub": "Q7–13 文脈規定 ・ 語を正しく判断"},
            {"file": "2024-12-paraphrase.md", "sid": "q3", "qfirst": 14,
             "label": "問題3 言い換え", "sub": "Q14–19 言い換え ・ 同義表現"},
            {"file": "2024-12-usage.md", "sid": "q4", "qfirst": 20,
             "label": "問題4 使い方", "sub": "Q20–25 使い方 ・ 文を作る"},
            {"file": "2024-12-grammar-choice.md", "sid": "q5", "qfirst": 26,
             "label": "問題5 文法選択", "sub": "Q26–35 文法選択 ・ 文型"},
            {"file": "2024-12-composition.md", "sid": "q6", "qfirst": 36,
             "label": "問題6 並べ替え", "sub": "Q36–40 並べ替え"},
            {"file": "2024-12-grammar-passage.md", "sid": "q7", "qfirst": 41,
             "label": "問題7 文章の文法", "sub": "Q41–44 記述問題・空欄文型"},
            {"file": "2024-12-reading-short.md", "sid": "q8", "qfirst": 45,
             "label": "問題8 短文読解", "sub": "Q45–48 短文読解"},
            {"file": "2024-12-reading-mid.md", "sid": "q9", "qfirst": 49,
             "label": "問題9 中文読解", "sub": "Q49–56 中文読解"},
            {"file": "2024-12-reading-long.md", "sid": "q10", "qfirst": 57,
             "label": "問題10 長文読解A", "sub": "Q57–66 長文読解"},
        ],
        "answers": {
            "q1": {1: "絶叫", 2: "背後", 3: "抱負", 4: "侮る", 5: "筋道", 6: "奔放"},
            "q2": {7: "適応", 8: "掲げる", 9: "踏襲", 10: "足止め", 11: "へとへと", 12: "払拭", 13: "とっさに"},
            "q3": {14: "能力", 15: "無駄にして", 16: "いいかげん", 17: "今", 18: "引き受ける", 19: "差し上げました"},
            "q4": {20: "加工", 21: "養う", 22: "質質", 23: "正当", 24: "ありがたい", 25: "間柄"},
        },
    },
}


@lru_cache(maxsize=None)
def wpron(word):
    for spelling in (word,) + (CARD_QUERY.get(word, ()),):
        hits = glob.glob(os.path.join(MOJI_WORD_AUDIO, f"{spelling}_*_w_*.mp3"))
        if hits:
            return sorted(hits)[0]
    return None


def example_normalize(s):
    # Key normalisation for the moji-example map (tools/data/*.json).
    s = FURIGANA_RE.sub(lambda m: m.group(1) + m.group(2), s)
    s = s.replace("「", "").replace("」", "")
    return re.sub(r"\s+", " ", s).strip()


def tts_normalize(s):
    # Text fed to / hashed for Edge-TTS; keeps 「」 for natural intonation.
    s = FURIGANA_RE.sub(lambda m: m.group(1) + m.group(2), s)
    return re.sub(r"\s+", " ", s).strip()


STEM_NUM_RE = re.compile(r"^\d+[.、]\s*")


def stem_text(s):
    # Edge-TTS text for 题干速览 lines: strip a leading "7. " question number.
    s = STEM_NUM_RE.sub("", s)
    return tts_normalize(s)


@lru_cache(maxsize=None)
def example_map():
    try:
        return json.load(open(EXAMPLE_MAP_JSON, encoding="utf-8"))
    except OSError:
        return {}


def exam_audio(word, sentence):
    # Prefer the dictionary's own example audio, else Edge-TTS fallback.
    t = example_normalize(sentence)
    f = example_map().get(word, {}).get(t)
    if f and os.path.exists(f):
        return f, "MOJi 原声"
    f = os.path.join(EDGE_TTS_DIR,
                     hashlib.sha1(tts_normalize(sentence).encode()).hexdigest()[:16]
                     + ".mp3")
    if os.path.exists(f):
        return f, "Edge TTS"
    return None


def datauri(path):
    with open(path, "rb") as fh:
        return "data:audio/mpeg;base64," + base64.b64encode(fh.read()).decode()


def ip_btn(src, cls, title=""):
    # Inline icon-only play button (placed right after the word/sentence it
    # reads out). cls ∈ {moji, edge, nade} decides the icon colour (see 凡例).
    tt = f' title="{esc(title)}"' if title else ""
    return (f'<span class="ip"><button class="pb pb--{esc(cls)}" aria-label="播放"{tt}>'
            '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">'
            '<path class="ic-play" d="M8 5.5v13l11-6.5z"/>'
            '<path class="ic-stop" d="M6 6h4v12H6zM14 6h4v12h-4z" style="display:none"/></svg>'
            f'</button><audio preload="none" src="{src}"></audio></span>')

ROOT = Path(__file__).resolve().parent.parent
ANALYSIS = ROOT / "analysis"
OUT = ROOT / "docs" / "vocab-words.html"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def autolink(s):
    def repl(m):
        url = m.group(0)
        if (url.endswith(".mp3") or url.endswith(".webp") or url.endswith(".png") or url.endswith(".jpg")):
            return f'<span class="url">{esc(url)}</span>'
        return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(url)}</a>'
    return re.sub(r"https?://[^\s\u3000]+", repl, s)


KAN_CLUSTER = r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\u3005\u3006\u3007々〆〇]+"
KANA_RUN = r"[ぁ-ゖァ-ヺー・ゝゞ]+"
FURIGANA_RE = re.compile(r"(" + KAN_CLUSTER + r")\((" + KANA_RUN + r")\)")


def rubify(s):
    # Convert inline 漢字(かな) furigana (half-width parens, the nadeshiko /
    # MOJi annotion style) into HTML ruby 注音. Full-width （…） is left as-is.
    return FURIGANA_RE.sub(lambda m: f"<ruby>{m.group(1)}"
                                       f"<rt>{m.group(2)}</rt></ruby>", s)


def fmt_inline(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return autolink(rubify(s))


def render(lines, qbase, answers=frozenset()):
    body = []
    cards = 0
    dist = 0
    word_idx = 0
    q_idx = qbase - 1
    cur = None
    open_detail = False
    cur_word = None
    in_stem = False
    last_s = None
    aud = {"word_audio": 0, "exam_audio": 0, "exam_moji": 0, "exam_edge": 0,
           "stem_audio": 0, "nade_audio": 0}

    def word_ip(word):
        mp3 = wpron(word)
        if not mp3:
            return ""
        aud["word_audio"] += 1
        return ip_btn(datauri(mp3), "moji")

    def exam_ip(word, sentence):
        hit = exam_audio(word, sentence)
        if not hit:
            return ""
        f, src = hit
        aud["exam_audio"] += 1
        aud["exam_moji" if src == "MOJi 原声" else "exam_edge"] += 1
        return ip_btn(datauri(f), "moji" if src == "MOJi 原声" else "edge")

    def stem_ip(sentence):
        h = hashlib.sha1(stem_text(sentence).encode()).hexdigest()[:16]
        f = Path(EDGE_TTS_DIR) / f"{h}.mp3"
        if not f.exists():
            return ""
        aud["stem_audio"] += 1
        return ip_btn(datauri(f), "edge")

    def close_card():
        nonlocal open_detail, last_s
        if open_detail:
            body.append("</div></details>")
            open_detail = False
        last_s = None

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("# "):
            close_card()
            continue
        if line.startswith("> "):
            close_card()
            body.append(f'<p class="note">{fmt_inline(line[2:])}</p>')
            continue
        if line == "---":
            close_card()
            body.append('<div class="hr"></div>')
            continue
        if line.startswith("## "):
            close_card()
            title = line[3:]
            in_stem = title.startswith("题干速览")
            mq = re.match(r"^([QT])(\d+)\t?　", title)
            if mq:
                # Exam-numbered sections (語彙 Q14+ / 文法 / 読解 / 聴解):
                # anchor by the exam question number so index.html deep links
                # (#q<n>) resolve. 聴解 uses #t<n> to avoid clashing with the
                # vocab #q1–13 anchors already present on the same page.
                nid = ("t" if mq.group(1) == "T" else "q") + mq.group(2)
                body.append(f'<h2 class="sec" id="{nid}">{esc(title)} '
                            f'<a class="qanchor" href="#{nid}">#{nid}</a></h2>')
                continue
            if title.startswith(("题干速览", "干扰项一览", "干扰项")):
                body.append(f'<h2 class="sec">{esc(title)}</h2>')
            else:
                q_idx += 1
                body.append(f'<h2 class="sec" id="q{q_idx}">{esc(title)}'
                            f' <a class="qanchor" href="#q{q_idx}">#q{q_idx}</a></h2>')
            continue
        if line.startswith("### "):
            close_card()
            t = line[4:]
            if t.startswith("【干扰项】"):
                body.append('<div class="dist-h">⚑ 干扰项 查缺补漏（错误选项 → 辨析）</div>')
                continue
            is_dist = "　" in t
            if is_dist and t.endswith("　干扰项"):
                t = t[:-4]
            m = re.match(r"(.+?)（([^）]+)）", t)
            word = m.group(1) if m else t
            yomi = m.group(2) if m else ""
            word_idx += 1
            cards += 1
            cur_word = word
            ans_flag = word in answers and not is_dist
            if is_dist:
                dist += 1
            wp = word_ip(word)
            ids = " ".join(f"w-{esc(w)}" for w in [word] + CARD_ID_ALIAS.get(word, []))
            body.append(
                f'<details class="card" id="{ids}" data-w="{esc(word)}"><summary>'
                f'<span class="wn">{esc(word)}</span>'
                f'{"<span class=\"wy\">" + esc(yomi) + "</span>" if yomi else ""}'
                f'{wp}'
                f'{"<span class=\"tag ok\">★正解</span>" if ans_flag else ""}'
                f'{"<span class=\"tag\">干扰项</span>" if is_dist else ""}'
                f'</summary><div class="cbody">')
            open_detail = True
            cur = body
            continue
        m = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if m:
            # 题干速览 lives before the first card; unlike other sections it
            # must still be rendered (its bullets carry the stem sentences).
            if cur is None and not in_stem:
                continue
            depth = m.group(1).count(" ")
            if depth == 0:
                text = m.group(2)
                if text.startswith("**备注**"):
                    cur.append(f'<p class="kv note-p">{fmt_inline(text)}</p>')
                elif "：" in text and text.split("：")[0].startswith("**"):
                    label, rest = text.split("：", 1)
                    lkey = label.strip("**")
                    if lkey == "作品台词":
                        cur.append(f'<p class="kv drain">{fmt_inline(text)}</p>')
                    elif lkey == "MOJi 例句":
                        cur.append(f'<p class="kv">{fmt_inline(label)}<span>：</span>'
                                   f'{fmt_inline(rest)}{exam_ip(cur_word, rest)}</p>')
                    elif lkey == "听力音频":
                        # remote exam audio (聴解原音) → nade-style play button
                        m_u = re.search(r"https?://[^\s\u3000]+", rest)
                        ip = ip_btn(esc(m_u.group(0)), "nade") if m_u else ""
                        cur.append(f'<p class="kv">{fmt_inline(label)}<span>：</span>'
                                   f'<span class="url">{fmt_inline(rest)}</span>{ip}</p>')
                    elif lkey == "听力原文" or lkey.startswith("用法例文") \
                            or lkey == "文法例文" or lkey == "考查句":
                        # generated study-page lines with Edge-TTS available
                        cur.append(f'<p class="kv">{fmt_inline(label)}<span>：</span>'
                                   f'{fmt_inline(rest)}{exam_ip(cur_word, rest)}</p>')
                    else:
                        cur.append(f'<p class="kv">{fmt_inline(label)}<span>：</span>{fmt_inline(rest)}</p>')
                elif in_stem:
                    (body if cur is None else cur).append(
                        f'<p class="kv stem">{fmt_inline(text)}{stem_ip(text)}</p>')
                else:
                    cur.append(f'<p>{fmt_inline(text)}</p>')
            elif depth == 2:
                t = m.group(2)
                if t.startswith("*") and t.endswith("*"):
                    cur.append(f'<p class="rare">{fmt_inline(t.strip("*"))}</p>')
                else:
                    cur.append(f'<div class="s-h"><span class="m-ico">🎬</span>{fmt_inline(t)}</div>')
                    last_s = len(cur) - 1
            elif depth == 4:
                t = m.group(2)
                if t.startswith("EN:"):
                    cur.append(f'<div class="en">{fmt_inline(t)}</div>')
                elif t.startswith("≪"):
                    cur.append(f'<div class="meta">{fmt_inline(t)}</div>')
                elif "http" in t:
                    urls = re.findall(r"https?://[^\s\u3000]+", t)
                    au = None
                    img = None
                    for u in urls:
                        if u.endswith(".mp3"):
                            au = u
                        elif u.endswith((".webp", ".png", ".jpg")):
                            img = u
                    if au:
                        if last_s is not None and cur is body:
                            body[last_s] = body[last_s][:-6] + ip_btn(esc(au), "nade") + "</div>"
                            aud["nade_audio"] += 1
                        else:
                            cur.append(ip_btn(esc(au), "nade"))
                    if img:
                        cur.append(f'<img loading="lazy" src="{esc(img)}" alt="场景截图">')
                    if not au and not img:
                        cur.append(f'<div class="linkline">{fmt_inline(t)}</div>')
                else:
                    cur.append(f'<div class="meta">{fmt_inline(t)}</div>')
            else:
                cur.append(f'<p>{fmt_inline(m.group(2))}</p>')
            continue
        (body if cur is None else cur).append(f'<p>{fmt_inline(line)}</p>')
    close_card()
    return body, cards, dist, aud


def main(title, sub, materials, answers, out_path):
    sections_html = []
    total_cards = 0
    total_dist = 0
    audio_tot = {}
    ready = {}
    for mat in materials:
        md = ANALYSIS / mat["file"]
        if not md.exists():
            print(f"  ! missing material file: {md.name}")
            continue
        text = md.read_text(encoding="utf-8")
        body, cards, dist, aud = render(text.splitlines(), qbase=mat["qfirst"],
                                        answers=frozenset(answers.get(mat["sid"], {}).values()))
        ready[mat["sid"]] = mat
        total_cards += cards
        total_dist += dist
        for k, v in aud.items():
            audio_tot[k] = audio_tot.get(k, 0) + v
        sections_html.append(
            f'<section class="bunrui" id="sec-{mat["sid"]}" data-label="{esc(mat["label"])}">'
            f'<div class="bsec"><span class="bno">{esc(mat["label"])}</span>'
            f'<span class="bsub">{esc(mat["sub"])}</span></div>'
            + "\n".join(body)
            + "</section>"
        )

    nav = []
    for sid, label in BUNRUI:
        if sid in ready:
            nav.append(f'<a class="chip on" href="#sec-{sid}">{esc(label)}</a>')
        else:
            nav.append(f'<span class="chip off">{esc(label)}<i>未作成</i></span>')

    answers_js = json_answers(answers)
    embeds = (audio_tot.get("word_audio", 0) + audio_tot.get("exam_audio", 0)
              + audio_tot.get("stem_audio", 0))

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{title}</title>
<style>
:root{{--bg:#f5f7fb;--card:#fff;--ink:#1c2333;--sub:#5b6478;--line:#e4e7f0;--acc:#4f6ef7;--acc2:#eef1ff;--warn:#e8590c;--ok:#1f9d55;--c:#7a4ff7}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font-family:"PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);line-height:1.85}}
header{{background:linear-gradient(135deg,#33418f,#7a4ff7);color:#fff;padding:34px 20px 28px;text-align:center}}
header h1{{font-size:23px;letter-spacing:1.5px}}
header p{{opacity:.92;font-size:13.5px;margin-top:10px}}
header .tags span{{display:inline-block;background:rgba(255,255,255,.22);border-radius:99px;padding:3px 12px;font-size:12px;margin:12px 4px 0}}
main{{max-width:960px;margin:-14px auto 40px;padding:0 16px}}
.nav{{position:sticky;top:0;z-index:40;background:rgba(255,255,255,.95);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;box-shadow:0 4px 14px rgba(30,40,90,.06)}}
.nav .nlabel{{font-size:12px;font-weight:700;color:var(--sub);margin-right:4px}}
.chip{{font-size:12.5px;text-decoration:none;border-radius:99px;padding:4px 12px;border:1.5px solid var(--line);background:#fff;color:#33418f;font-weight:600;transition:.15s}}
.chip.on:hover{{border-color:var(--c);background:var(--acc2);color:#33418f}}
.chip.on[data-cur="1"]{{background:#33418f;border-color:#33418f;color:#fff}}
.chip.off{{color:#b8becd;border-style:dashed;position:relative}}
.chip.off i{{font-style:normal;font-size:10.5px;margin-left:6px;color:#c8cdd9}}
.toolbar{{position:sticky;top:44px;z-index:39;background:rgba(245,247,251,.96);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
.legend{{display:flex;gap:0;flex-wrap:wrap;align-items:center;justify-content:center;background:var(--card);border-bottom:1px solid var(--line);padding:7px 16px;font-size:12px;color:var(--sub)}}
.legend>span{{display:inline-flex;align-items:center;gap:6px;padding:0 14px}}
.legend .lg{{width:11px;height:11px;border-radius:50%;display:inline-block}}
.lg--moji{{background:#4f6ef7}}
.lg--edge{{background:#e8590c}}
.lg--nade{{background:#1f9d55}}
.toolbar input{{flex:1;min-width:200px;border:1.5px solid var(--line);border-radius:99px;padding:8px 16px;font-size:13.5px;outline:none;background:#fff}}
.toolbar .cnt{{font-size:12.5px;color:var(--sub);font-weight:600}}
.bunrui{{scroll-margin-top:110px}}
.bsec{{background:linear-gradient(135deg,#33418f,#7a4ff7);color:#fff;border-radius:16px;padding:14px 20px;margin:22px 0 6px;display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;box-shadow:0 6px 18px rgba(51,65,143,.22)}}
.bsec .bno{{font-size:18px;font-weight:800;letter-spacing:1px}}
.bsec .bsub{{font-size:12.5px;opacity:.9}}
.note{{background:var(--acc2);border-left:3px solid var(--acc);border-radius:10px;padding:10px 14px;font-size:13px;color:#38405a;margin:14px 0}}
h2.sec{{background:var(--card);border-radius:16px;box-shadow:0 4px 16px rgba(30,40,90,.08);padding:16px 20px;margin:22px 0 14px;font-size:16px;color:#33418f;border-left:5px solid var(--c);word-break:break-all;scroll-margin-top:110px}}
.qanchor{{font-size:12px;color:#a8aebc;font-weight:600;text-decoration:none;margin-left:8px}}
.qanchor:hover{{color:var(--acc)}}
.dist-h{{background:#fff8f2;border:1.5px solid var(--warn);color:#c2410c;border-radius:12px;padding:9px 16px;margin:16px 0;font-size:13px;font-weight:700}}
details.card{{background:var(--card);border-radius:16px;box-shadow:0 4px 16px rgba(30,40,90,.08);margin:12px 0;border:1.5px solid var(--line);overflow:hidden;scroll-margin-top:110px}}
details.card>summary{{list-style:none;cursor:pointer;padding:14px 18px;font-size:16.5px;font-weight:700;display:flex;align-items:baseline;gap:12px}}
details.card>summary::-webkit-details-marker{{display:none}}
details.card>summary:hover{{background:var(--acc2)}}
details.card[open]>summary{{border-bottom:1px solid var(--line);background:var(--acc2)}}
.wn{{color:#33418f}}
.wy{{color:var(--c);font-size:14px;font-weight:600}}
.tag{{margin-left:auto;background:var(--warn);color:#fff;border-radius:99px;padding:2px 12px;font-size:11.5px;flex:none}}
.tag.ok{{background:var(--ok);margin-left:10px}}
.tag.ok+.tag{{margin-left:10px}}
.cbody{{padding:4px 18px 16px}}
.cbody p,.cbody div{{margin:7px 0;font-size:14px}}
.cbody ruby{{color:var(--ink)}}
.cbody rt{{font-size:.55em;color:var(--sub);font-weight:700}}
.ip{{display:inline-flex;align-items:center;vertical-align:-0.18em;margin-left:6px}}
.ip audio{{width:1px;height:1px;position:absolute;opacity:0;pointer-events:none}}
.pb{{flex:none;width:25px;height:25px;border-radius:50%;border:1.5px solid var(--pb);background:color-mix(in srgb,var(--pb) 10%,#fff);color:var(--pb);cursor:pointer;display:inline-flex;align-items:center;justify-content:center;transition:transform .12s ease,background .12s ease;padding:0}}
.pb--moji{{--pb:#4f6ef7}}
.pb--edge{{--pb:#e8590c}}
.pb--nade{{--pb:#1f9d55}}
.pb:hover,.pb.on{{background:var(--pb);color:#fff;transform:scale(1.1)}}
summary .ip{{vertical-align:-0.15em}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 0 0 rgba(79,110,247,.4)}}50%{{box-shadow:0 0 0 6px rgba(79,110,247,0)}}}}
.kv b{{color:var(--acc)}}
.note-p{{background:var(--acc2);border-radius:8px;padding:6px 10px;font-size:13px}}
.drain{{color:#7f2ff7}}
.en{{color:#5b6478;font-size:13px}}
.meta{{color:#5b6478;font-size:12.5px;word-break:break-all}}
.s-h{{font-size:15.5px;margin-top:12px!important}}
.m-ico{{margin-right:6px}}
.rare{{color:#e8590c;font-size:13px;background:#fff8f2;border-radius:8px;padding:6px 10px}}
img{{max-width:280px;width:100%;border-radius:10px;border:1px solid var(--line);margin:6px 0;display:block;cursor:zoom-in}}
img:active{{transform:scale(1.6);transform-origin:top left;cursor:zoom-out}}
.linkline{{word-break:break-all;font-size:12.5px}}
.url{{color:var(--sub);font-size:11.5px;word-break:break-all}}
a{{color:var(--acc)}}
.hr{{border-top:2px dashed var(--line);margin:22px 0}}
footer{{text-align:center;font-size:12px;color:var(--sub);padding:18px}}
.hidden{{display:none!important}}
a.toplink{{color:#fff;opacity:.9;font-size:12.5px;text-decoration:underline}}
</style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <p>{sub}</p>
  <div class="tags"><span>{total_cards} 词条</span><span>{total_dist} 干扰项</span><span>{embeds} 发音内嵌</span></div>
</header>
<div class="nav"><span class="nlabel">区分</span>{chr(10).join(nav)}</div>
<div class="legend"><span><span class="lg lg--moji"></span>MOJi辞書 原声</span><span><span class="lg lg--edge"></span>Edge TTS 合成</span><span><span class="lg lg--nade"></span>Nadeshiko 台词</span></div>
<div class="toolbar">
  <input id="q" placeholder="🔍 搜索词条 / 读音 / 例句…">
  <span class="cnt" id="cnt"></span>
</div>
<main id="main">
{chr(10).join(sections_html)}
</main>
<footer>学习材料由 moji × nadeshiko 生成・仅供个人备考学习 ・ <a href="index.html">← 返回题库首页</a></footer>
<script>
const cards=[...document.querySelectorAll('details.card')];
const cnt=document.getElementById('cnt');
function apply(){{
 const k=document.getElementById('q').value.trim().toLowerCase();
 let shown=0;
 cards.forEach(c=>{{const hit=c.dataset.w.includes(k)||c.textContent.toLowerCase().includes(k);c.classList.toggle('hidden',!hit);if(hit)shown++;}});
 cnt.textContent=shown+' / '+cards.length;
}}
document.getElementById('q').addEventListener('input',apply);
apply();
const chips=[...document.querySelectorAll('.chip.on')];
const secs=[...document.querySelectorAll('section.bunrui')];
const io=new IntersectionObserver(es=>es.forEach(e=>{{
 if(!e.isIntersecting)return;
 chips.forEach(c=>c.dataset.cur=c.getAttribute('href')==='#'+e.target.id?'1':'0');
}}),{{rootMargin:'-40% 0px -55% 0px'}});
secs.forEach(s=>io.observe(s));
// icon-only audio player (inline buttons): one source at a time; capture
// phase so a click on a button inside a <summary> can't toggle the card.
const PLAY_SVG='<path class="ic-play" d="M8 5.5v13l11-6.5z"/><path class="ic-stop" d="M6 6h4v12H6zM14 6h4v12h-4z" style="display:none"/>';
const STOP_SVG='<path class="ic-play" d="M8 5.5v13l11-6.5z" style="display:none"/><path class="ic-stop" d="M6 6h4v12H6zM14 6h4v12h-4z"/>';
function off(b){{
 b.classList.remove('on');
 const svg=b.querySelector('svg');svg.innerHTML=PLAY_SVG;
 const a=b.parentNode.querySelector('audio');if(a)a.pause();
}}
let cur=null;
document.addEventListener('click',e=>{{
 const btn=e.target.closest('.pb');if(!btn)return;
 e.preventDefault();e.stopImmediatePropagation();
 const a=btn.parentNode.querySelector('audio');if(!a)return;
 if(cur&&cur!==btn)off(cur);
 if(a.paused){{
  a.play();btn.classList.add('on');
  const svg=btn.querySelector('svg');svg.innerHTML=STOP_SVG;
  cur=btn;
 }}else{{
  off(btn);cur=null;
 }}
}},true);
document.addEventListener('ended',e=>{{
 if(cur&&e.target===cur.parentNode.querySelector('audio')){{
  off(cur);cur=null;
 }}
}},true);
document.addEventListener('ended',e=>{{
 if(cur&&e.target===cur.parentNode.querySelector('audio')){{
  off(cur);cur=null;
 }}
}},true);
</script>
</body>
</html>"""
    out_path.write_text(html, encoding="utf-8")
    embeds = audio_tot.get("word_audio", 0) + audio_tot.get("exam_audio", 0) + audio_tot.get("stem_audio", 0)
    print(f"WROTE {out_path}  [{total_cards}] cards ({total_dist} distractor) across {len(ready)}/{len(materials)} materials, "
          f"{len(html)//1024} KB, {embeds} 内嵌发音 = "
          f"{audio_tot.get('word_audio',0)} 辞典 + {audio_tot.get('exam_audio',0)} 例文 "
          f"(MOJi原声 {audio_tot.get('exam_moji',0)} / Edge TTS {audio_tot.get('exam_edge',0)}) "
          f"+ {audio_tot.get('stem_audio',0)} 题干 + {audio_tot.get('nade_audio',0)} 台词(远程)")


def json_answers(answers):
    return json.dumps(answers, ensure_ascii=False)


import json
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build vocab-words HTML page")
    parser.add_argument("--session",
                        help="Build a single session (e.g. 2024-07, 2024-12)")
    parser.add_argument("--all", action="store_true",
                        help="Build all sessions with study materials")
    args = parser.parse_args()

    sessions_to_build = []
    if args.all:
        sessions_to_build = all_sessions()
    elif args.session:
        sessions_to_build = [args.session]
    else:
        parser.print_help()
        raise SystemExit(1)

    for sid in sessions_to_build:
        cfg = session_cfg(sid)
        out = ROOT / "docs" / (f"vocab-words-{sid}.html" if sid != "2024-07" else "vocab-words.html")
        main(title=cfg["title"], sub=cfg["sub"], materials=cfg["materials"],
             answers=cfg["answers"], out_path=out)