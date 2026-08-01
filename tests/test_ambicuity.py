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


FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "ambicuity"


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


class AmbicuityFetchTests(unittest.TestCase):
    def test_public_feed_normalizes_every_record_and_preserves_source_state(self):
        with mock.patch.object(
            job_alert,
            "get_json",
            return_value=fixture("response.json"),
        ) as get_json:
            records, ok = job_alert.fetch_ambicuity()

        self.assertTrue(ok)
        get_json.assert_called_once_with(job_alert.AMBICUITY_URL)
        self.assertEqual(len(records), 5)
        self.assertEqual(records[0], {
            "uid": (
                "ambicuity:acme-software-engineer-i:"
                "d1ada3574f33920f61b42e561fcffef4"
            ),
            "title": "Software Engineer I",
            "company": "Acme",
            "locations": ["San Francisco, CA, United States"],
            "url": "https://job-boards.greenhouse.io/acme/jobs/12345",
            "posted": 1785501000,
            "degrees": [],
            "category": "Software Engineering",
            "sponsorship": "",
            "aggregator_source": "Greenhouse",
            "source": "Ambicuity",
            "feed_active": True,
        })
        self.assertEqual(
            (records[1]["sponsorship"], records[3]["feed_active"]),
            ("No sponsorship", False),
        )

    def test_nullable_company_is_retained_as_an_unknown_canonical_value(self):
        response = fixture("response.json")
        response["jobs"] = [dict(response["jobs"][0])]
        response["jobs"][0]["company"] = None
        response["meta"]["total_jobs"] = 1

        with mock.patch.object(job_alert, "get_json", return_value=response):
            records, ok = job_alert.fetch_ambicuity()

        self.assertEqual((ok, records[0]["company"]), (True, ""))

    def test_duplicate_feed_ids_keep_distinct_requisitions(self):
        response = fixture("response.json")
        first = dict(response["jobs"][0])
        second = dict(first)
        second["url"] = "https://job-boards.greenhouse.io/acme/jobs/67890"
        response["jobs"] = [first, second]
        response["meta"]["total_jobs"] = 2

        with mock.patch.object(job_alert, "get_json", return_value=response):
            records, ok = job_alert.fetch_ambicuity()

        self.assertEqual(
            (ok, [record["uid"] for record in records]),
            (
                True,
                [
                    "ambicuity:acme-software-engineer-i:"
                    "d1ada3574f33920f61b42e561fcffef4",
                    "ambicuity:acme-software-engineer-i:"
                    "0ba746bee6477c6b1161e0cebb6cd472",
                ],
            ),
        )

    def test_schema_mismatch_fails_the_source_fetch(self):
        response = fixture("response.json")
        response["meta"]["total_jobs"] = 6

        with (
            mock.patch.object(job_alert, "get_json", return_value=response),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            records, ok = job_alert.fetch_ambicuity()

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
            records, ok = job_alert.fetch_ambicuity()

        self.assertEqual((records, ok), ([], False))


class AmbicuityConfigurationTests(unittest.TestCase):
    def test_configured_feed_builds_a_source_fetch_adapter(self):
        fetches = job_alert.configured_source_fetches({
            "ambicuity": ["ambicuity/New-Grad-Jobs"],
        })

        source = next(
            fetch for fetch in fetches
            if fetch.name == "ambicuity"
        )
        self.assertEqual(
            (source.prefix, source.host),
            ("ambicuity:", "raw.githubusercontent.com"),
        )

    def test_empty_feed_requires_verification_before_activation(self):
        source = next(
            fetch for fetch in job_alert.configured_source_fetches({
                "ambicuity": ["ambicuity/New-Grad-Jobs"],
            })
            if fetch.name == "ambicuity"
        )
        empty = {
            "meta": {
                "generated_at": "2026-08-01T09:26:31.575971+00:00",
                "total_jobs": 0,
            },
            "jobs": [],
        }

        with mock.patch.object(job_alert, "get_json", return_value=empty):
            result = job_alert.fetch_sources([source])[0]

        self.assertEqual(
            (result.ok, result.verification_required, result.records),
            (False, True, []),
        )


class AmbicuityEndToEndTests(unittest.TestCase):
    def test_fixture_ingestion_groups_only_proven_cross_posts(self):
        simplify = [{
            "id": "simplify-wrapper",
            "company_name": "Acme Incorporated",
            "title": "Software Engineer, New Grad",
            "locations": ["Remote, United States"],
            "url": "https://careers.acme.example/apply?gh_jid=12345",
            "date_posted": 1785501000,
            "degrees": [],
            "category": "Software Engineering",
            "sponsorship": "",
            "active": True,
            "is_visible": True,
        }]
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
                "ambicuity": ["ambicuity/New-Grad-Jobs"],
            }))

            def fixture_api(url):
                if url == job_alert.SIMPLIFY_URL:
                    return simplify
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

        self.assertEqual(len(persisted.jobs), 6)
        self.assertEqual(
            {record["uid"] for record in candidates},
            {
                "simplify:simplify-wrapper",
                "ambicuity:acme-associate-ml-first:"
                "2e80c5e0217aaa3c0c3a60733ea37559",
                "ambicuity:acme-associate-ml-second:"
                "d727e6a57af03d2d8cdfdda2d5d828fc",
            },
        )
        self.assertEqual(
            job_alert.dedup_key(persisted.jobs["simplify:simplify-wrapper"]),
            job_alert.dedup_key(
                persisted.jobs[
                    "ambicuity:acme-software-engineer-i:"
                    "d1ada3574f33920f61b42e561fcffef4"
                ]
            ),
        )
        self.assertNotEqual(
            job_alert.dedup_key(
                persisted.jobs[
                    "ambicuity:acme-associate-ml-first:"
                    "2e80c5e0217aaa3c0c3a60733ea37559"
                ]
            ),
            job_alert.dedup_key(
                persisted.jobs[
                    "ambicuity:acme-associate-ml-second:"
                    "d727e6a57af03d2d8cdfdda2d5d828fc"
                ]
            ),
        )
        self.assertIsNotNone(
            persisted.jobs[
                "ambicuity:acme-new-grad-closed:"
                "ad7574eb19a8907db2e6b48659284358"
            ]["closed_at"]
        )
        post_discord.assert_called_once()


if __name__ == "__main__":
    unittest.main()
