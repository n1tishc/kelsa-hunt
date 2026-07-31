import json
import pathlib
import tempfile
import types
import unittest
from unittest import mock

import job_alert


class CanonicalStorePersistenceTests(unittest.TestCase):
    def test_reobserving_an_unchanged_record_keeps_store_byte_identical(self):
        record = {
            "uid": "gh:example:123",
            "title": "Software Engineer, New Grad",
            "company": "Example",
            "locations": ["San Francisco, CA"],
            "url": "https://job-boards.greenhouse.io/example/jobs/123",
            "source": "Greenhouse",
            "posted": 1_700_000_000,
            "first_seen": 1_700_100_000,
            "closed_at": None,
        }
        payload = {
            "version": job_alert.STORE_VERSION,
            "updated": "2026-07-30T12:00:00+00:00",
            "count": 1,
            "jobs": {record["uid"]: record},
        }

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store_path = root / "jobs.json"
            annotations_path = root / "annotations.json"
            original = json.dumps(payload, indent=0, sort_keys=True)
            store_path.write_text(original)
            store = job_alert.Store(store_path)

            observed = {
                key: value
                for key, value in record.items()
                if key not in {"first_seen", "closed_at"}
            }
            with (
                mock.patch.object(job_alert, "ANNOTATIONS_FILE", annotations_path),
                mock.patch.object(job_alert, "now", return_value=1_800_000_000),
            ):
                store.upsert(observed)
                store.save()

            self.assertEqual(store_path.read_text(), original)

    def test_new_record_is_persisted_as_meaningful_state(self):
        payload = {
            "version": job_alert.STORE_VERSION,
            "updated": "2026-07-30T12:00:00+00:00",
            "count": 0,
            "jobs": {},
        }
        observed = {
            "uid": "lever:example:abc",
            "title": "Software Engineer I",
            "company": "Example",
            "locations": ["Remote - US"],
            "url": "https://jobs.lever.co/example/abc",
            "source": "Lever",
            "posted": 1_700_000_000,
        }

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store_path = root / "jobs.json"
            annotations_path = root / "annotations.json"
            store_path.write_text(json.dumps(payload, indent=0, sort_keys=True))
            store = job_alert.Store(store_path)

            with (
                mock.patch.object(job_alert, "ANNOTATIONS_FILE", annotations_path),
                mock.patch.object(job_alert, "now", return_value=1_700_100_000),
            ):
                store.upsert(observed)
                store.save()

            persisted = json.loads(store_path.read_text())

        self.assertEqual(
            persisted["jobs"][observed["uid"]],
            {
                **observed,
                "first_seen": 1_700_100_000,
                "closed_at": None,
            },
        )

    def test_closure_transition_is_persisted(self):
        record = {
            "uid": "gh:example:123",
            "title": "Software Engineer, New Grad",
            "company": "Example",
            "locations": ["San Francisco, CA"],
            "first_seen": 1_700_000_000,
            "closed_at": None,
        }
        payload = {
            "version": job_alert.STORE_VERSION,
            "updated": "2026-07-30T12:00:00+00:00",
            "count": 1,
            "jobs": {record["uid"]: record},
        }

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store_path = root / "jobs.json"
            annotations_path = root / "annotations.json"
            store_path.write_text(json.dumps(payload, indent=0, sort_keys=True))
            store = job_alert.Store(store_path)

            with (
                mock.patch.object(job_alert, "ANNOTATIONS_FILE", annotations_path),
                mock.patch.object(job_alert, "now", return_value=1_800_000_000),
            ):
                store.mark_closed(["gh:example:"], live_uids=set())
                store.save()

            persisted = job_alert.Store(store_path)

        self.assertEqual(
            persisted.jobs[record["uid"]]["closed_at"],
            1_800_000_000,
        )

    def test_reopening_transition_is_persisted_without_resetting_first_seen(self):
        record = {
            "uid": "gh:example:123",
            "title": "Software Engineer, New Grad",
            "company": "Example",
            "locations": ["San Francisco, CA"],
            "first_seen": 1_700_000_000,
            "closed_at": 1_750_000_000,
        }
        payload = {
            "version": job_alert.STORE_VERSION,
            "updated": "2026-07-30T12:00:00+00:00",
            "count": 1,
            "jobs": {record["uid"]: record},
        }

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store_path = root / "jobs.json"
            annotations_path = root / "annotations.json"
            store_path.write_text(json.dumps(payload, indent=0, sort_keys=True))
            store = job_alert.Store(store_path)
            observed = {
                key: value
                for key, value in record.items()
                if key not in {"first_seen", "closed_at"}
            }

            with (
                mock.patch.object(job_alert, "ANNOTATIONS_FILE", annotations_path),
                mock.patch.object(job_alert, "now", return_value=1_800_000_000),
            ):
                store.upsert(observed)
                store.save()

            persisted = job_alert.Store(store_path)

        self.assertEqual(
            (
                persisted.jobs[record["uid"]]["closed_at"],
                persisted.jobs[record["uid"]]["first_seen"],
            ),
            (None, 1_700_000_000),
        )

    def test_notification_transition_is_persisted(self):
        record = {
            "uid": "gh:example:123",
            "title": "Software Engineer, New Grad",
            "company": "Example",
            "locations": ["San Francisco, CA"],
            "first_seen": 1_700_000_000,
            "closed_at": None,
        }
        payload = {
            "version": job_alert.STORE_VERSION,
            "updated": "2026-07-30T12:00:00+00:00",
            "count": 1,
            "jobs": {record["uid"]: record},
        }

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store_path = root / "jobs.json"
            annotations_path = root / "annotations.json"
            store_path.write_text(json.dumps(payload, indent=0, sort_keys=True))
            store = job_alert.Store(store_path)

            with mock.patch.object(
                job_alert,
                "ANNOTATIONS_FILE",
                annotations_path,
            ):
                store.mark_notified([record], timestamp=1_800_000_000)
                store.save()

            persisted = job_alert.Store(store_path)

        self.assertEqual(
            persisted.jobs[record["uid"]]["notified_at"],
            1_800_000_000,
        )

    def test_legacy_heartbeat_is_removed_once_then_store_is_stable(self):
        record = {
            "uid": "gh:example:123",
            "title": "Software Engineer, New Grad",
            "first_seen": 1_700_000_000,
            "last_seen": 1_799_000_000,
            "closed_at": None,
        }
        payload = {
            "version": job_alert.STORE_VERSION,
            "updated": "2026-07-30T12:00:00+00:00",
            "count": 1,
            "jobs": {record["uid"]: record},
        }

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store_path = root / "jobs.json"
            annotations_path = root / "annotations.json"
            store_path.write_text(json.dumps(payload, indent=0, sort_keys=True))

            with mock.patch.object(
                job_alert,
                "ANNOTATIONS_FILE",
                annotations_path,
            ):
                job_alert.Store(store_path).save()
                migrated = store_path.read_text()
                job_alert.Store(store_path).save()

            persisted = json.loads(store_path.read_text())
            stable_after_migration = store_path.read_text() == migrated

        self.assertEqual(
            (
                "last_seen" in persisted["jobs"][record["uid"]],
                persisted["updated"] == payload["updated"],
                stable_after_migration,
            ),
            (False, False, True),
        )

    def test_successful_unchanged_scan_creates_no_store_diff(self):
        record = {
            "uid": "simplify:example",
            "title": "Product Manager",
            "company": "Example",
            "locations": ["San Francisco, CA"],
            "url": "https://example.invalid/jobs/1",
            "source": "Simplify",
            "posted": 1_700_000_000,
            "first_seen": 1_700_100_000,
            "closed_at": None,
        }
        payload = {
            "version": job_alert.STORE_VERSION,
            "updated": "2026-07-30T12:00:00+00:00",
            "count": 1,
            "jobs": {record["uid"]: record},
        }

        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            store_path = root / "jobs.json"
            annotations_path = root / "annotations.json"
            sources_path = root / "sources.json"
            original = json.dumps(payload, indent=0, sort_keys=True)
            store_path.write_text(original)
            store = job_alert.Store(store_path)
            observed = {
                key: value
                for key, value in record.items()
                if key not in {"first_seen", "closed_at"}
            }
            args = types.SimpleNamespace(
                min_score=5,
                no_remote=False,
                dry_run=False,
                seed=False,
            )

            with (
                mock.patch.object(job_alert, "ANNOTATIONS_FILE", annotations_path),
                mock.patch.object(job_alert, "SOURCES_FILE", sources_path),
                mock.patch.object(
                    job_alert,
                    "fetch_simplify",
                    return_value=([observed], True),
                ),
                mock.patch.object(job_alert, "now", return_value=1_800_000_000),
            ):
                job_alert.cmd_scan(args, store)

            after_scan = store_path.read_text()

        self.assertEqual(after_scan, original)


if __name__ == "__main__":
    unittest.main()
