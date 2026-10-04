#!/usr/bin/env python3
"""jlpt-question-bank (N2-N5) — encrypt to password-protected Pages site.

Plaintext question JSONs live only locally (past-exams/, gitignored). This
script bundles them, encrypts with AES-256-GCM (PBKDF2-HMAC-SHA256, 310000
iterations) and writes `docs/data.json`; the viewer `docs/index.html` decrypts
in-browser with WebCrypto. Push only `docs/` + tooling.

    python3 tools/encrypt.py                 # reuse or generate password
    python3 tools/encrypt.py --show          # print current password
"""
import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "docs"
ITERATIONS = 310000
AAD = b"jlpt-n2n5-qb"


def collect_questions():
    seen = {}
    for path in sorted((ROOT / "past-exams").rglob("*.json")):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"  ! skip {path}: {e}")
            continue
        if isinstance(d, dict) and d.get("id"):
            seen[d["id"]] = d
    print(f"  collected {len(seen)} questions")
    return list(seen.values())


def encrypt_bundle(questions, password):
    payload = json.dumps({"questions": questions}, ensure_ascii=False).encode("utf-8")
    salt, iv = os.urandom(16), os.urandom(12)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS, 32)
    ct = AESGCM(key).encrypt(iv, payload, AAD)
    return {"v": 1, "kdf": "PBKDF2-SHA256", "iter": ITERATIONS,
            "salt": base64.b64encode(salt).decode(),
            "iv": base64.b64encode(iv).decode(),
            "ct": base64.b64encode(ct).decode()}


def build_meta(questions):
    by_level, by_type, years = {}, {}, set()
    for q in questions:
        by_level[q.get("level", "?")] = by_level.get(q.get("level", "?"), 0) + 1
        by_type[q.get("type", "?")] = by_type.get(q.get("type", "?"), 0) + 1
        if q.get("year"):
            years.add(int(q["year"]))
    span = f"{min(years)}–{max(years)}" if years else "-"
    answered = sum(1 for q in questions if q.get("answer"))
    return {"total": len(questions), "answered": answered, "span": span,
            "by_level": by_level, "by_type": by_type}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--password")
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()
    SITE.mkdir(exist_ok=True)
    if args.show:
        f = SITE / ".secret.txt"
        print(f.read_text(encoding="utf-8").strip() if f.exists() else "no password stored")
        return 0
    if args.password:
        password = args.password
    elif (SITE / ".secret.txt").exists():
        password = (SITE / ".secret.txt").read_text(encoding="utf-8").strip()
        print("  reusing stored password")
    else:
        alphabet = "abcdefghijkmnopqrstuvwxyz23456789"
        password = "".join(secrets.choice(alphabet) for _ in range(24))
        (SITE / ".secret.txt").write_text(password + "\n", encoding="utf-8")
        print(f"  generated password: {password}")
    questions = collect_questions()
    (SITE / "data.json").write_text(json.dumps(encrypt_bundle(questions, password), ensure_ascii=False), encoding="utf-8")
    (SITE / "index-meta.json").write_text(json.dumps(build_meta(questions), ensure_ascii=False), encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    print(f"  wrote docs/data.json ({len(questions)} questions, AES-256-GCM)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
