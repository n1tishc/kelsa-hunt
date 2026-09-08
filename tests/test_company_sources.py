import unittest
from unittest.mock import patch

import company_sources
import job_alert


def eightfold_row(job_id=1, company='Qualitrol'):
    return {'id': job_id, 'name': 'Software Engineer I',
            'locations': ['Fairport, NY, United States'], 'postedTs': 1788546944,
            'efcustomTextOperatingcompany': [company]}


def dayforce_row(job_id=1):
    return {'jobPostingId': job_id, 'clientNamespace': 'ibgllc',
            'jobTitle': 'Software Engineer I',
            'jobDescription': '<p>2 years of experience</p>',
            'postingLocations': [{'formattedAddress': 'New York, NY, United States'}],
            'postingStartTimestampUTC': '2026-09-08T00:30:00+00:00'}


class CareersFeedTests(unittest.TestCase):
    @patch.object(company_sources, 'CareersSession')
    def test_eightfold_fetches_all_pages_and_preserves_company_and_date(self, session):
        request = session.return_value.request
        request.side_effect = [b'page',
            {'status': 200, 'data': {'positions': [eightfold_row()], 'count': 2}},
            {'status': 200, 'data': {'positions': [eightfold_row(2)], 'count': 2}}]
        rows, ok = company_sources.fetch_eightfold('ralliant/qualitrol')
        self.assertTrue(ok)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['company'], 'Qualitrol')
        self.assertEqual(rows[0]['posted'], 1788546944)
        self.assertIn('start=1', request.call_args.args[0])
        self.assertIn('filter_efcustom_text_operatingcompany=qualitrol', request.call_args.args[0])

    @patch.object(company_sources, 'CareersSession')
    def test_dayforce_uses_csrf_and_pages_by_observed_rows(self, session):
        request = session.return_value.request
        request.side_effect = [{'csrfToken': 'public-token'},
            {'jobPostings': [dayforce_row()], 'maxCount': 2},
            {'jobPostings': [dayforce_row(2)], 'maxCount': 2}]
        rows, ok = company_sources.fetch_dayforce('ibgllc/CANDIDATEPORTAL')
        self.assertTrue(ok)
        self.assertEqual(len(rows), 2)
        self.assertEqual(request.call_args.kwargs['headers']['X-CSRF-TOKEN'], 'public-token')
        self.assertEqual(request.call_args.kwargs['payload']['paginationStart'], 1)
        self.assertEqual(rows[0]['company'], 'Interactive Brokers')
        self.assertEqual(rows[0]['experience_years'], [2])
        self.assertEqual(rows[0]['url'],
            'https://jobs.dayforcehcm.com/en-US/ibgllc/CANDIDATEPORTAL/jobs/1')

    @patch.object(company_sources, 'CareersSession')
    def test_eightfold_rejects_other_operating_companies(self, session):
        session.return_value.request.side_effect = [b'page', {'status': 200,
            'data': {'positions': [eightfold_row(company='Tektronix')], 'count': 1}}]
        with self.assertRaisesRegex(ValueError, 'company filter'):
            company_sources.fetch_eightfold('ralliant/qualitrol')

    @patch.object(company_sources, 'CareersSession')
    def test_incomplete_or_repeated_pages_supply_no_closure_evidence(self, session):
        for second in ([], [dayforce_row()]):
            with self.subTest(second=second):
                session.return_value.request.side_effect = [{'csrfToken': 'token'},
                    {'jobPostings': [dayforce_row()], 'maxCount': 2},
                    {'jobPostings': second, 'maxCount': 2}]
                sources = job_alert.configured_source_fetches({'dayforce': ['ibgllc/CANDIDATEPORTAL']})
                result = job_alert.fetch_sources([sources[-1]])[0]
                self.assertFalse(result.ok)
                self.assertEqual(result.records, [])

    @patch.object(company_sources, 'CareersSession')
    def test_partial_network_failure_discards_partial_inventory(self, session):
        session.return_value.request.side_effect = [{'csrfToken': 'token'},
            {'jobPostings': [dayforce_row()], 'maxCount': 2}, TimeoutError('timeout')]
        source = job_alert.configured_source_fetches({'dayforce': ['ibgllc/CANDIDATEPORTAL']})[-1]
        result = job_alert.fetch_sources([source])[0]
        self.assertFalse(result.ok)
        self.assertEqual(result.records, [])

    @patch.object(company_sources, 'CareersSession')
    def test_missing_location_fails_closed(self, session):
        row = dayforce_row()
        row['postingLocations'] = []
        session.return_value.request.side_effect = [{'csrfToken': 'token'},
            {'jobPostings': [row], 'maxCount': 1}]
        with self.assertRaisesRegex(ValueError, 'locations'):
            company_sources.fetch_dayforce('ibgllc/CANDIDATEPORTAL')

    @patch.object(job_alert, 'fetch_sources', return_value=[])
    def test_priority_scan_fetches_only_the_watchlist(self, fetch):
        import argparse
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            store = job_alert.Store(Path(directory) / 'jobs.json')
            args = argparse.Namespace(priority_only=True, min_score=5,
                no_remote=False, seed=False, dry_run=True, shard=None)
            job_alert.cmd_scan(args, store)
        self.assertEqual({s.name for s in fetch.call_args.args[0]},
                         company_sources.PRIORITY_SOURCES)

    def test_both_priority_companies_are_registered(self):
        import json
        sources = json.loads(job_alert.SOURCES_FILE.read_text())
        names = {s.name for s in job_alert.configured_source_fetches(sources)}
        self.assertTrue(company_sources.PRIORITY_SOURCES.issubset(names))


if __name__ == '__main__':
    unittest.main()
