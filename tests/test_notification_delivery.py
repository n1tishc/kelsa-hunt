import io
import json
import pathlib
import tempfile
import unittest
import urllib.error
from unittest import mock

import job_alert


class DiscordDeliveryTests(unittest.TestCase):
    def test_failed_discord_delivery_is_reported_to_the_caller(self):
        failure = urllib.error.HTTPError(
            "https://discord.invalid/webhook",
            401,
            "Unauthorized",
            {},
            io.BytesIO(b"{}"),
        )

        with (
            mock.patch("urllib.request.urlopen", side_effect=failure),
            mock.patch("time.sleep"),
        ):
            delivered = job_alert.post_discord(
                [{"title": "Example"}],
                "https://discord.invalid/webhook",
            )

        self.assertFalse(delivered)

    def test_exhausted_rate_limit_retries_are_reported_as_failed(self):
        def rate_limited(*_args, **_kwargs):
            raise urllib.error.HTTPError(
                "https://discord.invalid/webhook",
                429,
                "Too Many Requests",
                {},
                io.BytesIO(b'{"retry_after": 0}'),
            )

        with (
            mock.patch("urllib.request.urlopen", side_effect=rate_limited),
            mock.patch("time.sleep"),
        ):
            delivered = job_alert.post_discord(
                [{"title": "Example"}],
                "https://discord.invalid/webhook",
            )

        self.assertFalse(delivered)

    def test_transport_failure_is_reported_to_the_caller(self):
        with (
            mock.patch(
                "urllib.request.urlopen",
                side_effect=urllib.error.URLError("offline"),
            ),
            mock.patch("time.sleep"),
        ):
            delivered = job_alert.post_discord(
                [{"title": "Example"}],
                "https://discord.invalid/webhook",
            )

        self.assertFalse(delivered)

    def test_malformed_rate_limit_response_is_reported_as_failed(self):
        def malformed_rate_limit(*_args, **_kwargs):
            raise urllib.error.HTTPError(
                "https://discord.invalid/webhook",
                429,
                "Too Many Requests",
                {},
                io.BytesIO(b"not-json"),
            )

        with (
            mock.patch(
                "urllib.request.urlopen",
                side_effect=malformed_rate_limit,
            ),
            mock.patch("time.sleep"),
        ):
            delivered = job_alert.post_discord(
                [{"title": "Example"}],
                "https://discord.invalid/webhook",
            )

        self.assertFalse(delivered)

    def test_invalid_numeric_rate_limit_delay_is_reported_as_failed(self):
        for retry_after in (-1, "nan", "inf"):
            with self.subTest(retry_after=retry_after):
                failure = urllib.error.HTTPError(
                    "https://discord.invalid/webhook",
                    429,
                    "Too Many Requests",
                    {},
                    io.BytesIO(
                        json.dumps({"retry_after": retry_after}).encode()
                    ),
                )
                with mock.patch(
                    "urllib.request.urlopen",
                    side_effect=failure,
                ):
                    delivered = job_alert.post_discord(
                        [{"title": "Example"}],
                        "https://discord.invalid/webhook",
                    )

                self.assertFalse(delivered)


class NotificationStateTests(unittest.TestCase):
    def test_marking_a_candidate_prevents_its_cross_posts_from_refiring(self):
        payload = {
            "jobs": {
                "simplify:example": {
                    "uid": "simplify:example",
                    "title": "Software Engineer, New Grad",
                    "company": "Example",
                    "locations": ["London, UK", "San Francisco, CA"],
                    "url": "https://example.com/jobs?gh_jid=12345",
                },
                "gh:example:12345": {
                    "uid": "gh:example:12345",
                    "title": "Software Engineer I",
                    "company": "Example",
                    "locations": ["San Francisco, CA"],
                    "url": "https://job-boards.greenhouse.io/example/jobs/12345",
                },
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        candidates = store.candidates()
        self.assertEqual(len(candidates), 1)

        store.mark_notified(candidates, timestamp=123)

        self.assertEqual(store.candidates(), [])

    def test_marking_a_candidate_stamps_foreign_views_of_the_same_opening(self):
        payload = {
            "jobs": {
                "simplify:example": {
                    "uid": "simplify:example",
                    "title": "Software Engineer, New Grad",
                    "company": "Example",
                    "locations": ["San Francisco, CA"],
                    "url": "https://example.com/jobs?gh_jid=12345",
                },
                "gh:example:12345": {
                    "uid": "gh:example:12345",
                    "title": "Software Engineer, New Grad",
                    "company": "Example",
                    "locations": ["London, UK"],
                    "url": "https://job-boards.greenhouse.io/example/jobs/12345",
                },
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        store.mark_notified(store.candidates(), timestamp=123)
        store.jobs["gh:example:12345"]["locations"] = ["San Francisco, CA"]

        self.assertEqual(store.candidates(), [])


if __name__ == "__main__":
    unittest.main()
