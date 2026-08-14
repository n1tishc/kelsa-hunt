import json
import io
import pathlib
import re
import tempfile
import time
import unittest
import urllib.parse
from wsgiref.util import setup_testing_defaults

from career_command_centre.app import (
    FitPriority,
    GoogleIapJwtVerifier,
    SafeReviewFitPriorityProvider,
    SmartInboxService,
    create_application,
)
from career_command_centre.role_workspace import (
    InMemoryRoleWorkspace,
    ProfileItemRevision,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]


class StaticReader:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return self.payload


class AvailableFitPriorityProvider:
    def assess(self, reference):
        return FitPriority(
            state="available",
            band="high",
            explanation=f"Advisory triage for {reference.uid}.",
        )


class FailingReader:
    def read(self):
        raise OSError("network unavailable")


class FailingFitPriorityProvider:
    def assess(self, reference):
        raise RuntimeError("quota exhausted")


class StaticIdentityVerifier:
    def __init__(self, identity):
        self._identity = identity

    def identity(self, environ):
        return self._identity


class RecordingDescriptionFetcher:
    def __init__(self):
        self.calls = []

    def fetch(self, reference):
        self.calls.append(reference.uid)
        return "Build reliable developer tooling."


def payload(now):
    return {
        "version": 2,
        "jobs": {
            "new-grad": {
                "uid": "new-grad",
                "title": "Software Engineer, New Grad",
                "company": "<Acme>",
                "locations": ["San Francisco, CA"],
                "url": "https://example.invalid/new-grad",
                "source": "Fixture",
                "first_seen": now - 60,
                "posted": now - 60,
            },
            "old-open": {
                "uid": "old-open",
                "title": "Software Engineer I",
                "company": "Old Co",
                "locations": ["Austin, TX"],
                "url": "https://example.invalid/old",
                "source": "Fixture",
                "first_seen": now - 9 * 86400,
                "posted": now - 9 * 86400,
            },
            "closed": {
                "uid": "closed",
                "title": "Software Engineer, New Grad",
                "company": "Closed Co",
                "locations": ["San Francisco, CA"],
                "first_seen": now - 60,
                "closed_at": now - 30,
            },
            "foreign": {
                "uid": "foreign",
                "title": "Software Engineer, New Grad",
                "company": "Foreign Co",
                "locations": ["Toronto, Canada"],
                "first_seen": now - 60,
            },
        },
    }


def invoke(application, headers=(), method="GET", path="/", form_body=None):
    environ = {}
    setup_testing_defaults(environ)
    environ["REQUEST_METHOD"] = method
    environ["PATH_INFO"] = path
    if form_body is not None:
        encoded = form_body.encode()
        environ["CONTENT_LENGTH"] = str(len(encoded))
        environ["CONTENT_TYPE"] = "application/x-www-form-urlencoded"
        environ["wsgi.input"] = io.BytesIO(encoded)
    for name, value in headers:
        environ[name] = value
    received = {}

    def start_response(status, response_headers):
        received["status"] = status
        received["headers"] = response_headers

    body = b"".join(application(environ, start_response)).decode()
    return received["status"], body


def csrf_form(application):
    status, body = invoke(application)
    if status != "200 OK":
        raise AssertionError("could not retrieve CSRF token")
    token = re.search(r'name="csrf_token" value="([a-f0-9]+)"', body)
    if token is None:
        raise AssertionError("CSRF token missing")
    return urllib.parse.urlencode({"csrf_token": token.group(1)})


class SmartInboxTests(unittest.TestCase):
    def setUp(self):
        self.now = int(time.time())
        self.service = SmartInboxService(
            reader=StaticReader(payload(self.now)),
            fit_priority=AvailableFitPriorityProvider(),
            now=lambda: self.now,
            lookback_seconds=7 * 86400,
        )

    def test_inbox_is_a_read_only_recent_open_candidate_view(self):
        items = self.service.items()

        self.assertEqual([item.reference.uid for item in items], ["new-grad"])
        item = items[0]
        self.assertEqual(item.reference.score, 10)
        self.assertEqual(item.reference.score_reason, "explicit new-grad")
        self.assertEqual(item.fit_priority.band, "high")
        self.assertIn("Advisory", item.fit_priority.explanation)

    def test_model_or_quota_unavailability_is_a_safe_review_state(self):
        service = SmartInboxService(
            reader=StaticReader(payload(self.now)),
            fit_priority=SafeReviewFitPriorityProvider("quota unavailable"),
            now=lambda: self.now,
            lookback_seconds=7 * 86400,
        )

        item = service.items()[0]
        self.assertEqual(item.fit_priority.state, "safe_review")
        self.assertIsNone(item.fit_priority.band)
        self.assertEqual(item.fit_priority.explanation, "quota unavailable")

        service = SmartInboxService(
            reader=StaticReader(payload(self.now)),
            fit_priority=FailingFitPriorityProvider(),
            now=lambda: self.now,
        )
        self.assertEqual(service.items()[0].fit_priority.state, "safe_review")

    def test_authorized_page_shows_score_and_fit_as_separate_signals(self):
        application = create_application(
            self.service,
            "owner@example.com",
            StaticIdentityVerifier("owner@example.com"),
        )

        status, body = invoke(application)

        self.assertEqual(status, "200 OK")
        self.assertIn("Deterministic Score", body)
        self.assertIn("Fit Priority (advisory)", body)
        self.assertIn("&lt;Acme&gt;", body)
        self.assertIn("does not change Discord", body)

    def test_missing_or_wrong_iap_identity_is_denied_without_inbox_content(self):
        application = create_application(
            self.service,
            "owner@example.com",
            GoogleIapJwtVerifier("/projects/123/apps/smart-inbox"),
        )

        status, body = invoke(application, [("HTTP_X_GOOG_AUTHENTICATED_USER_EMAIL", "accounts.google.com:owner@example.com")])
        self.assertEqual(status, "403 Forbidden")
        self.assertNotIn("new-grad", body)
        self.assertNotIn("Acme", body)

    def test_public_store_failure_is_visible_without_an_error_body(self):
        service = SmartInboxService(reader=FailingReader(), now=lambda: self.now)
        application = create_application(
            service,
            "owner@example.com",
            StaticIdentityVerifier("owner@example.com"),
        )

        status, body = invoke(application)

        self.assertEqual(status, "503 Service Unavailable")
        self.assertIn("Smart Inbox is temporarily unavailable", body)
        self.assertNotIn("network unavailable", body)

    def test_json_reader_does_not_modify_the_public_canonical_store(self):
        with tempfile.TemporaryDirectory() as directory:
            store = pathlib.Path(directory) / "jobs.json"
            store.write_text(json.dumps(payload(self.now)))
            before = store.read_bytes()
            from career_command_centre.app import JsonFileCanonicalStoreReader

            service = SmartInboxService(
                reader=JsonFileCanonicalStoreReader(store),
                fit_priority=AvailableFitPriorityProvider(),
                now=lambda: self.now,
            )
            service.items()

            self.assertEqual(store.read_bytes(), before)

    def test_unsafe_public_source_url_is_not_rendered_as_a_link(self):
        unsafe = payload(self.now)
        unsafe["jobs"]["new-grad"]["url"] = "javascript:alert('nope')"
        service = SmartInboxService(
            reader=StaticReader(unsafe),
            fit_priority=AvailableFitPriorityProvider(),
            now=lambda: self.now,
        )
        application = create_application(
            service,
            "owner@example.com",
            StaticIdentityVerifier("owner@example.com"),
        )

        status, body = invoke(application)

        self.assertEqual(status, "200 OK")
        self.assertNotIn("href=\"javascript", body)

    def test_open_creates_one_owner_authorized_snapshot_and_shows_profile_context(self):
        fetcher = RecordingDescriptionFetcher()
        workspace = InMemoryRoleWorkspace(
            description_fetcher=fetcher,
            profile_items=(
                ProfileItemRevision("profile-item-1", "project", "Built a reliable API."),
                ProfileItemRevision("profile-item-2", "preference", "Prefer developer tools."),
                ProfileItemRevision("profile-item-3", "history", "Ran a marketing campaign."),
            ),
            now=lambda: 1_700_000_000,
        )
        application = create_application(
            self.service,
            "owner@example.com",
            StaticIdentityVerifier("owner@example.com"),
            role_workspace=workspace,
        )

        status, _ = invoke(
            application,
            method="POST",
            path="/roles/new-grad/open",
            form_body=csrf_form(application),
        )

        self.assertEqual(status, "303 See Other")
        self.assertEqual(fetcher.calls, ["new-grad"])
        snapshot = workspace.snapshot_for("new-grad")
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.source_url, "https://example.invalid/new-grad")
        self.assertEqual(snapshot.captured_at, 1_700_000_000)
        self.assertEqual(snapshot.description, "Build reliable developer tooling.")

        status, body = invoke(application, path=f"/workspace/{snapshot.id}")
        self.assertEqual(status, "200 OK")
        self.assertIn("Selected Role Snapshot", body)
        self.assertIn("Built a reliable API.", body)
        self.assertIn("Prefer developer tools.", body)
        self.assertNotIn("marketing campaign", body)
        self.assertIn("record reference only", body)

    def test_shortlist_is_owner_authorized_and_never_refetches_an_existing_snapshot(self):
        fetcher = RecordingDescriptionFetcher()
        workspace = InMemoryRoleWorkspace(description_fetcher=fetcher, now=lambda: 1_700_000_000)
        application = create_application(
            self.service,
            "owner@example.com",
            StaticIdentityVerifier("owner@example.com"),
            role_workspace=workspace,
        )

        form_body = csrf_form(application)
        first_status, _ = invoke(application, method="POST", path="/roles/new-grad/shortlist", form_body=form_body)
        second_status, _ = invoke(application, method="POST", path="/roles/new-grad/shortlist", form_body=form_body)

        self.assertEqual(first_status, "303 See Other")
        self.assertEqual(second_status, "303 See Other")
        self.assertEqual(fetcher.calls, ["new-grad"])
        self.assertTrue(workspace.is_shortlisted("new-grad"))

    def test_snapshot_action_rejects_a_role_that_is_not_in_the_current_inbox(self):
        workspace = InMemoryRoleWorkspace(description_fetcher=RecordingDescriptionFetcher())
        application = create_application(
            self.service,
            "owner@example.com",
            StaticIdentityVerifier("owner@example.com"),
            role_workspace=workspace,
        )

        status, _ = invoke(
            application,
            method="POST",
            path="/roles/foreign/open",
            form_body=csrf_form(application),
        )

        self.assertEqual(status, "404 Not Found")
        self.assertEqual(workspace.snapshot_for("foreign"), None)

    def test_cross_site_snapshot_post_without_csrf_token_is_rejected_before_fetch(self):
        fetcher = RecordingDescriptionFetcher()
        workspace = InMemoryRoleWorkspace(description_fetcher=fetcher)
        application = create_application(
            self.service,
            "owner@example.com",
            StaticIdentityVerifier("owner@example.com"),
            role_workspace=workspace,
        )

        status, _ = invoke(application, method="POST", path="/roles/new-grad/open")

        self.assertEqual(status, "403 Forbidden")
        self.assertEqual(fetcher.calls, [])

    def test_inbox_reads_never_fetch_a_description_or_create_private_workspace_state(self):
        fetcher = RecordingDescriptionFetcher()
        workspace = InMemoryRoleWorkspace(description_fetcher=fetcher)

        self.service.items()

        self.assertEqual(fetcher.calls, [])
        self.assertEqual(workspace.snapshot_for("new-grad"), None)


if __name__ == "__main__":
    unittest.main()
