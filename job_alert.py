#!/usr/bin/env python3
"""
Bay Area new-grad / entry-level SWE + MLE job alerter.

Stores every job record it fetches (jobs.json) and keeps a separate ledger of
what it has already pinged about. Filtering happens at query time, so you can
change your criteria later and re-run over history without losing anything.

Commands:
    scan      fetch sources, store, notify on new matches   (default)
    query     re-filter stored data locally, no fetch
    stats     summary of the store
    applied   mark a role as applied to
    export    dump the US-only Derived View to SQLite for ad-hoc SQL
"""

import argparse
import json
import os
import pathlib
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).parent
STORE_FILE = HERE / "jobs.json"
ANNOTATIONS_FILE = HERE / "annotations.json"
LEGACY_STATE = HERE / "seen.json"
SOURCES_FILE = HERE / "sources.json"

SIMPLIFY_URL = (
    "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions"
    "/dev/.github/scripts/listings.json"
)

UA = {"User-Agent": "Mozilla/5.0 (compatible; job-alert/2.0)"}
STORE_VERSION = 2

# Don't ping about postings older than this. Storage keeps them regardless.
MAX_AGE_DAYS = 21


def now() -> int:
    return int(time.time())


# ==========================================================================
# Location
# ==========================================================================

BAY_TERMS = [
    "san francisco", "sf bay", "bay area", "south san francisco",
    "oakland", "berkeley", "emeryville", "alameda",
    "palo alto", "east palo alto", "menlo park", "mountain view",
    "sunnyvale", "santa clara", "san jose", "cupertino", "milpitas",
    "redwood city", "san mateo", "foster city", "burlingame", "belmont",
    "fremont", "hayward", "union city", "newark, ca", "san carlos",
    "campbell", "los gatos", "los altos", "saratoga", "brisbane",
    "daly city", "south bay", "peninsula", "silicon valley",
    "walnut creek", "pleasanton", "dublin, ca", "san ramon", "concord, ca",
]

REMOTE_OK = re.compile(r"\bremote\b", re.I)
US_COUNTRY = re.compile(
    r"(?<![A-Za-z])(?:(?i:united\s+states(?:\s+of\s+america)?)|"
    r"U\.?S\.?(?:A\.?)?)(?![A-Za-z])",
)
US_JURISDICTION_NAMES = (
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
    "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
    "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
    "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
    "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York",
    "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
    "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
    "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
    "West Virginia", "Wisconsin", "Wyoming", "District of Columbia",
    "American Samoa", "Guam", "Northern Mariana Islands", "Puerto Rico",
    "U.S. Virgin Islands", "United States Minor Outlying Islands",
)
US_JURISDICTION_NAME = re.compile(
    r"\b(?:" + "|".join(map(re.escape, US_JURISDICTION_NAMES)) + r")\b",
    re.I,
)
US_JURISDICTION_CODES = (
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "AS", "GU", "MP", "PR", "VI", "UM",
)
US_JURISDICTION_CODE = re.compile(
    r"(?:^|,\s*|[-–—]\s*)(?:" + "|".join(US_JURISDICTION_CODES) + r")(?:\b|$)"
)
MULTI_LOCATION_SEPARATOR = re.compile(
    r"\s*[|•;]\s*|\s+/\s+|(?<!,)\s+or\s+",
    re.I,
)
US_LOCALITY_ALIASES = ({term.lower() for term in BAY_TERMS} - {
    "belmont", "brisbane",
}) | {
    "sf", "nyc", "la", "san francisco", "san francisco hq",
    "south san francisco", "sf bay", "bay area", "silicon valley",
    "atlanta", "new york", "new york city", "new york city office",
}
KNOWN_NON_US_LOCALITIES = {
    "bengaluru", "bangalore", "brisbane", "london", "mexico city",
    "singapore", "tbilisi", "toronto", "vancouver",
}
NON_US_MARKER = re.compile(
    r"\b(?:APAC|EMEA|LATAM|global|Australia|Brazil|Canada|China|England|"
    r"Europe|France|Germany|India|Ireland|Japan|London|(?<!New )Mexico|"
    r"Singapore|Spain|"
    r"United Kingdom|UK)\b",
    re.I,
)
US_JURISDICTION_CODE_TOKEN = re.compile(
    r"^(?:" + "|".join(US_JURISDICTION_CODES) + r")(?:\b.*)?$"
)


def _has_explicit_us_evidence(location):
    normalized = " ".join(location.lower().split())
    country_match = US_COUNTRY.search(location)
    first_component = normalized.split(",", 1)[0]
    locality_probe = re.sub(
        r"^remote(?:\s+in)?(?:\s*[-–—:])?\s*",
        "",
        first_component,
    )
    if locality_probe in KNOWN_NON_US_LOCALITIES and not country_match:
        return False
    jurisdiction_name_match = False
    for match in US_JURISDICTION_NAME.finditer(location):
        name = match.group(0).lower()
        suffix = location[match.end():].strip(" ,-/–—")
        if name == "georgia" and not country_match:
            continue
        if country_match or not suffix:
            jurisdiction_name_match = True
            break
    return bool(
        country_match
        or jurisdiction_name_match
        or US_JURISDICTION_CODE.search(location.replace("D.C.", "DC"))
        or normalized in US_LOCALITY_ALIASES
    )


def _mixed_us_fragments(location):
    if REMOTE_OK.search(location) and "/" in location and US_COUNTRY.search(location):
        return ["Remote (US)"]
    components = [part.strip() for part in location.split(",") if part.strip()]
    fragments = []
    strong_evidence = False
    weak_fragment_count = 0
    index = 0
    while index < len(components):
        component = components[index]
        if (
            index + 1 < len(components)
            and US_JURISDICTION_CODE_TOKEN.match(
                components[index + 1].replace("D.C.", "DC")
            )
        ):
            candidate = f"{component}, {components[index + 1]}"
            if (
                not NON_US_MARKER.search(component)
                and _has_explicit_us_evidence(candidate)
            ):
                fragments.append(candidate)
                strong_evidence = True
            index += 2
            continue
        if (
            index + 1 == len(components) - 1
            and " ".join(component.lower().split()) in US_LOCALITY_ALIASES
            and US_JURISDICTION_NAME.fullmatch(components[index + 1])
        ):
            fragments.append(f"{component}, {components[index + 1]}")
            strong_evidence = True
            index += 2
            continue
        if (
            index == len(components) - 1
            and component.lower() != "georgia"
            and US_JURISDICTION_NAME.fullmatch(component)
        ):
            previous = components[index - 1] if index else ""
            if (
                previous
                and not NON_US_MARKER.search(previous)
                and not US_COUNTRY.search(previous)
                and not US_JURISDICTION_CODE_TOKEN.fullmatch(
                    previous.replace("D.C.", "DC")
                )
            ):
                fragments.append(f"{previous}, {component}")
            else:
                fragments.append(component)
            strong_evidence = True
            index += 1
            continue
        if (
            not NON_US_MARKER.search(component)
            and (
                US_COUNTRY.search(component)
                or US_JURISDICTION_CODE.search(component)
                or " ".join(component.lower().split()) in US_LOCALITY_ALIASES
            )
        ):
            fragments.append(component)
            if (
                US_COUNTRY.search(component)
                or US_JURISDICTION_CODE.search(component)
            ):
                strong_evidence = True
            else:
                weak_fragment_count += 1
        index += 1
    if not fragments:
        country_fragments = [
            match.group(0) for match in US_COUNTRY.finditer(location)
        ]
        fragments.extend(country_fragments)
        strong_evidence = bool(country_fragments)
    if strong_evidence or (
        weak_fragment_count >= 2 and not NON_US_MARKER.search(location)
    ):
        return fragments
    return []


def _location_parts(locations):
    parts = []
    for location in locations:
        parts.extend(
            part.strip() for part in MULTI_LOCATION_SEPARATOR.split(location)
            if part.strip()
        )
    return parts


def us_locations(locations):
    """Return source locations with explicit evidence of US eligibility."""
    filtered = []
    for part in _location_parts(locations):
        if NON_US_MARKER.search(part) or not _has_explicit_us_evidence(part):
            filtered.extend(_mixed_us_fragments(part))
        else:
            filtered.append(part)
    return list(dict.fromkeys(filtered))


def is_bay_area(locations, allow_remote=True):
    for loc in us_locations(locations):
        low = loc.lower()
        if low == "sf" or any(t in low for t in BAY_TERMS):
            return True
    if allow_remote and any(
        REMOTE_OK.search(part) and us_locations([part])
        for part in _location_parts(locations)
    ):
        return True
    return False


def _us_record(rec):
    if rec.get("migrated"):
        return None
    locations = us_locations(rec.get("locations") or [])
    if not locations:
        return None
    row = dict(rec)
    row["locations"] = locations
    return row


# ==========================================================================
# Level classification
# ==========================================================================

HARD_NEG = re.compile(
    r"\b(senior|sr\.?|staff|principal|distinguished|lead|manager|director|"
    r"head of|vp|vice president|architect|fellow|II|III|IV|"
    r"level\s*[4-9]|l[4-9]\b|e[4-9]\b)\b",
    re.I,
)
STRONG_POS = re.compile(
    r"(new\s*grad|new\s*graduate|university\s*grad|recent\s*grad|campus|"
    r"early\s*career|entry[\s-]*level|rotational|apprentice|"
    r"\b(20\d\d)\s*(start|grad)|\bgrad\b)",
    re.I,
)
WEAK_POS = re.compile(
    r"\b(junior|jr\.?|associate|graduate|"
    r"engineer\s*(i|1)\b|sde\s*(i|1)\b|swe\s*(i|1)\b|"
    r"l3\b|e3\b|ic1\b|t1\b|level\s*1\b)\b",
    re.I,
)
# "Engineer 2", "Developer 3" — Arabic-numeral levels, which the Roman-numeral
# rule above misses entirely.
MID_LEVEL = re.compile(
    r"(engineer|developer|scientist|analyst|programmer|swe|sde)\s*[2-9]\b"
    r"|level\s*[2-9]\b",
    re.I,
)
PHD_SIGNAL = re.compile(r"research scientist|research engineer|applied scientist", re.I)
ROLE_MATCH = re.compile(
    r"software|swe\b|sde\b|engineer|developer|machine learning|\bml\b|"
    r"mle\b|ai\b|data scientist|infrastructure|backend|frontend|full[\s-]?stack",
    re.I,
)
# "Member of Technical Staff" is the entry-level IC title at most SF AI labs.
MTS = re.compile(r"member\s+of\s+(the\s+)?technical\s+staff", re.I)


def classify(title, degrees=None, category=None):
    """Return (keep: bool, score: int, reason: str)."""
    degrees = degrees or []
    t = (title or "").strip()

    is_mts = bool(MTS.search(t))
    probe = MTS.sub("MTS", t) if is_mts else t

    if HARD_NEG.search(probe):
        return False, 0, "senior-level title"
    if MID_LEVEL.search(probe):
        return False, 0, "mid-level (numeric)"
    if not ROLE_MATCH.search(probe) and not is_mts:
        return False, 0, "not an eng/ML role"
    if degrees and set(degrees) == {"PhD"}:
        return False, 0, "PhD-only requirement"
    if PHD_SIGNAL.search(probe) and "PhD" in degrees and "Bachelor's" not in degrees:
        return False, 0, "PhD research role"

    score, reasons = 0, []
    if STRONG_POS.search(probe):
        score += 10
        reasons.append("explicit new-grad")
    if WEAK_POS.search(probe):
        score += 5
        reasons.append("junior-level marker")
    if is_mts:
        score += 5
        reasons.append("MTS (lab entry title)")
    if score == 0 and "Bachelor's" in degrees:
        score += 3
        reasons.append("bachelors-eligible")

    if score == 0:
        return False, 0, "no entry-level signal"
    return True, score, ", ".join(reasons)


# ==========================================================================
# Store
# ==========================================================================

class Store:
    """
    jobs.json holds every record we've ever fetched, keyed by uid.

    The critical distinction: `notified_at` gates Discord, NOT presence in the
    store. A job stored but never notified is still eligible to fire later if
    you loosen your filters.
    """

    def __init__(self, path=STORE_FILE):
        self.path = path
        self.jobs = {}
        self.load()

    def load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text())
            self.jobs = data.get("jobs", {})
        # Migrate a v1 seen.json if present: those uids were already pinged.
        elif LEGACY_STATE.exists():
            legacy = json.loads(LEGACY_STATE.read_text()).get("seen", [])
            ts = now()
            for uid in legacy:
                self.jobs[uid] = {"uid": uid, "notified_at": ts, "migrated": True}
            print(f"migrated {len(legacy)} ids from seen.json")

        # applied_at/hidden are personal annotations, not fetched data — kept
        # out of the tracked (public) store and merged back in from a
        # gitignored local file. Records saved before this split still carry
        # them embedded in jobs.json; save() below moves them out from here on.
        if ANNOTATIONS_FILE.exists():
            annotations = json.loads(ANNOTATIONS_FILE.read_text())
            for uid, ann in annotations.items():
                if uid in self.jobs:
                    self.jobs[uid].update(ann)

    def save(self):
        annotations = {}
        jobs = {}
        for uid, rec in self.jobs.items():
            rec = dict(rec)
            ann = {k: rec.pop(k) for k in ("applied_at", "hidden") if k in rec}
            if ann:
                annotations[uid] = ann
            jobs[uid] = rec

        payload = {
            "version": STORE_VERSION,
            "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "count": len(jobs),
            # Sort keys so git diffs stay small and readable.
            "jobs": dict(sorted(jobs.items())),
        }
        self.path.write_text(json.dumps(payload, indent=0, sort_keys=True))
        ANNOTATIONS_FILE.write_text(
            json.dumps(dict(sorted(annotations.items())), indent=0, sort_keys=True))

    def upsert(self, rec):
        """Merge a freshly fetched record, preserving our own annotations."""
        uid = rec["uid"]
        existing = self.jobs.get(uid, {})
        ts = now()
        merged = dict(existing)
        merged.update(rec)
        merged["first_seen"] = existing.get("first_seen", ts)
        merged["last_seen"] = ts
        merged["closed_at"] = None          # present in feed => still open
        # Never clobber our own annotations.
        for k in ("notified_at", "applied_at", "hidden"):
            if k in existing:
                merged[k] = existing[k]
        self.jobs[uid] = merged
        return merged

    def mark_closed(self, source_prefixes, live_uids):
        """
        Anything we previously saw from a *successfully fetched* source that is
        no longer in the feed has closed. Only called for sources that actually
        returned data — otherwise a 403 would mark the whole store closed.
        """
        n = 0
        for uid, rec in self.jobs.items():
            if rec.get("closed_at") or rec.get("migrated"):
                continue
            if not any(uid.startswith(p) for p in source_prefixes):
                continue
            if uid not in live_uids:
                rec["closed_at"] = now()
                n += 1
        return n

    def us_records(self):
        """Return US-eligible Record copies for user-visible Derived Views."""
        return [
            row for rec in self.jobs.values()
            if (row := _us_record(rec)) is not None
        ]

    def candidates(self, min_score=5, allow_remote=True, include_closed=False,
                   unnotified_only=True, max_age_days=MAX_AGE_DAYS):
        """Filter the store. This is the query-time filtering step."""
        out = []
        cutoff = now() - max_age_days * 86400
        for source_rec in self.jobs.values():
            rec = _us_record(source_rec)
            if rec is None:
                continue
            if rec.get("migrated") or rec.get("hidden"):
                continue
            if not rec.get("title"):
                continue
            if rec.get("closed_at") and not include_closed:
                continue
            if unnotified_only and rec.get("notified_at"):
                continue
            if not is_bay_area(source_rec.get("locations") or [], allow_remote):
                continue
            keep, score, reason = classify(
                rec["title"], rec.get("degrees"), rec.get("category"))
            if not keep or score < min_score:
                continue
            # Age gate uses posted date if we have it, else when we first saw it.
            ref = rec.get("posted") or rec.get("first_seen") or 0
            if max_age_days and ref and ref < cutoff:
                continue
            row = dict(rec)
            row["score"], row["reason"] = score, reason
            out.append(row)
        return dedup(out)

    def mark_notified(self, candidates, timestamp=None):
        """Stamp every stored Cross-post represented by the Candidates."""
        candidate_keys = {dedup_key(rec) for rec in candidates}
        notified_at = now() if timestamp is None else timestamp
        marked = 0
        for rec in self.jobs.values():
            view = _us_record(rec)
            if view is not None and dedup_key(view) in candidate_keys:
                rec["notified_at"] = notified_at
                marked += 1
        return marked


# ==========================================================================
# Fetchers  — each returns (records, ok)
# ==========================================================================

def get_json(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_simplify():
    try:
        data = get_json(SIMPLIFY_URL)
    except Exception as e:
        print(f"  ! simplify: {e}", file=sys.stderr)
        return [], False

    out = []
    for j in data:
        if not j.get("is_visible"):
            continue
        cat = j.get("category") or ""
        if not re.search(r"software|ai/ml|data|machine", cat, re.I):
            continue
        out.append({
            "uid": f"simplify:{j['id']}",
            "title": j.get("title", ""),
            "company": j.get("company_name", ""),
            "locations": j.get("locations") or [],
            "url": j.get("url", ""),
            "posted": j.get("date_posted") or 0,
            "degrees": j.get("degrees") or [],
            "category": cat,
            "sponsorship": j.get("sponsorship") or "",
            "source": "Simplify",
            # Simplify tracks this itself; treat inactive as closed.
            "feed_active": bool(j.get("active")),
        })
    return out, True


def fetch_greenhouse(slug):
    try:
        data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
    except Exception as e:
        print(f"  ! greenhouse/{slug}: {e}", file=sys.stderr)
        return [], False

    out = []
    for j in data.get("jobs", []):
        loc = (j.get("location") or {}).get("name", "")
        ts = 0
        if j.get("updated_at"):
            try:
                ts = int(datetime.fromisoformat(
                    j["updated_at"].replace("Z", "+00:00")).timestamp())
            except Exception:
                pass
        out.append({
            "uid": f"gh:{slug}:{j['id']}",
            "title": j.get("title", ""),
            "company": slug.replace("-", " ").title(),
            "locations": [loc] if loc else [],
            "url": j.get("absolute_url", ""),
            "posted": ts,
            "degrees": [],
            "category": "",
            "source": "Greenhouse",
            "feed_active": True,
        })
    return out, True


def fetch_lever(slug):
    try:
        data = get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    except Exception as e:
        print(f"  ! lever/{slug}: {e}", file=sys.stderr)
        return [], False

    out = []
    for j in data:
        cats = j.get("categories") or {}
        loc = cats.get("location") or ""
        out.append({
            "uid": f"lever:{slug}:{j['id']}",
            "title": j.get("text", ""),
            "company": slug.replace("-", " ").title(),
            "locations": [loc] if loc else [],
            "url": j.get("hostedUrl", ""),
            "posted": int((j.get("createdAt") or 0) / 1000),
            "degrees": [],
            "category": cats.get("team", ""),
            "source": "Lever",
            "feed_active": True,
        })
    return out, True


def fetch_ashby(slug):
    try:
        data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    except Exception as e:
        print(f"  ! ashby/{slug}: {e}", file=sys.stderr)
        return [], False

    out = []
    for j in data.get("jobs", []):
        if not j.get("isListed", True):
            continue
        loc = j.get("location", "")
        ts = 0
        if j.get("publishedAt"):
            try:
                ts = int(datetime.fromisoformat(
                    j["publishedAt"].replace("Z", "+00:00")).timestamp())
            except Exception:
                pass
        out.append({
            "uid": f"ashby:{slug}:{j['id']}",
            "title": j.get("title", ""),
            "company": slug.replace("-", " ").title(),
            "locations": [loc] if loc else [],
            "url": j.get("jobUrl") or j.get("applyUrl", ""),
            "posted": ts,
            "degrees": [],
            "category": j.get("department", ""),
            "source": "Ashby",
            "feed_active": True,
        })
    return out, True


# ==========================================================================
# Discord
# ==========================================================================

def color_for(score):
    return 0x2ECC71 if score >= 10 else 0x3498DB if score >= 5 else 0x95A5A6


def build_embed(job):
    loc = ", ".join(job.get("locations") or [])[:100] or "—"
    embed = {
        "title": (job.get("title") or "")[:250],
        "url": job.get("url") or None,
        "color": color_for(job["score"]),
        "fields": [
            {"name": "Company", "value": (job.get("company") or "—")[:100],
             "inline": True},
            {"name": "Location", "value": loc, "inline": True},
        ],
        "footer": {"text": f"{job.get('source','?')} • {job['reason']}"},
    }
    if job.get("posted"):
        embed["timestamp"] = datetime.fromtimestamp(
            job["posted"], tz=timezone.utc).isoformat()
    return embed


def post_discord(embeds, webhook, dry=False):
    if dry or not webhook:
        print(f"  [no-send] {len(embeds)} embed(s) withheld")
        return False
    for i in range(0, len(embeds), 10):
        payload = json.dumps({"embeds": embeds[i:i + 10]}).encode()
        for _ in range(5):
            req = urllib.request.Request(
                webhook, data=payload,
                headers={"Content-Type": "application/json", **UA})
            try:
                urllib.request.urlopen(req, timeout=20).read()
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait = float(json.loads(e.read() or b"{}").get("retry_after", 2))
                    print(f"  rate limited, sleeping {wait}s")
                    time.sleep(wait + 0.3)
                    continue
                print(f"  ! discord {e.code}", file=sys.stderr)
                return False
        else:
            print("  ! discord rate-limit retries exhausted", file=sys.stderr)
            return False
        time.sleep(1.0)
    return True


# ==========================================================================
# Commands
# ==========================================================================

GH_ID_PATTERNS = (
    re.compile(r"gh_jid=(\d+)"),        # e.g. stripe.com/jobs/search?gh_jid=123
    re.compile(r"[?&]token=(\d+)"),     # e.g. boards.greenhouse.io/embed/job_app?token=123
    re.compile(r"/jobs/(\d+)\b"),       # e.g. job-boards.greenhouse.io/<slug>/jobs/123
)


def extract_gh_id(url):
    """
    Pull the underlying Greenhouse job id out of a URL, whatever shape it's
    wrapped in. Simplify sometimes links to the board URL directly, and
    sometimes wraps the same id in a company-site query param instead — so
    string-equality on the URL itself isn't enough to recognize a cross-post.
    """
    for pat in GH_ID_PATTERNS:
        m = pat.search(url or "")
        if m:
            return m.group(1)
    return None


def dedup_key(record):
    """Return the current Cross-post identity key for a Record."""
    gh_id = extract_gh_id(record.get("url"))
    if gh_id:
        return ("gh", gh_id)
    title = re.sub(
        r"[^a-z0-9 ]", " ", (record.get("title") or "").lower()
    )
    title = re.sub(
        r"\b(i|1|new grad|new graduate|entry level|early career)\b",
        " ",
        title,
    )
    title = " ".join(title.split())
    location = (record.get("locations") or ["?"])[0].lower()
    return ((record.get("company") or "").lower(), title, location)


def dedup(rows):
    """
    Collapse the same role posted twice. A Greenhouse job id extracted from
    the URL is the strongest signal (same req, different source) and is used
    when available; otherwise fall back to company + location + a title
    stripped of punctuation and level markers. Keeps the highest score.
    """
    best = {}
    for r in rows:
        k = dedup_key(r)
        if k not in best or r["score"] > best[k]["score"]:
            best[k] = r
    out = list(best.values())
    out.sort(key=lambda r: (-r["score"], -(r.get("posted") or 0)))
    return out


def show(rows, limit=50):
    if not rows:
        print("  (none)")
        return
    for r in rows[:limit]:
        age = ""
        if r.get("posted"):
            days = (now() - r["posted"]) // 86400
            age = f"{days}d"
        flag = "✓" if r.get("applied_at") else " "
        print(f"  {flag}[{r['score']:>2}] {age:>4}  "
              f"{(r.get('company') or '')[:20]:<20} {(r.get('title') or '')[:52]}")
    if len(rows) > limit:
        print(f"  ... and {len(rows) - limit} more")


def cmd_scan(args, store):
    sources = {"greenhouse": [], "lever": [], "ashby": []}
    if SOURCES_FILE.exists():
        sources.update(json.loads(SOURCES_FILE.read_text()))

    fetched, ok_prefixes = [], []

    recs, ok = fetch_simplify()
    print(f"simplify: {len(recs)} listings ({'ok' if ok else 'FAILED'})")
    fetched += recs
    if ok:
        ok_prefixes.append("simplify:")

    for slug in sources.get("greenhouse", []):
        recs, ok = fetch_greenhouse(slug)
        print(f"  greenhouse/{slug}: {len(recs)}")
        fetched += recs
        if ok:
            ok_prefixes.append(f"gh:{slug}:")
        time.sleep(0.3)

    for slug in sources.get("lever", []):
        recs, ok = fetch_lever(slug)
        print(f"  lever/{slug}: {len(recs)}")
        fetched += recs
        if ok:
            ok_prefixes.append(f"lever:{slug}:")
        time.sleep(0.3)

    for slug in sources.get("ashby", []):
        recs, ok = fetch_ashby(slug)
        print(f"  ashby/{slug}: {len(recs)}")
        fetched += recs
        if ok:
            ok_prefixes.append(f"ashby:{slug}:")
        time.sleep(0.3)

    live = set()
    for rec in fetched:
        active = rec.pop("feed_active", True)
        merged = store.upsert(rec)
        if active:
            live.add(rec["uid"])
        else:
            merged["closed_at"] = merged.get("closed_at") or now()

    closed = store.mark_closed(ok_prefixes, live)
    print(f"\nstore: {len(store.jobs)} records, {closed} newly closed")

    rows = store.candidates(min_score=args.min_score,
                            allow_remote=not args.no_remote)
    print(f"{len(rows)} new match(es)")
    show(rows)

    if args.seed:
        store.mark_notified(rows)
        print("seeded — marked as notified without sending")
    elif rows:
        sent = post_discord([build_embed(r) for r in rows],
                            os.environ.get("DISCORD_WEBHOOK", ""),
                            dry=args.dry_run)
        if sent:
            store.mark_notified(rows)

    if not args.dry_run:
        store.save()
        print(f"saved {store.path.name}")


def cmd_query(args, store):
    rows = store.candidates(
        min_score=args.min_score,
        allow_remote=not args.no_remote,
        include_closed=args.include_closed,
        unnotified_only=not args.all,
        max_age_days=args.max_age,
    )
    label = "all stored" if args.all else "un-notified"
    print(f"{len(rows)} {label} match(es) at min-score {args.min_score}\n")
    show(rows, limit=args.limit)

    if args.notify and rows:
        sent = post_discord([build_embed(r) for r in rows],
                            os.environ.get("DISCORD_WEBHOOK", ""),
                            dry=args.dry_run)
        if sent and not args.dry_run:
            store.mark_notified(rows)
            store.save()


def cmd_stats(args, store):
    jobs = [j for j in store.jobs.values() if not j.get("migrated")]
    openj = [j for j in jobs if not j.get("closed_at")]
    print(f"records        {len(store.jobs)}")
    print(f"  real         {len(jobs)}")
    print(f"  open         {len(openj)}")
    print(f"  closed       {len(jobs) - len(openj)}")
    print(f"  notified     {sum(1 for j in jobs if j.get('notified_at'))}")
    print(f"  applied      {sum(1 for j in jobs if j.get('applied_at'))}")
    print(f"file size      {store.path.stat().st_size / 1e6:.1f} MB"
          if store.path.exists() else "file size      —")
    print("\nby score band (open, Bay Area):")
    for lo in (10, 5, 3):
        n = len(store.candidates(min_score=lo, unnotified_only=False,
                                 max_age_days=0))
        print(f"  >= {lo:<3} {n}")


def cmd_applied(args, store):
    hits = [u for u, r in store.jobs.items()
            if args.needle in u or args.needle in (r.get("url") or "")]
    if not hits:
        print("no match for that uid or url")
        return
    if len(hits) > 3 and not args.force:
        print(f"'{args.needle}' matches {len(hits)} roles — too broad. "
              f"Use a longer needle, or --force. First few:")
        for uid in hits[:5]:
            print(f"  {uid}  {store.jobs[uid].get('title','')[:50]}")
        return
    for uid in hits:
        store.jobs[uid]["applied_at"] = now()
        print(f"marked applied: {store.jobs[uid].get('title', uid)}")
    store.save()


def cmd_export(args, store):
    out = HERE / "jobs.db"
    if out.exists():
        out.unlink()
    con = sqlite3.connect(out)
    con.execute("""CREATE TABLE jobs (
        uid TEXT PRIMARY KEY, title TEXT, company TEXT, locations TEXT,
        url TEXT, source TEXT, category TEXT, degrees TEXT,
        posted INT, first_seen INT, last_seen INT,
        closed_at INT, notified_at INT, applied_at INT,
        score INT, reason TEXT)""")
    rows = []
    for r in store.us_records():
        uid = r.get("uid")
        _, score, reason = classify(r.get("title", ""), r.get("degrees"))
        rows.append((
            uid, r.get("title"), r.get("company"),
            "; ".join(r.get("locations") or []), r.get("url"), r.get("source"),
            r.get("category"), "; ".join(r.get("degrees") or []),
            r.get("posted"), r.get("first_seen"), r.get("last_seen"),
            r.get("closed_at"), r.get("notified_at"), r.get("applied_at"),
            score, reason))
    con.executemany("INSERT INTO jobs VALUES (%s)" % ",".join("?" * 16), rows)
    con.commit()
    con.close()
    print(f"wrote {out} ({len(rows)} US-eligible rows)")
    print("try:  sqlite3 jobs.db \"select company,title from jobs "
          "where score>=10 and closed_at is null limit 20\"")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")

    def common(p):
        p.add_argument("--min-score", type=int, default=5)
        p.add_argument("--no-remote", action="store_true")
        p.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("scan", help="fetch, store, notify")
    common(s)
    s.add_argument("--seed", action="store_true",
                   help="mark current matches notified without sending")

    q = sub.add_parser("query", help="re-filter stored data, no fetch")
    common(q)
    q.add_argument("--all", action="store_true",
                   help="include already-notified roles")
    q.add_argument("--include-closed", action="store_true")
    q.add_argument("--max-age", type=int, default=MAX_AGE_DAYS,
                   help="0 = no age limit")
    q.add_argument("--limit", type=int, default=50)
    q.add_argument("--notify", action="store_true",
                   help="actually send these to Discord")

    sub.add_parser("stats", help="summary of the store")

    a = sub.add_parser("applied", help="mark a role applied")
    a.add_argument("needle", help="uid substring or apply URL")
    a.add_argument("--force", action="store_true",
                   help="allow marking more than 3 matches at once")

    sub.add_parser("export", help="dump US-eligible records to SQLite")

    args = ap.parse_args()
    if not args.cmd:
        args.cmd = "scan"
        for k, v in (("min_score", 5), ("no_remote", False),
                     ("dry_run", False), ("seed", False)):
            setattr(args, k, v)

    store = Store()
    {"scan": cmd_scan, "query": cmd_query, "stats": cmd_stats,
     "applied": cmd_applied, "export": cmd_export}[args.cmd](args, store)


if __name__ == "__main__":
    main()
