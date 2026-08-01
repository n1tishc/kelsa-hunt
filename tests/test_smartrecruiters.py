import json
import contextlib
import io
import pathlib
import tempfile
import types
import unittest
import urllib.error
from unittest import mock

import job_alert


FIXTURES = pathlib.Path(__file__).parent / "fixtures" / "smartrecruiters"


def fixture(name):
    return json.loads((FIXTURES / name).read_text())


def smartrecruiters_fixture_api():
    pages = {0: fixture("page-0.json"), 2: fixture("page-2.json")}
    details = fixture("details.json")

    def get(url):
        if url == job_alert.SIMPLIFY_URL:
            return []
        if "/postings?" in url:
            offset = int(url.rsplit("offset=", 1)[1])
            return pages[offset]
        return details[url.rsplit("/", 1)[1]]

    return get


class SmartRecruitersFetchTests(unittest.TestCase):
    def test_fetches_all_pages_and_normalizes_records(self):
        with mock.patch.object(
            job_alert,
            "get_json",
            side_effect=smartrecruiters_fixture_api(),
        ):
            records, ok = job_alert.fetch_smartrecruiters("ExampleCo", page_size=2)

        self.assertTrue(ok)
        self.assertEqual(
            records,
            [
                {
                    "uid": "smartrecruiters:ExampleCo:744000100000001",
                    "title": "Software Engineer I",
                    "company": "Example Co",
                    "locations": ["San Francisco, CA, United States"],
                    "url": "https://jobs.smartrecruiters.com/ExampleCo/744000100000001-software-engineer-i",
                    "posted": 1785501000,
                    "degrees": [],
                    "category": "Engineering",
                    "source": "SmartRecruiters",
                    "feed_active": True,
                },
                {
                    "uid": "smartrecruiters:ExampleCo:744000100000002",
                    "title": "Senior Software Engineer",
                    "company": "Example Co",
                    "locations": ["London, United Kingdom"],
                    "url": "https://jobs.smartrecruiters.com/ExampleCo/744000100000002-senior-software-engineer",
                    "posted": 1785398400,
                    "degrees": [],
                    "category": "Engineering",
                    "source": "SmartRecruiters",
                    "feed_active": True,
                },
                {
                    "uid": "smartrecruiters:ExampleCo:744000100000003",
                    "title": "Associate Machine Learning Engineer",
                    "company": "Example Co",
                    "locations": ["Remote, United States"],
                    "url": "https://jobs.smartrecruiters.com/ExampleCo/744000100000003-associate-machine-learning-engineer",
                    "posted": 1785316500,
                    "degrees": [],
                    "category": "Machine Learning",
                    "source": "SmartRecruiters",
                    "feed_active": True,
                },
            ],
        )

    def test_required_field_omission_fails_the_source_fetch(self):
        malformed_page = {
            "offset": 0,
            "limit": 100,
            "totalFound": 1,
            "content": [
                {
                    "id": "744000100000004",
                    "company": {"identifier": "ExampleCo", "name": "Example Co"},
                    "location": {"fullLocation": "San Francisco, CA, United States"},
                    "postingUrl": "https://jobs.smartrecruiters.com/ExampleCo/744000100000004",
                }
            ],
        }

        with mock.patch.object(job_alert, "get_json", return_value=malformed_page):
            records, ok = job_alert.fetch_smartrecruiters("ExampleCo")

        self.assertEqual((records, ok), ([], False))

    def test_detail_resource_fills_fields_omitted_from_the_list(self):
        page = fixture("page-0.json")
        page["content"] = [dict(page["content"][0])]
        page["content"][0].pop("name")
        page["content"][0]["company"] = {"identifier": "ExampleCo"}
        page["content"][0]["location"] = {"country": "us"}
        page["totalFound"] = 1
        detail = dict(fixture("details.json")["744000100000001"])
        detail.update({
            "name": "Software Engineer I",
            "company": {"identifier": "ExampleCo", "name": "Example Co"},
            "location": {
                "fullLocation": "San Francisco, CA, United States",
            },
        })

        with mock.patch.object(
            job_alert,
            "get_json",
            side_effect=[page, detail],
        ):
            records, ok = job_alert.fetch_smartrecruiters("ExampleCo")

        self.assertEqual(
            (ok, records[0]["title"], records[0]["locations"]),
            (True, "Software Engineer I", ["San Francisco, CA, United States"]),
        )

    def test_transport_failure_returns_no_closure_evidence(self):
        with (
            mock.patch.object(
                job_alert,
                "get_json",
                side_effect=urllib.error.URLError("offline"),
            ),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            records, ok = job_alert.fetch_smartrecruiters("ExampleCo")

        self.assertEqual((records, ok), ([], False))


class SmartRecruitersConfigurationTests(unittest.TestCase):
    def test_configured_board_builds_a_source_fetch_adapter(self):
        fetches = job_alert.configured_source_fetches({
            "smartrecruiters": ["Visa"],
        })

        source = next(
            fetch for fetch in fetches
            if fetch.name == "smartrecruiters/Visa"
        )
        self.assertEqual(
            (source.prefix, source.host),
            ("smartrecruiters:Visa:", "api.smartrecruiters.com"),
        )

    def test_empty_board_requires_verification_before_activation(self):
        source = next(
            fetch for fetch in job_alert.configured_source_fetches({
                "smartrecruiters": ["ExampleCo"],
            })
            if fetch.name == "smartrecruiters/ExampleCo"
        )
        empty_page = {
            "offset": 0,
            "limit": 100,
            "totalFound": 0,
            "content": [],
        }

        with mock.patch.object(job_alert, "get_json", return_value=empty_page):
            result = job_alert.fetch_sources([source])[0]

        self.assertEqual(
            (result.ok, result.verification_required, result.records),
            (False, True, []),
        )


class SmartRecruitersEndToEndTests(unittest.TestCase):
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
                "smartrecruiters": ["ExampleCo"],
            }))
            with (
                mock.patch.object(job_alert, "SOURCES_FILE", source_path),
                mock.patch.object(job_alert, "ANNOTATIONS_FILE", root / "annotations.json"),
                mock.patch.object(
                    job_alert,
                    "get_json",
                    side_effect=smartrecruiters_fixture_api(),
                ),
                mock.patch.object(job_alert, "post_discord", return_value=False),
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
                "smartrecruiters:ExampleCo:744000100000001",
                "smartrecruiters:ExampleCo:744000100000003",
            ],
        )
        self.assertEqual(
            persisted.jobs["smartrecruiters:ExampleCo:744000100000001"]["source"],
            "SmartRecruiters",
        )


if __name__ == "__main__":
    unittest.main()
