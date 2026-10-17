# Contributing

Small repo, two rules.

## 1. Every performance claim needs a command

If a README sentence says "1.5x", there must be a case in `algopt/bench.py` that
prints that number. Add the case first, run it, then write the sentence.

Numbers go stale. If you change an implementation, re-run:

```bash
python -m benchmarks.run_all --json benchmarks/results.json --markdown benchmarks/RESULTS.md
python -m benchmarks.run_all --mode interleaved
```

and update the tables in both READMEs.

## 2. Don't "simplify" the benchmark

It looks like a lot of ceremony for measuring four little functions. It is the
minimum needed to make the numbers mean anything.

**One process per (case, variant).** Not one process for the whole run. A
variant that allocates 3 million integers leaves a different heap and GC state
behind; whatever runs next is measured on a dirtier machine. In this repository
the effect is small, but in the sibling projects it has flipped conclusions: an
eager CSV reader that allocated 57 MB made the *next* algorithm look 2.4x slower
than it was.

**Best of N, not the mean.** Interference (a virus scan, a browser tab, thermal
throttling) can only make one run slower, never faster, so the minimum is the
least contaminated estimate. The mean tells you about your desktop, not about the
code. `median_ms` is reported too, for honesty, but claims use the best.

**Warm up once before timing.** The first call pays for lazy imports, branch
predictor warm-up and (in some cases) page faults.

**Fixed seeds.** `algopt/data.py` is the only source of inputs, and every
generator takes a seed. A benchmark whose input changes between runs cannot
support a comparison — the original version of this repo used bare
`random.randint` and produced two different conclusions from the same command.

**Interleaved mode for ratios.** On a laptop, absolute times drift by 40%
between runs (this was measured: the same naive loop took 123 ms and 173 ms in
two consecutive isolated runs). What stays stable is the *ratio* measured inside
one round, because drift hits every variant equally. So: use `--mode isolated`
for the numbers you quote, and `--mode interleaved` to confirm a difference is
real before you quote it.

If a "simplification" makes two of those paragraphs false, it isn't one.

## Adding a variant

1. Put the implementation in `algopt/<group>.py`, with a docstring saying what it
   costs and why.
2. Register it in the matching `*_FNS` dict in `algopt/bench.py`.
3. Add a case (or a variant to an existing case) in `build_cases`.
4. Add a correctness test in `tests/test_implementations.py` — the harness guard
   catches a broken function, but the test is what pins the expected values.
5. Re-run and update the tables.

## Running the checks

```bash
python -m unittest discover -s tests -t . -v   # 32 tests, ~0.5 s
python benchmarks/count_comparisons.py          # comparison counts, ~1 s
python -m benchmarks.run_all --quick            # harness smoke test, ~5 s
```
