import importlib.util
import pathlib
import sys
import unittest


MODULE_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "evaluate_application_studio.py"
SPEC = importlib.util.spec_from_file_location("evaluate_application_studio", MODULE_PATH)
evaluation = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = evaluation
SPEC.loader.exec_module(evaluation)


class ApplicationStudioEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.example = {
            "id": "synthetic-platform-01",
            "record": {"title": "Platform Engineer", "location": "Bay Area, US", "description": "Improve reliable services."},
            "profile_context": {"project": "Improved API reliability."},
            "evidence_catalog": [
                {"id": "role-reliability", "source_id": "record.description", "quote": "Improve reliable services."},
                {"id": "profile-api", "source_id": "profile.project", "quote": "Improved API reliability."},
            ],
            "labels": {"useful": True, "expected_verdict": "recommend", "accepted_evidence_ids": ["role-reliability", "profile-api"]},
        }
        self.proposal = {
            "verdict": "recommend",
            "summary": "A reviewable fit.",
            "evidence_ids": ["role-reliability", "profile-api"],
            "review_questions": ["Confirm ownership scope."],
            "abstain_reason": None,
        }

    def test_local_validation_requires_human_approved_stable_evidence_ids(self):
        result = evaluation.validate_proposal(self.example, self.proposal)
        self.assertTrue(result.valid)
        self.assertEqual(result.supported_cards, 2)

        unsupported = dict(self.proposal)
        unsupported["evidence_ids"] = ["not-in-catalog"]
        result = evaluation.validate_proposal(self.example, unsupported)
        self.assertFalse(result.valid)
        self.assertEqual(result.reason, "invalid_evidence_id")

        unlabelled = dict(self.proposal)
        self.example["evidence_catalog"].append({"id": "unrelated", "source_id": "record.description", "quote": "Improve reliable services."})
        unlabelled["evidence_ids"] = ["unrelated"]
        result = evaluation.validate_proposal(self.example, unlabelled)
        self.assertFalse(result.valid)
        self.assertEqual(result.reason, "evidence_id_not_human_labelled")

    def test_recommendation_requires_evidence_but_abstention_is_a_safe_valid_result(self):
        recommendation = dict(self.proposal, evidence_ids=[])
        self.assertEqual(evaluation.validate_proposal(self.example, recommendation).reason, "missing_evidence_ids")
        abstention = dict(self.proposal, verdict="abstain", evidence_ids=[], abstain_reason="not enough support")
        self.assertTrue(evaluation.validate_proposal(self.example, abstention).valid)

    def test_stage_failure_abstains_and_never_calls_another_comparator(self):
        calls = []

        def direct(_example):
            calls.append("direct")
            return evaluation.Invocation.fail("timeout", latency_ms=12)

        report = evaluation.evaluate([self.example], {"direct": direct})
        row = report["comparators"]["direct"]
        self.assertEqual(calls, ["direct"])
        self.assertEqual(row["abstain_count"], 0)
        self.assertEqual(row["no_valid_packet_count"], 1)
        self.assertEqual(row["valid_proposal_count"], 0)
        self.assertEqual(row["failure_counts"], {"timeout": 1})

    def test_aggregate_report_excludes_raw_corpus_and_model_content(self):
        report = evaluation.evaluate(
            [self.example],
            {"pipeline": lambda _example: evaluation.Invocation.success(self.proposal, latency_ms=9, input_tokens=4, output_tokens=6)},
        )
        rendered = evaluation.safe_report_json(report)
        self.assertNotIn("Improve reliable services", rendered)
        self.assertNotIn("A reviewable fit", rendered)
        self.assertIn("input_hash", rendered)
        self.assertEqual(report["comparators"]["pipeline"]["evidence_support_rate"], 1.0)
        self.assertEqual(report["comparators"]["pipeline"]["packet_review_usefulness_rate"], 1.0)

    def test_corpus_rejects_direct_identifiers_and_network_urls(self):
        unsafe = dict(self.example)
        unsafe["record"] = dict(self.example["record"], description="Email person@example.com")
        with self.assertRaisesRegex(ValueError, "de-identified"):
            evaluation.validate_corpus([unsafe])

    def test_corpus_rejects_unbounded_or_non_synthetic_profile_input(self):
        unsafe = dict(self.example, id="real-profile", profile_context={"project": "x" * 241})
        with self.assertRaisesRegex(ValueError, "synthetic identifiers"):
            evaluation.validate_corpus([unsafe])

    def test_model_json_parser_tolerates_a_markdown_fence_but_not_other_text(self):
        self.assertEqual(evaluation.parse_model_json('```json\n{"verdict": "abstain"}\n```'), {"verdict": "abstain"})
        with self.assertRaises(ValueError):
            evaluation.parse_model_json("here is the JSON: {}")

    def test_schema_limits_model_to_catalog_evidence_ids(self):
        evidence_ids = evaluation.proposal_schema(self.example)["properties"]["evidence_ids"]["items"]["enum"]
        self.assertEqual(evidence_ids, ["role-reliability", "profile-api"])


if __name__ == "__main__":
    unittest.main()
