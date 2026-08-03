import unittest

import job_alert


class ClassifyUsTitleTests(unittest.TestCase):
    """US title classification should remain unchanged."""

    def test_explicit_new_grad_scores_10(self):
        titles = [
            "Software Engineer - New Grad",
            "New Graduate Software Engineer",
            "University Grad Software Engineer",
            "Recent Grad Software Engineer",
            "Campus Software Engineer",
            "Early Career Software Engineer",
            "Entry Level Software Engineer",
            "Entry-Level Software Engineer",
            "Rotational Software Engineer",
            "Software Engineer Apprentice",
            "Software Engineer (2025 start)",
            "Software Engineer (2025 grad)",
            "Software Engineer Grad",
        ]
        for title in titles:
            with self.subTest(title=title):
                keep, score, reason = job_alert.classify(title)
                self.assertTrue(keep, f"{title} should be kept")
                self.assertEqual(score, 10, f"{title} should score 10, got {score}")

    def test_junior_marker_scores_5(self):
        titles = [
            "Junior Software Engineer",
            "Jr. Software Engineer",
            "Associate Software Engineer",
            "Software Engineer I",
            "SDE I",
            "SWE I",
            "Engineer I",
            "Software Engineer L3",
            "Software Engineer E3",
            "Software Engineer IC1",
            "Software Engineer T1",
            "Software Engineer Level 1",
        ]
        for title in titles:
            with self.subTest(title=title):
                keep, score, reason = job_alert.classify(title)
                self.assertTrue(keep, f"{title} should be kept")
                self.assertEqual(score, 5, f"{title} should score 5, got {score}")

    def test_mts_scores_5(self):
        titles = [
            "Member of Technical Staff",
            "Member of the Technical Staff",
        ]
        for title in titles:
            with self.subTest(title=title):
                keep, score, reason = job_alert.classify(title)
                self.assertTrue(keep, f"{title} should be kept")
                self.assertEqual(score, 5, f"{title} should score 5, got {score}")

    def test_bachelors_eligible_scores_3(self):
        titles = [
            "Software Engineer",
            "Backend Engineer",
            "Frontend Engineer",
            "Full Stack Engineer",
            "ML Engineer",
            "Machine Learning Engineer",
            "Data Scientist",
            "Infrastructure Engineer",
        ]
        for title in titles:
            with self.subTest(title=title):
                keep, score, reason = job_alert.classify(title, degrees=["Bachelor's"])
                self.assertTrue(keep, f"{title} should be kept with Bachelor's")
                self.assertEqual(score, 3, f"{title} should score 3, got {score}")

    def test_senior_titles_rejected(self):
        titles = [
            "Senior Software Engineer",
            "Sr. Software Engineer",
            "Staff Software Engineer",
            "Principal Software Engineer",
            "Distinguished Engineer",
            "Lead Software Engineer",
            "Engineering Manager",
            "Director of Engineering",
            "VP Engineering",
            "Head of Engineering",
            "Software Architect",
            "Software Engineer II",
            "Software Engineer III",
            "Software Engineer IV",
            "Software Engineer L4",
            "Software Engineer E4",
            "Software Engineer L5",
            "Software Engineer 2",
            "Software Engineer 3",
            "Engineer 2",
            "Developer 3",
        ]
        for title in titles:
            with self.subTest(title=title):
                keep, score, reason = job_alert.classify(title)
                self.assertFalse(keep, f"{title} should be rejected")

    def test_non_eng_roles_rejected(self):
        titles = [
            "Product Manager",
            "Designer",
            "Sales Engineer",
            "Technical Writer",
            "Recruiter",
        ]
        for title in titles:
            with self.subTest(title=title):
                keep, score, reason = job_alert.classify(title)
                self.assertFalse(keep, f"{title} should be rejected")

    def test_phd_only_rejected(self):
        # Research Scientist fails ROLE_MATCH before reaching the PhD check
        keep, score, reason = job_alert.classify("Research Scientist", degrees=["PhD"])
        self.assertFalse(keep)
        self.assertEqual(reason, "not an eng/ML role")

    def test_phd_research_role_rejected(self):
        # Research Scientist fails ROLE_MATCH before reaching the PhD check
        keep, score, reason = job_alert.classify(
            "Research Scientist", degrees=["PhD", "Bachelor's"]
        )
        self.assertFalse(keep)
        self.assertEqual(reason, "not an eng/ML role")

    def test_phd_research_role_allowed_with_bachelors(self):
        keep, score, reason = job_alert.classify(
            "Software Engineer", degrees=["PhD", "Bachelor's"]
        )
        self.assertTrue(keep)


class ClassifyUkTitleTests(unittest.TestCase):
    """UK title classification - new behavior for UK conventions."""

    def test_graduate_software_engineer_scores_10(self):
        """UK canonical explicit-new-grad wording should score Band 10."""
        titles = [
            "Graduate Software Engineer",
            "Graduate Software Developer",
            "Software Engineering Graduate Programme",
            "Graduate Programme - Engineering",
            "Graduate Software Engineer - 2025",
        ]
        for title in titles:
            with self.subTest(title=title):
                keep, score, reason = job_alert.classify(title)
                self.assertTrue(keep, f"{title} should be kept")
                self.assertEqual(score, 10, f"{title} should score 10, got {score}: {reason}")

    def test_technology_graduate_scheme_scores_10(self):
        """Big-employer grad schemes should be visible (Band 10)."""
        titles = [
            "Technology Graduate Scheme",
            "DXC Graduate Programme",
            "Graduate Trainee Programme",
            "Graduate Scheme - Technology",
            "Technology Graduate Programme",
        ]
        for title in titles:
            with self.subTest(title=title):
                keep, score, reason = job_alert.classify(title)
                self.assertTrue(keep, f"{title} should be kept")
                self.assertEqual(score, 10, f"{title} should score 10, got {score}: {reason}")

    def test_analyst_programmer_scores_10(self):
        """UK-common titles with no US analogue should score Band 10."""
        titles = [
            "Graduate Analyst Programmer",
        ]
        for title in titles:
            with self.subTest(title=title):
                keep, score, reason = job_alert.classify(title)
                self.assertTrue(keep, f"{title} should be kept")
                self.assertEqual(score, 10, f"{title} should score 10, got {score}: {reason}")

    def test_analyst_programmer_scores_10(self):
        """'Analyst Programmer' now scores Band 10 as a UK grad scheme."""
        keep, score, reason = job_alert.classify("Analyst Programmer")
        self.assertTrue(keep)
        self.assertEqual(score, 10)

    def test_technology_analyst_scores_10(self):
        keep, score, reason = job_alert.classify("Technology Analyst")
        self.assertTrue(keep)
        self.assertEqual(score, 10)

    def test_graduate_developer_scores_10(self):
        keep, score, reason = job_alert.classify("Graduate Developer")
        self.assertTrue(keep)
        self.assertEqual(score, 10)

    def test_technologist_scores_10(self):
        """Technologist with 'graduate' prefix scores Band 10."""
        keep, score, reason = job_alert.classify("Graduate Technologist")
        self.assertTrue(keep)
        self.assertEqual(score, 10)

    def test_placement_student_scores_3(self):
        """Placement and internship titles stay at Band 3 (bachelors-eligible)."""
        titles = [
            "Industrial Placement - Software",
            "Placement Student - Software Engineering",
        ]
        for title in titles:
            with self.subTest(title=title):
                keep, score, reason = job_alert.classify(title, degrees=["Bachelor's"])
                self.assertTrue(keep, f"{title} should be kept with Bachelor's")
                self.assertEqual(score, 3, f"{title} should score 3, got {score}")

    def test_graduate_not_in_weak_pos(self):
        """'graduate' was moved from WEAK_POS to STRONG_POS (not duplicated)."""
        # 'graduate' alone (without Engineer I) should score 10
        keep, score, reason = job_alert.classify("Graduate Software Engineer")
        self.assertTrue(keep)
        self.assertEqual(score, 10, f"graduate should score 10, got {score}")

    def test_graduate_engineer_i_scores_15(self):
        """Band 15 occurs when STRONG_POS and WEAK_POS both match.

        This is pre-existing behavior (e.g. 'Software Developer (Graduate, 2027 start)')
        and is documented in CONTEXT.md. The fix is that 'graduate' no longer
        appears in both WEAK_POS and STRONG_POS simultaneously.
        """
        keep, score, reason = job_alert.classify(
            "Graduate Software Engineer I", degrees=["Bachelor's"]
        )
        self.assertTrue(keep)
        self.assertEqual(score, 15)

    def test_graduate_analyst_boundary(self):
        """'Graduate Analyst' - should this score 10? Decide boundary."""
        # Analyst alone is not an eng role, but "Graduate Analyst" with UK context
        # is a grad scheme. We accept it at Band 10.
        keep, score, reason = job_alert.classify("Graduate Analyst")
        self.assertTrue(keep)
        self.assertEqual(score, 10)


class ClassifyHardNegTests(unittest.TestCase):
    """HARD_NEG and MID_LEVEL should not misfire on UK conventions."""

    def test_l3_still_accepted(self):
        # L3 is the new-grad rung, not mid-level
        keep, score, reason = job_alert.classify(
            "Software Engineer L3", degrees=["Bachelor's"]
        )
        self.assertTrue(keep)
        self.assertEqual(score, 5)

    def test_level_3_hard_rejected(self):
        # Level 3 (numeric) is mid-level and hard-rejected
        keep, score, reason = job_alert.classify(
            "Software Engineer Level 3", degrees=["Bachelor's"]
        )
        self.assertFalse(keep)

    def test_l4_e4_still_rejected(self):
        # The L4+/E4+ hard reject remains a deliberate permanent choice
        titles = [
            "Software Engineer L4",
            "Software Engineer E4",
            "Software Engineer Level 4",
        ]
        for title in titles:
            with self.subTest(title=title):
                keep, score, reason = job_alert.classify(title)
                self.assertFalse(keep, f"{title} should still be hard-rejected")


class ClassifyNoBand15Tests(unittest.TestCase):
    """Ensure no accidental Band 15 scores."""

    def test_no_unexpected_band_15(self):
        # Band 15 can occur when STRONG_POS and WEAK_POS both match
        # (e.g. "Graduate Software Engineer I" → Graduate +10, Engineer I +5).
        # This is pre-existing behavior; the key fix is that "graduate" no longer
        # appears in both WEAK_POS and STRONG_POS simultaneously.
        keep, score, reason = job_alert.classify(
            "Graduate Software Engineer I", degrees=["Bachelor's"]
        )
        self.assertTrue(keep)
        self.assertEqual(score, 15)


if __name__ == "__main__":
    unittest.main()