# Claims and their evidence

Every performance sentence in `README.md`, mapped to the case that produces it.
Numbers are from `benchmarks/results.json` (isolated mode, best of N) and
`benchmarks/results-interleaved.json` (per-round ratios) on 2026-10-17:
CPython 3.13.14, Windows 11 10.0.26300, Ryzen 7 H 255.

| # | Claim | Case id | Reproduce | Isolated | Interleaved |
|---|---|---|---|---|---|
| 1 | Pairwise min/max uses 25% fewer comparisons | — | `python benchmarks/count_comparisons.py` | 2,000 → 1,500 at n=1001, exact | — |
| 2 | …but is 1.58× **slower** than the naive loop | `min-max/3000k` | `python -m benchmarks.run_all` | 127.73 / 80.82 ms | 1.51× |
| 3 | The same algorithm with `zip(it, it)` is faster than naive | `min-max/3000k` | same | 60.10 / 80.82 ms = 0.74× | 0.76× |
| 4 | `min()/max()` beats everything, at the same comparison count | `min-max/3000k` | same | 38.54 ms = 0.48× | 0.48× |
| 5 | Removing the `arr[1:]` copy does not rescue the naive baseline | `min-max/3000k` | same | 88.08 ms = 1.09× | 1.16× |
| 6 | Cache blocking gives no reproducible gain | `matmul/128`, `/160`, `/192` | same | 1.01–1.25× | 0.91–1.06× |
| 7 | `zip` + `sum(map(mul))` is 1.3–1.5× faster | `matmul/128`, `/160`, `/192` | same | 0.66–0.75× | 0.65–0.81× |
| 8 | Early exit alone explains the near-sorted win | `sort/sorted/2000`, `sort/adjacent-50/2000` | same | 0.0716 vs 0.0718 ms | same rank |
| 9 | Bidirectional alone explains the far-apart win | `sort/far-50/2000` | same | 6.82 ms vs 69.56 ms for early | 0.09× |
| 10 | Cocktail is slower on reversed input | `sort/reversed/2000` | same | 155.28 / 150.30 = 1.03× | 1.11× |
| 11 | Naive Fibonacci grows by ~1.6× per n | `fib/naive/25..32` | same | 9.64 → 282.35 ms | — |
| 12 | Matrix version overtakes DP between n=100 and n=1000 | `fib/dp/*`, `fib/matrix/*` | same | 0.85× at 100, 0.24× at 1000 | — |
| 13 | Both fast versions are superlinear in wall clock | `fib/dp/1000..100000` | same | 2290× for 100× n | — |

## Notes on the two modes

`isolated` spawns one process per (case, variant) and reports the best of N runs.
Use it for the numbers you quote.

`interleaved` runs every variant of a case once per round in a single process and
reports the median of the per-round ratios. Use it to check that a difference is
real: on this laptop absolute times drift by up to 40% between runs, while the
ratios stay within ±10%.

Where the two columns disagree by more than that (claims 6 and 10), the honest
reading is "no reliable difference" or "small, direction-consistent effect", not
the larger of the two numbers. Claim 6 is the worst case: isolated says 1.01–1.25×,
interleaved says 0.91–1.06×, so the sign flips — which is why the README calls it
"no reproducible gain" rather than "slower".

## What is deliberately not claimed

- No claim that the blocking implementation is wrong — it is correct, and the
  tests pin it against the naive version at six block sizes. It is simply the
  wrong layer for CPython.
- No claim about PyPy, Cython, NumPy or C. The whole point is that the cost model
  changes with the runtime.
- No cross-machine comparison. Every number here is from one machine, recorded
  with its CPU and interpreter version in `RESULTS.md`.
