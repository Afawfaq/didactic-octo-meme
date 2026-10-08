import unittest
import pathlib
import subprocess
import sys

from selfplay_fuzz.engine import FuzzerConfig, FuzzerEngine
from selfplay_fuzz.genetic_repair import GeneticRepair
from selfplay_fuzz.run import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_engine_module_runs_as_script(self):
        repo_root = pathlib.Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, str(repo_root / "selfplay_fuzz" / "engine.py")],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_guided_fuzzer_runs_and_collects_metrics(self):
        engine = FuzzerEngine(FuzzerConfig(iterations=400, use_learned_guidance=True))
        metrics = engine.run()
        self.assertGreater(metrics.exec_per_sec, 0)
        self.assertGreater(metrics.coverage_over_time[-1][1], 0)
        self.assertGreater(len(metrics.coverage_over_time), 0)
        self.assertIn("bit_flip", metrics.mutation_success_by_op)

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
        self.assertIn("comparison", report["direction_a"])
        self.assertIn("coverage_over_time", report["direction_a"]["guided"])
        self.assertIn("direction_b", report)


if __name__ == "__main__":
    unittest.main()
