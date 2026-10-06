#!/usr/bin/env python3
"""keymap.py — build verified answer keys for JLPT N1 sessions.

Text-maps every answer source's correct-option TEXT against the
trynihongo transcript options (order-independent), because trynihongo
shuffles option order vs official papers.

Usage:
  python3 tools/keymap.py <session>          # one session
  python3 tools/keymap.py --all             # all sessions with sources
  python3 tools/keymap.py --report         # coverage report over all

Outputs per session:
  refs/<s>_keys.json   {qnum: {"ans","source","note"}}  (qnum are trynihongo numbers)
  refs/<s>_keyreport.txt
"""
import json, re, os, sys, glob, unicodedata, difflib
from html import unescape as html_unescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFS = os.path.join(ROOT, "refs")

SESSIONS = ["2010-07","2010-12","2011-07","2011-12","2012-07","2012-12",
            "2013-07","2013-12","2014-07","2014-12","2015-07","2015-12",
            "2016-07","2016-12","2017-07","2017-12","2018-07","2018-12",
            "2019-07","2019-12","2020-12","2021-07"]


def norm(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("\u3000", " ").replace("\xa0", " ")
    s = re.sub(r"[^\w\u3040-\u30ff\u4e00-\u9fff]", "", s)
    s = re.sub(r"(ー+|[っッ])$", "", s)  # drop trailing elongation/double-consonant marks
    return s


def norm_lenient(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"[ \t\u3000\u2460-\u2473\u2160-\u217f\u00ad\u200b]+", "", s)
    return s


def best_match(qtext, options, threshold=0.82):
    qn = norm_lenient(qtext)
    cands = [(difflib.SequenceMatcher(None, qn, norm_lenient(o)).ratio(), i + 1, o)
             for i, o in enumerate(options)]
    cands.sort(key=lambda x: -x[0])
    best = cands[0]
    if best[0] >= threshold:
        return best[1], best[0]
    return None, best[0]


def load_transcript(s):
    p = os.path.join(REFS, f"{s}_trynihongo.json")
    if not os.path.exists(p):
        return None
    tn = json.load(open(p))
    return {q["num"]: q for q in tn["questions"]}


def load_jlptzhen_keys(s):
    p = os.path.join(REFS, f"{s}_vocab_jlptzhen.json")
    if not os.path.exists(p):
        return {}, {}
    jz = json.load(open(p))
    off = {"問題1": (1, 6), "問題2": (7, 13), "問題3": (14, 19), "問題4": (20, 25)}
    seen = {}
    table, byq = {}, {}
    for q in jz["questions"]:
        a, b = off[q["section"]]
        seen[q["section"]] = seen.get(q["section"], a - 1) + 1
        num = seen[q["section"]]
        if q["answer"] not in (1, 2, 3, 4):
            continue
        table[num] = {"answer": q["answer"], "correct": q["options"][q["answer"] - 1],
                      "target": q.get("target"), "explanation": q.get("explanation", "")}
        byq[num] = q
    return table, byq


def digit_to_text_answers(s, digit_array_map, official_options_text):
    """digit_array_map: {qnum: digit} in OFFICIAL positions.
    official_options_text: {qnum: [opt1..opt4]} official option texts.
    Returns {qnum: {"answer_text","pos_official"}}."""
    out = {}
    for qn, dig in digit_array_map.items():
        opts = official_options_text.get(qn)
        if not opts or not (1 <= dig <= len(opts)):
            continue
        out[qn] = {"answer_text": opts[dig - 1], "pos_official": dig}
    return out


def parse_digit_layout(text):
    """Parse xdf/koolearn layout:
    問題1
    1-6
    4 3 1 3 1 2
    Returns [(sec, a, b, [digits])] in document order. Multiple runs allowed."""
    blocks = []
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    i = 0
    while i < len(lines):
        m = re.match(r"^(?:問題|问)\s*(\d{1,2})$", lines[i])
        if not m:
            i += 1; continue
        sec = int(m.group(1))
        j = i + 1
        rng = None
        while j < len(lines) and not re.match(r"^(?:問題|问)", lines[j]):
            r = re.match(r"^(\d{1,2})\s*[-—–~～]\s*(\d{1,2})$", lines[j].strip())
            if r:
                rng = (int(r.group(1)), int(r.group(2)))
                j += 1
                break
            j += 1
        if not rng:
            i += 1; continue
        a, b = rng
        digit_lines = []
        k = j
        while k < len(lines):
            dl = re.sub(r"[\s，,、]+", "", lines[k])
            if re.fullmatch(r"[1-4]+", dl) and len(dl) <= b - a + 1 + 4:
                digit_lines.append(dl)
                k += 1
                if sum(len(d) for d in digit_lines) >= b - a + 1:
                    break
            elif re.match(r"^\d{1,2}\s*[-—–~～]\s*\d{1,2}$", lines[k]) or re.match(r"^(?:問題|问)", lines[k]):
                break
            else:
                k += 1
        flat = "".join(digit_lines)[: b - a + 1]
        if len(flat) == b - a + 1:
            blocks.append((sec, a, b, [int(c) for c in flat]))
        i = k
    # find the run of blocks whose ranges tile 1..70/69/68 starting at 1
    best = None
    if blocks:
        for start in range(len(blocks)):
            run = [blocks[start]]
            for t in blocks[start + 1:]:
                if t[1] == run[-1][2] + 1:
                    run.append(t)
                elif t[1] <= run[-1][2]:
                    continue
                else:
                    break
            if run[0][1] == 1 and run[-1][2] in (70, 69, 68):
                best = run
                break
    return best if not None else blocks[:1]


def digit_to_keylist(blocks):
    out = {}
    for sec, a, b, digs in blocks:
        for i, d in enumerate(digs):
            out[a + i] = d
    return out


def parse_weilan_digits(text, session):
    """Parse weilanliuxue '参考答案' digit pages (position-based official keys).

    Layout per section: '问题N' header, question-number rows ('NN问', individual
    digits may be split from '问' by HTML tags), then a run of answer-digit lines.
    Answers are the [1-4] tokens after the last '问' marker (or the whole run for
    sections with no number rows). Returns {(sec, a, b): [digits]} per section."""
    rng = official_ranges(session)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    sec = None
    cur = []
    secs = []
    for idx, l in enumerate(lines):
        m = re.match(r"^(问题|問)\s*(\d{1,2})$", l)
        if m:
            if sec:
                secs.append((sec, cur))
            sec = int(m.group(2))
            cur = []
        else:
            cur.append(l)
    if sec:
        secs.append((sec, cur))
    out = {}
    for sec, toks in secs:
        a, b = rng.get("問題%d" % sec)
        if not a:
            continue
        n = b - a + 1
        last_q = -1
        for i, t in enumerate(toks):
            if re.fullmatch(r"\d{1,2}问?", t) and not re.fullmatch(r"[1-4]", t):
                last_q = i
        slice_from = max(last_q + 1, 0) if last_q >= 0 else 0
        cand = [t for t in toks[slice_from:] if re.fullmatch(r"[1-4]", t)]
        digs = cand[-n:] if len(cand) >= n else cand
        if digs and len(digs) == n:
            out[(sec, a)] = [int(d) for d in digs]
    return out


def parse_inline_answers(html_files):
    """Parse koolearn-style full paper pages: question line then options 1..4 then '(4)'."""
    out = {}
    cur = None
    opt_re = re.compile(r"^\s*[1-4][\.、．]\s*(.+)$")
    for f in html_files:
        h = open(f, encoding="utf-8", errors="ignore").read()
        h = re.sub(r"<script.*?</script>", "", h, flags=re.S)
        h = re.sub(r"<style.*?</style>", "", h, flags=re.S)
        h = re.sub(r"<[^>]+>", "\n", h)
        h = re.sub(r"[ \t\u3000]+", " ", h)
        txt = h.replace("問題 1", "問題1").replace("問題 2", "問題2")
        for line in txt.split("\n"):
            line = line.strip()
            m = re.match(r"(\d{1,2})\s*[、\.]?\s*(.+)", line)
            qm = re.match(r"問題(\d{1,2})", line)
            if qm:
                cur = None
                continue
            if m and len(line) < 120 and not line.startswith("1") and re.search(r"[\u3040-\u30ff\uff00-\uffef]", line):
                pass
            am = re.match(r"\(([1-4])\)$", line)
            if am and cur and cur["opts"]:
                cur["ans"] = tuple(int(x) for x in am.group(1))
                continue
            om = opt_re.match(line)
            if om and cur is None:
                # a new question starts with number + sentence; options come next
                continue
    return out


def write_report(s, tn_by, keys, srcstats):
    lines = [f"{s} key report — {len(keys)}/{len(tn_by)} questions answered"]
    hdr = official_ranges(s)
    for sec, (a, b) in hdr.items():
        got = [n for n in range(a, b + 1) if n in keys]
        lines.append(f"  {sec} ({a}-{b}): {len(got)}/{b+1-a}  " + "".join(str(keys[n]["ans"]) if n in keys else "·" for n in range(a, b + 1)))
    lines.append("  sources: " + ", ".join(f"{k}={v}" for k, v in srcstats.items()))
    open(os.path.join(REFS, f"{s}_keyreport.txt"), "w").write("\n".join(lines))
    json.dump({str(k): v for k, v in sorted(keys.items())},
              open(os.path.join(REFS, f"{s}_keys.json"), "w"), ensure_ascii=False, indent=1)


SECTIONS = {"問題1": (1, 6), "問題2": (7, 13), "問題3": (14, 19), "問題4": (20, 25),
            "問題5": (26, 35), "問題6": (36, 40), "問題7": (41, 45),
            "問題8": (46, 49), "問題9": (50, 58), "問題10": (59, 62),
            "問題11": (63, 64), "問題12": (65, 68), "問題13": (69, 70)}


def official_ranges(s):
    """Per-session true section boundaries may differ from SECTIONS standard."""
    r = dict(SECTIONS)
    if s in ("2019-07", "2019-12"):
        r["問題9"] = (50, 57); r["問題10"] = (58, 61); r["問題11"] = (62, 63)
        r["問題12"] = (64, 67); r["問題13"] = (68, 69)
    elif s == "2020-12":
        r["問題7"] = (41, 44); r["問題8"] = (45, 48); r["問題9"] = (49, 57)
        r["問題10"] = (58, 60); r["問題11"] = (61, 62); r["問題12"] = (63, 66)
        r["問題13"] = (67, 68)
    elif s == "2021-07":
        r["問題13"] = (68, 68)
    return r


def parse_qiantu(text):
    """Parse xiamen qiántú format: lines 'QNUM [opt] [answer text]'.
    NFKC first; skip junk bare page numbers / nav counts."""
    text_ans, digit_only = {}, {}
    ans_re = re.compile(r"^(\d{1,2})\s*[\.、．)]?\s*([1-4])\s*([^\n]*)$")
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = unicodedata.normalize("NFKC", lines[i]).strip()
        i += 1
        if not line:
            continue
        m = ans_re.match(line)
        if not m:
            continue
        n = int(m.group(1)); dig = m.group(2); tail = m.group(3).strip()
        if not (1 <= n <= 70):
            continue
        if tail and tail[0].isdigit():
            continue
        if not tail:
            while i < len(lines):
                nxt = unicodedata.normalize("NFKC", lines[i]).strip()
                if re.match(r"^問題|^问题|^读解|^聴解|^听", nxt):
                    break
                if not nxt:
                    i += 1
                    continue
                if nxt[0].isdigit():
                    break
                i += 1
                tail = nxt
                break
            if not tail:
                if n >= 45:
                    digit_only[n] = dig
                continue
            text_ans[n] = {"ans": dig, "text": tail}
        else:
            text_ans[n] = {"ans": dig, "text": tail}
    return text_ans, digit_only


def count_containment(text, options):
    t = norm_lenient(text)
    if not t:
        return 0
    return sum(1 for o in options if norm_lenient(o) and (t in norm_lenient(o) or norm_lenient(o) in t))


def match_text_to_options(text, options):
    """Return best-matching option index for a short answer text.
    Exact normalized equality wins; else containment; else best ratio >= 0.7."""
    t = norm_lenient(text)
    if not t:
        return None
    norm_opts = [norm_lenient(o) for o in options]
    for i, no in enumerate(norm_opts):
        if no == t:
            return i + 1
    for i, no in enumerate(norm_opts):
        if t and (no in t or t in no):
            return i + 1
    scores = [(difflib.SequenceMatcher(None, t, no).ratio(), i + 1) for i, no in enumerate(norm_opts)]
    scores.sort(reverse=True)
    if scores and scores[0][0] >= 0.7:
        return scores[0][1]
    return None


def build_keys(s, tn_by):
    keys = {}
    srcstats = {}
    hdr = official_ranges(s)

    # source type 1: jlptzhen vocab text (問題1-4)
    jtable, byq = load_jlptzhen_keys(s)
    for n, rec in jtable.items():
        tq = tn_by.get(n)
        if not tq:
            continue
        hit, score = best_match(rec["correct"], tq["options"])
        if hit:
            keys[n] = {"ans": str(hit), "source": "jlptzhen-text", "note": rec["target"]}
            continue
        hit = match_text_to_options(rec["correct"], tq["options"])
        if hit:
            keys[n] = {"ans": str(hit), "source": "jlptzhen-sub", "note": rec["target"]}
            continue
        keys[n] = {"ans": str(rec["answer"]), "source": "jlptzhen-posf", "note": rec["target"]}
        srcstats["jlptzhen-posf"] = srcstats.get("jlptzhen-posf", 0) + 1
    srcstats["jlptzhen-text"] = sum(1 for r in keys.values() if r["source"] == "jlptzhen-text")
    srcstats["jlptzhen-sub"] = sum(1 for r in keys.values() if r["source"] == "jlptzhen-sub")

    # source type 2: digit arrays (official positions) per session
    keyfiles = sorted(glob.glob(os.path.join(REFS, f"{s}_key_*.html"))) + \
               sorted(glob.glob(os.path.join(REFS, f"{s}*koolearn*.html"))) + \
               sorted(glob.glob('/tmp/opencode/k_%s_p*.html' % s))
    for f in keyfiles:
        txt = open(f, encoding="utf-8", errors="ignore").read()
        txt2 = re.sub(r"<script.*?</script>", "", txt, flags=re.S)
        txt2 = re.sub(r"<style.*?</style>", "", txt2, flags=re.S)
        txt2 = re.sub(r"<[^>]+>", "\n", txt2)
        if re.search(r"weilan", os.path.basename(f)):
            blocks = None
            wl = parse_weilan_digits(txt2, s)
            dmap = {}
            for (sec, a), digs in wl.items():
                for i, d in enumerate(digs):
                    dmap[a + i] = d
        else:
            blocks = parse_digit_layout(txt2)
            dmap = digit_to_keylist(blocks) if blocks else {}
        for qn, d in dmap.items():
            if qn in tn_by and qn not in keys and qn <= 70:
                keys[qn] = {"ans": str(d), "source": "digits-" + os.path.basename(f), "note": "official-pos"}
                srcstats["digits-" + os.path.basename(f)] = srcstats.get("digits-" + os.path.basename(f), 0) + 1

# source type 3: xdf 前途 per-question answer text (e.g. 2020-12)
    for f in glob.glob(os.path.join(REFS, f"{s}_key_xdfqiantu.html")):
        raw = open(f, encoding="utf-8", errors="ignore").read()
        txt = re.sub(r"<script.*?</script>", "", raw, flags=re.S)
        txt = re.sub(r"<[^>]+>", "\n", txt)
        txt = html_unescape(txt)
        text_ans, digit_only = parse_qiantu(txt)
        sa, sb = hdr.get("問題6", (36, 40))
        for n, rec in text_ans.items():
            if not (1 <= n <= 70) or n not in tn_by:
                continue
            # sorting items: use the key page's own digit (piece order preserved)
            if sa <= n <= sb:
                keys[n] = {"ans": rec["ans"], "source": "qiantu-sort-digit", "note": rec["text"][:26]}
                srcstats["qiantu-sort-digit"] = srcstats.get("qiantu-sort-digit", 0) + 1
                continue
            hit = match_text_to_options(rec["text"], tn_by[n]["options"])
            uniq = count_containment(rec["text"], tn_by[n]["options"])
            if hit and uniq == 1:
                keys[n] = {"ans": str(hit), "source": "qiantu-text", "note": rec["text"][:40]}
                srcstats["qiantu-text"] = srcstats.get("qiantu-text", 0) + 1
            else:
                keys[n] = {"ans": rec["ans"], "source": "qiantu-reserve", "note": rec["text"][:40]}
                srcstats["qiantu-reserve"] = srcstats.get("qiantu-reserve", 0) + 1
        for n, dig in digit_only.items():
            if n in tn_by and n not in keys:
                keys[n] = {"ans": dig, "source": "qiantu-digit", "note": "no answer text"}
                srcstats["qiantu-digit"] = srcstats.get("qiantu-digit", 0) + 1

    # source type 4: inline (N) answers from koolearn full-paper pages (2010-2012)
    for f in keyfiles:
        h = open(f, encoding="utf-8", errors="ignore").read()
        h2 = re.sub(r"<script.*?</script>", "", h, flags=re.S)
        h2 = re.sub(r"<style.*?</style>", "", h2, flags=re.S)
        h2 = re.sub(r"<[^>]+>", "\n", h2)
        h2 = re.sub(r"[ \t\u3000]+", " ", h2)
        lines = [l.strip() for l in h2.split("\n") if l.strip()]
        qn = None
        expect_ans = False
        last_opt_pos = None
        for i, line in enumerate(lines):
            m = re.match(r"^\(([1-4])\)$", line)
            qm = re.match(r"^(\d{1,2})\s+[\u4e00-\u9fff\u3040-\u30ff]", line)
            if qm and int(qm.group(1)) in tn_by and 1 <= int(qm.group(1)) <= 70:
                qn = int(qm.group(1)); expect_ans = True
            if m and expect_ans and qn and 46 <= qn <= 70:
                if qn in tn_by and qn not in keys:
                    keys[qn] = {"ans": m.group(1), "source": "inline-" + os.path.basename(f),
                                "note": "koolearn paper (N) mark"}
                expect_ans = False; qn = None
            if re.search(r"問題[１-９0-9]", line):
                qn = None
    return keys, srcstats


def main():
    args = sys.argv[1:]
    if "--all" in args:
        sels = SESSIONS
    else:
        sels = [a for a in args if not a.startswith("--")] or SESSIONS
    for s in sels:
        tn_by = load_transcript(s)
        if tn_by is None:
            print(f"{s}: no transcript"); continue
        keys, srcstats = build_keys(s, tn_by)
        write_report(s, tn_by, keys, srcstats)
        cov = len(keys) / len(tn_by) * 100
        print(f"{s}: {len(keys)}/{len(tn_by)} ({cov:.0f}%)  src={srcstats}")


if __name__ == "__main__":
    main()