import contextlib
import io
import json
import pathlib
import tempfile
import types
import unittest
import urllib.error
from unittest import mock

import job_alert


FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "recruitee"


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


class RecruiteeFetchTests(unittest.TestCase):
    def test_public_board_normalizes_every_offer_and_location(self):
        with mock.patch.object(
            job_alert,
            "get_json",
            return_value=fixture("response.json"),
        ) as get_json:
            records, ok = job_alert.fetch_recruitee("example-aerospace")

        self.assertTrue(ok)
        get_json.assert_called_once_with(
            "https://example-aerospace.recruitee.com/api/offers/"
        )
        self.assertEqual(
            records,
            [
                {
                    "uid": "recruitee:example-aerospace:eng1a",
                    "recruitee_slug": "software-engineer-i",
                    "title": "Software Engineer I",
                    "company": "Example Aerospace",
                    "locations": [
                        "San Carlos, California, United States",
                        "London, England, United Kingdom",
                    ],
                    "url": "https://example-aerospace.recruitee.com/o/software-engineer-i",
                    "posted": 1785501000,
                    "degrees": ["Bachelor's"],
                    "category": "Software Engineering",
                    "source": "Recruitee",
                    "feed_active": True,
                },
                {
                    "uid": "recruitee:example-aerospace:eng2b",
                    "recruitee_slug": "senior-software-engineer",
                    "title": "Senior Software Engineer",
                    "company": "Example Aerospace",
                    "locations": ["London, England, United Kingdom"],
                    "url": "https://example-aerospace.recruitee.com/o/senior-software-engineer",
                    "posted": 1785402000,
                    "degrees": [],
                    "category": "Software Engineering",
                    "source": "Recruitee",
                    "feed_active": True,
                },
                {
                    "uid": "recruitee:example-aerospace:ml01c",
                    "recruitee_slug": "associate-machine-learning-engineer",
                    "title": "Associate Machine Learning Engineer",
                    "company": "Example Aerospace",
                    "locations": ["Remote, United States"],
                    "url": "https://example-aerospace.recruitee.com/o/associate-machine-learning-engineer",
                    "posted": 1785339900,
                    "degrees": [],
                    "category": "Machine Learning",
                    "source": "Recruitee",
                    "feed_active": True,
                },
            ],
        )

    def test_title_slug_change_preserves_the_source_uid(self):
        original = fixture("response.json")
        original["offers"] = [dict(original["offers"][0])]
        renamed = fixture("response.json")
        renamed["offers"] = [dict(renamed["offers"][0])]
        renamed["offers"][0].update({
            "title": "Embedded Software Engineer I",
            "slug": "embedded-software-engineer-i",
            "careers_url": (
                "https://example-aerospace.recruitee.com/o/"
                "embedded-software-engineer-i"
            ),
        })

        with mock.patch.object(
            job_alert,
            "get_json",
            side_effect=[original, renamed],
        ):
            before, _ = job_alert.fetch_recruitee("example-aerospace")
            after, _ = job_alert.fetch_recruitee("example-aerospace")

        self.assertEqual(
            (before[0]["uid"], after[0]["uid"]),
            (
                "recruitee:example-aerospace:eng1a",
                "recruitee:example-aerospace:eng1a",
            ),
        )
        self.assertEqual(
            job_alert.dedup_key(after[0]),
            ("recruitee", "example-aerospace", "embedded-software-engineer-i"),
        )

    def test_malformed_offer_fails_the_source_fetch(self):
        response = {"offers": [{
            "title": "Software Engineer I",
            "company_name": "Example Aerospace",
        }]}

        with (
            mock.patch.object(job_alert, "get_json", return_value=response),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            records, ok = job_alert.fetch_recruitee("example-aerospace")

        self.assertEqual((records, ok), ([], False))

    def test_transport_failure_returns_no_closure_evidence(self):
        with (
            mock.patch.object(
                job_alert,
                "get_json",
                side_effect=urllib.error.URLError("offline"),
            ),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            records, ok = job_alert.fetch_recruitee("example-aerospace")

        self.assertEqual((records, ok), ([], False))


class RecruiteeConfigurationTests(unittest.TestCase):
    def test_configured_board_builds_a_source_fetch_adapter(self):
        fetches = job_alert.configured_source_fetches({
            "recruitee": ["aetherflux"],
        })

        source = next(
            fetch for fetch in fetches
            if fetch.name == "recruitee/aetherflux"
        )
        self.assertEqual(
            (source.prefix, source.host),
            ("recruitee:aetherflux:", "aetherflux.recruitee.com"),
        )

    def test_empty_board_requires_verification_before_activation(self):
        source = next(
            fetch for fetch in job_alert.configured_source_fetches({
                "recruitee": ["example-aerospace"],
            })
            if fetch.name == "recruitee/example-aerospace"
        )

        with mock.patch.object(
            job_alert,
            "get_json",
            return_value={"offers": []},
        ):
            result = job_alert.fetch_sources([source])[0]

        self.assertEqual(
            (result.ok, result.verification_required, result.records),
            (False, True, []),
        )


class RecruiteeEndToEndTests(unittest.TestCase):
    def test_fixture_response_becomes_persisted_records_and_us_candidates(self):
        args = types.SimpleNamespace(
            min_score=5,
            no_remote=False,
            dry_run=False,
            seed=False,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store_path = root / "jobs.json"
            source_path = root / "sources.json"
            source_path.write_text(json.dumps({
                "recruitee": ["example-aerospace"],
            }))

            def fixture_api(url):
                if url == job_alert.SIMPLIFY_URL:
                    return []
                return fixture("response.json")

            with (
                mock.patch.object(job_alert, "SOURCES_FILE", source_path),
                mock.patch.object(
                    job_alert,
                    "ANNOTATIONS_FILE",
                    root / "annotations.json",
                ),
                mock.patch.object(job_alert, "get_json", side_effect=fixture_api),
                mock.patch.object(
                    job_alert,
                    "post_discord",
                    return_value=False,
                ) as post_discord,
                mock.patch.object(job_alert, "now", return_value=1785542400),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                store = job_alert.Store(store_path)
                job_alert.cmd_scan(args, store)
                persisted = job_alert.Store(store_path)
                candidates = persisted.candidates()

        self.assertEqual(len(persisted.jobs), 3)
        self.assertEqual(
            sorted(record["uid"] for record in candidates),
            [
                "recruitee:example-aerospace:eng1a",
                "recruitee:example-aerospace:ml01c",
            ],
        )
        self.assertEqual(
            candidates[0]["locations"],
            ["San Carlos, California, United States"],
        )
        self.assertEqual(
            job_alert.dedup_key(
                persisted.jobs["recruitee:example-aerospace:eng1a"]
            ),
            ("recruitee", "example-aerospace", "software-engineer-i"),
        )
        post_discord.assert_called_once()


if __name__ == "__main__":
    unittest.main()
