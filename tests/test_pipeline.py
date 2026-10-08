from selfplay_fuzz.engine import FuzzerConfig, FuzzerEngine
from selfplay_fuzz.genetic_repair import GeneticRepair
from selfplay_fuzz.run import run_pipeline


def test_guided_fuzzer_runs_and_collects_metrics():
    engine = FuzzerEngine(FuzzerConfig(iterations=400, use_learned_guidance=True))
    metrics = engine.run()
    assert metrics.exec_per_sec > 0
    assert metrics.coverage_over_time[-1][1] > 0


def test_damage_and_repair_contract():
    engine = FuzzerEngine(FuzzerConfig(iterations=400, use_learned_guidance=True))
    engine.run()
    stats = engine.damage_and_repair(damage_ratio=0.3, max_iters=400)
    assert "iterations_to_recover" in stats
    assert stats["coverage_before"] >= stats["coverage_after_damage"]


def test_genetic_repair_uses_heldout_validation():
    result = GeneticRepair().search(generations=60, population=8)
    assert result.best_train_score > 0
    assert result.heldout_score >= 0


def test_end_to_end_pipeline_shape():
    report = run_pipeline()
    assert "direction_a" in report
    assert "baseline" in report["direction_a"]
    assert "direction_b" in report
