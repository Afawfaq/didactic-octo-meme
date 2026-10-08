from __future__ import annotations

import json

try:
    from .engine import FuzzerConfig, FuzzerEngine
    from .genetic_repair import GeneticRepair
except ImportError:  # allow running as a script from the package directory
    from engine import FuzzerConfig, FuzzerEngine
    from genetic_repair import GeneticRepair


def run_pipeline() -> dict:
    baseline_engine = FuzzerEngine(FuzzerConfig(iterations=1500, use_learned_guidance=False))
    baseline = baseline_engine.run()

    guided_engine = FuzzerEngine(FuzzerConfig(iterations=1500, use_learned_guidance=True))
    guided = guided_engine.run()
    repair_stats = guided_engine.damage_and_repair(damage_ratio=0.3, max_iters=1000)

    repair = GeneticRepair().search()

    return {
        "direction_a": {
            "baseline": {
                "coverage": baseline.coverage_over_time[-1][1],
                "coverage_over_time": baseline.coverage_over_time,
                "exec_per_sec": round(baseline.exec_per_sec, 2),
                "time_to_first_crash": baseline.time_to_first_crash,
                "unique_crashes": baseline.unique_crashes,
                "mutation_success_by_op": baseline.mutation_success_by_op,
                "crash_classes": baseline.crash_classes,
            },
            "guided": {
                "coverage": guided.coverage_over_time[-1][1],
                "coverage_over_time": guided.coverage_over_time,
                "exec_per_sec": round(guided.exec_per_sec, 2),
                "time_to_first_crash": guided.time_to_first_crash,
                "unique_crashes": guided.unique_crashes,
                "mutation_success_by_op": guided.mutation_success_by_op,
                "crash_classes": guided.crash_classes,
            },
            "comparison": {
                "coverage_gain": guided.coverage_over_time[-1][1] - baseline.coverage_over_time[-1][1],
                "exec_per_sec_ratio": round(
                    guided.exec_per_sec / baseline.exec_per_sec if baseline.exec_per_sec else 0.0, 3
                ),
                "crash_gain": guided.unique_crashes - baseline.unique_crashes,
            },
            "damage_repair": repair_stats,
            "diagnosis_events": guided_engine.diagnosis_events,
            "final_corpus_size": len(guided_engine.corpus),
        },
        "direction_b": {
            "found_patch": repair.found_patch,
            "generations": repair.generations,
            "best_train_score": repair.best_train_score,
            "heldout_score": repair.heldout_score,
            "candidate": repair.candidate,
        },
    }


if __name__ == "__main__":
    print(json.dumps(run_pipeline(), indent=2))
