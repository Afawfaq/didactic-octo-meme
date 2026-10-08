from __future__ import annotations

from dataclasses import dataclass, field
import random

try:
    from .mutators import MUTATORS
except ImportError:  # allow running as a script from the package directory
    from mutators import MUTATORS


@dataclass
class LearnedMutationModel:
    op_success: dict[str, int] = field(default_factory=lambda: {m: 1 for m in MUTATORS})
    op_fail: dict[str, int] = field(default_factory=lambda: {m: 1 for m in MUTATORS})
    pos_success: dict[int, int] = field(default_factory=dict)
    pos_fail: dict[int, int] = field(default_factory=dict)

    def choose_op(self, rnd: random.Random) -> str:
        scores = {
            op: rnd.betavariate(self.op_success[op], self.op_fail[op]) for op in MUTATORS
        }
        return max(scores, key=scores.get)

    def choose_focus(self, seed_len: int, rnd: random.Random) -> int | None:
        if seed_len == 0:
            return None
        if not self.pos_success:
            return rnd.randrange(seed_len)
        sampled = []
        for i in range(seed_len):
            a = self.pos_success.get(i, 1)
            b = self.pos_fail.get(i, 1)
            sampled.append((rnd.betavariate(a, b), i))
        sampled.sort(reverse=True)
        return sampled[0][1]

    def update(self, op: str, focus: int | None, improved: bool) -> None:
        if improved:
            self.op_success[op] += 1
            if focus is not None:
                self.pos_success[focus] = self.pos_success.get(focus, 1) + 1
        else:
            self.op_fail[op] += 1
            if focus is not None:
                self.pos_fail[focus] = self.pos_fail.get(focus, 1) + 1
