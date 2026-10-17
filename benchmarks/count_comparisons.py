"""Count comparisons instead of milliseconds.

The classic claim is that pairwise min/max uses ``3*floor(n/2)`` comparisons
instead of ``2(n-1)``, a ~25% reduction. This script counts them exactly, by
wrapping the values in a proxy that tallies every ``<`` and ``>``.

Compare this table with ``RESULTS.md``: the comparison counts are exactly as
advertised, and the wall clock does not follow them.

    python benchmarks/count_comparisons.py
"""

from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from algopt import min_max  # noqa: E402


class Counted:
    """A value that reports every comparison it takes part in."""

    __slots__ = ("value",)

    count = 0

    def __init__(self, value):
        self.value = value

    def __lt__(self, other):
        Counted.count += 1
        return self.value < other.value

    def __gt__(self, other):
        Counted.count += 1
        return self.value > other.value

    def __repr__(self):
        return f"Counted({self.value})"


def count(fn, n, order="random"):
    values = list(range(n))
    if order == "descending":
        values.reverse()
    arr = [Counted(v) for v in values]
    Counted.count = 0  # don't count the construction
    low, high = fn(arr)
    return Counted.count, (low.value, high.value)


def _linear(n):
    """2(n-1) comparisons: one `<` and one `>` per element after the first."""
    return 2 * (n - 1)


def _pairwise(n):
    """Exact pairwise count.

    The textbook bound is 3*floor(n/2). The last pair is compared with an
    `elif`, which saves one comparison, and the initial pair costs one instead
    of three: for even n the exact count is 3*floor(n/2) - 2, for odd n it is
    3*(n-1)/2.
    """
    return 3 * (n - 1) // 2 if n % 2 else 3 * n // 2 - 2


FUNCS = (
    ("min_max_naive", min_max.min_max_naive, _linear),
    ("min_max_pairwise_indexed", min_max.min_max_pairwise_indexed, _pairwise),
    ("min_max_pairwise", min_max.min_max_pairwise, _pairwise),
    ("min_max_builtin", min_max.min_max_builtin, _linear),
)


def main() -> int:
    header = f"{'n':>8} | " + " | ".join(f"{name:>24}" for name, _, _ in FUNCS)
    print(header)
    print("-" * len(header))
    for n in (2, 3, 10, 100, 1001, 100_000):
        cells = []
        for _, fn, exact in FUNCS:
            got, result = count(fn, n)
            expected = (min(range(n)), max(range(n)))
            if result != expected:
                raise AssertionError(f"{fn.__name__} returned {result}, expected {expected}")
            mark = "ok" if got == exact(n) else "MISMATCH"
            cells.append(f"{got:>10,} / {exact(n):<10,} {mark[:2]}")
        print(f"{n:>8} | " + " | ".join(cells))

    print()
    print("cell = measured / exact. naive and builtin both use 2(n-1) comparisons;")
    print("the pairwise versions use 3*floor(n/2) - 2 (even n) or 3*(n-1)/2 (odd n),")
    print("i.e. the textbook 25% cut, exactly.")
    print()
    print("builtin does it in two C-level passes, so it wins on the clock with the")
    print("same comparison count. Counting comparisons is not counting time.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
