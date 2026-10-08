# didactic-octo-meme

## Goal
Build a **learns-from-nothing** security research prototype where the oracle is fully programmatic:
- **Direction A (primary):** neural-guided coverage fuzzing with corpus self-repair.
- **Direction B (secondary):** genetic-improvement patch search validated only by tests.

No labeled dataset is required; fitness comes from runtime coverage, sanitizer/crash signals, and test outcomes.

## Direction A: Neural-guided evolutionary fuzzer

### Environment (no dataset)
- Target: a real OSS parser with a harness (recommended: small C JSON parser first).
- Instrumentation: AFL++/libFuzzer-style coverage instrumentation.
- Oracle: each execution yields coverage delta, crash/sanitizer result, and runtime cost.

### Genome
Each seed stores:
- input bytes
- mutation strategy state (mutator weights, aggressiveness, focus offsets)

### Fitness
Multi-objective score from:
- new edges/paths discovered
- crash/sanitizer findings
- execution throughput
- input size (smaller preferred when equivalent)

### Core loop (baseline)
1. Select promising seeds.
2. Mutate.
3. Execute instrumented target.
4. Keep seeds that improve fitness/coverage.
5. Prune redundant seeds.

### Learned mutation layer
Online model trained only from fuzzer history:
- Training tuples: `(input features, mutation type/location, new_coverage? yes/no)`
- Output: mutation-type and byte-position priors used by the mutator.
- Retraining: periodic (time- or sample-based).

### Self-repair loop
Detect stale corpus members that no longer reproduce their previous path signal (e.g., after minimization or target drift), then regenerate replacements from nearest surviving seed families.

**Primary benchmark metric:**
- Deliberately drop 30% corpus.
- Measure iterations/time required to regrow prior coverage.

### Self-* features in scope (prioritized)
1. **Self-tuning:** bandit-based mutator scheduling (UCB1/Thompson).
2. **Self-triaging:** crash dedupe + minimization + severity heuristics.
3. **Self-pruning:** periodic corpus minimization without coverage loss.
4. **Self-benchmarking:** run a shadow AFL++ baseline and report relative gain.
5. **Self-archiving:** novelty memory / hall-of-fame for rare-but-valuable seeds.
6. **Self-diagnosing:** stall detection triggers automatic strategy shifts.

### Safety constraints
- Per-input CPU/memory/time caps.
- Sandbox execution.
- Kill-switch on pathological resource usage.

## Direction B: Automated repair via genetic improvement

Given failing tests, evolve patch candidates (AST-level delete/insert/swap or equivalent transforms).

### Fitness
- maximize tests fixed
- minimize regressions on previously passing tests

### Required safeguard: self-validation
Patch candidates must be checked against **held-out tests** not optimized during search to reduce test-suite overfitting.

### Optional accelerator
LLM-proposed patch hypotheses may be used as candidate generators, but acceptance is strictly test-oracle based.

## Evaluation plan

### Baseline vs guided fuzzing
- Compare plain AFL++ loop vs learned-mutation loop.
- Report time-to-first-crash, coverage-over-time, and exec/s.

### Self-repair quality
- Corpus-damage experiments (e.g., 10/30/50% deletion).
- Report coverage recovery curve and recovery half-life.

### Repair quality
- Pass rate on optimization tests.
- Generalization rate on held-out tests.

## Build order
1. Stand up target + harness + baseline coverage loop.
2. Add online mutation model.
3. Add corpus self-repair + damage benchmark.
4. Add triage/pruning/diagnostics.
5. Add genetic-improvement repair with held-out validation.
