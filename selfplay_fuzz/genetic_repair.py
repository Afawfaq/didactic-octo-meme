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
    candidate: dict[str, str]


class GeneticRepair:
    def __init__(self, seed: int = 13):
        self.rnd = random.Random(seed)
        self.base_candidate = {"3": "buzz", "5": "fizz"}
        self.training = [(3, "fizz"), (5, "buzz"), (2, "other"), (15, "fizzbuzz")]
        self.heldout = [(6, "fizz"), (10, "buzz"), (30, "fizzbuzz"), (7, "other")]

    def _run_candidate(self, candidate: dict[str, str], n: int) -> str:
        if n % 15 == 0:
            return "fizzbuzz"
        if n % 3 == 0:
            return candidate["3"]
        if n % 5 == 0:
            return candidate["5"]
        return "other"

    def _score(self, candidate: dict[str, str], cases: list[tuple[int, str]]) -> int:
        return sum(1 for n, expected in cases if self._run_candidate(candidate, n) == expected)

    def _mutate(self, candidate: dict[str, str]) -> dict[str, str]:
        cand = dict(candidate)
        if self.rnd.random() < 0.5:
            cand["3"], cand["5"] = cand["5"], cand["3"]
        else:
            key = self.rnd.choice(["3", "5"])
            cand[key] = self.rnd.choice(["fizz", "buzz"])
        return cand

    def search(self, generations: int = 40, population: int = 8) -> PatchResult:
        pop = [dict(self.base_candidate)]
        while len(pop) < population:
            pop.append(self._mutate(self.base_candidate))

        best = pop[0]
        best_score = self._score(best, self.training)

        for gen in range(1, generations + 1):
            scored = sorted(((self._score(c, self.training), c) for c in pop), key=lambda x: x[0], reverse=True)
            best_score, best = scored[0]
            if best_score == len(self.training):
                heldout = self._score(best, self.heldout)
                return PatchResult(True, gen, best_score, heldout, best)

            elites = [c for _, c in scored[:2]]
            next_pop = elites[:]
            while len(next_pop) < population:
                parent = self.rnd.choice(elites)
                next_pop.append(self._mutate(parent))
            pop = next_pop

        heldout = self._score(best, self.heldout)
        return PatchResult(False, generations, best_score, heldout, best)
