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
            {"greenhouse": 91, "lever": 5, "ashby": 70},
        )
        self.assertTrue({"deepgram", "granola", "wayve"}.issubset(sources["ashby"]))
        self.assertEqual(sources["lever"][2], "palantir")
        self.assertTrue(all(
            len(slugs) == len(set(slugs))
            for slugs in sources.values()
        ))

        fetches = job_alert.configured_source_fetches(sources)
        configured_names = {source.name for source in fetches}
        self.assertEqual(len(fetches), 174)
        self.assertIn("greenhouse/zscaler", configured_names)
        self.assertIn("lever/palantir", configured_names)
        self.assertIn("ashby/openai", configured_names)
        self.assertIn("workable/renewhome", configured_names)
        self.assertIn("recruitee/aetherflux", configured_names)
        self.assertIn("ambicuity", configured_names)


if __name__ == "__main__":
    unittest.main()
