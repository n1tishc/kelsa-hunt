#!/usr/bin/env python3
"""Measure a pinned Ambicuity snapshot against active Simplify Records."""

import argparse
import hashlib
import json
import pathlib
import re

import job_alert


def normalized_text(value):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).split())


def canonical_location(value):
    value = re.sub(
        r"\b(?:united states(?: of america)?|u\.?s\.?(?:a\.?)?)\b",
        " ",
        value or "",
        flags=re.I,
    )
    for name, code in zip(
        job_alert.US_JURISDICTION_NAMES,
        job_alert.US_JURISDICTION_CODES,
    ):
        value = re.sub(rf"\b{re.escape(name)}\b", code, value, flags=re.I)
    normalized = normalized_text(value)
    aliases = {
        "sf": "san francisco ca",
        "nyc": "new york ny",
        "washington dc": "washington dc",
    }
    normalized = aliases.get(normalized, normalized)
    return frozenset(
        token for token in normalized.split()
        if token not in {"office", "offices"}
    )


def proven_identity(url, row_number):
    identity = job_alert.dedup_key({
        "uid": f"overlap-measurement:{row_number}",
        "url": url,
    })
    return None if identity[0] == "record" else identity


def measure(ambicuity_payload, simplify_payload):
    ambicuity = ambicuity_payload["jobs"]
    simplify = [
        row for row in simplify_payload
        if row.get("active") and row.get("is_visible")
    ]

    simplify_identities = {
        identity
        for index, row in enumerate(simplify)
        if (identity := proven_identity(row.get("url"), index)) is not None
    }
    simplify_by_description = {}
    for row in simplify:
        description = (
            normalized_text(row.get("company_name")),
            normalized_text(row.get("title")),
        )
        simplify_by_description.setdefault(description, set()).update(
            canonical_location(location)
            for location in row.get("locations") or []
        )

    proven_matches = 0
    measurement_only_matches = 0
    for index, row in enumerate(ambicuity):
        identity = proven_identity(row.get("url"), len(simplify) + index)
        if identity is not None and identity in simplify_identities:
            proven_matches += 1
            continue
        description = (
            normalized_text(row.get("company")),
            normalized_text(row.get("title")),
        )
        location = canonical_location(row.get("location"))
        if location and location in simplify_by_description.get(description, set()):
            measurement_only_matches += 1

    matched = proven_matches + measurement_only_matches
    return {
        "ambicuity_rows": len(ambicuity),
        "simplify_active_visible_rows": len(simplify),
        "proven_opening_identity_matches": proven_matches,
        "measurement_only_description_matches": measurement_only_matches,
        "total_measured_overlap": matched,
        "apparently_unique_ambicuity_rows": len(ambicuity) - matched,
        "measured_overlap_percent": round(100 * matched / len(ambicuity), 1),
    }


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ambicuity", type=pathlib.Path)
    parser.add_argument("simplify", type=pathlib.Path)
    parser.add_argument("--ambicuity-commit", required=True)
    parser.add_argument("--simplify-commit", required=True)
    args = parser.parse_args()

    ambicuity = json.loads(args.ambicuity.read_text())
    simplify = json.loads(args.simplify.read_text())
    result = measure(ambicuity, simplify)
    result.update({
        "ambicuity_commit": args.ambicuity_commit,
        "ambicuity_sha256": sha256(args.ambicuity),
        "ambicuity_generated_at": ambicuity.get("meta", {}).get("generated_at"),
        "simplify_commit": args.simplify_commit,
        "simplify_sha256": sha256(args.simplify),
    })
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
