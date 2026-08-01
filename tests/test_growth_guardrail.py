import contextlib
import io
import json
import pathlib
import tempfile
import types
import unittest
from unittest import mock

import growth_guardrail
import job_alert


MiB = 1024 * 1024


class GrowthBoundaryTests(unittest.TestCase):
    def test_size_and_git_boundaries_warn_then_activate_the_gate(self):
        warning = growth_guardrail.assess_growth(
            serialized_bytes=20 * MiB,
            timing_check_medians=(),
            packed_git_bytes=200 * MiB,
        )
        hard_limit = growth_guardrail.assess_growth(
            serialized_bytes=25 * MiB,
            timing_check_medians=(),
            packed_git_bytes=250 * MiB,
        )

        self.assertEqual(
            (warning.warning_reasons, warning.gate_reasons),
            (
                (
                    "Canonical Store is at or above 20 MiB",
                    "packed full-history Git is at or above 200 MiB",
                ),
                (),
            ),
        )
        self.assertEqual(
            hard_limit.gate_reasons,
            (
                "Canonical Store is at or above 25 MiB",
                "packed full-history Git is at or above 250 MiB",
            ),
        )

    def test_timing_gate_requires_two_consecutive_five_round_trip_medians(self):
        warning_boundary = growth_guardrail.assess_growth(
            serialized_bytes=0,
            timing_check_medians=(1.6,),
        )
        first_breach = growth_guardrail.assess_growth(
            serialized_bytes=0,
            timing_check_medians=(1.99, 2.0),
        )
        repeated_breach = growth_guardrail.assess_growth(
            serialized_bytes=0,
            timing_check_medians=(2.0, 2.0),
        )
        recovered = growth_guardrail.assess_growth(
            serialized_bytes=0,
            timing_check_medians=(2.1, 1.5),
        )

        self.assertEqual(
            warning_boundary.warning_reasons,
            ("median load-plus-save time is at or above 1.6 seconds",),
        )
        self.assertEqual(
            (first_breach.warning_reasons, first_breach.gate_reasons),
            (("median load-plus-save time is at or above 1.6 seconds",), ()),
        )
        self.assertEqual(
            repeated_breach.gate_reasons,
            (
                "median load-plus-save time was at or above 2 seconds "
                "on two consecutive checks",
            ),
        )
        self.assertEqual(
            (recovered.warning_reasons, recovered.gate_reasons),
            ((), ()),
        )

    def test_timing_measurement_runs_five_round_trips_twice_without_mutation(self):
        payload = {"jobs": {"fixture": {"uid": "fixture"}}}
        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            original = json.dumps(payload)
            store_path.write_text(original)
            with mock.patch.object(
                growth_guardrail.time,
                "perf_counter",
                side_effect=range(20),
            ) as clock:
                medians = growth_guardrail.measure_timing_checks(store_path)
            unchanged = store_path.read_text() == original

        self.assertEqual((medians, clock.call_count, unchanged), ((1, 1), 20, True))


class SourceExpansionGateTests(unittest.TestCase):
    def test_active_gate_blocks_only_an_increase_in_configured_sources(self):
        active_gate = growth_guardrail.assess_growth(
            serialized_bytes=25 * MiB,
            timing_check_medians=(),
        )
        approved = {
            "greenhouse": ["first", "second"],
            "lever": ["third"],
        }
        unchanged = {
            "greenhouse": ["first", "second"],
            "lever": ["third"],
        }
        expanded = {
            **unchanged,
            "ashby": ["fourth"],
        }

        growth_guardrail.enforce_source_expansion(
            active_gate,
            approved,
            unchanged,
        )
        with self.assertRaisesRegex(
            growth_guardrail.SourceExpansionBlocked,
            "deterministic 16-way uid sharding.*does not migrate or prune",
        ):
            growth_guardrail.enforce_source_expansion(
                active_gate,
                approved,
                expanded,
            )

        self.assertEqual(
            (
                growth_guardrail.configured_source_count(approved),
                growth_guardrail.configured_source_count(expanded),
            ),
            (4, 5),
        )


class ScanGrowthMetricsTests(unittest.TestCase):
    def test_normal_scan_reports_store_count_bytes_and_load_save_durations(self):
        payload = {
            "jobs": {
                "fixture:one": {
                    "uid": "fixture:one",
                    "title": "Product Manager",
                    "locations": ["San Francisco, CA"],
                }
            }
        }
        args = types.SimpleNamespace(
            min_score=5,
            no_remote=False,
            dry_run=False,
            seed=False,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store_path = root / "jobs.json"
            store_path.write_text(json.dumps(payload))
            with mock.patch.object(
                job_alert,
                "ANNOTATIONS_FILE",
                root / "annotations.json",
            ), mock.patch.object(
                growth_guardrail,
                "STORE_WARNING_BYTES",
                0,
            ), mock.patch.object(
                growth_guardrail,
                "STORE_HARD_BYTES",
                0,
            ):
                store = job_alert.Store(store_path)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    job_alert.cmd_scan(args, store, source_fetches=[])

        self.assertRegex(
            output.getvalue(),
            r"store metrics: records=1 serialized_bytes=\d+ "
            r"load_seconds=\d+\.\d{4} save_seconds=\d+\.\d{4}",
        )
        self.assertIn(
            "WARNING growth guardrail: Canonical Store is at or above 20 MiB",
            output.getvalue(),
        )
        self.assertIn(
            "next response if gated: deterministic 16-way uid sharding",
            output.getvalue(),
        )
        self.assertIn(
            "EXPANSION GATE ACTIVE: Canonical Store is at or above 25 MiB",
            output.getvalue(),
        )
        self.assertIn("store unchanged", output.getvalue())


class GrowthWorkflowTests(unittest.TestCase):
    def test_monthly_check_uses_full_history_and_checks_source_change_events(self):
        workflow_path = (
            pathlib.Path(__file__).parents[1]
            / ".github"
            / "workflows"
            / "growth-guardrail.yml"
        )
        workflow = workflow_path.read_text()

        self.assertIn('cron: "23 9 1 * *"', workflow)
        self.assertIn("pull_request:", workflow)
        self.assertIn("sources.json", workflow)
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("git gc", workflow)
        self.assertIn("github.event.pull_request.base.sha", workflow)
        self.assertIn("github.event.before", workflow)
        self.assertIn('python growth_guardrail.py --baseline-ref "$BASE_REF"', workflow)
        self.assertNotIn("git add", workflow)
        self.assertNotIn("git commit", workflow)


if __name__ == "__main__":
    unittest.main()
