#!/usr/bin/env python3
"""Generate 耳から勉強 audio from a past-exam session (2024-07 by default):
every Japanese sentence that appeared in the paper, read aloud (Edge-TTS,
ja-JP-NanamiNeural) in exam order, with echo gaps designed for the brain's
memory loop (shadowing / subvocal repetition).

Layout (study-friendly chunking, not capped at one file):
  <session>-01-vocab.mp3            文字・語彙  Q1-25
  <session>-02-grammar.mp3          文法        Q26-44
  <session>-03-reading-short-mid.mp3 読解 前半   Q45-56
  <session>-04-reading-long.mp3     読解 後半   Q57-66
  <session>-05-listening.mp3        聴解        T101-503
  <session>-all-sentences.mp3       combined in exam order

Audio pattern per sentence:  read → 2.0s echo gap → next (repeat aloud).
Each unit file starts with a one-phrase spoken cue. Between units ~3s.

Output: refs/exam_tts/<session>/ (gitignored). Tool itself is pushable.
Usage:
  python3 tools/gen_exam_tts.py --session 2024-07
  python3 tools/gen_exam_tts.py --all
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

VOICE = "ja-JP-NanamiNeural"
REPO = Path(__file__).resolve().parent.parent
SESSIONS = {"2024-07": "2024/07", "2024-12": "2024/12"}
SECTION_RANK = {"vocab": 0, "grammar": 1, "reading": 2, "listening": 3}
ECHO_GAP, UNIT_GAP = 2.0, 3.0
KANA = re.compile(r"[ぁ-んァ-ン]")
SPK = re.compile(r"^[^：:]{0,8}[:：]\s*")
LEAD = re.compile(r"^[（(]\s*\d+\s*[）)]\s*")
OP = re.compile(r"^[1-4]\s*[.、．]\s*(.*)$")
QUOTE = re.compile(r"「([^」]{4,})」")

UNITS = [
    ("01-vocab", "文字・語彙", lambda m: m[0] == "vocab"),
    ("02-grammar", "文法", lambda m: m[0] == "grammar"),
    ("03-reading-short-mid", "読解 前半",
     lambda m: m[0] == "reading" and m[1] in ("short", "mid")),
    ("04-reading-long", "読解 後半", lambda m: m[0] == "reading" and m[1] == "long"),
    ("05-listening", "聴解", lambda m: m[0] == "listening"),
]


def has_kana(s: str) -> bool:
    return bool(KANA.search(s))


def split_sent(text: str):
    out, cur = [], ""
    for ch in text.replace("\u3000", " "):
        cur += ch
        if ch in "。！？":
            s = cur.strip()
            if s:
                out.append(s)
            cur = ""
    s = cur.strip()
    if s:
        out.append(s)
    return out


NOTE_RE = re.compile(r"[（(]?\s*注[\s０-９\d]*\s*[）)]")
CHUURYAKU = re.compile(r"[（(]中略[）)]")


def paraphrase_sub(q: str, target: str, ans: str):
    for c in ("している", "した", "する", "なので", "で", "に", "だ"):
        if ans.endswith(c) and target and (target + c) in q:
            return q.replace(target + c, ans, 1)
    if target and target in q:
        return q.replace(target, ans, 1)
    return None


def degloss(s: str) -> str:
    s = CHUURYAKU.sub("", s or "")
    out, pos = [], 0
    for m in NOTE_RE.finditer(s or ""):
        if ":" in s[m.end():] or "：" in s[m.end():]:
            out.append(s[pos:m.start()])
            return " ".join(p for p in out if p and p.strip())
        out.append(s[pos:m.start()])
        pos = m.end()
    out.append(s[pos:])
    return " ".join(p for p in out if p and p.strip())


def clean(s: str) -> str:
    s = LEAD.sub("", s or "")
    s = s.replace("変 わる", "変わる")
    s = re.sub(r"[_★]+", "", s)
    s = re.sub(r"\s+", " ", s)
    return re.sub(r"(?<=\S) (?=\S)", "", s).strip()


BLANK = re.compile(r"[（(][　\s]*[）)]|【\d+】")
SLOT = re.compile(r"[_★＿]+")


def fill_blank(q: str, word: str):
    m = BLANK.search(q or "")
    if not m:
        return None
    q = q[:m.start()] + word + q[m.end():]
    q = re.sub(r"\s+", " ", q)
    q = re.sub(r"(?<=\d)[.．]\s+(?=[一-龯ぁ-ん])", "", q)
    q = re.sub(r"(?<=\S) (?=\S)", "", q)
    return q.strip()


def order_from_quote(qtext: str, opts):
    cand, pos, out = list(opts), 0, []
    while cand:
        best = None
        for o in cand:
            i = qtext.find(o, pos)
            if i >= 0 and (best is None or i < best[0]):
                best = (i, o)
        if not best:
            return None
        pos = best[0] + len(best[1])
        out.append(best[1])
        cand.remove(best[1])
    return out


def composition_full(d):
    q = re.sub(r"^\d+\.\s*", "", d.get("question") or "")
    opts = [o for o in (d.get("options") or []) if o]
    exp = d.get("explanation") or ""
    cands = [sm.group(1) for sm in QUOTE.finditer(exp)]
    cands += [ln for ln in exp.splitlines() if has_kana(ln)]
    cands += [exp]
    for qt in cands:
        order = order_from_quote(qt, opts)
        if len(order) != len(opts):
            continue
        slots = list(SLOT.finditer(q))
        if len(slots) != len(opts):
            continue
        filled, prev = "", 0
        for (s, o) in zip(slots, order):
            filled += q[prev:s.start()] + o
            prev = s.end()
        filled += q[prev:]
        filled = re.sub(r"\s+", "", filled).strip()
        for o in order:
            if re.search(r"(から|つつも|ものの|のに|ながら|すれば|たら|ば)$", o):
                if not filled.endswith("、"):  # insert 読点 right after that clause
                    lim = filled.find(o) + len(o)
                    filled = filled[:lim] + "、" + filled[lim:]
        if filled.endswith("多い。"):
            filled = filled[:-len("多い。")] + "おおい。"
        if has_kana(filled):
            return filled
    return None


def sort_key(d):
    sec = d.get("section") or ""
    num = int(d.get("number") or 0)
    if sec == "listening":
        m = re.search(r"問題(\d+)\((\d+)\)", d.get("source") or "")
        return (3, int(m.group(1)) if m else 99, int(m.group(2)) if m else num)
    return (SECTION_RANK.get(sec, 9), num)


def listen_items(d):
    out = []
    for raw in (d.get("explanation") or "").split("\n"):
        t = raw.strip()
        if not t:
            continue
        if re.match(r"^(选项翻译|译文|翻译|解析|参考译)", t):
            break
        if t == "原文":
            continue
        m = OP.match(t)
        if m:
            t = m.group(1)
        t = clean(SPK.sub("", t))
        if not has_kana(t) or len(t) < 2 or re.fullmatch(r"[男女]", t):
            continue
        out.append(t)
    return out


def collect(session: str):
    base = REPO / "past-exams" / SESSIONS[session]
    files = []
    for s in ("vocab", "grammar", "reading", "listening"):
        files += list((base / s).glob("*.json"))
    pfill = {}
    for pf in (base / "grammar").glob("passage_*.json"):
        pd = json.load(open(pf, encoding="utf-8"))
        nm = int(re.search(r"\d+", pf.stem).group(0))
        pfill[nm] = (pd.get("options") or [""] * 4)[int(pd.get("answer") or 1) - 1]
    rows, seen = [], set()
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        kind, sec = d.get("type"), d.get("section")
        texts = []
        if sec == "vocab":
            if kind == "reading":
                texts += split_sent(clean(d.get("question") or ""))
            elif kind == "context":
                f = fill_blank(d.get("question") or "",
                               (d.get("options") or [""] * 4)[int(d.get("answer") or 1) - 1])
                texts += split_sent(f) if f else split_sent(clean(d.get("question") or ""))
            elif kind == "paraphrase":
                q = clean(d.get("question") or "")
                ans = (d.get("options") or [""] * 4)[int(d.get("answer") or 1) - 1]
                target = (d.get("target") or "").strip()
                texts += split_sent(q)
                s2 = paraphrase_sub(q, target, ans)
                if s2 and has_kana(s2):
                    texts.append(s2)
            elif kind == "usage":
                ans = (d.get("options") or [""] * 4)[int(d.get("answer") or 1) - 1]
                s = clean(ans)
                if has_kana(s) and len(s) >= 4:
                    texts.append(s)
        elif sec == "grammar" and kind == "choice":
            f = fill_blank(d.get("question") or "",
                           (d.get("options") or [""] * 4)[int(d.get("answer") or 1) - 1])
            texts += split_sent(f) if f else split_sent(clean(d.get("question") or ""))
        elif kind == "composition":
            for s in (composition_full(d),):
                if s and has_kana(s):
                    texts.append(s)
        elif sec == "grammar" and kind == "passage":
            q = d.get("question") or ""
            q = re.sub(r"(?m)^[　\s]*【\d+】[　\s]*$", "", q)
            for ln in q.split("\n"):
                ln = re.sub(r"【(\d+)】",
                            lambda m: pfill.get(int(m.group(1)), m.group(0)), ln)
                ln = clean(ln)
                if ln:
                    texts += split_sent(ln)
        elif sec == "reading":
            for ln in (d.get("question") or "").split("\n"):
                t = clean(degloss(ln))
                if t:
                    texts += split_sent(t)
            for o in (d.get("options") or []):
                s = clean(degloss(o))
                if has_kana(s) and len(s) >= 4:
                    texts.append(s)
        elif sec == "listening":
            texts += listen_items(d)
        for t in texts:
            t = t.strip()
            if not has_kana(t) or t in seen:
                continue
            seen.add(t)
            rows.append((sort_key(d), (sec, kind, d.get("number")), t))
    rows.sort(key=lambda x: x[0])
    return [(t, m) for _, m, t in rows]


def sha(txt: str) -> str:
    return hashlib.sha1(txt.encode("utf-8")).hexdigest()[:16]


def tts_one(txt: str, out: Path, retries: int) -> bool:
    if out.exists() and out.stat().st_size > 512:
        return True
    args = ["edge-tts", "--voice", VOICE, "--text", txt, "--write-media", str(out)]
    for _ in range(retries):
        try:
            r = subprocess.run(args, capture_output=True, timeout=150)
            if r.returncode == 0 and out.exists() and out.stat().st_size > 512:
                return True
        except Exception:
            pass
        time.sleep(1.5)
    return False


def sil(outdir: Path, name: str, secs: float):
    p = outdir / name
    if not p.exists():
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                        "anullsrc=r=24000:cl=mono", "-t", str(secs),
                        "-c:a", "libmp3lame", "-b:a", "48k", str(p)],
                       capture_output=True)
    return p


def concat(outdir: Path, lst: Path, out: Path):
    base = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst)]
    r = subprocess.run(base + ["-c", "copy", str(out)], capture_output=True)
    if r.returncode != 0:
        subprocess.run(base + ["-ar", "24000", "-ac", "1", "-b:a", "48k", str(out)],
                       capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="2024-07")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--retries", type=int, default=6)
    args = ap.parse_args()
    if not shutil.which("ffmpeg"):
        print("ffmpeg not found", file=sys.stderr)
        sys.exit(2)
    sessions = list(SESSIONS) if args.all else [args.session]
    for session in sessions:
        items = collect(session)
        print(f"[{session}] {len(items)} unique sentences")
        outdir = REPO / "refs" / "exam_tts" / session
        sdir, hdir = outdir / "s", outdir / "h"
        sdir.mkdir(parents=True, exist_ok=True)
        hdir.mkdir(parents=True, exist_ok=True)
        echo = sil(outdir, "echo2s.mp3", ECHO_GAP)
        ugap = sil(outdir, "unit3s.mp3", UNIT_GAP)

        # 1) headers
        for _, head, _ in UNITS:
            if not tts_one(head, hdir / f"{sha(head)}.mp3", args.retries):
                print(f"  WARN header failed: {head}", flush=True)
        # 2) sentence clips (missing only, reuse existing)
        def okp(p):
            return p.exists() and p.stat().st_size > 512
        todo = [it for it in items if not okp(sdir / f"{sha(it[0])}.mp3")]
        failed = []
        print(f"  clips to make: {len(todo)}")
        ts = time.time()
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(tts_one, t, sdir / f"{sha(t)}.mp3", args.retries): t
                    for t, _ in todo}
            for k, fut in enumerate(as_completed(futs), 1):
                if not fut.result():
                    failed.append(futs[fut])
                if k % 50 == 0:
                    print(f"  tts {k}/{len(todo)} ({time.time()-ts:.0f}s)", flush=True)
        if failed:
            print("FAILED:", *[t[:30] for t in failed], sep="\n  ")
            sys.exit(3)
        # 3) unit files + combined
        for slug, head, pred in UNITS:
            unit_items = [(t, m) for t, m in items if pred(m)]
            lst = outdir / f"{slug}.lst"
            lines = [f"file 'h/{sha(head)}.mp3'"]
            for t, _ in unit_items:
                lines += [f"file 's/{sha(t)}.mp3'", f"file 'echo2s.mp3'"]
            lst.write_text("\n".join(lines) + "\n", encoding="utf-8")
            concat(outdir, lst, outdir / f"{session}-{slug}.mp3")
            print(f"  built {slug} ({len(unit_items)} sentences)")
        lst = outdir / "combined.lst"
        lines = []
        for i, (slug, _, _) in enumerate(UNITS):
            if i:
                lines.append("file 'unit3s.mp3'")
            lines.append(f"file '{session}-{slug}.mp3'")
        lst.write_text("\n".join(lines) + "\n", encoding="utf-8")
        concat(outdir, lst, outdir / f"{session}-all-sentences.mp3")
        manifest = {"session": session, "voice": VOICE, "echo_gap": ECHO_GAP,
                    "unit_gap": UNIT_GAP, "units": [], "items": []}
        for slug, head, pred in UNITS:
            unit_items = [x for x in items if pred(x[1])]
            manifest["units"].append({"slug": slug, "header": head,
                                      "count": len(unit_items),
                                      "file": f"{session}-{slug}.mp3"})
        manifest["items"] = [{"unit": next(slug for slug, _, p in UNITS if p(m)),
                              "text": t, "sec": m[0], "kind": m[1], "num": m[2],
                              "file": f"s/{sha(t)}.mp3"} for t, m in items]
        (outdir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{session}] done -> {outdir}")


if __name__ == "__main__":
    main()