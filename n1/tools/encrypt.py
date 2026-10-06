#!/usr/bin/env python3
"""
JLPT N1 Question Bank — encrypt to password-protected Pages site.

Workflow (every time question content changes):
    python3 tools/encrypt.py --password 'YOUR_PASSWORD'

Reads ALL plaintext question JSONs (canonical source of truth, kept local only),
builds a deduplicated bundle, encrypts it with AES-256-GCM (key derived via
PBKDF2-HMAC-SHA256, 310000 iterations), and writes the ciphertext to
`docs/data.json`. The Pages viewer (`docs/index.html`) decrypts in-browser with
WebCrypto using the same parameters.

Only `docs/` is meant to be pushed to GitHub. Plaintext JSONs are gitignored.
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
SITE_DIR = ROOT / "docs"
ITERATIONS = 310000  # OWASP-recommended for PBKDF2-SHA256 (must match docs/index.html)


def collect_questions() -> list[dict]:
    """Gather every plaintext question JSON, deduplicated by `id`."""
    seen: dict[str, dict] = {}
    sources = [
        ROOT / "past-exams",
        ROOT / "question-bank" / "by-type",
        ROOT / "question-bank" / "by-year",
        ROOT / "question-bank" / "by-theme",
    ]
    for base in sources:
        for path in sorted(base.rglob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                print(f"  ! skip {path.relative_to(ROOT)}: {e}")
                continue
            qid = data.get("id")
            if not qid:
                # tolerate a bare list of question dicts
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("id"):
                            seen.setdefault(item["id"], item)
                    continue
                print(f"  ! no id in {path.relative_to(ROOT)}, skipping")
                continue
            seen[qid] = data

    print(f"  collected {len(seen)} unique question(s)")
    if seen:
        years = sorted({int(q.get("year", 0)) for q in seen.values() if q.get("year")})
        sections = sorted({q.get("section", "?") for q in seen.values()})
        print(f"  years: {years}")
        print(f"  sections: {sections}")
    return list(seen.values())


def encrypt_bundle(questions: list[dict], password: str) -> dict[str, str]:
    """Encrypt the question bundle. Returns {v, kdf, iter, salt, iv, ct}."""
    payload = json.dumps({"questions": questions}, ensure_ascii=False).encode("utf-8")
    salt = os.urandom(16)
    iv = os.urandom(12)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS, 32)
    ct = AESGCM(key).encrypt(iv, payload, b"jlpt-n1-qb")
    return {
        "v": 1,
        "kdf": "PBKDF2-SHA256",
        "iter": ITERATIONS,
        "salt": base64.b64encode(salt).decode(),
        "iv": base64.b64encode(iv).decode(),
        "ct": base64.b64encode(ct).decode(),
    }


def build_meta(questions: list[dict]) -> dict:
    """Non-sensitive index metadata shown on the landing page before unlock."""
    by_year: dict[str, int] = {}
    by_section: dict[str, int] = {}
    for q in questions:
        by_year[str(q.get("year", 0))] = by_year.get(str(q.get("year", 0)), 0) + 1
        s = q.get("section", "?")
        by_section[s] = by_section.get(s, 0) + 1
    years = sorted(by_year)
    return {
        "total": len(questions),
        "updated": os.path.getmtime(__file__),
        "span": f"{years[0]}–{years[-1]}" if years else "-",
        "by_year": by_year,
        "by_section": by_section,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Encrypt question bank for Pages")
    parser.add_argument("--password", help="Site password (if omitted, a secure random one is generated)")
    parser.add_argument("--show", action="store_true", help="Print the current password for this site (from docs/.secret.txt)")
    args = parser.parse_args()

    SITE_DIR.mkdir(exist_ok=True)

    if args.show:
        secret_file = SITE_DIR / ".secret.txt"
        if secret_file.exists():
            print(secret_file.read_text(encoding="utf-8").strip())
            return 0
        print("No password stored yet. Run encrypt.py first.")
        return 1

    if args.password:
        password = args.password
        print("  using provided password")
    elif (SITE_DIR / ".secret.txt").exists():
        password = (SITE_DIR / ".secret.txt").read_text(encoding="utf-8").strip()
        print(f"  reusing stored password: {password}")
    else:
        alphabet = "abcdefghijkmnopqrstuvwxyz23456789"
        password = "".join(secrets.choice(alphabet) for _ in range(24))
        (SITE_DIR / ".secret.txt").write_text(password + "\n", encoding="utf-8")
        print(f"  generated new password: {password}")

    questions = collect_questions()
    (SITE_DIR / "data.json").write_text(
        json.dumps(encrypt_bundle(questions, password), ensure_ascii=False),
        encoding="utf-8",
    )
    (SITE_DIR / "index-meta.json").write_text(
        json.dumps(build_meta(questions), ensure_ascii=False),
        encoding="utf-8",
    )
    (SITE_DIR / ".nojekyll").write_text("", encoding="utf-8")
    print(f"  wrote docs/data.json ({len(questions)} questions, AES-256-GCM)")
    print("  DONE. Push docs/ to GitHub Pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())