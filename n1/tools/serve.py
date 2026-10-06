#!/usr/bin/env python3
"""
JLPT N1 Question Bank — local transparent dev server.

Serves a full-featured local web frontend reflecting the ENTIRE repo
(uncrypted, binds to 127.0.0.1 only). Intended for authoring/review; the
public GitHub Pages site uses the encrypted `docs/` version instead.

Endpoints:
  /                     -> local/index.html (the app)
  /api/questions        -> all plaintext questions (dedup by id) + meta
  /api/tree             -> repo file tree (excludes .git/pycache/secret)
  /api/file?path=REL    -> text content of a repo file (md/json/txt/...)

Usage:
  python3 tools/serve.py [--port PORT]        # auto-picks free port if taken
"""

import argparse
import io
import json
import mimetypes
import os
import re
import socket
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
SKIP_FILES = {".secret.txt", ".DS_Store"}
TEXT_EXT = {".md", ".json", ".txt", ".srt", ".py", ".html", ".css", ".js", ".gitignore", ".jsonc", ".yaml", ".yml", ".toml", ".csv", ".sh", ".ts", ".tsx", ".ini", ".log"}


def collect_questions() -> dict:
    seen: dict[str, dict] = {}
    for base in (ROOT / "past-exams", ROOT / "question-bank" / "by-type",
                 ROOT / "question-bank" / "by-year", ROOT / "question-bank" / "by-theme"):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(data, dict) and data.get("id"):
                seen[data["id"]] = data
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("id"):
                        seen.setdefault(item["id"], item)
    return seen


def build_questions_payload() -> dict:
    qs = list(collect_questions().values())
    meta = {"total": len(qs), "by_year": {}, "by_section": {}, "by_type": {}, "by_difficulty": {}}
    for q in qs:
        meta["by_year"][str(q.get("year", 0))] = meta["by_year"].get(str(q.get("year", 0)), 0) + 1
        s = q.get("section", "?")
        meta["by_section"][s] = meta["by_section"].get(s, 0) + 1
        t = f"{s}-{q.get('type','?')}"
        meta["by_type"][t] = meta["by_type"].get(t, 0) + 1
        d = q.get("difficulty", "?")
        meta["by_difficulty"][d] = meta["by_difficulty"].get(d, 0) + 1
    return {"questions": qs, "meta": meta}


def tree_node(path: Path, rel: str) -> dict:
    if path.is_dir():
        children = []
        for c in sorted(path.iterdir()):
            if c.name in SKIP_DIRS or c.name in SKIP_FILES:
                continue
            children.append(tree_node(c, str(c.relative_to(ROOT))))
        return {"name": path.name, "rel": rel, "type": "dir", "children": children}
    if path.suffix.lower() in TEXT_EXT or path.name == ".gitignore":
        return {"name": path.name, "rel": rel, "type": "text", "bytes": path.stat().st_size}
    return {"name": path.name, "rel": rel, "type": "bin", "bytes": path.stat().st_size}


def read_safe(rel: str) -> tuple[bool, str]:
    p = (ROOT / rel).resolve()
    if not p.is_relative_to(ROOT):
        return False, "forbidden"
    if not p.is_file() or p.name in SKIP_FILES:
        return False, "not found"
    if p.suffix.lower() not in TEXT_EXT and p.name != ".gitignore":
        return False, "binary"
    return True, p.read_text(encoding="utf-8", errors="replace")


class Handler(BaseHTTPRequestHandler):
    server_version = "jlpt-qb-local/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def _send(self, code, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        path = parsed.path

        if path == "/":
            self._send(200, (ROOT / "local" / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        if path == "/api/questions":
            self._json(build_questions_payload())
            return
        if path == "/api/tree":
            self._json({"root": ROOT.name, "tree": tree_node(ROOT, ROOT.name)})
            return
        if path == "/api/file":
            rel = (query.get("path") or [""])[0]
            ok, content = read_safe(rel)
            if not ok:
                self._json({"ok": False, "error": content}, 404)
                return
            self._json({"ok": True, "path": rel, "content": content})
            return
        # static files (e.g. /docs/vocab-words.html on both local & Pages)
        rel = path.lstrip("/")
        if not rel or rel.startswith(".") or rel.startswith("/"):
            self._json({"error": "not found"}, 404)
            return
        candidate = (ROOT / rel).resolve()
        if candidate.is_relative_to(ROOT) and candidate.is_file() and candidate.name not in SKIP_FILES:
            ctype = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            self._send(200, candidate.read_bytes(), ctype + ("; charset=utf-8" if ctype.startswith("text/") else ""))
            return
        self._json({"error": "not found"}, 404)


def pick_port(preferred: int) -> int:
    for port in (preferred, *range(preferred + 1, preferred + 50)):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("no free port")


def main() -> int:
    parser = argparse.ArgumentParser(description="Local transparent dev server")
    parser.add_argument("--port", type=int, default=8123, help="preferred port (default 8123, auto-bumps if busy)")
    parser.add_argument("--daemon", action="store_true",
                        help="run in background as a real daemon (double-fork, detached; use --stop to kill)")
    parser.add_argument("--stop", action="store_true", help="stop the running daemon by its pidfile")
    args = parser.parse_args()

    pidfile = Path(os.environ.get("JLPT_QB_PIDFILE", "/tmp/jlpt-qb-serve.pid"))
    if args.stop:
        if not pidfile.exists():
            print("no daemon running (pidfile not found)")
            return 1
        pid = int(pidfile.read_text().strip())
        try:
            os.kill(pid, 15)
            print(f"sent SIGTERM to daemon {pid}")
        except ProcessLookupError:
            print(f"daemon {pid} already gone")
        pidfile.unlink(missing_ok=True)
        return 0

    port = pick_port(args.port)
    if not args.daemon:
        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        url = f"http://127.0.0.1:{port}/"
        print(f"Serving {ROOT} at {url}  (Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0

    # daemonize: double-fork so the grandchild is reparented away from the
    # launching shell and survives regardless of how the shell exits.
    pid = os.fork()
    if pid > 0:
        os._exit(0)
    os.setsid()
    pid = os.fork()
    if pid > 0:
        os._exit(0)
    logf = open("/tmp/jlpt-qb-serve.log", "ab", buffering=0)
    os.dup2(logf.fileno(), 0)
    os.dup2(logf.fileno(), 1)
    os.dup2(logf.fileno(), 2)
    pidfile.write_text(str(os.getpid()))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"[daemon {os.getpid()}] Serving {ROOT} at http://127.0.0.1:{port}/", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())