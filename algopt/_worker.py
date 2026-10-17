"""Internal worker: measures exactly one case in its own process.

Invoked by ``algopt.bench`` as::

    python -m algopt._worker one <case_id> <variant> <repeat> <quick:0|1>
    python -m algopt._worker interleave <case_id> <rounds> <quick:0|1>

It exists as a separate process so that one variant's allocations, GC state and
warm caches cannot leak into the next variant's timing.
"""

from __future__ import annotations

import json
import sys
import time

from . import bench


def _one(case_id: str, variant: str, repeat: int, quick: bool) -> dict:
    case = bench.case_by_id(case_id, quick)
    fn = case.resolve(variant)
    args = case.prepare()
    if case.check is not None:
        case.check(fn)
    out = bench.measure(fn, args, repeat)
    out["case"] = case_id
    out["variant"] = variant
    return out


def _interleave(case_id: str, rounds: int, quick: bool) -> dict:
    case = bench.case_by_id(case_id, quick)
    args = case.prepare()
    resolved = {}
    for variant in case.variants:
        fn = case.resolve(variant)
        if case.check is not None:
            case.check(fn)
        resolved[variant] = fn

    # warm everything once so no variant pays first-call costs inside a round
    for fn in resolved.values():
        fn(*args)

    times = {variant: [] for variant in case.variants}
    for _ in range(rounds):
        for variant, fn in resolved.items():
            start = time.perf_counter()
            fn(*args)
            times[variant].append(time.perf_counter() - start)

    base = case.variants[0]
    variants = {
        variant: {
            "best_ms": min(v) * 1000.0,
            "median_ms": sorted(v)[len(v) // 2] * 1000.0,
            "runs_ms": [round(t * 1000.0, 6) for t in v],
        }
        for variant, v in times.items()
    }
    # guard against a zero-duration round (a case fast enough to read as 0.0)
    ratios = {
        variant: sorted(
            times[variant][i] / max(times[base][i], 1e-9) for i in range(rounds)
        )[rounds // 2]
        for variant in times
    }
    return {"case": case_id, "rounds": rounds, "variants": variants, "ratios": ratios}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    kind = argv[0]
    if kind == "one":
        _, case_id, variant, repeat, quick = argv
        out = _one(case_id, variant, int(repeat), quick == "1")
    elif kind == "interleave":
        _, case_id, rounds, quick = argv
        out = _interleave(case_id, int(rounds), quick == "1")
    else:
        raise SystemExit(f"unknown worker mode: {kind}")
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
