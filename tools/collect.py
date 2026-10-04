#!/usr/bin/env python3
"""Discover and archive JLPT N2-N5 past-paper pages from jlptzhen + jlpt247.

Builds a session inventory from both sites' sitemaps, then (optionally)
downloads raw HTML into refs/ for offline processing. Source attribution is
kept per page: level, session (YYYY-MM), site.

Usage:
    python3 tools/collect.py --inventory          # list sessions, no download
    python3 tools/collect.py --download           # fetch missing pages (rate-limited)
    python3 tools/collect.py --download --level n2
"""
import argparse
import json
import re
import ssl
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = ROOT / "refs"
INVENTORY = ROOT / "sessions.json"

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36"
CTX = ssl.create_default_context()

SITEMAPS = {
    "jlptzhen": "https://www.jlptzhen.com/wp-sitemap-posts-post-1.xml",
    "jlpt247": "https://jlpt247.com/wp-sitemap-posts-post-1.xml",
}


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read().decode("utf-8", "replace")


def locs(xml):
    return re.findall(r"<loc>([^<]+)</loc>", xml)


# ---------------------------------------------------------------- jlptzhen
def parse_jlptzhen(url):
    d = urllib.parse.unquote(url)
    m = re.search(r"[nN]([2-5])(?:真题|真題|).{0,4}?在线做.{0,4}?(\d{4})年(\d{1,2})月", d)
    if not m:
        m = re.search(r"n([2-5]).{0,10}?(\d{4})年(\d{1,2})月", d)
    if not m:
        return None
    level = f"n{m.group(1)}"
    session = f"{m.group(2)}-{int(m.group(3)):02d}"
    return level, session


# ---------------------------------------------------------------- jlpt247
JLPT247_PATTERNS = [
    re.compile(r"^(?:jlpt-)?n([2-5])-jlpt-(\d{1,2})-(\d{4})(?:-\d+)?/?$"),
    re.compile(r"^(?:jlpt-)?n([2-5])-(\d{1,2})-(\d{4})(?:-\d+)?/?$"),
    re.compile(r"^n([2-5])(\d{1,2})(\d{4})(?:-\d+)?/?$"),
    re.compile(r"^n([2-5])-(\d{4})年(\d{1,2})月(?:-\d+)?/?$"),
    re.compile(r"^jlpt-n([2-5])-(\d{1,2})-(\d{4})(?:-\d+)?/?$"),
]


def parse_jlpt247(url):
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    for i, pat in enumerate(JLPT247_PATTERNS):
        m = pat.match(slug)
        if m:
            level = f"n{m.group(1)}"
            if i in (0, 1, 4):
                month, year = int(m.group(2)), m.group(3)
            elif i == 2:
                month, year = int(m.group(2)), m.group(3)
            else:  # n2-2016年07月
                year, month = m.group(2), int(m.group(3))
            return level, f"{year}-{month:02d}"
    return None


def build_inventory():
    inv = {}
    for site, sm in SITEMAPS.items():
        try:
            xml = fetch(sm)
        except Exception as e:
            print(f"[!] {site} sitemap failed: {e}")
            continue
        urls = locs(xml)
        for u in urls:
            parsed = parse_jlptzhen(u) if site == "jlptzhen" else parse_jlpt247(u)
            if not parsed:
                continue
            level, session = parsed
            key = f"{level}/{session}"
            slot = inv.setdefault(key, {"level": level, "session": session, "sources": {}})
            # prefer canonical (non-精品/随机, shorter slug)
            old = slot["sources"].get(site)
            if old is None or len(u) < len(old):
                slot["sources"][site] = u
    return inv


def fname(level, session, site):
    return f"{session}_{site}_{level}.html"


def download(inv, only_level=None):
    REFS.mkdir(exist_ok=True)
    tasks = []
    for key, rec in sorted(inv.items()):
        if only_level and rec["level"] != only_level:
            continue
        for site, url in rec["sources"].items():
            out = REFS / fname(rec["level"], rec["session"], site)
            if out.exists() and out.stat().st_size > 5000:
                continue
            tasks.append((rec, site, url, out))
    print(f"download tasks: {len(tasks)}")
    for i, (rec, site, url, out) in enumerate(tasks, 1):
        try:
            data = fetch(url)
            out.write_text(data, encoding="utf-8")
            print(f"[{i}/{len(tasks)}] {out.name} {len(data)//1024}KB")
        except Exception as e:
            print(f"[{i}/{len(tasks)}] FAIL {out.name}: {e}")
        time.sleep(1.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", action="store_true")
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--level")
    args = ap.parse_args()

    inv = build_inventory()
    INVENTORY.write_text(json.dumps(inv, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"sessions: {len(inv)}")
    by_level = {}
    both = 0
    for key, rec in sorted(inv.items()):
        by_level.setdefault(rec["level"], []).append(rec["session"])
        if len(rec["sources"]) >= 2:
            both += 1
    for lv in sorted(by_level):
        print(f"  {lv}: {len(by_level[lv])} sessions — {', '.join(sorted(by_level[lv]))}")
    print(f"  sessions with 2 sources: {both}")
    if args.download:
        download(inv, args.level)


if __name__ == "__main__":
    main()
