"""Measurement harness.

A laptop's absolute timings drift (thermal throttling, background processes,
a governor that changes its mind). So the harness offers two modes, and it is
worth knowing which one you are looking at:

``isolated``
    One subprocess per (case, variant), best of N. This is the mode the numbers
    in ``README.md`` come from. "Best of N" is the ``timeit`` convention:
    interference can only make a single run slower, never faster.

``interleaved``
    One process per case; every variant runs once per round. Reports the median
    of the per-round *ratios*. Slow drift affects all variants in a round
    equally, so a ratio survives even when the absolute milliseconds do not.
    Use this to decide whether a difference is real before quoting it.

Every case re-checks its variant on a tiny input before timing it, so a
benchmark cannot quietly measure a broken function.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from . import data, fibonacci, matmul, min_max, sorting

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SORT_FNS = {
    "naive": sorting.bubble_sort,
    "early": sorting.bubble_sort_early,
    "cocktail": sorting.cocktail_sort,
}

MINMAX_FNS = {
    "naive": min_max.min_max_naive,
    "naive-nocopy": min_max.min_max_naive_nocopy,
    "pairwise-indexed": min_max.min_max_pairwise_indexed,
    "pairwise": min_max.min_max_pairwise,
    "builtin": min_max.min_max_builtin,
}

FIB_FNS = {
    "naive": fibonacci.fib_naive,
    "dp": fibonacci.fib_dp,
    "matrix": fibonacci.fib_matrix,
}


# --------------------------------------------------------------------------- #
# tiny correctness guards (run once per process, ~1 ms)
# --------------------------------------------------------------------------- #
def _check_sort(fn):
    sample = [5, 3, 8, 1, 9, 2, 7, 4, 6, 0, 3, 3, -1]
    if fn(sample) != sorted(sample):
        raise AssertionError(f"{fn} failed its guard on {sample}")


def _check_minmax(fn):
    sample = [5, 3, 8, 1, 9, 2, 7, 4, 6, 0, 3, 3, -1]
    if fn(sample) != (min(sample), max(sample)):
        raise AssertionError(f"{fn} failed its guard on {sample}")


def _check_fib(fn):
    if fn(20) != 6765:
        raise AssertionError(f"{fn} failed its guard: fib(20) != 6765")


def _check_matmul(fn):
    a, b = [[1, 2], [3, 4]], [[5, 6], [7, 8]]
    if fn(a, b) != [[19, 22], [43, 50]]:
        raise AssertionError(f"{fn} failed its guard")


@dataclass(frozen=True)
class Case:
    id: str
    group: str
    variants: tuple
    repeat: int
    prepare: object  # () -> args tuple
    resolve: object  # variant -> callable
    check: object = None  # callable -> None


def _matmul_resolve(variant):
    if variant.startswith("blocked-"):
        return functools.partial(matmul.matmul_blocked, block_size=int(variant.split("-")[1]))
    return {"naive": matmul.matmul_naive, "zip": matmul.matmul_zip}[variant]


def _sort_case(shape, n, repeat):
    return Case(
        id=f"sort/{shape}",
        group="sorting",
        variants=tuple(SORT_FNS),
        repeat=repeat,
        prepare=lambda: (data.sort_data(shape, n),),
        resolve=SORT_FNS.__getitem__,
        check=_check_sort,
    )


def _minmax_case(n, repeat):
    return Case(
        id=f"min-max/{n // 1000}k",
        group="min-max",
        variants=tuple(MINMAX_FNS),
        repeat=repeat,
        prepare=lambda: (data.int_list(n),),
        resolve=MINMAX_FNS.__getitem__,
        check=_check_minmax,
    )


def _fib_case(variant, n, repeat):
    return Case(
        id=f"fib/{variant}/{n}",
        group="fibonacci",
        variants=(variant,),
        repeat=repeat,
        prepare=lambda: (n,),
        resolve=lambda _v: FIB_FNS[variant],
        check=_check_fib,
    )


def _matmul_case(n, variants, repeat):
    return Case(
        id=f"matmul/{n}",
        group="matmul",
        variants=tuple(variants),
        repeat=repeat,
        prepare=lambda: data.square_matrices(n),
        resolve=_matmul_resolve,
        check=_check_matmul,
    )


def build_cases(quick: bool = False) -> list:
    """The full case list. ``quick=True`` shrinks every size for CI smoke runs."""
    repeat = 2 if quick else 5
    cases = [_sort_case(shape, 400 if quick else 2000, repeat) for shape in data.SORT_SHAPES]
    cases.append(_minmax_case(200_000 if quick else 3_000_000, repeat))

    if quick:
        cases.append(_fib_case("naive", 20, 2))
        for variant in ("dp", "matrix"):
            cases.append(_fib_case(variant, 1000, repeat))
    else:
        for n in (25, 28, 30, 32):
            cases.append(_fib_case("naive", n, 2))
        for variant in ("dp", "matrix"):
            for n in (100, 1_000, 10_000, 100_000):
                cases.append(_fib_case(variant, n, repeat))

    if quick:
        cases.append(_matmul_case(48, ("naive", "blocked-32", "zip"), repeat))
    else:
        cases.append(_matmul_case(128, ("naive", "blocked-32", "zip"), 5))
        cases.append(_matmul_case(160, ("naive", "blocked-8", "blocked-32", "blocked-64", "zip"), 5))
        cases.append(_matmul_case(192, ("naive", "blocked-32", "blocked-64", "zip"), 5))
    return cases


def case_by_id(case_id: str, quick: bool = False) -> Case:
    for case in build_cases(quick):
        if case.id == case_id:
            return case
    raise SystemExit(f"unknown case: {case_id}")


# --------------------------------------------------------------------------- #
# measurement
# --------------------------------------------------------------------------- #
def measure(fn, args, repeat: int, warmup: int = 1) -> dict:
    for _ in range(warmup):
        fn(*args)
    times = []
    for _ in range(repeat):
        start = time.perf_counter()
        fn(*args)
        times.append(time.perf_counter() - start)
    times.sort()
    return {
        "best_ms": times[0] * 1000.0,
        "median_ms": times[len(times) // 2] * 1000.0,
        "runs_ms": [round(t * 1000.0, 6) for t in times],
    }


def machine_info() -> dict:
    return {
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "cpu_count": os.cpu_count(),
    }


def _subprocess_env() -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = REPO_ROOT + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    env["PYTHONHASHSEED"] = "0"
    return env


def _worker(args: list) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "algopt._worker", *args],
        capture_output=True,
        text=True,
        env=_subprocess_env(),
        cwd=REPO_ROOT,
    )
    if proc.returncode != 0:
        raise SystemExit(f"worker failed: {' '.join(args)}\n{proc.stderr[-2000:]}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def run_isolated(cases, quick: bool, note=print) -> dict:
    results = {}
    for case in cases:
        row = {}
        for variant in case.variants:
            out = _worker(["one", case.id, variant, str(case.repeat), "1" if quick else "0"])
            row[variant] = out
            note(
                f"  {case.id:22s} {variant:18s} best={out['best_ms']:10.4f} ms"
                f"  median={out['median_ms']:10.4f} ms"
            )
        results[case.id] = {"group": case.group, "variants": row}
    return results


def run_interleaved(cases, quick: bool, note=print) -> dict:
    results = {}
    for case in cases:
        out = _worker(["interleave", case.id, str(case.repeat), "1" if quick else "0"])
        results[case.id] = {"group": case.group, "variants": out["variants"], "ratios": out["ratios"]}
        base = case.variants[0]
        for variant, stats in out["variants"].items():
            ratio = out["ratios"].get(variant)
            tail = "" if variant == base else f"  ratio vs {base} = {ratio:.3f}x"
            note(f"  {case.id:22s} {variant:18s} median={stats['median_ms']:10.4f} ms{tail}")
    return results


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #
def to_markdown(results: dict, mode: str, info: dict) -> str:
    lines = [
        "# Measured results",
        "",
        f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} "
        f"in `{mode}` mode.",
        "",
        f"- Platform: `{info['platform']}`",
        f"- Processor: `{info['processor']}`",
        f"- Python: `{info['python']}` ({info['implementation']})",
        f"- CPUs: {info['cpu_count']}",
        "",
        "`best` is the fastest of N runs. `ratio` is variant / baseline of the same",
        "case (smaller is faster; below 1.00 means the variant wins).",
        "",
    ]
    for group in ("sorting", "min-max", "fibonacci", "matmul"):
        rows = [(cid, r) for cid, r in results.items() if r["group"] == group]
        if not rows:
            continue
        lines += [f"## {group}", "", "| case | variant | best ms | median ms | ratio |", "|---|---|---|---|---|"]
        for cid, r in rows:
            names = list(r["variants"])
            base = r["variants"][names[0]]
            base_key = "best_ms" if mode == "isolated" else "median_ms"
            base_val = base[base_key]
            for name in names:
                v = r["variants"][name]
                val = v[base_key]
                ratio = val / base_val if base_val else float("nan")
                lines.append(
                    f"| `{cid}` | {name} | {v['best_ms']:.4f} | {v['median_ms']:.4f} | {ratio:.3f} |"
                )
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="algopt-bench",
        description="Run the benchmarks. Every number in README.md comes from here.",
    )
    parser.add_argument("--mode", choices=("isolated", "interleaved"), default="isolated")
    parser.add_argument("--quick", action="store_true", help="small sizes, for CI")
    parser.add_argument("--list", action="store_true", help="list cases and variants")
    parser.add_argument("--json", default=None, help="write raw results here")
    parser.add_argument("--markdown", default=None, help="write a markdown table here")
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):  # Windows runners default to cp1252
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    cases = build_cases(quick=args.quick)
    if args.list:
        for case in cases:
            print(f"{case.id:22s} repeat={case.repeat}  variants={', '.join(case.variants)}")
        return 0

    info = machine_info()
    print(f"Algorithm optimizations benchmark — mode={args.mode} quick={args.quick}")
    print(f"  {info['platform']} | {info['processor']} | Python {info['python']}")
    print()

    runner = run_isolated if args.mode == "isolated" else run_interleaved
    results = runner(cases, args.quick)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": args.mode,
        "quick": args.quick,
        "machine": info,
        "cases": results,
    }
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print(f"\nwrote {args.json}")
    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(to_markdown(results, args.mode, info))
        print(f"wrote {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
