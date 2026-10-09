import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pipeline", ROOT / "scripts" / "pipeline.py")
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)

EPISODE = ROOT / "stories" / "lion" / "part-01.json"


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.ep = json.loads(EPISODE.read_text(encoding="utf-8"))

    def test_sample_episode_is_valid(self):
        self.assertEqual(pipeline.validate(self.ep), [])

    def test_hook_longer_than_two_seconds_rejected(self):
        ep = copy.deepcopy(self.ep)
        ep["hook"]["seconds"] = 5
        self.assertTrue(any("hook.seconds" in e for e in pipeline.validate(ep)))

    def test_too_long_episode_rejected(self):
        ep = copy.deepcopy(self.ep)
        ep["scenes"][0]["seconds"] = 90
        self.assertTrue(any("exceeds" in e for e in pipeline.validate(ep)))

    def test_missing_scene_key_rejected(self):
        ep = copy.deepcopy(self.ep)
        del ep["scenes"][1]["image_prompt"]
        self.assertTrue(any("image_prompt" in e for e in pipeline.validate(ep)))

    def test_unverified_neuron_cost_blocks_real_run(self):
        plan = pipeline.quota_plan(self.ep, None)
        self.assertEqual(plan["status"], "blocked")

    def test_quota_ok_within_budget(self):
        plan = pipeline.quota_plan(self.ep, 10)  # 7 images * 10 = 70 < 8000
        self.assertEqual(plan["status"], "ok")
        self.assertEqual(plan["images"], 7)

    def test_quota_over_budget(self):
        plan = pipeline.quota_plan(self.ep, 2000)  # 14000 > 8000
        self.assertEqual(plan["status"], "over_budget")


if __name__ == "__main__":
    unittest.main()
