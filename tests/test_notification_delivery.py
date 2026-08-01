import io
import json
import pathlib
import tempfile
import types
import unittest
import urllib.error
from unittest import mock

import job_alert


def candidate(uid, score=5, posted=0, company="Example", title=None):
    return {
        "uid": uid,
        "title": title or f"Software Engineer {uid}",
        "company": company,
        "locations": ["San Francisco, CA"],
        "url": f"https://example.invalid/{uid}",
        "source": "Fixture",
        "score": score,
        "reason": "explicit new-grad" if score == 10 else "junior-level marker",
        "posted": posted,
    }


class DiscordDeliveryTests(unittest.TestCase):
    def test_empty_notification_batch_sends_and_persists_nothing(self):
        store = mock.Mock()

        with mock.patch.object(job_alert, "post_discord") as post:
            delivered = job_alert.deliver_notification_batch(
                store,
                [],
                "https://discord.invalid/webhook",
            )

        self.assertEqual(
            (delivered, post.call_count, store.method_calls),
            (True, 0, []),
        )

    def test_batches_of_one_and_five_use_one_rich_embed_per_candidate(self):
        for size in (1, 5):
            with self.subTest(size=size):
                candidates = [
                    {
                        "uid": f"source:{index}",
                        "title": f"Software Engineer {index}",
                        "company": "Example",
                        "locations": ["San Francisco, CA"],
                        "url": f"https://example.invalid/{index}",
                        "source": "Fixture",
                        "score": 5,
                        "reason": "junior-level marker",
                    }
                    for index in range(size)
                ]
                store = mock.Mock()

                with mock.patch.object(
                    job_alert,
                    "post_discord",
                    return_value=True,
                ) as post:
                    delivered = job_alert.deliver_notification_batch(
                        store,
                        candidates,
                        "https://discord.invalid/webhook",
                    )

                embeds = post.call_args.args[0]
                self.assertEqual(
                    (
                        delivered,
                        len(embeds),
                        [embed["title"] for embed in embeds],
                        store.method_calls,
                    ),
                    (
                        True,
                        size,
                        [candidate["title"] for candidate in candidates],
                        [
                            mock.call.mark_notified(candidates),
                            mock.call.save(),
                        ],
                    ),
                )

    def test_six_candidates_use_one_ordered_compact_digest_page(self):
        candidates = [
            candidate("z-five", score=5, posted=200, company="Zulu"),
            candidate(
                "b-ten",
                score=10,
                posted=100,
                company="Alpha",
                title="Software Engineer Beta",
            ),
            candidate(
                "a-ten",
                score=10,
                posted=100,
                company="Alpha",
                title="Software Engineer Zulu",
            ),
            candidate("new-ten", score=10, posted=300, company="New"),
            candidate("a-five", score=5, posted=200, company="Alpha"),
            candidate(
                "c-ten",
                score=10,
                posted=100,
                company="Alpha",
                title="Software Engineer Beta",
            ),
        ]
        candidates[0]["url"] = ""
        store = mock.Mock()

        with mock.patch.object(
            job_alert,
            "post_discord",
            return_value=True,
        ) as post:
            delivered = job_alert.deliver_notification_batch(
                store,
                candidates,
                "https://discord.invalid/webhook",
            )

        embeds = post.call_args.args[0]
        digest = embeds[0]
        description = digest["description"]
        ordered_uids = [
            "new-ten",
            "b-ten",
            "c-ten",
            "a-ten",
            "a-five",
            "z-five",
        ]

        self.assertEqual(
            (
                delivered,
                len(embeds),
                digest["title"],
                [description.index(uid) for uid in ordered_uids],
                "**[Software Engineer new-ten]" in description,
                "[Software Engineer a-five]" in description,
                "San Francisco, CA" in description,
                "Score 10" in description,
                "<t:300:R>" in description,
                "https://www.google.com/search?" in description,
                store.mark_notified.call_args.args[0],
            ),
            (
                True,
                1,
                "New job digest",
                sorted(description.index(uid) for uid in ordered_uids),
                True,
                True,
                True,
                True,
                True,
                True,
                [
                    next(row for row in candidates if row["uid"] == uid)
                    for uid in ordered_uids
                ],
            ),
        )

    def test_seventeen_candidates_are_delivered_losslessly_in_two_pages(self):
        candidates = [candidate(f"job-{index:02}") for index in range(17)]
        store = mock.Mock()

        with mock.patch.object(
            job_alert,
            "post_discord",
            return_value=True,
        ) as post:
            delivered = job_alert.deliver_notification_batch(
                store,
                candidates,
                "https://discord.invalid/webhook",
            )

        sent_descriptions = [
            call.args[0][0]["description"] for call in post.call_args_list
        ]
        stamped_pages = [
            call.args[0]
            for call in store.mark_notified.call_args_list
        ]

        self.assertEqual(
            (
                delivered,
                post.call_count,
                [len(page) for page in stamped_pages],
                store.method_calls,
                all(
                    candidate_row["uid"] in "\n".join(sent_descriptions)
                    for candidate_row in candidates
                ),
            ),
            (
                True,
                2,
                [10, 7],
                [
                    mock.call.mark_notified(candidates[:10]),
                    mock.call.save(),
                    mock.call.mark_notified(candidates[10:]),
                    mock.call.save(),
                ],
                True,
            ),
        )

    def test_page_two_failure_keeps_page_one_groups_checkpointed(self):
        shared = {
            "title": "Software Engineer I",
            "company": "Example",
            "locations": ["San Francisco, CA"],
            "posted": 100,
        }
        records = {
            f"custom:{index:02}": {
                **shared,
                "uid": f"custom:{index:02}",
                "url": f"https://example.invalid/{index}",
            }
            for index in range(1, 11)
        }
        records.update({
            "gh:example:12345": {
                **shared,
                "uid": "gh:example:12345",
                "title": "Software Engineer, New Grad",
                "url": "https://job-boards.greenhouse.io/example/jobs/12345",
            },
            "simplify:wrapped": {
                **shared,
                "uid": "simplify:wrapped",
                "title": "Software Engineer, New Grad",
                "url": "https://example.invalid/jobs?gh_jid=12345",
            },
        })

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store_path = root / "jobs.json"
            annotations_path = root / "annotations.json"
            store_path.write_text(json.dumps({"jobs": records}))
            store = job_alert.Store(store_path)
            candidates = store.candidates(max_age_days=0)

            with (
                mock.patch.object(
                    job_alert,
                    "post_discord",
                    side_effect=[True, False],
                ),
                mock.patch.object(
                    job_alert,
                    "ANNOTATIONS_FILE",
                    annotations_path,
                ),
                mock.patch.object(job_alert, "now", return_value=999),
            ):
                delivered = job_alert.deliver_notification_batch(
                    store,
                    candidates,
                    "https://discord.invalid/webhook",
                )

            persisted = job_alert.Store(store_path)

        pending = {
            row["uid"]
            for row in persisted.candidates(max_age_days=0)
        }
        self.assertEqual(
            (
                delivered,
                persisted.jobs["gh:example:12345"].get("notified_at"),
                persisted.jobs["simplify:wrapped"].get("notified_at"),
                pending,
            ),
            (False, 999, 999, {"custom:10"}),
        )

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

    def test_rate_limited_page_retries_then_checkpoints_after_acceptance(self):
        rate_limited = urllib.error.HTTPError(
            "https://discord.invalid/webhook",
            429,
            "Too Many Requests",
            {},
            io.BytesIO(b'{"retry_after": 0}'),
        )
        accepted = mock.Mock()
        accepted.read.return_value = b""
        store = mock.Mock()
        candidates = [candidate("retry")]

        with (
            mock.patch(
                "urllib.request.urlopen",
                side_effect=[rate_limited, accepted],
            ) as open_url,
            mock.patch("time.sleep"),
        ):
            delivered = job_alert.deliver_notification_batch(
                store,
                candidates,
                "https://discord.invalid/webhook",
            )

        self.assertEqual(
            (delivered, open_url.call_count, store.method_calls),
            (
                True,
                2,
                [
                    mock.call.mark_notified(candidates),
                    mock.call.save(),
                ],
            ),
        )

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
    def test_scan_fails_visibly_when_a_notification_page_is_rejected(self):
        records = {
            f"custom:{index}": {
                "uid": f"custom:{index}",
                "title": "Software Engineer I",
                "company": "Example",
                "locations": ["San Francisco, CA"],
                "url": f"https://example.invalid/{index}",
            }
            for index in range(6)
        }
        args = types.SimpleNamespace(
            min_score=5,
            no_remote=False,
            dry_run=False,
            seed=False,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store_path = root / "jobs.json"
            annotations_path = root / "annotations.json"
            store_path.write_text(json.dumps({"jobs": records}))
            store = job_alert.Store(store_path)

            with (
                mock.patch.object(
                    job_alert,
                    "post_discord",
                    return_value=False,
                ),
                mock.patch.object(
                    job_alert,
                    "ANNOTATIONS_FILE",
                    annotations_path,
                ),
                mock.patch.dict(
                    job_alert.os.environ,
                    {"DISCORD_WEBHOOK": "https://discord.invalid/webhook"},
                ),
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Discord delivery failed",
                ):
                    job_alert.cmd_scan(args, store, source_fetches=[])

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
