"""Extract transcript-position answers from a trynihongo past-paper page.

Method: for each real question box on the page, POST every answer option to
check_single_question_ajax until the server returns is_correct=true. That
position is the transcript option index (options are shuffled vs the official
paper, so this is the position-safe answer for the bank).

Numbering: passage boxes reuse question ids, so the k-th option-bearing box in
document order == question k (validated on 2017-12/2018-07/2019-12).

Usage: python3 tools/trynihongo_api.py SESSION URL [--start N]
Results are checkpointed into refs/<SESSION>_answer_trynihongo.json.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__)) + "/.."
REFS = os.path.join(ROOT, "refs")
UA = "Mozilla/5.0"


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def parse_boxes(html):
    real = []
    for mobj in re.finditer(r'id="question-(\d+)"', html):
        seg = html[mobj.end():mobj.end() + 20000]
        j = seg.find('<div class="q-icons-bottom"')
        body = seg[:j] if j > 0 else seg
        if "custom-option" not in body:
            continue
        qid = re.search(r'data-question-id="(\d+)"', body)
        opts = []
        for lbl in re.finditer(r'<label class="custom-option[^"]*"(.*?)</label>', body, re.S):
            inner = lbl.group(1)
            aid = re.search(r'data-answer-id="(\d+)"', inner)
            m = re.search(r'answer-text[^>]*>(.*?)</div>', inner, re.S)
            txt = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
            opts.append((int(aid.group(1)), txt))
        if opts:
            real.append({"box": int(mobj.group(1)), "qid": int(qid.group(1)), "opts": opts})
    return real


def bind(url, ck, bf, tmp):
    subprocess.run(["curl", "-s", "-c", ck, "-A", UA, "-b", ck, "-o", bf, url],
                   capture_output=True, timeout=40, cwd=tmp)
    b = open(bf, encoding="utf-8", errors="ignore").read()
    m = re.search(r"token:\s*'([^']+)'", b)
    return m.group(1) if m else None


def check(ck, tok, qid, aid, tmp):
    r = subprocess.run(
        ["curl", "-s", "-b", ck, "-c", ck, "-A", UA,
         "-H", "X-Requested-With: XMLHttpRequest",
         "-H", "Content-Type: application/x-www-form-urlencoded; charset=UTF-8",
         "--data", f"_token={tok}&question_id={qid}&answer_id={aid}&selected_fraction=1",
         "https://trynihongo.com/quiz/check_single_question_ajax"],
        capture_output=True, timeout=25, cwd=tmp)
    try:
        return json.loads(r.stdout.decode("utf-8", "ignore"))
    except Exception:
        return {"raw": r.stdout.decode("utf-8", "ignore")[:60]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session")
    ap.add_argument("url")
    ap.add_argument("--start", type=int, default=1)
    args = ap.parse_args()
    out_path = os.path.join(REFS, f"{args.session}_answer_trynihongo.json")
    out = {}
    if os.path.exists(out_path):
        out = json.load(open(out_path))
    page = os.path.join("/tmp/opencode", f"p{args.session}.html")
    if not os.path.exists(page):
        subprocess.run(["curl", "-s", "-A", UA, "-o", page, args.url], timeout=60)
    html = open(page, encoding="utf-8").read()
    boxes = parse_boxes(html)
    print("real question boxes:", len(boxes))
    tmp = "/tmp/opencode"
    for i, bx in enumerate(boxes, start=1):
        if i < args.start:
            continue
        if out.get(str(i), {}).get("answer_pos") is not None:
            continue
        ck = os.path.join(tmp, f"tk_{args.session}_{i}.txt")
        bf = os.path.join(tmp, f"tb_{args.session}_{i}.html")
        tok = bind(args.url, ck, bf, tmp)
        got = None
        for round_ in range(8):
            for idx, (aid, txt) in enumerate(bx["opts"], start=1):
                r = check(ck, tok, bx["qid"], aid, tmp)
                if r.get("data", {}).get("is_correct") is True:
                    got = (idx, aid, txt)
                    break
                if r.get("data", {}).get("is_correct") is False:
                    time.sleep(1.0)
                else:
                    time.sleep(15)
                    tok = bind(args.url, ck, bf, tmp)
                    break
            if got:
                break
        out[str(i)] = {
            "box": bx["box"], "qid": bx["qid"],
            "answer_pos": got[0] if got else None,
            "answer_text": got[2] if got else None,
            "nopts": len(bx["opts"]), "src": "tryni-api",
        }
        print(f"Q{i}: {'OK ' + str(got[0]) if got else 'MISS'}", flush=True)
        json.dump(out, open(out_path, "w"), ensure_ascii=False, indent=1)
        time.sleep(3)
    miss = [int(k) for k in out if out[k]["answer_pos"] is None]
    print("done — unresolved:", miss)


if __name__ == "__main__":
    main()