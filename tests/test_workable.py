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


FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "workable"


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


class WorkableFetchTests(unittest.TestCase):
    def test_public_board_normalizes_every_job_and_location(self):
        with mock.patch.object(
            job_alert,
            "get_json",
            return_value=fixture("response.json"),
        ) as get_json:
            records, ok = job_alert.fetch_workable("example-energy")

        self.assertTrue(ok)
        get_json.assert_called_once_with(
            "https://www.workable.com/api/accounts/example-energy?details=true"
        )
        self.assertEqual(
            records,
            [
                {
                    "uid": "workable:example-energy:ENG1ABCDEF",
                    "title": "Software Engineer I",
                    "company": "Example Energy",
                    "locations": [
                        "San Francisco, California, United States",
                        "London, England, United Kingdom",
                    ],
                    "url": "https://apply.workable.com/j/ENG1ABCDEF",
                    "posted": 1785456000,
                    "degrees": [],
                    "category": "Engineering",
                    "source": "Workable",
                    "feed_active": True,
                },
                {
                    "uid": "workable:example-energy:ENG2ABCDEF",
                    "title": "Senior Software Engineer",
                    "company": "Example Energy",
                    "locations": ["London, England, United Kingdom"],
                    "url": "https://apply.workable.com/j/ENG2ABCDEF",
                    "posted": 1785369600,
                    "degrees": [],
                    "category": "Engineering",
                    "source": "Workable",
                    "feed_active": True,
                },
                {
                    "uid": "workable:example-energy:ML01ABCDEF",
                    "title": "Associate Machine Learning Engineer",
                    "company": "Example Energy",
                    "locations": ["Remote, United States"],
                    "url": "https://apply.workable.com/j/ML01ABCDEF",
                    "posted": 1785283200,
                    "degrees": [],
                    "category": "Machine Learning",
                    "source": "Workable",
                    "feed_active": True,
                },
            ],
        )

    def test_empty_multi_location_shape_falls_back_to_primary_location(self):
        response = fixture("response.json")
        response["jobs"] = [dict(response["jobs"][0])]
        response["jobs"][0].update({
            "locations": [],
            "city": "San Francisco",
            "state": "California",
            "country": "United States",
        })

        with mock.patch.object(job_alert, "get_json", return_value=response):
            records, ok = job_alert.fetch_workable("example-energy")

        self.assertEqual(
            (ok, records[0]["locations"]),
            (True, ["San Francisco, California, United States"]),
        )

    def test_malformed_job_fails_the_source_fetch(self):
        response = fixture("response.json")
        response["jobs"] = [{
            "title": "Software Engineer I",
            "url": "https://apply.workable.com/j/MISSING",
        }]

        with (
            mock.patch.object(job_alert, "get_json", return_value=response),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            records, ok = job_alert.fetch_workable("example-energy")

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
            records, ok = job_alert.fetch_workable("example-energy")

        self.assertEqual((records, ok), ([], False))


class WorkableConfigurationTests(unittest.TestCase):
    def test_configured_account_builds_a_source_fetch_adapter(self):
        fetches = job_alert.configured_source_fetches({
            "workable": ["renewhome"],
        })

        source = next(
            fetch for fetch in fetches
            if fetch.name == "workable/renewhome"
        )
        self.assertEqual(
            (source.prefix, source.host),
            ("workable:renewhome:", "www.workable.com"),
        )

    def test_empty_account_requires_verification_before_activation(self):
        source = next(
            fetch for fetch in job_alert.configured_source_fetches({
                "workable": ["example-energy"],
            })
            if fetch.name == "workable/example-energy"
        )

        with mock.patch.object(job_alert, "get_json", return_value={
            "name": "Example Energy",
            "jobs": [],
        }):
            result = job_alert.fetch_sources([source])[0]

        self.assertEqual(
            (result.ok, result.verification_required, result.records),
            (False, True, []),
        )


class WorkableEndToEndTests(unittest.TestCase):
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
                "workable": ["example-energy"],
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
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Discord delivery failed",
                ):
                    job_alert.cmd_scan(args, store)
                persisted = job_alert.Store(store_path)
                candidates = persisted.candidates()

        self.assertEqual(len(persisted.jobs), 3)
        self.assertEqual(
            sorted(record["uid"] for record in candidates),
            [
                "workable:example-energy:ENG1ABCDEF",
                "workable:example-energy:ML01ABCDEF",
            ],
        )
        self.assertEqual(
            candidates[0]["locations"],
            ["San Francisco, California, United States"],
        )
        self.assertEqual(
            job_alert.dedup_key(
                persisted.jobs["workable:example-energy:ENG1ABCDEF"]
            ),
            ("workable", "ENG1ABCDEF"),
        )
        post_discord.assert_called_once()


if __name__ == "__main__":
    unittest.main()
