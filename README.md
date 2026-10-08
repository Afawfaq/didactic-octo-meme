# didactic-octo-meme

Prototype implementation of:
- **Direction A:** neural-guided coverage fuzzing with self-repair/self-* instrumentation.
- **Direction B:** genetic-improvement repair validated with held-out tests.

## Run

```bash
python -m selfplay_fuzz.run
```

This prints JSON including:
- baseline vs guided coverage
- exec/s
- time-to-first-crash
- corpus damage/recovery metrics (30% deletion)
- repair search held-out validation score

## Test

```bash
python -m unittest discover -s tests -q
```
