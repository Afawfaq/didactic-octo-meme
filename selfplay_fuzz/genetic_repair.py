from __future__ import annotations

from dataclasses import dataclass
import random


def classify_number(n: int) -> str:
    if n % 15 == 0:
        return "fizzbuzz"
    if n % 3 == 0:
        return "buzz"
    if n % 5 == 0:
        return "fizz"
    return "other"


@dataclass
class PatchResult:
    found_patch: bool
    generations: int
    best_train_score: int
    heldout_score: int
    candidate_order: list[int]


class GeneticRepair:
    def __init__(self, seed: int = 13):
        self.rnd = random.Random(seed)
        self.base_order = [0, 1, 2]  # statement order for divisibility checks after fizzbuzz
        self.training = [(3, "fizz"), (5, "buzz"), (2, "other"), (15, "fizzbuzz")]
        self.heldout = [(6, "fizz"), (10, "buzz"), (30, "fizzbuzz"), (7, "other")]

    def _run_candidate(self, order: list[int], n: int) -> str:
        checks = [(3, "buzz"), (5, "fizz"), (15, "fizzbuzz")]
        if n % 15 == 0:
            return "fizzbuzz"
        for idx in order:
            d, out = checks[idx]
            if n % d == 0:
                return out
        return "other"

    def _score(self, order: list[int], cases: list[tuple[int, str]]) -> int:
        return sum(1 for n, expected in cases if self._run_candidate(order, n) == expected)

    def _mutate(self, order: list[int]) -> list[int]:
        cand = order[:]
        i, j = self.rnd.sample(range(len(cand)), 2)
        cand[i], cand[j] = cand[j], cand[i]
        return cand

    def search(self, generations: int = 80, population: int = 10) -> PatchResult:
        pop = [self.base_order[:]]
        for _ in range(population - 1):
            cand = self.base_order[:]
            self.rnd.shuffle(cand)
            pop.append(cand)

        best = pop[0]
        best_score = self._score(best, self.training)

        for gen in range(1, generations + 1):
            scored = sorted(((self._score(c, self.training), c) for c in pop), reverse=True)
            best_score, best = scored[0]
            if best_score == len(self.training):
                heldout = self._score(best, self.heldout)
                return PatchResult(True, gen, best_score, heldout, best)

            next_pop = [best]
            elites = [c for _, c in scored[:3]]
            while len(next_pop) < population:
                parent = self.rnd.choice(elites)
                next_pop.append(self._mutate(parent))
            pop = next_pop

        heldout = self._score(best, self.heldout)
        return PatchResult(False, generations, best_score, heldout, best)
