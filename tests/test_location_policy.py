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

        for locations, expected in cases:
            with self.subTest(locations=locations):
                self.assertEqual(job_alert.us_locations(locations), expected)


if __name__ == "__main__":
    unittest.main()
