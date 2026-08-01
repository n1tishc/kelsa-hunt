#!/usr/bin/env python3
"""Build the disposable strict-US job ledger Pages artifact."""

import argparse
import json
import pathlib
import shutil
import sys
import urllib.parse


ROOT = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

import job_alert  # noqa: E402


PUBLIC_FIELDS = (
    "uid",
    "title",
    "company",
    "locations",
    "url",
    "source",
    "posted",
    "first_seen",
    "closed_at",
)
DASHBOARD_SOURCE = ROOT / "dashboard"
STATIC_ASSETS = ("index.html", "filters.js", "app.js", "styles.css")


def public_url(value):
    try:
        parsed = urllib.parse.urlsplit(value or "")
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return value


def derived_record(record):
    view = job_alert.strict_us_record(record)
    if view is None:
        return None
    _, score, reason = job_alert.classify(
        view.get("title") or "",
        view.get("degrees"),
        view.get("category"),
    )
    row = {field: view.get(field) for field in PUBLIC_FIELDS}
    row["url"] = public_url(view.get("url"))
    row.update({
        "score": score,
        "reason": reason,
        "status": "closed" if view.get("closed_at") else "open",
    })
    return row


def build(store_path, output_directory):
    canonical = json.loads(store_path.read_text())
    records = [
        row
        for record in canonical.get("jobs", {}).values()
        if (row := derived_record(record)) is not None
    ]
    records.sort(key=lambda row: row["uid"] or "")
    payload = {
        "canonical_updated": canonical.get("updated"),
        "defaults": {"score": "3+", "status": "open"},
        "records": records,
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    for filename in STATIC_ASSETS:
        shutil.copyfile(
            DASHBOARD_SOURCE / filename,
            output_directory / filename,
        )
    (output_directory / "jobs.json").write_text(
        json.dumps(payload, separators=(",", ":"), sort_keys=True)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("store", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    build(args.store, args.output)


if __name__ == "__main__":
    main()
