"""IAP-gated, read-only Smart Inbox vertical slice.

The application deliberately reads a public Canonical Store snapshot and derives an
ephemeral inbox for the request. It has no mutation route, persistent repository,
Vertex call, or access to application/Discord state.
"""

from __future__ import annotations

import html
import json
import os
import time
import urllib.request
import urllib.parse
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from wsgiref.simple_server import make_server

from job_alert import MAX_AGE_DAYS, candidates_from_records


class CanonicalStoreUnavailable(Exception):
    """The public Store could not be read for this request."""


class CanonicalStoreReader(Protocol):
    """Read, but never mutate, the public Canonical Store payload."""

    def read(self) -> Mapping[str, object]: ...


class FitPriorityProvider(Protocol):
    """Return a private advisory triage result for a compact Record reference."""

    def assess(self, reference: "RecordReference") -> "FitPriority": ...


class IdentityVerifier(Protocol):
    """Verify an IAP assertion and return the authenticated email, if any."""

    def identity(self, environ: Mapping[str, str]) -> str | None: ...


@dataclass(frozen=True)
class RecordReference:
    """A request-scoped reference to a Canonical Record, never a private copy."""

    uid: str
    title: str
    company: str
    locations: tuple[str, ...]
    source: str
    source_url: str | None
    first_seen: int
    score: int
    score_reason: str


@dataclass(frozen=True)
class FitPriority:
    """Private advisory output; it never represents candidate eligibility."""

    state: str
    band: str | None
    explanation: str


@dataclass(frozen=True)
class SmartInboxItem:
    reference: RecordReference
    fit_priority: FitPriority


class JsonFileCanonicalStoreReader:
    """Local read-only adapter for tests and an owner-operated preview."""

    def __init__(self, path: Path):
        self.path = path

    def read(self) -> Mapping[str, object]:
        try:
            payload = json.loads(self.path.read_text())
        except (OSError, json.JSONDecodeError) as error:
            raise CanonicalStoreUnavailable from error
        return _validated_payload(payload)


class HttpCanonicalStoreReader:
    """Fetch a public Canonical Store snapshot without retaining it."""

    def __init__(self, url: str, timeout_seconds: float = 5):
        self.url = url
        self.timeout_seconds = timeout_seconds

    def read(self) -> Mapping[str, object]:
        try:
            request = urllib.request.Request(self.url, headers={"User-Agent": "kelsa-smart-inbox/1.0"})
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise CanonicalStoreUnavailable from error
        return _validated_payload(payload)


class SafeReviewFitPriorityProvider:
    """Safe default while private profile/model admission is unavailable."""

    def __init__(self, reason: str = "Fit Priority is unavailable; review this role without advisory triage."):
        self.reason = reason

    def assess(self, reference: RecordReference) -> FitPriority:
        return FitPriority(state="safe_review", band=None, explanation=self.reason)


class GoogleIapJwtVerifier:
    """Verify the IAP JWT before accepting its owner identity header."""

    _IAP_CERTS_URL = "https://www.gstatic.com/iap/verify/public_key"
    _IAP_ISSUER = "https://cloud.google.com/iap"

    def __init__(self, audience: str):
        if not audience:
            raise ValueError("IAP audience is required")
        self.audience = audience

    def identity(self, environ: Mapping[str, str]) -> str | None:
        assertion = environ.get("HTTP_X_GOOG_IAP_JWT_ASSERTION", "")
        if not assertion:
            return None
        try:
            from google.auth.transport.requests import Request
            from google.oauth2 import id_token

            claims = id_token.verify_token(
                assertion,
                Request(),
                audience=self.audience,
                certs_url=self._IAP_CERTS_URL,
            )
        except Exception:
            return None
        if claims.get("iss") != self._IAP_ISSUER:
            return None
        return _normalize_iap_email(str(claims.get("email") or "")) or None


class SmartInboxService:
    """Builds a transient Smart Inbox from the authoritative public Store."""

    def __init__(
        self,
        reader: CanonicalStoreReader,
        fit_priority: FitPriorityProvider | None = None,
        now: Callable[[], float] = time.time,
        lookback_seconds: int = 7 * 86400,
    ):
        if lookback_seconds <= 0:
            raise ValueError("lookback_seconds must be positive")
        self.reader = reader
        self.fit_priority = fit_priority or SafeReviewFitPriorityProvider()
        self.now = now
        self.lookback_seconds = lookback_seconds

    def items(self) -> list[SmartInboxItem]:
        try:
            payload = self.reader.read()
            jobs = payload["jobs"]
            assert isinstance(jobs, dict)
            threshold = int(self.now()) - self.lookback_seconds
            candidates = candidates_from_records(
                jobs,
                min_score=5,
                unnotified_only=False,
                max_age_days=MAX_AGE_DAYS,
            )
            references = [
                _reference_from(candidate)
                for candidate in candidates
                if int(candidate.get("first_seen") or 0) >= threshold
            ]
        except Exception as error:
            raise CanonicalStoreUnavailable from error
        references.sort(key=lambda item: (-item.score, -item.first_seen, item.uid))
        return [SmartInboxItem(reference, self._fit_priority(reference)) for reference in references]

    def _fit_priority(self, reference: RecordReference) -> FitPriority:
        try:
            result = self.fit_priority.assess(reference)
            if not isinstance(result, FitPriority):
                raise TypeError("Fit Priority provider returned an invalid result")
            return result
        except Exception:
            return SafeReviewFitPriorityProvider().assess(reference)


def create_application(
    service: SmartInboxService,
    owner_email: str,
    identity_verifier: IdentityVerifier,
):
    """Create the WSGI app protected by direct Cloud Run IAP.

    IAP must protect the Cloud Run service at the platform level. The signed IAP JWT
    binds the email to this service audience; the exact-email check is defense in depth.
    """
    normalized_owner = _normalize_iap_email(owner_email)
    if not normalized_owner:
        raise ValueError("owner_email must be a non-empty email address")

    def application(environ, start_response):
        caller = identity_verifier.identity(environ)
        if caller != normalized_owner:
            return _response(start_response, "403 Forbidden", _forbidden_page())
        if environ.get("PATH_INFO", "/") == "/healthz":
            return _response(start_response, "200 OK", "ok", content_type="text/plain; charset=utf-8")
        if environ.get("REQUEST_METHOD", "GET") != "GET" or environ.get("PATH_INFO", "/") != "/":
            return _response(start_response, "404 Not Found", "Not found", content_type="text/plain; charset=utf-8")
        try:
            return _response(start_response, "200 OK", _inbox_page(service.items()))
        except CanonicalStoreUnavailable:
            return _response(start_response, "503 Service Unavailable", _unavailable_page())

    return application


def application_from_environment():
    """Production entrypoint. Missing configuration remains closed, not permissive."""
    owner_email = os.environ.get("SMART_INBOX_OWNER_EMAIL", "")
    store_url = os.environ.get("SMART_INBOX_CANONICAL_STORE_URL", "")
    iap_audience = os.environ.get("SMART_INBOX_IAP_AUDIENCE", "")
    if not store_url:
        raise RuntimeError("SMART_INBOX_CANONICAL_STORE_URL is required")
    lookback_hours = int(os.environ.get("SMART_INBOX_LOOKBACK_HOURS", "168"))
    return create_application(
        SmartInboxService(HttpCanonicalStoreReader(store_url), lookback_seconds=lookback_hours * 3600),
        owner_email,
        GoogleIapJwtVerifier(iap_audience),
    )


def _validated_payload(payload: object) -> Mapping[str, object]:
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), dict):
        raise CanonicalStoreUnavailable
    if any(not isinstance(uid, str) or not isinstance(record, dict) for uid, record in payload["jobs"].items()):
        raise CanonicalStoreUnavailable
    return payload


def _reference_from(record: Mapping[str, object]) -> RecordReference:
    locations = record.get("locations") or []
    return RecordReference(
        uid=str(record["uid"]),
        title=str(record.get("title") or "Untitled role"),
        company=str(record.get("company") or "Unknown company"),
        locations=tuple(str(location) for location in locations if isinstance(location, str)),
        source=str(record.get("source") or "Unknown source"),
        source_url=str(record["url"]) if record.get("url") else None,
        first_seen=int(record.get("first_seen") or 0),
        score=int(record["score"]),
        score_reason=str(record["reason"]),
    )


def _normalize_iap_email(value: str) -> str:
    prefix = "accounts.google.com:"
    return value.removeprefix(prefix).strip().lower()


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _inbox_page(items: Iterable[SmartInboxItem]) -> str:
    rows = "".join(_item_row(item) for item in items)
    if not rows:
        rows = '<p class="empty">No newly eligible open Records in this review window.</p>'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smart Inbox</title><style>{_STYLE}</style></head><body><main>
<p class="eyebrow">Career Command Centre · private read-only view</p><h1>Smart Inbox</h1>
<p class="boundary">The Canonical Store remains authoritative. This workspace cannot change Candidate, Eligible Region, Score, scan behavior, or Discord; Fit Priority does not change Discord.</p>
<section aria-label="Newly eligible open Records">{rows}</section>
</main></body></html>"""


def _item_row(item: SmartInboxItem) -> str:
    ref = item.reference
    role = _escape(ref.title)
    if _safe_source_url(ref.source_url):
        role = f'<a href="{_escape(ref.source_url)}" rel="noopener noreferrer" target="_blank">{role}</a>'
    fit = "Safe review state" if item.fit_priority.state == "safe_review" else _escape(item.fit_priority.band or "Unranked")
    return f"""<article><h2>{role}</h2><p>{_escape(ref.company)} · {_escape(' · '.join(ref.locations) or 'Location unavailable')} · {_escape(ref.source)}</p>
<dl><div><dt>Deterministic Score</dt><dd>{ref.score} · {_escape(ref.score_reason)}</dd></div>
<div><dt>Fit Priority (advisory)</dt><dd>{fit}</dd></div></dl>
<p class="explanation">{_escape(item.fit_priority.explanation)}</p></article>"""


def _forbidden_page() -> str:
    return "<!doctype html><title>Access denied</title><h1>Access denied</h1>"


def _unavailable_page() -> str:
    return "<!doctype html><title>Smart Inbox unavailable</title><h1>Smart Inbox is temporarily unavailable</h1><p>No private or advisory result was produced. Try again later.</p>"


def _response(start_response, status: str, body: str, content_type: str = "text/html; charset=utf-8"):
    encoded = body.encode("utf-8")
    start_response(status, [("Content-Type", content_type), ("Content-Length", str(len(encoded))), ("Cache-Control", "no-store")])
    return [encoded]


def _safe_source_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urllib.parse.urlsplit(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


_STYLE = """
body { background: #0b1220; color: #edf2f7; font: 16px system-ui, sans-serif; margin: 0; }
main { max-width: 900px; margin: 0 auto; padding: 3rem 1.25rem; }
h1 { margin: .1rem 0 1rem; } .eyebrow { color: #91caff; font-weight: 700; margin: 0; }
.boundary { border-left: 4px solid #f4c95d; padding-left: 1rem; color: #dce7f5; }
article { background: #162033; border: 1px solid #30445f; border-radius: 10px; margin: 1rem 0; padding: 1.1rem 1.25rem; }
h2 { margin: 0 0 .45rem; } a { color: #91caff; } dl { display: flex; flex-wrap: wrap; gap: 1.5rem; } dt { color: #a9b9cf; font-size: .85rem; } dd { font-weight: 700; margin: .15rem 0 0; } .explanation { color: #dce7f5; } .empty { color: #dce7f5; }
"""


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    with make_server("0.0.0.0", port, application_from_environment()) as server:
        server.serve_forever()
