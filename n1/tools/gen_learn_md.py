#!/usr/bin/env python3
"""Generate public 語注・例句集 markdown for ALL bank question types.

Reads the (gitignored) plaintext bank JSONs under past-exams/ and emits, for
every question type beyond the existing 問題1/問題2 pages, an analysis/*.md in
the exact markdown shape that tools/build_words_html.py renders into the public
docs/ pages.

Type mapping (resolved per file, both 2024-07 and 2024-12):
  語彙: paraphrase→q3, usage→q4
  文法: choice→q5, composition→q6, passage→q7
  読解: short→q8, mid→q9, long→q10
  聴解: all sub-types → toki

Every covered vocabulary word / grammar pattern is enriched ONCE (cached in
tools/data/learn_cache.json) from:
  - moji      : reading, meanings, MOJi example + word/example audio
  - nadeshiko : real anime/J-Drama segments (furigana line, EN, screenshot +
                audio URLs)
聴解 exam audio is referenced by its remote URL (直线). 听力原文 / 用法例文 /
文法例文 / 考查句 lines get Edge-TTS speech in ~/edge_tts_examples under the
same sha1 hash the renderer's exam_ip() looks up.

Usage:  python3 tools/gen_learn_md.py --session 2024-07 | --all
"""
import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "past-exams"
ANALYSIS = ROOT / "analysis"
CACHE = ROOT / "tools" / "data" / "learn_cache.json"
EXAMPLE_MAP = ROOT / "tools" / "data" / "moji_example_map.json"
MOJI_AUDIO = Path(os.path.expanduser("~/moji_audio"))
EDGE_TTS_DIR = Path(os.path.expanduser("~/edge_tts_examples"))
TMP = Path("/tmp/opencode")
TMP.mkdir(parents=True, exist_ok=True)

KANJI = r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\u3005\u3006\u3007々〆〇]"
KOKU = KANJI + r"{2,}"
KATA_RE = re.compile(r"[ァ-ヶヴー]")
KATA_RUN = re.compile(r"[ァ-ヶヴー]{3,}")
KANA_RE = re.compile(r"[ぁ-ゖァ-ヺ]")
FURIGANA_PAIR = re.compile(r"(" + KANJI + r"+)(\([" + "ぁ-ゖァ-ヺー・ゝゞ" + r"]+\))")
SPEAKER_RE = re.compile(r"^[^:：]{1,10}[:：]\s*")
OPT_NO_RE = re.compile(r"^\d+[.、．．]?\s*")

# JLPT N1 聴解 問題1〜5 official type names (問題4 即時応答's old name was 発話表現)
LISTEN_DESC = {"point": "課題理解", "grammar": "ポイント理解",
               "overview": "概要理解", "detailed": "即時応答", "implication": "統合理解"}
NONKEY_TAGS = ("言葉の意味", "文脈規定", "文法選択", "文法", "聴解")

SESSIONS = (
    "2010-07", "2010-12", "2011-07", "2011-12", "2012-07", "2012-12",
    "2013-07", "2013-12", "2014-07", "2014-12", "2015-07", "2015-12",
    "2016-07", "2016-12", "2017-12", "2018-07", "2018-12", "2019-07",
    "2019-12", "2020-12", "2021-12", "2022-07", "2022-12", "2023-07",
    "2024-07", "2024-12", "2025-07",
)
SESSION_DIR = {s: f"{s.split('-')[0]}/{s.split('-')[1]}" for s in SESSIONS}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt_tts(s):
    s = FURIGANA_PAIR.sub(lambda m: m.group(1) + m.group(2), s)
    return re.sub(r"\s+", " ", str(s)).strip()


def example_norm(s):
    s = FURIGANA_PAIR.sub(lambda m: m.group(1) + m.group(2), s)
    s = s.replace("「", "").replace("」", "")
    return re.sub(r"\s+", " ", s).strip()


def edge_audio(text):
    h = hashlib.sha1(fmt_tts(text).encode()).hexdigest()[:16]
    f = EDGE_TTS_DIR / f"{h}.mp3"
    if f.exists():
        return str(f)
    try:
        subprocess.run(["edge-tts", "--voice", "ja-JP-NanamiNeural", "--text", text,
                        "--write-media", str(f)], capture_output=True, timeout=90)
    except FileNotFoundError:
        return None
    return str(f) if f.exists() else None


# --------------------------------------------------------------- enrichment

def cache_load():
    if CACHE.exists():
        try:
            return json.load(open(CACHE, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # salvage the valid prefix written before a dump was interrupted
            txt = CACHE.read_text(encoding="utf-8", errors="ignore")
            try:
                i = txt.index('"tokens"')
                i = txt.index("{", txt.index(":", i))
            except ValueError:
                i = -1
            tok, n = {}, len(txt)
            dec = json.JSONDecoder()
            while i >= 0 and i < n:
                while i < n and txt[i] in " \t\n\r":
                    i += 1
                if i >= n or txt[i] != '"':
                    break
                try:
                    k, i = dec.raw_decode(txt, i)
                except json.JSONDecodeError:
                    break
                while i < n and txt[i] in " \t\n\r":
                    i += 1
                if i >= n or txt[i] != ":":
                    break
                i += 1
                while i < n and txt[i] in " \t\n\r":
                    i += 1
                try:
                    v, i = dec.raw_decode(txt, i)
                except json.JSONDecodeError:
                    break
                tok[k] = v
                while i < n and txt[i] in " \t\n\r":
                    i += 1
                if i < n and txt[i] == ",":
                    i += 1
                else:
                    break
            if tok:
                print(f"[cache repair] salvaged {len(tok)} token entries")
                return {"tokens": tok}
    return {"tokens": {}}


CACHE_LOCK = threading.Lock()


def cache_save(c):
    with CACHE_LOCK:
        snap = dict(c["tokens"])
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"tokens": snap}, open(CACHE, "w", encoding="utf-8"),
              ensure_ascii=False)


def word_like(tok):
    return bool(re.search(KANJI, tok)) or len(tok) >= 3


def moji_query(tok, download):
    rec = {"moji": None, "ok": False}
    jf = TMP / f"moji_{hashlib.sha1(tok.encode()).hexdigest()[:10]}.json"
    for attempt in (1, 2):
        try:
            args = ["moji", tok, "-a" if download else "", "--once", "--json", str(jf)]
            subprocess.run([a for a in args if a], input=b"0\n",
                           capture_output=True, timeout=100)
        except FileNotFoundError:
            return rec
        except subprocess.TimeoutExpired:
            continue
        if jf.exists() and jf.stat().st_size:
            break
        time.sleep(2)
    if jf.exists():
        try:
            d = json.load(open(jf))
        except (json.JSONDecodeError, OSError):
            d = None
        if d and d.get("word"):
            rec["moji"] = d
            rec["ok"] = (d["word"].get("spell") == tok)
            if rec["ok"] and download:
                rec["audio"] = True
    try:
        jf.unlink()
    except OSError:
        pass
    return rec


def kana_to_hira(s):
    return "".join(chr(ord(c) - 0x60) if 0x30A1 <= ord(c) <= 0x30F6 else c for c in s)


def nade_seg_ok(seg):
    content = (seg.get("textJa") or {}).get("content") or ""
    cleaned = re.sub(r"\s", "", content)
    if not cleaned:
        return False
    kana = len(KANA_RE.findall(cleaned)) + len(re.findall(KATA_RE, cleaned))
    if kana / len(cleaned) < 0.30:
        return False
    return True


def nade_query(tok):
    rec = {"nade": [], "media": {}}
    jf = TMP / f"nade_{hashlib.sha1(tok.encode()).hexdigest()[:10]}.json"
    try:
        subprocess.run(["nadeshiko", "search", tok, "--once", "-n", "2",
                        "--exact", "--json", str(jf)], capture_output=True, timeout=100)
    except FileNotFoundError:
        return rec
    if jf.exists():
        try:
            d = json.load(open(jf))
        except (json.JSONDecodeError, OSError):
            d = None
        if d:
            rec["nade"] = [s for s in (d.get("segments") or []) if nade_seg_ok(s)]
            med = (d.get("includes") or {}).get("media") or {}
            rec["media"] = {k: (v.get("nameJa") or v.get("nameRomaji") or k)
                            for k, v in med.items()}
    try:
        jf.unlink()
    except OSError:
        pass
    return rec


def enrich(tok, cache):
    with CACHE_LOCK:
        if tok in cache["tokens"]:
            return cache["tokens"][tok]
    if not tok or len(tok) > 64:
        with CACHE_LOCK:
            cache["tokens"][tok] = {"skip": True}
        return {"skip": True}
    rec = {"skip": True}
    if len(tok) >= 2 and word_like(tok):
        rec = {"skip": False}
        rec.update(moji_query(tok, True))
        rec.update(nade_query(tok))
    with CACHE_LOCK:
        cache["tokens"][tok] = rec
    return rec


def attrs_examples(rec):
    md = rec.get("moji") or {}
    w = md.get("word") or {}
    spell = w.get("spell", "")
    exs = md.get("examples") or []
    if not spell or not exs:
        return None
    files = sorted(glob.glob(str(MOJI_AUDIO / f"{spell}_*_e*_*.mp3")))
    idx = {}
    for f in files:
        m = re.search(rf"^{re.escape(spell)}_(\d+)_e(\d+)_[\w-]+\.mp3$",
                      os.path.basename(f))
        if m:
            idx.setdefault(int(m.group(2)), f)
    if not idx:
        return None
    out = {}
    for i, ex in enumerate(exs):
        f = idx.get(i)
        if not f:
            continue
        t = example_norm(ex.get("title", ""))
        if t and t not in out:
            out[t] = f
    return out


def init_example_map():
    try:
        return json.load(open(EXAMPLE_MAP, encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


# ---------------------------------------------------------------- inventory

def jp_line(line):
    line = line.strip()
    if not line:
        return None
    if OPT_NO_RE.match(line) or line.startswith(("原文", "选项翻译", "译文", "翻译",
                                                 "构思", "解析", "参考译")):
        return None
    line = SPEAKER_RE.sub("", line, count=1)
    cleaned = re.sub(r"\s", "", line)
    if not cleaned:
        return None
    kana = len(KANA_RE.findall(cleaned))
    if kana / len(cleaned) < 0.40:
        return None
    return line


def key_lines(expl, limit=3):
    got = []
    for ln in (expl or "").splitlines():
        j = jp_line(ln)
        if j and len(j) >= 5 and not re.match(r"^\d+[.、]", j):
            got.append(j)
        if len(got) >= limit:
            break
    return got


def freq_words(text, limit=6):
    cap = re.sub(r"[（）()【】「」『』…、，,。．.!?！？・\s《》〈〉“”\"]", "", text)
    cands = []
    for m in re.finditer(KOKU, cap):
        cands.append(m.group(0))
    for m in KATA_RUN.finditer(cap):
        cands.append(m.group(0))
    cnt = {}
    for w in cands:
        if len(w) >= 2:
            cnt[w] = cnt.get(w, 0) + 1
    return sorted(cnt, key=lambda w: (-cnt[w], -len(w)))[:limit]


def basic_inv():
    inv = {}
    for session in SESSIONS:
        inv.setdefault(session, {})
        root = BANK / SESSION_DIR[session]
        for sdir in ("vocab", "grammar", "reading", "listening"):
            for f in glob.glob(str(root / sdir / "*.json")):
                d = json.load(open(f))
                kind = d.get("type")
                if kind in ("reading", "context"):
                    continue
                try:
                    num = int(d.get("number") or 0)
                except ValueError:
                    num = 0
                inv[session][d["id"]] = (kind, num, d)
    return inv


# ---------------------------------------------------------------- markdown

def grain(rec):
    if not rec:
        return ""
    w = (rec.get("moji") or {}).get("word") or {}
    return (w.get("pron") or "").lower()


def card(word, rec):
    """Full card detail (without the ### heading)."""
    md = rec.get("moji") if rec else None
    L = []
    if md and rec.get("ok"):
        defs = []
        for s in (md.get("subdetails") or []):
            t = s.get("title", "")
            if t and t not in defs:
                defs.append(t)
        for s in (md.get("details") or []):
            t = s.get("title")
            if t and t not in defs:
                defs.append(t)
        L.append(f"- **释义**：{'；'.join(defs[:4])}")
        exs = md.get("examples") or []
        if exs:
            L.append(f"- **MOJi 例句**：{exs[0].get('title','')}")
        else:
            L.append("- **备注**：MOJi に例文なし。")
    elif md and not rec.get("ok"):
        alt = (md.get("word") or {}).get("spell", "")
        defs = []
        for s in (md.get("subdetails") or [])[:2]:
            t = s.get("title", "")
            if t and t not in defs:
                defs.append(t)
        for s in (md.get("details") or [])[:1]:
            t = s.get("title")
            if t and t not in defs:
                defs.append(t)
        if alt and defs and len(word) <= 6:
            L.append(f"- **释义（近義・{alt}）**：{'；'.join(defs[:3])}")
        else:
            L.append(f"- **备注**：MOJi に「{word}」そのままの見出しなし（候補と読み合わせ）。")
    else:
        L.append(f"- **备注**：MOJi 未収録（主に文型・間投詞）。")
    n = rec.get("nade") if rec else None
    if n:
        if not rec.get("ok"):
            n = [s for s in n if word in ((s.get("textJa") or {}).get("content") or "")]
        if n:
            L.append("- **作品台词**：")
            media = rec.get("media") or {}
            for seg in n[:2]:
                L += nade_line(seg, media)
    return L


def nade_line(seg, media):
    toks = (seg.get("textJa") or {}).get("tokens") or []
    parts = []
    for t in toks:
        s = t.get("s", "")
        if not s.strip():
            continue
        r = kana_to_hira(t.get("r") or "")
        if r and re.search(KANJI, s) and r not in (s, s.lower()):
            parts.append(f"{s}({r})")
        else:
            parts.append(s)
    text = "".join(parts).strip()
    if not text:
        text = (seg.get("textJa") or {}).get("content", "")
    ten = seg.get("textEn") or {}
    en = ten.get("content", "") if isinstance(ten, dict) else ""
    ep = seg.get("episode") or "?"
    ms = int((seg.get("startTimeMs") or 0) / 1000)
    pid = seg.get("mediaPublicId") or ""
    title = media.get(pid, pid)
    spid = seg.get("publicId") or ""
    urls = seg.get("urls") or {}
    L = [f"  - {text}"]
    if en:
        L.append(f"    - EN: {en}")
    L.append(f"    - ≪{title}≫ EP{ep} @ {ms//60}:{ms%60:02d}　https://nadeshiko.co/en/sentence/{spid}")
    piece = urls.get("audioUrl", "")
    if urls.get("imageUrl"):
        piece += f"  🖼 {urls['imageUrl']}"
    if piece:
        L.append(f"    - {piece}")
    return L


def quoted(expl):
    m = re.search(r"「([^」]{6,120}」)", expl or "")
    return m.group(1).rstrip("」") if m else ""


def listen_tag(d):
    m = re.search(r"問題(\d+)\((\d+)\)", (d.get("source") or ""))
    if m:
        return f"T{m.group(1)}{int(m.group(2)):02d}"
    return "T000"


def build_session(session, inv, cache, emap):
    grp = {}
    for (kind, num, d) in inv[session].values():
        grp.setdefault(kind, []).append((num, d))
    out = {}

    def emit(sid, label, file_stem, note, rows, per_row, kind):
        L = [f"# {session} {label} 語注・例句集　（moji × nadeshiko）",
             "",
             f"> {note} 語注・発音例文は MOJi辞書、実例台詞は Nadeshiko（アニメ・日劇の音声＋場面画像）。",
             f"> 収録範囲: {label} 全{len(rows)}問。" if kind == "listening"
             else f"> 収録範囲: {label} 全{len(rows)}問（Q{min(n for n, _ in rows)}〜Q{max(n for n, _ in rows)}）。",
             ""]
        for num, d in sorted(rows, key=lambda x: (listen_tag(x[1]) if kind == "listening" else int(x[0]))):
            if kind == "listening":
                tag = listen_tag(d)
                L.append(f"## {tag}　{sec_title(d, kind)}")
            else:
                L.append(f"## Q{num}　{sec_title(d, kind)}")
            L.append("")
            per_row(d, L)
            L.append("---")
            L.append("")
        fname = f"{file_stem}.md"
        ANALYSIS.mkdir(parents=True, exist_ok=True)
        (ANALYSIS / fname).write_text("\n".join(L).rstrip() + "\n", encoding="utf-8")
        out[sid] = fname

    if "paraphrase" in grp:
        def per(d, L):
            target = (d.get("target") or "").strip()
            tr = cache["tokens"].get(target, {})
            L += card_d(head(target, tr), card(target, tr))
            L.append("")
            ans_i = None
            try:
                ans_i = int(d["answer"]) - 1
            except (KeyError, ValueError):
                pass
            for i, o in enumerate(d.get("options") or []):
                if not o:
                    continue
                rec = cache["tokens"].get(o, {})
                h = head(o, rec) + ("　干扰项" if i != ans_i else "")
                L += card_d(h, card(o, rec))
                L.append("")
        emit("q3", "問題3 言い換え", f"{session}-paraphrase",
             "語彙・言葉の言い換え（同義表現）。選択肢を語注付きで一括収録。",
             grp["paraphrase"], per, "paraphrase")

    if "usage" in grp:
        def per(d, L):
            target = (d.get("target") or "").strip()
            rec = cache["tokens"].get(target, {})
            L += card_d(head(target, rec), card(target, rec))
            L.append("")
            for i, o in enumerate(d.get("options") or [], 1):
                if not o:
                    continue
                edge_audio(o)
                L.append(f"- **用法例文{i}**：{o}")
            L.append("")
        emit("q4", "問題4 使い方", f"{session}-usage",
             "語彙の使い分け（文を作る問題）。正解語の語注＋MOJi 例文。",
             grp["usage"], per, "usage")

    for kind, sid, label, fstem, blurb in (
            ("choice", "q5", "問題5 文法選択", f"{session}-grammar-choice", "文型選択。正解の文型を MOJi ＋ Nadeshiko で用例ごと収録。"),
            ("passage", "q7", "問題7 文法問題", f"{session}-grammar-passage", "文章中の空欄文型。正解文型の用例を収録。"),
    ):
        if kind not in grp:
            continue
        def per(d, L, kind=kind):
            opts = d.get("options") or []
            try:
                pat = opts[int(d["answer"]) - 1]
            except (KeyError, ValueError, IndexError):
                pat = ""
            if not pat:
                pat = next((t for t in (d.get("tags") or []) if t not in NONKEY_TAGS), "")
            rec = cache["tokens"].get(pat, {})
            L += card_d(head(pat, rec), card(pat, rec))
            L.append("")
            sent = quoted(d.get("explanation"))
            if sent and re.search(KANJI, sent) and KANA_RE.search(sent):
                edge_audio(sent)
                L.append(f"- **文法例文**：{sent}")
                L.append("")
        emit(sid, label, fstem, blurb, grp[kind], per, kind)  # type branch

    if "composition" in grp:
        def per(d, L):
            sent = quoted(d.get("explanation"))
            tag = next((t for t in (d.get("tags") or []) if t not in NONKEY_TAGS), "")
            if sent:
                edge_audio(sent)
                L.append(f"- **文法例文**：{sent}")
                L.append("")
            rec = cache["tokens"].get(tag, {}) if tag else {}
            L += card_d(head(tag, rec), card(tag, rec))
            L.append("")
        emit("q6", "問題6 並べ替え", f"{session}-composition",
             "フレーズ並べ替え。要点となる文型・フレーズの語注＋用例。",
             grp["composition"], per, "composition")

    for kind, sid, label, fstem, blurb in (
            ("short", "q8", "問題8 短文読解", f"{session}-reading-short", "短文の要点語彙。"),
            ("mid", "q9", "問題9 中文読解", f"{session}-reading-mid", "中文の要点語彙。"),
            ("long", "q10", "問題10 長文読解", f"{session}-reading-long", "長文の要点語彙。"),
    ):
        if kind not in grp:
            continue
        def per(d, L, kind=kind):
            target = (d.get("target") or "").strip()
            if target:
                edge_audio(target)
                L.append(f"- **考查句**：{target}")
                L.append("")
            qtext = (d.get("question") or "")
            seen = set()
            for w in freq_words(qtext[:1500] + " " + target, limit=10):
                rec = cache["tokens"].get(w)
                if w in seen or not rec or rec.get("skip"):
                    continue
                if not (rec.get("ok") or rec.get("nade")):
                    continue
                seen.add(w)
                L += card_d(head(w, rec), card(w, rec))
                L.append("")
                if len(seen) >= 3:
                    break
        emit(sid, label, fstem, blurb, grp[kind], per, kind)  # type branch

    listen_rows = [(num, d)
                   for kind in LISTEN_DESC for (num, d) in grp.get(kind, [])]
    if listen_rows:
        def per(d, L):
            lines = key_lines(d.get("explanation"), 3)
            for kl in lines:
                edge_audio(kl)
                L.append(f"- **听力原文**：{kl}")
            au = (d.get("audio") or [""])[0]
            if au:
                L.append(f"- **听力音频**：{au}")
            L.append("")
            text = " ".join(lines)
            seen = set()
            for w in freq_words(text, limit=8):
                rec = cache["tokens"].get(w)
                if w in seen or not rec or rec.get("skip"):
                    continue
                if not (rec.get("ok") or rec.get("nade")):
                    continue
                seen.add(w)
                L += card_d(head(w, rec), card(w, rec))
                L.append("")
                if len(seen) >= 2:
                    break
            L.append("")
        emit("toki", "聴解 全問題", f"{session}-listening",
             "聴解の原文抜粋＋当該語彙の語注。試験音声は原音リンク付き。",
             listen_rows, per, "listening")
    return out


def head(word, rec):
    y = grain(rec)
    return f"### {word}（{y}）" if y else f"### {word}"


def card_d(heading, body):
    return [heading] + body


def sec_title(d, kind):
    if kind in ("short", "mid", "long"):
        return {"short": "短文読解", "mid": "中文読解", "long": "長文読解"}[kind]
    if kind == "listening":
        return LISTEN_DESC.get(d.get("type"), "聴解")
    t = (d.get("target") or "").strip()
    if t:
        return t[:24]
    for tag in (d.get("tags") or []):
        if tag not in NONKEY_TAGS and len(tag) <= 24:
            return tag
    return d.get("type", "")


# -------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    sessions = list(SESSIONS) if args.all else [args.session]
    sessions = [s for s in sessions if s in SESSIONS]
    if not sessions:
        ap.error("need --session 2024-07/2024-12 or --all")
    inv = basic_inv()
    cache = cache_load()
    emap = init_example_map()

    todo = []
    for s in sessions:
        for (kind, num, d) in inv[s].values():
            target = (d.get("target") or "").strip()
            if kind == "paraphrase":
                todo += [target] + [o for o in (d.get("options") or []) if o]
            elif kind == "usage":
                todo.append(target)
            elif kind in ("choice", "passage"):
                opts = d.get("options") or []
                try:
                    pat = opts[int(d["answer"]) - 1]
                except (KeyError, ValueError, IndexError):
                    pat = next((t for t in (d.get("tags") or []) if t not in NONKEY_TAGS), "")
                todo.append(pat)
            elif kind == "composition":
                todo.append(next((t for t in (d.get("tags") or []) if t not in NONKEY_TAGS), ""))
            elif kind in ("short", "mid", "long"):
                todo += freq_words((d.get("question") or "")[:1500] + " " + target, limit=8)
                if target:
                    todo.append(target)
            elif kind in LISTEN_DESC:
                todo += freq_words(" ".join(key_lines(d.get("explanation") or "", 3)), limit=8)
    uniq = []
    seen = set()
    for t in todo:
        if t and t not in seen:
            seen.add(t)
            uniq.append(t)
    need = [t for t in uniq if t not in cache["tokens"]]
    print(f"tokens: {len(uniq)} unique, {len(need)} uncached — enriching…")
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(enrich, t, cache): t for t in need}
        for fut in as_completed(futs):
            try:
                fut.result()
            except Exception as e:
                print("  ! enrich failed:", e)
            done += 1
            if done % 25 == 0:
                cache_save(cache)
                print(f"  enriched {done}/{len(need)}  ({time.time()-t0:.0f}s)")
    cache_save(cache)
    print(f"enrichment done in {time.time()-t0:.0f}s")

    changed = False
    for tok, rec in cache["tokens"].items():
        if rec.get("audio"):
            attrs = attrs_examples(rec)
            if attrs:
                emap.setdefault(tok, {}).update(attrs)
                changed = True
    if changed:
        EXAMPLE_MAP.parent.mkdir(parents=True, exist_ok=True)
        json.dump(emap, open(EXAMPLE_MAP, "w", encoding="utf-8"),
                  ensure_ascii=False)
        print(f"merged example audio map ({len(emap)} words)")

    for s in sessions:
        print("building", s)
        for sid, fname in sorted(build_session(s, inv, cache, emap).items()):
            print("  ", sid, "->", fname)


if __name__ == "__main__":
    main()