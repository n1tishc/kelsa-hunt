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


class NotificationStateTests(unittest.TestCase):
    def test_marking_a_candidate_prevents_its_cross_posts_from_refiring(self):
        payload = {
            "jobs": {
                "simplify:example": {
                    "uid": "simplify:example",
                    "title": "Software Engineer, New Grad",
                    "company": "Example",
                    "locations": ["London, UK", "San Francisco, CA"],
                    "url": "https://aggregator.invalid/example-role",
                },
                "gh:example:12345": {
                    "uid": "gh:example:12345",
                    "title": "Software Engineer I",
                    "company": "Example",
                    "locations": ["San Francisco, CA"],
                    "url": "https://company.invalid/example-role",
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


if __name__ == "__main__":
    unittest.main()
