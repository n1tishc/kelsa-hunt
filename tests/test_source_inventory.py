import json
import pathlib
import unittest

import growth_guardrail
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
            {"greenhouse": 100, "lever": 5, "ashby": 82},
        )
        self.assertTrue({"deepgram", "granola", "wayve"}.issubset(sources["ashby"]))
        self.assertEqual(sources["lever"][2], "palantir")
        self.assertTrue(all(
            len(slugs) == len(set(slugs))
            for slugs in sources.values()
        ))

        fetches = job_alert.configured_source_fetches(sources)
        configured_names = {source.name for source in fetches}
        self.assertEqual(len(fetches), 195)
        self.assertIn("greenhouse/zscaler", configured_names)
        self.assertIn("lever/palantir", configured_names)
        self.assertIn("ashby/openai", configured_names)
        self.assertIn("workable/renewhome", configured_names)
        self.assertIn("recruitee/aetherflux", configured_names)
        self.assertIn("ambicuity", configured_names)

    def test_no_slug_is_configured_on_more_than_one_platform(self):
        sources = json.loads((ROOT / "sources.json").read_text())
        self.assertEqual(growth_guardrail.duplicate_source_names(sources), {})

    def test_shard_sources_splits_boards_without_overlap_or_loss(self):
        sources = json.loads((ROOT / "sources.json").read_text())

        shard0 = job_alert.shard_sources(sources, 0, 2)
        shard1 = job_alert.shard_sources(sources, 1, 2)
        fetches = job_alert.configured_source_fetches(sources)
        names0 = {f.name for f in job_alert.configured_source_fetches(shard0)}
        names1 = {f.name for f in job_alert.configured_source_fetches(shard1)}
        always_on = {"simplify", "ambicuity"}

        self.assertEqual(names0 & names1, always_on)
        self.assertEqual(
            names0 | names1,
            {source.name for source in fetches},
        )
        # Neither shard should carry more than a handful extra over an even split.
        self.assertLessEqual(abs(len(names0) - len(names1)), 5)


if __name__ == "__main__":
    unittest.main()
