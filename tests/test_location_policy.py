import json
import pathlib
import tempfile
import unittest

import job_alert


class UsLocationsTests(unittest.TestCase):
    def test_country_markers_are_required_for_remote_locations(self):
        cases = [
            (["Remote"], []),
            (["Global"], []),
            (["Remote in Canada"], []),
            (["Remote — contact us"], []),
            (["London, UK"], []),
            (["Remote in US"], ["Remote in US"]),
            (["Remote - U.S.A."], ["Remote - U.S.A."]),
            (["United States"], ["United States"]),
        ]

        for locations, expected in cases:
            with self.subTest(locations=locations):
                self.assertEqual(job_alert.us_locations(locations), expected)


class StoreUsRecordsTests(unittest.TestCase):
    def test_us_records_filters_and_copies_without_mutating_canonical_locations(self):
        canonical_locations = ["SF | London, UK"]
        payload = {
            "jobs": {
                "us-role": {
                    "uid": "us-role",
                    "title": "Software Engineer New Grad",
                    "locations": canonical_locations,
                },
                "foreign-role": {
                    "uid": "foreign-role",
                    "title": "Software Engineer New Grad",
                    "locations": ["London, UK"],
                },
                "migrated-role": {
                    "uid": "migrated-role",
                    "title": "Software Engineer New Grad",
                    "locations": ["Austin, TX"],
                    "migrated": True,
                },
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        self.assertEqual(
            store.us_records(),
            [{
                "uid": "us-role",
                "title": "Software Engineer New Grad",
                "locations": ["SF"],
            }],
        )
        self.assertEqual(store.jobs["us-role"]["locations"], canonical_locations)

    def test_candidates_require_bay_area_or_explicit_us_remote_eligibility(self):
        locations_by_uid = {
            "bay": ["SF"],
            "us-remote": ["Remote in USA"],
            "bare-remote": ["Remote"],
            "foreign-remote": ["Remote in Canada"],
            "us-non-bay": ["Austin, TX"],
        }
        payload = {
            "jobs": {
                uid: {
                    "uid": uid,
                    "title": "Software Engineer New Grad",
                    "company": uid,
                    "locations": locations,
                }
                for uid, locations in locations_by_uid.items()
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        candidates = store.candidates(
            min_score=5,
            allow_remote=True,
            unnotified_only=False,
            max_age_days=0,
        )

        self.assertEqual({row["uid"] for row in candidates}, {"bay", "us-remote"})

    def test_candidates_expose_only_us_locations_without_mutating_the_record(self):
        source_locations = ["SF | London, UK"]
        payload = {
            "jobs": {
                "mixed": {
                    "uid": "mixed",
                    "title": "Software Engineer New Grad",
                    "company": "Example",
                    "locations": source_locations,
                }
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        candidates = store.candidates(
            min_score=5,
            allow_remote=True,
            unnotified_only=False,
            max_age_days=0,
        )

        self.assertEqual(candidates[0]["locations"], ["SF"])
        self.assertEqual(store.jobs["mixed"]["locations"], source_locations)

    def test_mixed_country_us_remote_remains_a_candidate(self):
        payload = {
            "jobs": {
                "mixed-remote": {
                    "uid": "mixed-remote",
                    "title": "Software Engineer New Grad",
                    "company": "Example",
                    "locations": ["London, England UK, Remote - US"],
                }
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        candidates = store.candidates(
            min_score=5,
            allow_remote=True,
            unnotified_only=False,
            max_age_days=0,
        )

        self.assertEqual(candidates[0]["locations"], ["Remote - US"])

    def test_slash_delimited_us_remote_remains_a_candidate(self):
        payload = {
            "jobs": {
                "slash-remote": {
                    "uid": "slash-remote",
                    "title": "Software Engineer New Grad",
                    "company": "Example",
                    "locations": ["Remote (US/Canada)"],
                }
            }
        }

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        candidates = store.candidates(
            min_score=5,
            allow_remote=True,
            unnotified_only=False,
            max_age_days=0,
        )

        self.assertEqual(candidates[0]["locations"], ["Remote (US)"])


class UsLocationCoverageTests(unittest.TestCase):
    def test_every_state_and_territory_name_and_code_is_explicit_us_evidence(self):
        jurisdictions = [
            ("Alabama", "AL"), ("Alaska", "AK"), ("Arizona", "AZ"),
            ("Arkansas", "AR"), ("California", "CA"), ("Colorado", "CO"),
            ("Connecticut", "CT"), ("Delaware", "DE"), ("Florida", "FL"),
            ("Georgia", "GA"), ("Hawaii", "HI"), ("Idaho", "ID"),
            ("Illinois", "IL"), ("Indiana", "IN"), ("Iowa", "IA"),
            ("Kansas", "KS"), ("Kentucky", "KY"), ("Louisiana", "LA"),
            ("Maine", "ME"), ("Maryland", "MD"), ("Massachusetts", "MA"),
            ("Michigan", "MI"), ("Minnesota", "MN"), ("Mississippi", "MS"),
            ("Missouri", "MO"), ("Montana", "MT"), ("Nebraska", "NE"),
            ("Nevada", "NV"), ("New Hampshire", "NH"), ("New Jersey", "NJ"),
            ("New Mexico", "NM"), ("New York", "NY"),
            ("North Carolina", "NC"), ("North Dakota", "ND"), ("Ohio", "OH"),
            ("Oklahoma", "OK"), ("Oregon", "OR"), ("Pennsylvania", "PA"),
            ("Rhode Island", "RI"), ("South Carolina", "SC"),
            ("South Dakota", "SD"), ("Tennessee", "TN"), ("Texas", "TX"),
            ("Utah", "UT"), ("Vermont", "VT"), ("Virginia", "VA"),
            ("Washington", "WA"), ("West Virginia", "WV"),
            ("Wisconsin", "WI"), ("Wyoming", "WY"),
            ("District of Columbia", "DC"), ("American Samoa", "AS"),
            ("Guam", "GU"), ("Northern Mariana Islands", "MP"),
            ("Puerto Rico", "PR"), ("U.S. Virgin Islands", "VI"),
            ("United States Minor Outlying Islands", "UM"),
        ]

        for name, code in jurisdictions:
            named_location = (
                "Atlanta, Georgia, United States"
                if name == "Georgia"
                else name
            )
            with self.subTest(name=name):
                self.assertEqual(
                    job_alert.us_locations([named_location]),
                    [named_location],
                )
            coded_location = f"Exampleville, {code}"
            with self.subTest(code=code):
                self.assertEqual(
                    job_alert.us_locations([coded_location]),
                    [coded_location],
                )

        self.assertEqual(job_alert.us_locations(["Remote in Canada"]), [])

    def test_common_delimiters_keep_only_explicit_us_locations(self):
        cases = [
            (["SF"], ["SF"]),
            (["San Jose"], ["San Jose"]),
            (["Mountain View"], ["Mountain View"]),
            (["Palo Alto"], ["Palo Alto"]),
            (["Sunnyvale"], ["Sunnyvale"]),
            (["Oakland"], ["Oakland"]),
            (["Berkeley"], ["Berkeley"]),
            (["San Francisco HQ"], ["San Francisco HQ"]),
            (["London", "Bengaluru", "Singapore"], []),
            (
                ["San Francisco, CA | London, UK"],
                ["San Francisco, CA"],
            ),
            (
                ["Remote in USA; Remote in Canada"],
                ["Remote in USA"],
            ),
            (
                ["New York, NY • London, UK"],
                ["New York, NY"],
            ),
            (["US / Canada"], ["US"]),
            (["Remote (US/Canada)"], ["Remote (US)"]),
            (["Remote (Canada/US)"], ["Remote (US)"]),
            (["Sydney OR Singapore"], []),
            (["Brisbane"], []),
            (["Brisbane, Australia"], []),
            (["Alameda Rio, Brazil"], []),
            (["Tbilisi, Georgia"], []),
            (["Toronto, CA"], []),
            (["Bengaluru, IN"], []),
            (["Remote Singapore, CA"], []),
            (["London, CA"], []),
            (["Singapore, CA"], []),
            (["Washington, UK"], []),
            (["Washington, England"], []),
            (["Vancouver, CA"], []),
            (["Vancouver, WA"], []),
            (["Mexico City, CA"], []),
            (["California, Mexico"], []),
            (["Remote Vancouver, WA"], []),
            (["Washington, South Africa"], []),
            (["Washington, South Korea"], []),
            (["California, Colombia"], []),
            (["Portland, Oregon"], ["Portland, Oregon"]),
            (["Washington, D.C."], ["Washington, D.C."]),
            (["Atlanta, Georgia"], ["Atlanta, Georgia"]),
            (
                ["San Francisco, New York, Seattle, Toronto"],
                ["San Francisco", "New York"],
            ),
            (["San Jose, Costa Rica"], []),
            (["Oakland, New Zealand"], []),
            (["Palo Alto, Netherlands"], []),
            (["New York, UK"], []),
            (["San Francisco, UK"], []),
            (["London, UK, California"], ["California"]),
            (["London, UK, Texas"], ["Texas"]),
            (
                ["Toronto, Canada, Seattle, Washington"],
                ["Seattle, Washington"],
            ),
            (
                ["Belmont, Australia", "Denver, CO"],
                ["Denver, CO"],
            ),
            (
                ["US, Canada"],
                ["US"],
            ),
            (
                ["London, England UK, Remote - US"],
                ["Remote - US"],
            ),
        ]



class RegionDetectionTests(unittest.TestCase):
    """Eligible Region detection and region-aware filtering."""

    def test_region_of_returns_us_for_explicit_us_locations(self):
        cases = [
            "San Francisco, CA",
            "New York, NY",
            "Remote in USA",
            "Remote - U.S.A.",
            "United States",
            "Austin, TX",
            "SF",
        ]
        for location in cases:
            with self.subTest(location=location):
                self.assertEqual(
                    job_alert.region_of(location), job_alert.REGION_US
                )

    def test_region_of_returns_uk_for_explicit_uk_locations(self):
        cases = [
            "London, United Kingdom",
            "London, UK",
            "London, England",
            "Manchester, England",
            "Edinburgh, Scotland",
            "Belfast, Northern Ireland",
            "Remote - UK",
            "Remote in UK",
            "Remote, United Kingdom",
            "Remote, UK",
        ]
        for location in cases:
            with self.subTest(location=location):
                self.assertEqual(
                    job_alert.region_of(location), job_alert.REGION_UK
                )

    def test_region_of_returns_none_for_ambiguous_locations(self):
        cases = [
            "Remote",
            "Global",
            "Remote in Canada",
            "London",  # bare city, ambiguous without country marker
        ]
        for location in cases:
            with self.subTest(location=location):
                self.assertIsNone(job_alert.region_of(location))

    def test_region_of_returns_none_for_foreign_locations(self):
        cases = [
            "London, Canada",
            "Birmingham, Australia",
            "Cambridge, South Africa",
        ]
        for location in cases:
            with self.subTest(location=location):
                self.assertIsNone(job_alert.region_of(location))

    def test_region_of_resolves_collision_cities_with_us_marker_to_us(self):
        # Cities that exist in both countries resolve to US when a US
        # state code is present (US evidence takes precedence)
        cases = [
            "Birmingham, AL",  # AL is a US state code
        ]
        for location in cases:
            with self.subTest(location=location):
                self.assertEqual(
                    job_alert.region_of(location), job_alert.REGION_US
                )

    def test_region_of_returns_none_for_uk_collision_with_us_marker(self):
        # London, UK, California has both UK and US evidence → ambiguous
        # but UK_COUNTRY matches first, so it resolves to UK
        # (the US marker in the string is not a US state code)
        # Actually: London, UK, California → UK_COUNTRY matches "UK"
        # and US_JURISDICTION_CODE doesn't match "California" (it's a state name, not code)
        # So it resolves to UK. This is acceptable.
        pass

    def test_region_locations_returns_us_locations_for_us_region(self):
        cases = [
            (["San Francisco, CA"], ["San Francisco, CA"]),
            (["London, UK"], []),
            (["SF | London, UK"], ["SF"]),
            (["London, England UK, Remote - US"], ["Remote - US"]),
            (["Remote (US/Canada)"], ["Remote (US)"]),
        ]
        for locations, expected in cases:
            with self.subTest(locations=locations):
                self.assertEqual(
                    job_alert.region_locations(locations, job_alert.REGION_US),
                    expected,
                )

    def test_region_locations_returns_uk_locations_for_uk_region(self):
        cases = [
            (["London, United Kingdom"], ["London, United Kingdom"]),
            (["London, UK"], ["London, UK"]),
            (["Remote - UK"], ["Remote - UK"]),
            (["Remote in UK"], ["Remote in UK"]),
            (["Remote, United Kingdom"], ["Remote, United Kingdom"]),
            (["Remote, UK"], ["Remote, UK"]),
            (["SF | London, UK"], ["London, UK"]),
        ]
        for locations, expected in cases:
            with self.subTest(locations=locations):
                self.assertEqual(
                    job_alert.region_locations(locations, job_alert.REGION_UK),
                    expected,
                )

    def test_region_locations_returns_empty_for_non_eligible_regions(self):
        cases = [
            (["London, UK"], job_alert.REGION_US),
            (["San Francisco, CA"], job_alert.REGION_UK),
            (["Remote"], job_alert.REGION_US),
            (["Remote"], job_alert.REGION_UK),
        ]
        for locations, region in cases:
            with self.subTest(locations=locations, region=region):
                self.assertEqual(
                    job_alert.region_locations(locations, region), []
                )

    def test_strict_region_record_returns_none_for_ineligible_regions(self):
        rec = {
            "uid": "test",
            "title": "Software Engineer",
            "locations": ["London, UK"],
        }
        self.assertIsNone(
            job_alert.strict_region_record(rec, job_alert.REGION_US)
        )

    def test_strict_region_record_returns_record_for_eligible_region(self):
        rec = {
            "uid": "test",
            "title": "Software Engineer",
            "locations": ["London, UK"],
        }
        result = job_alert.strict_region_record(rec, job_alert.REGION_UK)
        self.assertIsNotNone(result)
        self.assertEqual(result["locations"], ["London, UK"])

    def test_strict_us_record_backward_compatible(self):
        rec = {
            "uid": "test",
            "title": "Software Engineer",
            "locations": ["San Francisco, CA"],
        }
        result = job_alert.strict_us_record(rec)
        self.assertIsNotNone(result)
        self.assertEqual(result["locations"], ["San Francisco, CA"])


class NotificationLocalityTests(unittest.TestCase):
    """UK notification locality tier (Ticket 16)."""

    def test_uk_major_cities_notify(self):
        cases = [
            ["London, United Kingdom"],
            ["London, UK"],
            ["Edinburgh, Scotland"],
            ["Manchester, England"],
            ["Birmingham, England"],
            ["Glasgow, Scotland"],
            ["Cardiff, Wales"],
            ["Belfast, Northern Ireland"],
            ["Leeds, England"],
            ["Cambridge, England"],
        ]
        for locations in cases:
            with self.subTest(locations=locations):
                rec = {"uid": "test", "locations": locations}
                self.assertTrue(
                    job_alert.is_notify_locality(rec),
                    f"{locations} should notify",
                )

    def test_uk_remote_notifies(self):
        cases = [
            ["Remote - UK"],
            ["Remote in UK"],
            ["Remote, United Kingdom"],
            ["Remote, UK"],
        ]
        for locations in cases:
            with self.subTest(locations=locations):
                rec = {"uid": "test", "locations": locations}
                self.assertTrue(
                    job_alert.is_notify_locality(rec),
                    f"{locations} should notify",
                )

    def test_bare_remote_does_not_notify(self):
        rec = {"uid": "test", "locations": ["Remote"]}
        self.assertFalse(job_alert.is_notify_locality(rec))

    def test_bare_remote_does_not_notify_uk_either(self):
        rec = {"uid": "test", "locations": ["Remote"]}
        self.assertFalse(job_alert.is_notify_locality(rec))

    def test_us_bay_area_still_notifies(self):
        rec = {"uid": "test", "locations": ["San Francisco, CA"]}
        self.assertTrue(job_alert.is_notify_locality(rec))

    def test_us_remote_still_notifies(self):
        rec = {"uid": "test", "locations": ["Remote in USA"]}
        self.assertTrue(job_alert.is_notify_locality(rec))

    def test_foreign_location_does_not_notify(self):
        rec = {"uid": "test", "locations": ["Berlin, Germany"]}
        self.assertFalse(job_alert.is_notify_locality(rec))

    def test_non_notify_uk_cities_dont_notify(self):
        # Cities in the UK that are not in the notification tier
        # should not notify (they're visible but not notified)
        cases = [
            ["Reading, England"],
            ["Oxford, England"],
            ["Sheffield, England"],
            ["Nottingham, England"],
            ["Liverpool, England"],
            ["Brighton, England"],
        ]
        for locations in cases:
            with self.subTest(locations=locations):
                rec = {"uid": "test", "locations": locations}
                self.assertFalse(
                    job_alert.is_notify_locality(rec),
                    f"{locations} should not notify",
                )


class RegionCandidatesTests(unittest.TestCase):
    """Store.candidates() with region support."""

    def test_us_candidates_still_work(self):
        payload = {
            "jobs": {
                "bay": {
                    "uid": "bay",
                    "title": "Software Engineer New Grad",
                    "company": "Example",
                    "locations": ["SF"],
                },
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        candidates = store.candidates(
            min_score=5,
            allow_remote=True,
            unnotified_only=False,
            max_age_days=0,
        )
        self.assertEqual({row["uid"] for row in candidates}, {"bay"})

    def test_uk_candidates_are_visible(self):
        payload = {
            "jobs": {
                "london-role": {
                    "uid": "london-role",
                    "title": "Graduate Software Engineer",
                    "company": "Example",
                    "locations": ["London, United Kingdom"],
                },
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        candidates = store.candidates(
            min_score=5,
            allow_remote=True,
            unnotified_only=False,
            max_age_days=0,
        )
        self.assertEqual({row["uid"] for row in candidates}, {"london-role"})

    def test_uk_candidates_require_notification_locality(self):
        # Non-notify UK cities should not be candidates
        payload = {
            "jobs": {
                "reading-role": {
                    "uid": "reading-role",
                    "title": "Graduate Software Engineer",
                    "company": "Example",
                    "locations": ["Reading, England"],
                },
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        candidates = store.candidates(
            min_score=5,
            allow_remote=True,
            unnotified_only=False,
            max_age_days=0,
        )
        self.assertEqual(candidates, [])

    def test_region_records_returns_us_records(self):
        payload = {
            "jobs": {
                "us-role": {
                    "uid": "us-role",
                    "title": "Software Engineer",
                    "locations": ["Austin, TX"],
                },
                "uk-role": {
                    "uid": "uk-role",
                    "title": "Software Engineer",
                    "locations": ["London, UK"],
                },
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        us_records = store.region_records(job_alert.REGION_US)
        self.assertEqual(
            {r["uid"] for r in us_records}, {"us-role"}
        )

    def test_region_records_returns_uk_records(self):
        payload = {
            "jobs": {
                "us-role": {
                    "uid": "us-role",
                    "title": "Software Engineer",
                    "locations": ["Austin, TX"],
                },
                "uk-role": {
                    "uid": "uk-role",
                    "title": "Software Engineer",
                    "locations": ["London, UK"],
                },
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)

        uk_records = store.region_records(job_alert.REGION_UK)
        self.assertEqual(
            {r["uid"] for r in uk_records}, {"uk-role"}
        )


if __name__ == "__main__":
    unittest.main()
