import json
import pathlib
import unittest

import job_alert


ROOT = pathlib.Path(__file__).parents[1]


class VerifiedSourceInventoryTests(unittest.TestCase):
    def test_config_activates_the_verified_greenhouse_lever_and_ashby_inventory(self):
        sources = json.loads((ROOT / "sources.json").read_text())

        self.assertEqual(
            {
                family: len(sources[family])
                for family in ("greenhouse", "lever", "ashby")
            },
            {"greenhouse": 73, "lever": 1, "ashby": 31},
        )
        self.assertEqual(set(sources["greenhouse"]), {
            "anthropic", "databricks", "stripe", "figma", "scaleai",
            "airtable", "vercel", "attentive", "robinhood", "gusto",
            "brex", "cloudflare", "asana", "lyft", "reddit", "nuro",
            "datadog", "twilio", "mongodb", "samsara", "pinterest",
            "gitlab", "flexport", "affirm", "algolia", "amplitude",
            "braze", "checkr", "circleci", "cockroachlabs", "contentful",
            "coursera", "cribl", "elastic", "epicgames", "fivetran",
            "gofundme", "hightouch", "instabase", "intercom", "klaviyo",
            "launchdarkly", "bitwarden", "blend", "carta", "celonis",
            "chime", "earnin", "fastly", "lattice", "mixpanel",
            "opentable", "pagerduty", "postscript", "qualtrics", "rubrik",
            "sisense", "smartsheet", "sofi", "toast", "workato",
            "ziprecruiter", "duolingo", "fireblocks", "humaninterest",
            "khanacademy", "newrelic", "sendbird", "smartasset", "udemy",
            "upwork", "yext", "zscaler",
        })
        self.assertEqual(sources["lever"], ["palantir"])
        self.assertEqual(set(sources["ashby"]), {
            "notion", "benchling", "ramp", "plaid", "linear", "vanta",
            "posthog", "moderntreasury", "anyscale", "perplexity", "runway",
            "harvey", "decagon", "cognition", "sierra", "cursor", "baseten",
            "modal", "pinecone", "langchain", "llamaindex", "supabase",
            "neon", "materialize", "motherduck", "semgrep", "crusoe",
            "skydio", "pylon", "orb", "openai",
        })
        self.assertTrue(all(
            len(slugs) == len(set(slugs))
            for slugs in sources.values()
        ))

        fetches = job_alert.configured_source_fetches(sources)
        configured_names = {source.name for source in fetches}
        self.assertEqual(len(fetches), 108)
        self.assertIn("greenhouse/zscaler", configured_names)
        self.assertIn("lever/palantir", configured_names)
        self.assertIn("ashby/openai", configured_names)
        self.assertIn("workable/renewhome", configured_names)


if __name__ == "__main__":
    unittest.main()
