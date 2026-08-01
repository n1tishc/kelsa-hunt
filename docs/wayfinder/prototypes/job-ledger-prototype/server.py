#!/usr/bin/env python3
"""THROWAWAY PROTOTYPE — serve three job-ledger UI variants with real store data."""

import json
import pathlib
import sys
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PROTOTYPE_DIR = pathlib.Path(__file__).resolve().parent
REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

import job_alert  # noqa: E402


def build_derived_view():
    store = job_alert.Store(REPO_ROOT / "jobs.json")
    rows = []
    now = int(time.time())
    for rec in store.us_records():
        keep, score, reason = job_alert.classify(
            rec.get("title", ""),
            rec.get("degrees"),
            rec.get("category"),
        )
        ref = rec.get("posted") or rec.get("first_seen") or 0
        rows.append(
            {
                "uid": rec.get("uid", ""),
                "title": rec.get("title", ""),
                "company": rec.get("company", ""),
                "location": " · ".join(rec.get("locations") or []),
                "url": rec.get("url", ""),
                "source": rec.get("source", "Unknown"),
                "score": score if keep else 0,
                "reason": reason,
                "state": "closed" if rec.get("closed_at") else "open",
                "posted": rec.get("posted") or 0,
                "first_seen": rec.get("first_seen") or 0,
                "closed_at": rec.get("closed_at") or 0,
                "notified": bool(rec.get("notified_at")),
                "age_days": max(0, int((now - ref) / 86400)) if ref else None,
            }
        )
    rows.sort(key=lambda row: (row["first_seen"], row["posted"]), reverse=True)
    return {
        "generated_at": now,
        "count": len(rows),
        "rows": rows,
    }


DERIVED_VIEW = json.dumps(build_derived_view()).encode()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROTOTYPE_DIR), **kwargs)

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/prototype-data.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(DERIVED_VIEW)))
            self.end_headers()
            self.wfile.write(DERIVED_VIEW)
            return
        super().do_GET()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    port = 8765
    print(f"Job ledger prototype: http://127.0.0.1:{port}/?variant=A")
    print("Variants: A spreadsheet · B archive inspector · C timeline")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
