from __future__ import annotations

from dataclasses import dataclass, field
import random
import time

from .mutators import MUTATORS, mutate
from .neural_guidance import LearnedMutationModel
from .target_json import evaluate_input


@dataclass
class Seed:
    data: bytes
    edges: set[str]


@dataclass
class RunMetrics:
    coverage_over_time: list[tuple[int, int]] = field(default_factory=list)
    exec_per_sec: float = 0.0
    time_to_first_crash: float | None = None
    unique_crashes: int = 0
    mutation_success_by_op: dict[str, dict[str, int]] = field(default_factory=dict)
    crash_classes: dict[str, int] = field(default_factory=dict)


@dataclass
class FuzzerConfig:
    iterations: int = 2500
    random_seed: int = 7
    use_learned_guidance: bool = False
    self_prune_every: int = 250
    self_diagnose_window: int = 200
    coverage_sample_every: int = 100


class FuzzerEngine:
    def __init__(self, config: FuzzerConfig):
        self.config = config
        self.rnd = random.Random(config.random_seed)
        self.model = LearnedMutationModel()
        self.corpus: list[Seed] = [
            Seed(b"{}", set()),
            Seed(b"[]", set()),
            Seed(b"\"x\"", set()),
        ]
        self.global_edges: set[str] = set()
        self.crash_signatures: set[str] = set()
        self.hall_of_fame: list[bytes] = []
        self.op_plays = {m: 1 for m in MUTATORS}
        self.op_rewards = {m: 1.0 for m in MUTATORS}
        self.last_new_edge_iter = 0
        self.diagnosis_events: list[str] = []
        self.crash_classes: dict[str, int] = {}

        for seed in self.corpus:
            result = evaluate_input(seed.data)
            seed.edges = result.edges
            self.global_edges |= result.edges

    def _ucb1_op(self) -> str:
        total = sum(self.op_plays.values())
        best = None
        best_score = -1.0
        for op in MUTATORS:
            mean = self.op_rewards[op] / self.op_plays[op]
            bonus = (2 * (total.bit_length()) / self.op_plays[op]) ** 0.5
            score = mean + bonus
            if score > best_score:
                best_score = score
                best = op
        return best or MUTATORS[0]

    def _choose_seed(self) -> Seed:
        return self.rnd.choice(self.corpus)

    def _prune(self) -> None:
        needed = set(self.global_edges)
        kept: list[Seed] = []
        for seed in sorted(self.corpus, key=lambda s: len(s.edges), reverse=True):
            if not needed:
                break
            contrib = seed.edges & needed
            if contrib:
                kept.append(seed)
                needed -= contrib
        if not kept:
            kept = self.corpus[:1]
        self.corpus = kept

    def _triage(self, signature: str) -> bool:
        if signature in self.crash_signatures:
            return False
        self.crash_signatures.add(signature)
        crash_class = signature.split(":", 1)[0]
        self.crash_classes[crash_class] = self.crash_classes.get(crash_class, 0) + 1
        return True

    def run(self, iterations: int | None = None) -> RunMetrics:
        limit = iterations or self.config.iterations
        start = time.time()
        first_crash_at = None
        coverage_samples: list[tuple[int, int]] = []
        op_attempts = {m: 0 for m in MUTATORS}
        op_success = {m: 0 for m in MUTATORS}

        for i in range(1, limit + 1):
            seed = self._choose_seed()
            corpus_bytes = [s.data for s in self.corpus]

            op = self.model.choose_op(self.rnd) if self.config.use_learned_guidance else self._ucb1_op()
            focus = self.model.choose_focus(len(seed.data), self.rnd) if self.config.use_learned_guidance else None
            op_attempts[op] += 1

            child = mutate(seed.data, op, focus, corpus_bytes, self.rnd)
            result = evaluate_input(child)

            new_edges = result.edges - self.global_edges
            improved = bool(new_edges)

            if improved:
                self.global_edges |= new_edges
                self.corpus.append(Seed(child, result.edges))
                self.hall_of_fame.append(child)
                self.last_new_edge_iter = i
                op_success[op] += 1

            if result.crashed and result.crash_signature and self._triage(result.crash_signature):
                if first_crash_at is None:
                    first_crash_at = time.time() - start

            self.model.update(op, focus, improved)
            self.op_plays[op] += 1
            self.op_rewards[op] += 1.0 if improved else 0.0

            if i % self.config.self_prune_every == 0:
                self._prune()

            if i - self.last_new_edge_iter >= self.config.self_diagnose_window:
                self.diagnosis_events.append(f"stall@{i}")
                self.op_rewards["dictionary_insert"] += 2.0
                self.last_new_edge_iter = i

            if i % 100 == 0:
                self.corpus.sort(key=lambda s: len(s.edges), reverse=True)

            if i % self.config.coverage_sample_every == 0:
                coverage_samples.append((i, len(self.global_edges)))

        elapsed = max(time.time() - start, 1e-6)
        if not coverage_samples or coverage_samples[-1][0] != limit:
            coverage_samples.append((limit, len(self.global_edges)))
        return RunMetrics(
            coverage_over_time=coverage_samples,
            exec_per_sec=limit / elapsed,
            time_to_first_crash=first_crash_at,
            unique_crashes=len(self.crash_signatures),
            mutation_success_by_op={
                op: {"attempts": op_attempts[op], "successes": op_success[op]} for op in MUTATORS
            },
            crash_classes=dict(self.crash_classes),
        )

    def damage_and_repair(self, damage_ratio: float = 0.3, max_iters: int = 1200) -> dict[str, float | int | bool]:
        target_coverage = len(self.global_edges)
        drop_count = max(1, int(len(self.corpus) * damage_ratio))
        survivors = self.corpus[:]
        self.rnd.shuffle(survivors)
        self.corpus = survivors[drop_count:] or survivors[-1:]
        self.global_edges = set().union(*(s.edges for s in self.corpus))

        start = time.time()
        recovered = len(self.global_edges) >= target_coverage
        spent = 0
        while not recovered and spent < max_iters:
            self.run(iterations=100)
            spent += 100
            recovered = len(self.global_edges) >= target_coverage

        return {
            "coverage_before": target_coverage,
            "coverage_after_damage": len(set().union(*(s.edges for s in survivors[drop_count:]))) if survivors[drop_count:] else 0,
            "coverage_after_repair": len(self.global_edges),
            "iterations_to_recover": spent,
            "seconds_to_recover": round(time.time() - start, 4),
            "recovered": recovered,
        }
