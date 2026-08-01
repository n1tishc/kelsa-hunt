import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).parents[1]
BUILD_DASHBOARD = ROOT / "scripts" / "build_dashboard.py"


class DashboardGenerationTests(unittest.TestCase):
    def test_compact_view_is_strict_us_and_excludes_private_state(self):
        records = {
            "mixed": {
                "uid": "mixed",
                "title": "Software Engineer, New Grad",
                "company": "Example",
                "locations": ["San Francisco, CA | London, UK"],
                "url": "javascript:alert('from feed')",
                "source": "Fixture",
                "posted": 100,
                "first_seen": 200,
                "closed_at": 300,
                "applied_at": 250,
                "hidden": True,
                "notified_at": 225,
            },
            "foreign": {
                "uid": "foreign",
                "title": "Software Engineer I",
                "company": "Foreign",
                "locations": ["London, UK"],
            },
            "bare-remote": {
                "uid": "bare-remote",
                "title": "Software Engineer I",
                "company": "Unknown",
                "locations": ["Remote"],
            },
        }
        payload = {
            "version": 2,
            "updated": "2026-08-01T12:00:00+00:00",
            "jobs": records,
        }

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store_path = root / "jobs.json"
            output = root / "site"
            store_path.write_text(json.dumps(payload))

            subprocess.run(
                [sys.executable, BUILD_DASHBOARD, store_path, output],
                cwd=ROOT,
                check=True,
            )
            derived = json.loads((output / "jobs.json").read_text())

        self.assertEqual(
            derived,
            {
                "canonical_updated": "2026-08-01T12:00:00+00:00",
                "defaults": {"score": "3+", "status": "open"},
                "records": [{
                    "closed_at": 300,
                    "company": "Example",
                    "first_seen": 200,
                    "locations": ["San Francisco, CA"],
                    "posted": 100,
                    "reason": "explicit new-grad",
                    "score": 10,
                    "source": "Fixture",
                    "status": "closed",
                    "title": "Software Engineer, New Grad",
                    "uid": "mixed",
                    "url": None,
                }],
            },
        )

    def test_generation_is_reproducible_and_emits_one_complete_pages_artifact(self):
        payload = {
            "updated": "2026-08-01T12:00:00+00:00",
            "jobs": {
                "open-score-three": {
                    "uid": "open-score-three",
                    "title": "Software Engineer",
                    "company": "Example",
                    "locations": ["Austin, TX"],
                    "url": "https://example.invalid/open",
                    "source": "Fixture",
                    "degrees": ["Bachelor's"],
                    "posted": 100,
                    "first_seen": 200,
                },
                "closed-score-zero": {
                    "uid": "closed-score-zero",
                    "title": "Account Executive",
                    "company": "Archive",
                    "locations": ["New York, NY"],
                    "url": "https://example.invalid/closed",
                    "source": "Legacy",
                    "posted": 10,
                    "first_seen": 20,
                    "closed_at": 30,
                },
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store_path = root / "jobs.json"
            first = root / "first"
            second = root / "second"
            store_path.write_text(json.dumps(payload))

            for output in (first, second):
                subprocess.run(
                    [sys.executable, BUILD_DASHBOARD, store_path, output],
                    cwd=ROOT,
                    check=True,
                )

            first_files = {
                path.relative_to(first): path.read_bytes()
                for path in first.iterdir()
            }
            second_files = {
                path.relative_to(second): path.read_bytes()
                for path in second.iterdir()
            }
            derived = json.loads(first_files[pathlib.Path("jobs.json")])

        self.assertEqual(
            set(first_files),
            {
                pathlib.Path("app.js"),
                pathlib.Path("filters.js"),
                pathlib.Path("index.html"),
                pathlib.Path("jobs.json"),
                pathlib.Path("styles.css"),
            },
        )
        self.assertEqual(first_files, second_files)
        self.assertEqual(
            [(row["uid"], row["score"], row["status"]) for row in derived["records"]],
            [
                ("closed-score-zero", 0, "closed"),
                ("open-score-three", 3, "open"),
            ],
        )


class DashboardWorkflowTests(unittest.TestCase):
    def test_pages_deploys_only_after_a_persisted_store_change(self):
        workflow = (ROOT / ".github" / "workflows" / "alert.yml").read_text()
        gitignore = (ROOT / ".gitignore").read_text().splitlines()

        self.assertIn("pages: write", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("store_changed: ${{ steps.persist.outputs.store_changed }}", workflow)
        self.assertIn("id: persist", workflow)
        self.assertIn("git diff --quiet -- jobs.json", workflow)
        self.assertIn('echo "store_changed=false" >> "$GITHUB_OUTPUT"', workflow)
        self.assertIn('echo "store_changed=true" >> "$GITHUB_OUTPUT"', workflow)
        self.assertIn("needs.scan.outputs.store_changed == 'true'", workflow)
        self.assertIn(
            'python scripts/build_dashboard.py jobs.json "$RUNNER_TEMP/job-ledger"',
            workflow,
        )
        self.assertIn("actions/upload-pages-artifact@v4", workflow)
        self.assertIn("actions/deploy-pages@v4", workflow)
        self.assertIn("git add jobs.json", workflow)
        self.assertNotIn("git add .", workflow)
        self.assertIn("dashboard-dist/", gitignore)


class LedgerFilterTests(unittest.TestCase):
    def test_default_search_and_filters_retain_complete_history(self):
        records = [
            {
                "uid": "open-three",
                "title": "Software Engineer",
                "company": "Acme",
                "locations": ["Austin, TX"],
                "source": "Greenhouse",
                "score": 3,
                "status": "open",
            },
            {
                "uid": "open-zero",
                "title": "Account Executive",
                "company": "Beta",
                "locations": ["New York, NY"],
                "source": "Lever",
                "score": 0,
                "status": "open",
            },
            {
                "uid": "closed-ten",
                "title": "Machine Learning Engineer, New Grad",
                "company": "Archive Labs",
                "locations": ["San Francisco, CA"],
                "source": "Greenhouse",
                "score": 10,
                "status": "closed",
            },
        ]
        states = [
            {"query": "", "status": "open", "source": "all", "score": "3+"},
            {"query": "", "status": "all", "source": "all", "score": "all"},
            {"query": "archive", "status": "all", "source": "all", "score": "all"},
            {"query": "san francisco", "status": "all", "source": "all", "score": "all"},
            {"query": "", "status": "all", "source": "Lever", "score": "0"},
        ]
        program = """
const { filterRecords } = require(process.argv[1]);
const records = JSON.parse(process.argv[2]);
const states = JSON.parse(process.argv[3]);
process.stdout.write(JSON.stringify(states.map(
  state => filterRecords(records, state).map(record => record.uid).sort()
)));
"""

        result = subprocess.run(
            [
                "node",
                "-e",
                program,
                ROOT / "dashboard" / "filters.js",
                json.dumps(records),
                json.dumps(states),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            json.loads(result.stdout),
            [
                ["open-three"],
                ["closed-ten", "open-three", "open-zero"],
                ["closed-ten"],
                ["closed-ten"],
                ["open-zero"],
            ],
        )


if __name__ == "__main__":
    unittest.main()
