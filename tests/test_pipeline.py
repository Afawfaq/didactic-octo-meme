import unittest

from selfplay_fuzz.engine import FuzzerConfig, FuzzerEngine
from selfplay_fuzz.genetic_repair import GeneticRepair
from selfplay_fuzz.run import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_guided_fuzzer_runs_and_collects_metrics(self):
        engine = FuzzerEngine(FuzzerConfig(iterations=400, use_learned_guidance=True))
        metrics = engine.run()
        self.assertGreater(metrics.exec_per_sec, 0)
        self.assertGreater(metrics.coverage_over_time[-1][1], 0)

    def test_damage_and_repair_contract(self):
        engine = FuzzerEngine(FuzzerConfig(iterations=400, use_learned_guidance=True))
        engine.run()
        stats = engine.damage_and_repair(damage_ratio=0.3, max_iters=400)
        self.assertIn("iterations_to_recover", stats)
        self.assertGreaterEqual(stats["coverage_before"], stats["coverage_after_damage"])

    def test_genetic_repair_uses_heldout_validation(self):
        result = GeneticRepair().search(generations=40, population=8)
        self.assertTrue(result.found_patch)
        self.assertEqual(result.best_train_score, 4)
        self.assertGreaterEqual(result.heldout_score, 3)

    def test_end_to_end_pipeline_shape(self):
        report = run_pipeline()
        self.assertIn("direction_a", report)
        self.assertIn("baseline", report["direction_a"])
        self.assertIn("direction_b", report)


if __name__ == "__main__":
    unittest.main()
