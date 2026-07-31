import copy
import json
import pathlib
import tempfile
import unittest

import job_alert


class CrossPostGroupTests(unittest.TestCase):
    def test_unknown_records_ignore_presentation_and_generic_url_equality(self):
        shared = {
            "title": "Software Engineer, New Grad",
            "company": "Example",
            "locations": ["San Francisco, CA"],
        }
        payload = {
            "jobs": {
                "custom:first": {
                    **shared,
                    "uid": "custom:first",
                    "url": "https://careers.example.invalid/openings/first",
                },
                "custom:second": {
                    **shared,
                    "uid": "custom:second",
                    "url": "https://careers.example.invalid/openings/first",
                },
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        candidates = store.candidates(
            unnotified_only=False,
            max_age_days=0,
        )

        self.assertEqual(
            {candidate["uid"] for candidate in candidates},
            {"custom:first", "custom:second"},
        )

    def test_structured_greenhouse_record_groups_with_wrapper_url(self):
        payload = {
            "jobs": {
                "gh:example:12345": {
                    "uid": "gh:example:12345",
                    "title": "Software Engineer I",
                    "company": "Example",
                    "locations": ["San Francisco, CA"],
                    "url": "https://careers.example.invalid/apply",
                },
                "simplify:wrapped": {
                    "uid": "simplify:wrapped",
                    "title": "Software Engineer, New Grad",
                    "company": "Example Incorporated",
                    "locations": ["Remote - US"],
                    "url": "https://example.com/jobs?gh_jid=12345",
                },
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        candidates = store.candidates(
            unnotified_only=False,
            max_age_days=0,
        )

        self.assertEqual(
            [candidate["uid"] for candidate in candidates],
            ["simplify:wrapped"],
        )

    def test_registry_groups_structured_records_with_recognized_ats_urls(self):
        cases = [
            (
                "lever:acme:lever-123",
                "https://jobs.lever.co/acme/lever-123",
            ),
            (
                "ashby:acme:ashby-123",
                "https://jobs.ashbyhq.com/acme/ashby-123",
            ),
            (
                "workday:acme:External:JR-123",
                "https://acme.wd5.myworkdayjobs.com/wday/cxs/"
                "acme/External/job/San-Francisco/Engineer_JR-123",
            ),
            (
                "smartrecruiters:Acme:posting-123",
                "https://api.smartrecruiters.com/v1/companies/"
                "Acme/postings/posting-123",
            ),
            (
                "workable:acme:ABC123",
                "https://apply.workable.com/j/ABC123/",
            ),
            (
                "recruitee:acme:engineer-123",
                "https://acme.recruitee.com/o/engineer-123",
            ),
        ]

        for structured_uid, recognized_url in cases:
            with self.subTest(structured_uid=structured_uid):
                payload = {
                    "jobs": {
                        structured_uid: {
                            "uid": structured_uid,
                            "title": "Software Engineer I",
                            "company": "Acme",
                            "locations": ["San Francisco, CA"],
                            "url": "https://careers.acme.invalid/apply",
                        },
                        "simplify:wrapped": {
                            "uid": "simplify:wrapped",
                            "title": "Software Engineer, New Grad",
                            "company": "Acme Corporation",
                            "locations": ["Remote - US"],
                            "url": recognized_url,
                        },
                    }
                }

                with tempfile.TemporaryDirectory() as directory:
                    store_path = pathlib.Path(directory) / "jobs.json"
                    store_path.write_text(json.dumps(payload))
                    store = job_alert.Store(store_path)

                candidates = store.candidates(
                    unnotified_only=False,
                    max_age_days=0,
                )

                self.assertEqual(
                    [candidate["uid"] for candidate in candidates],
                    ["simplify:wrapped"],
                )

    def test_notified_sibling_suppresses_the_entire_cross_post_group(self):
        payload = {
            "jobs": {
                "gh:example:12345": {
                    "uid": "gh:example:12345",
                    "title": "Software Engineer, New Grad",
                    "company": "Example",
                    "locations": ["London, UK"],
                    "url": "https://job-boards.greenhouse.io/example/jobs/12345",
                    "closed_at": 1_700_000_000,
                    "notified_at": 1_690_000_000,
                },
                "simplify:wrapped": {
                    "uid": "simplify:wrapped",
                    "title": "Software Engineer, New Grad",
                    "company": "Example",
                    "locations": ["San Francisco, CA"],
                    "url": "https://example.com/jobs?gh_jid=12345",
                    "closed_at": None,
                },
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        self.assertEqual(store.candidates(max_age_days=0), [])

    def test_representative_uses_score_then_freshness_then_stable_uid(self):
        shared = {
            "title": "Software Engineer, New Grad",
            "company": "Example",
            "locations": ["San Francisco, CA"],
        }
        payload = {
            "jobs": {
                "source:old": {
                    **shared,
                    "uid": "source:old",
                    "url": "https://example.com/jobs?gh_jid=12345",
                    "posted": 100,
                },
                "source:z-new": {
                    **shared,
                    "uid": "source:z-new",
                    "url": "https://example.com/jobs?gh_jid=12345",
                    "posted": 200,
                },
                "source:a-new": {
                    **shared,
                    "uid": "source:a-new",
                    "url": "https://example.com/jobs?gh_jid=12345",
                    "posted": 200,
                },
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        candidates = store.candidates(
            unnotified_only=False,
            max_age_days=0,
        )

        self.assertEqual(
            [candidate["uid"] for candidate in candidates],
            ["source:a-new"],
        )

    def test_distinct_ashby_and_workday_requisitions_do_not_collapse(self):
        cases = [
            ("ashby:acme:req-1", "ashby:acme:req-2"),
            (
                "workday:acme:External:req-1",
                "workday:acme:External:req-2",
            ),
        ]
        shared = {
            "title": "Software Engineer, New Grad",
            "company": "Acme",
            "locations": ["San Francisco, CA"],
        }

        for first_uid, second_uid in cases:
            with self.subTest(first_uid=first_uid):
                payload = {
                    "jobs": {
                        first_uid: {**shared, "uid": first_uid},
                        second_uid: {**shared, "uid": second_uid},
                    }
                }
                with tempfile.TemporaryDirectory() as directory:
                    store_path = pathlib.Path(directory) / "jobs.json"
                    store_path.write_text(json.dumps(payload))
                    store = job_alert.Store(store_path)

                candidates = store.candidates(
                    unnotified_only=False,
                    max_age_days=0,
                )

                self.assertEqual(
                    {candidate["uid"] for candidate in candidates},
                    {first_uid, second_uid},
                )

    def test_identifier_tokens_are_scoped_to_their_tenant(self):
        cases = [
            ("lever:first:same-token", "lever:second:same-token"),
            ("ashby:first:same-token", "ashby:second:same-token"),
            (
                "workday:first:External:same-token",
                "workday:second:External:same-token",
            ),
            (
                "smartrecruiters:first:same-token",
                "smartrecruiters:second:same-token",
            ),
            (
                "smartrecruiters:Acme:same-token",
                "smartrecruiters:acme:same-token",
            ),
            ("recruitee:first:same-token", "recruitee:second:same-token"),
        ]
        shared = {
            "title": "Software Engineer, New Grad",
            "company": "Example",
            "locations": ["San Francisco, CA"],
        }

        for first_uid, second_uid in cases:
            with self.subTest(first_uid=first_uid):
                payload = {
                    "jobs": {
                        first_uid: {**shared, "uid": first_uid},
                        second_uid: {**shared, "uid": second_uid},
                    }
                }
                with tempfile.TemporaryDirectory() as directory:
                    store_path = pathlib.Path(directory) / "jobs.json"
                    store_path.write_text(json.dumps(payload))
                    store = job_alert.Store(store_path)

                candidates = store.candidates(
                    unnotified_only=False,
                    max_age_days=0,
                )

                self.assertEqual(
                    {candidate["uid"] for candidate in candidates},
                    {first_uid, second_uid},
                )

    def test_structured_identity_takes_priority_over_a_conflicting_url(self):
        shared = {
            "title": "Software Engineer, New Grad",
            "company": "Example",
            "locations": ["San Francisco, CA"],
        }
        payload = {
            "jobs": {
                "gh:example:111": {
                    **shared,
                    "uid": "gh:example:111",
                    "url": "https://example.com/jobs?gh_jid=222",
                },
                "wrapper:111": {
                    **shared,
                    "uid": "wrapper:111",
                    "url": "https://example.com/jobs?gh_jid=111",
                },
                "wrapper:222": {
                    **shared,
                    "uid": "wrapper:222",
                    "url": "https://example.com/jobs?gh_jid=222",
                },
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        candidates = store.candidates(
            unnotified_only=False,
            max_age_days=0,
        )

        self.assertEqual(
            {candidate["uid"] for candidate in candidates},
            {"gh:example:111", "wrapper:222"},
        )

    def test_notification_stamps_group_without_merging_canonical_records(self):
        payload = {
            "jobs": {
                "gh:example:12345": {
                    "uid": "gh:example:12345",
                    "title": "Software Engineer I",
                    "company": "Example",
                    "locations": ["San Francisco, CA"],
                    "url": "https://job-boards.greenhouse.io/example/jobs/12345",
                    "source": "Greenhouse",
                },
                "simplify:wrapped": {
                    "uid": "simplify:wrapped",
                    "title": "Software Engineer, New Grad",
                    "company": "Example Incorporated",
                    "locations": ["Remote - US"],
                    "url": "https://example.com/jobs?gh_jid=12345",
                    "source": "Simplify",
                },
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        before = copy.deepcopy(store.jobs)
        store.mark_notified(store.candidates(max_age_days=0), timestamp=123)
        without_notification_state = {
            uid: {
                key: value
                for key, value in record.items()
                if key != "notified_at"
            }
            for uid, record in store.jobs.items()
        }

        self.assertEqual(
            (
                without_notification_state,
                {record.get("notified_at") for record in store.jobs.values()},
            ),
            (before, {123}),
        )

    def test_group_is_live_when_any_qualifying_member_is_live(self):
        payload = {
            "jobs": {
                "gh:example:12345": {
                    "uid": "gh:example:12345",
                    "title": "Software Engineer, New Grad",
                    "company": "Example",
                    "locations": ["San Francisco, CA"],
                    "url": "https://job-boards.greenhouse.io/example/jobs/12345",
                    "closed_at": 1_700_000_000,
                },
                "simplify:live": {
                    "uid": "simplify:live",
                    "title": "Software Engineer I",
                    "company": "Example",
                    "locations": ["San Francisco, CA"],
                    "url": "https://example.com/jobs?gh_jid=12345",
                    "closed_at": None,
                },
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        candidates = store.candidates(
            unnotified_only=False,
            max_age_days=0,
        )

        self.assertEqual(
            [candidate["uid"] for candidate in candidates],
            ["simplify:live"],
        )


if __name__ == "__main__":
    unittest.main()
