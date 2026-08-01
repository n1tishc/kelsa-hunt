import collections
import contextlib
import io
import json
import pathlib
import tempfile
import threading
import time
import types
import unittest
import urllib.error
from unittest import mock

import job_alert


class ConcurrentSourceFetchTests(unittest.TestCase):
    def test_scan_uses_eight_workers_and_at_most_four_per_host(self):
        lock = threading.Lock()
        active_by_host = collections.Counter()
        active_total = 0
        maximum_by_host = collections.Counter()
        maximum_total = 0
        concurrent_wave = threading.Barrier(8, timeout=2)

        def controlled_fetch(host, uid):
            def fetch():
                nonlocal active_total, maximum_total
                with lock:
                    active_total += 1
                    active_by_host[host] += 1
                    maximum_total = max(maximum_total, active_total)
                    maximum_by_host[host] = max(
                        maximum_by_host[host],
                        active_by_host[host],
                    )
                concurrent_wave.wait()
                with lock:
                    active_total -= 1
                    active_by_host[host] -= 1
                return [{"uid": uid}], True

            return fetch

        sources = []
        for index in range(8):
            for host in ("first.example", "second.example"):
                uid = f"source:{host}:{index}"
                sources.append(
                    job_alert.SourceFetch(
                        name=uid,
                        prefix=f"{uid}:",
                        host=host,
                        fetch=controlled_fetch(host, uid),
                    )
                )

        results = job_alert.fetch_sources(sources)

        self.assertEqual(
            (
                len(results),
                all(result.ok for result in results),
                maximum_total,
                dict(maximum_by_host),
            ),
            (
                16,
                True,
                8,
                {"first.example": 4, "second.example": 4},
            ),
        )

    def test_busy_host_cannot_starve_a_healthy_different_host(self):
        release_slow = threading.Event()
        fast_finished = threading.Event()
        slow_started = 0
        lock = threading.Lock()

        def slow_fetch(index):
            def fetch():
                nonlocal slow_started
                with lock:
                    slow_started += 1
                release_slow.wait(timeout=2)
                return [{"uid": f"slow:{index}"}], True

            return fetch

        def fast_fetch():
            fast_finished.set()
            return [{"uid": "fast:1"}], True

        sources = [
            job_alert.SourceFetch(
                name=f"slow/{index}",
                prefix=f"slow:{index}:",
                host="slow.example",
                fetch=slow_fetch(index),
            )
            for index in range(8)
        ]
        sources.append(job_alert.SourceFetch(
            name="fast/1",
            prefix="fast:1:",
            host="fast.example",
            fetch=fast_fetch,
        ))

        worker = threading.Thread(target=job_alert.fetch_sources, args=(sources,))
        worker.start()
        fast_completed_while_slow_was_blocked = fast_finished.wait(timeout=1)
        with lock:
            slow_started_before_release = slow_started
        release_slow.set()
        worker.join(timeout=2)

        self.assertEqual(
            (
                fast_completed_while_slow_was_blocked,
                slow_started_before_release <= 4,
                worker.is_alive(),
            ),
            (True, True, False),
        )

    def test_previously_non_empty_source_retries_empty_then_requires_verification(self):
        attempts = 0

        def empty_fetch():
            nonlocal attempts
            attempts += 1
            return [], True

        source = job_alert.SourceFetch(
            name="greenhouse/example",
            prefix="gh:example:",
            host="boards-api.greenhouse.io",
            fetch=empty_fetch,
        )

        result = job_alert.fetch_sources(
            [source],
            previously_non_empty={source.prefix},
        )[0]

        self.assertEqual(
            (
                attempts,
                result.records,
                result.ok,
                result.verification_required,
            ),
            (2, [], False, True),
        )

    def test_new_empty_source_is_not_activated_or_retried(self):
        attempts = 0

        def empty_fetch():
            nonlocal attempts
            attempts += 1
            return [], True

        source = job_alert.SourceFetch(
            name="greenhouse/new",
            prefix="gh:new:",
            host="boards-api.greenhouse.io",
            fetch=empty_fetch,
        )

        result = job_alert.fetch_sources([source])[0]

        self.assertEqual(
            (attempts, result.ok, result.verification_required),
            (1, False, True),
        )


class RequestRetryTests(unittest.TestCase):
    def test_timeout_retries_once_with_ten_second_budget_and_backoff(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"status": "ok"}
        ).encode()

        with (
            mock.patch(
                "urllib.request.urlopen",
                side_effect=[TimeoutError("slow"), response],
            ) as open_url,
            mock.patch("random.uniform", return_value=0.2),
            mock.patch("time.sleep") as sleep,
        ):
            result = job_alert.get_json("https://api.example/jobs")

        self.assertEqual(
            (
                result,
                [call.kwargs["timeout"] for call in open_url.call_args_list],
                sleep.call_args_list,
            ),
            ({"status": "ok"}, [10, 10], [mock.call(0.2)]),
        )

    def test_rate_limits_and_server_errors_retry_but_other_4xx_do_not(self):
        for status in (429, 500, 503):
            with self.subTest(status=status):
                failure = urllib.error.HTTPError(
                    "https://api.example/jobs",
                    status,
                    "failed",
                    {},
                    io.BytesIO(b"{}"),
                )
                response = mock.MagicMock()
                response.__enter__.return_value.read.return_value = b'{"ok": true}'
                with (
                    mock.patch(
                        "urllib.request.urlopen",
                        side_effect=[failure, response],
                    ) as open_url,
                    mock.patch("random.uniform", return_value=0.1),
                    mock.patch("time.sleep"),
                ):
                    result = job_alert.get_json("https://api.example/jobs")

                self.assertEqual((result, open_url.call_count), ({"ok": True}, 2))

        not_found = urllib.error.HTTPError(
            "https://api.example/jobs",
            404,
            "not found",
            {},
            io.BytesIO(b"{}"),
        )
        with mock.patch(
            "urllib.request.urlopen",
            side_effect=not_found,
        ) as open_url:
            with self.assertRaises(urllib.error.HTTPError):
                job_alert.get_json("https://api.example/jobs")

        self.assertEqual(open_url.call_count, 1)

    def test_wrapped_timeout_retries_but_other_transport_errors_do_not(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"ok": true}'
        wrapped_timeout = urllib.error.URLError(TimeoutError("slow"))

        with (
            mock.patch(
                "urllib.request.urlopen",
                side_effect=[wrapped_timeout, response],
            ) as open_url,
            mock.patch("random.uniform", return_value=0.1),
            mock.patch("time.sleep"),
        ):
            result = job_alert.get_json("https://api.example/jobs")

        offline = urllib.error.URLError("offline")
        with mock.patch(
            "urllib.request.urlopen",
            side_effect=offline,
        ) as offline_open:
            with self.assertRaises(urllib.error.URLError):
                job_alert.get_json("https://api.example/jobs")

        self.assertEqual(
            (result, open_url.call_count, offline_open.call_count),
            ({"ok": True}, 2, 1),
        )


class ScanClosureSafetyTests(unittest.TestCase):
    def test_failed_source_cannot_close_records_while_healthy_source_completes(self):
        payload = {
            "jobs": {
                "gh:broken:old": {
                    "uid": "gh:broken:old",
                    "title": "Product Manager",
                    "locations": ["San Francisco, CA"],
                    "closed_at": None,
                },
                "gh:healthy:old": {
                    "uid": "gh:healthy:old",
                    "title": "Product Manager",
                    "locations": ["San Francisco, CA"],
                    "closed_at": None,
                },
            }
        }

        def malformed_fetch():
            return [{"title": "missing stable uid"}], True

        def healthy_fetch():
            return [
                {
                    "uid": "gh:healthy:new",
                    "title": "Product Manager",
                    "locations": ["San Francisco, CA"],
                    "feed_active": True,
                }
            ], True

        source_fetches = [
            job_alert.SourceFetch(
                name="greenhouse/broken",
                prefix="gh:broken:",
                host="boards-api.greenhouse.io",
                fetch=malformed_fetch,
            ),
            job_alert.SourceFetch(
                name="greenhouse/healthy",
                prefix="gh:healthy:",
                host="boards-api.greenhouse.io",
                fetch=healthy_fetch,
            ),
        ]
        args = types.SimpleNamespace(
            min_score=5,
            no_remote=False,
            dry_run=True,
            seed=False,
        )

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)
            with mock.patch.object(job_alert, "now", return_value=1_800_000_000):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    job_alert.cmd_scan(
                        args,
                        store,
                        source_fetches=source_fetches,
                    )

        self.assertEqual(
            (
                store.jobs["gh:broken:old"]["closed_at"],
                store.jobs["gh:healthy:old"]["closed_at"],
                "gh:healthy:new" in store.jobs,
                "greenhouse/broken: 0 listings (FAILED" in output.getvalue(),
                "greenhouse/healthy: 1 listings (ok" in output.getvalue(),
                "fetch total:" in output.getvalue(),
                "scan total:" in output.getvalue(),
            ),
            (None, 1_800_000_000, True, True, True, True, True),
        )

    def test_suspicious_empty_source_cannot_close_existing_records(self):
        payload = {
            "jobs": {
                "gh:empty:old": {
                    "uid": "gh:empty:old",
                    "title": "Product Manager",
                    "locations": ["San Francisco, CA"],
                    "closed_at": None,
                }
            }
        }
        attempts = 0

        def empty_fetch():
            nonlocal attempts
            attempts += 1
            return [], True

        source = job_alert.SourceFetch(
            name="greenhouse/empty",
            prefix="gh:empty:",
            host="boards-api.greenhouse.io",
            fetch=empty_fetch,
        )
        args = types.SimpleNamespace(
            min_score=5,
            no_remote=False,
            dry_run=True,
            seed=False,
        )

        with tempfile.TemporaryDirectory() as directory:
            store_path = pathlib.Path(directory) / "jobs.json"
            store_path.write_text(json.dumps(payload))
            store = job_alert.Store(store_path)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                job_alert.cmd_scan(args, store, source_fetches=[source])

        self.assertEqual(
            (
                attempts,
                store.jobs["gh:empty:old"]["closed_at"],
                "greenhouse/empty: 0 listings (VERIFY" in output.getvalue(),
            ),
            (2, None, True),
        )


class WorkflowBudgetTests(unittest.TestCase):
    def test_workflow_uses_agreed_cadence_and_five_minute_envelope(self):
        workflow_path = (
            pathlib.Path(__file__).parents[1]
            / ".github"
            / "workflows"
            / "alert.yml"
        )
        workflow = workflow_path.read_text()

        self.assertEqual(
            (
                'cron: "17,47 14-23 * * 1-5"' in workflow,
                'cron: "17 0-12/2 * * 1-5"' in workflow,
                'cron: "17 */2 * * 0,6"' in workflow,
                "timeout-minutes: 5" in workflow,
                "cancel-in-progress: false" in workflow,
                "if: always()" in workflow,
                'cron: "*/15' not in workflow,
                'cron: "0 ' not in workflow,
            ),
            (True, True, True, True, True, True, True, True),
        )


if __name__ == "__main__":
    unittest.main()
