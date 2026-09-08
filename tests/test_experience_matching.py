import unittest
from unittest.mock import patch

import job_alert
from experience import experience_years


class ExperienceMatchingTests(unittest.TestCase):
    def test_junior_is_priority_ten(self):
        for title in ("Junior Software Engineer", "Jr. Developer", "Junior ML Engineer",
                      "Graduate Junior Software Engineer"):
            self.assertEqual(job_alert.classify(title)[:2], (True, 10))

    def test_common_experience_wording_and_html(self):
        for text, expected in (
            ("1–3 years of experience", [1]),
            ("two to three years’ professional experience", [2]),
            ("3+ years of software development experience", [3]),
            ("&lt;p&gt;2 &lt;b&gt;years&lt;/b&gt; experience&lt;/p&gt;", [2]),
            ("5 years of experience overall; 2 years of Python experience", [2, 5]),
            ("Founded 20 years ago. Three-year degree. 3 years of warranty.", []),
            ("13 years of experience", [13]),
        ):
            with self.subTest(text=text):
                self.assertEqual(experience_years(text), expected)

    def test_experience_can_qualify_plain_and_level_two_titles(self):
        for title in ("Software Engineer", "Backend Developer", "Software Engineer II",
                      "Software Engineer 2"):
            for years in ([1], [2], [3]):
                self.assertEqual(job_alert.classify(title, experience=years)[:2], (True, 5))
        self.assertTrue(job_alert.classify("Software Engineer (1-3 years experience)")[0])

    def test_senior_and_conflicting_requirements_do_not_slip_through(self):
        for title in ("Senior Software Engineer", "Staff Engineer", "Software Engineer III",
                      "Software Engineer L4", "Engineering Manager", "Accountant"):
            self.assertFalse(job_alert.classify(title, experience=[2])[0])
        for title in ("Junior Software Engineer", "Software Engineer II", "Software Engineer"):
            self.assertFalse(job_alert.classify(title, experience=[2, 5])[0])
        self.assertFalse(job_alert.classify("Software Engineer II")[0])

    def test_bulk_sources_extract_without_storing_description(self):
        fixtures = (
            (job_alert.fetch_greenhouse, {"jobs": [{"id": 1, "title": "Software Engineer",
                "content": "2 years of experience"}]}),
            (job_alert.fetch_lever, [{"id": 1, "text": "Software Engineer",
                "lists": [{"content": "2 years of experience"}]}]),
            (job_alert.fetch_ashby, {"jobs": [{"id": 1, "title": "Software Engineer",
                "descriptionPlain": "2 years of experience"}]}),
        )
        for fetch, payload in fixtures:
            with self.subTest(source=fetch.__name__), patch.object(job_alert, "get_json", return_value=payload):
                rows, success = fetch("example")
                self.assertTrue(success)
                self.assertEqual(rows[0]["experience_years"], [2])
                self.assertNotIn("description", rows[0])

    def test_candidate_flow_preserves_location_age_and_duplicate_rules(self):
        record = dict(uid="test:1", title="Software Engineer II", company="Example",
                      locations=["San Francisco, CA"], experience_years=[2], posted=job_alert.now())
        self.assertEqual(len(job_alert.candidates_from_records({"test:1": record})), 1)
        for changes in (dict(locations=["New York, NY"]), dict(posted=1),
                        dict(notified_at=1), dict(closed_at=1), dict(hidden=True)):
            self.assertEqual(job_alert.candidates_from_records({"test:1": dict(record, **changes)}), [])

    def test_secondary_ashby_office_and_remote_country_are_searchable(self):
        locations = job_alert.ashby_locations({"location": "New York, NY", "secondaryLocations": [
            {"location": "San Francisco", "address": {"addressCountry": "USA"}}]})
        self.assertTrue(job_alert.is_bay_area(locations))
        remote = job_alert.ashby_locations({"location": "Remote", "isRemote": True,
            "address": {"postalAddress": {"addressCountry": "USA"}}})
        self.assertTrue(job_alert.is_bay_area(remote))
        self.assertFalse(job_alert.is_bay_area(job_alert.ashby_locations(
            {"location": "Remote", "isRemote": True})))


if __name__ == "__main__":
    unittest.main()
