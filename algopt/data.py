"""Deterministic benchmark inputs.

Every generator takes a seed and returns the same data on every run, on every
machine. That is the whole point: a benchmark whose input changes between runs
cannot support a claim.
"""

from __future__ import annotations

import random

SORT_SHAPES = ("sorted", "adjacent-50", "far-50", "random", "reversed")


def int_list(n: int, seed: int = 3) -> list:
    """``n`` random ints in [0, 1e9)."""
    rnd = random.Random(seed)
    return [rnd.randint(0, 10**9) for _ in range(n)]


def sort_data(shape: str, n: int = 2000) -> list:
    """Five input shapes for the sorting comparison.

    ``sorted``       -- already ascending.
    ``adjacent-50``  -- 50 swaps of neighbouring elements: nearly sorted in the
                        sense that every element is within 50 slots of home.
    ``far-50``       -- 50 swaps of *arbitrary* pairs: few inversions, but each
                        one spans hundreds of slots. This is the shape the
                        original benchmark used, and it is not "nearly sorted"
                        in the algorithmic sense.
    ``random``       -- shuffled.
    ``reversed``     -- descending.
    """
    base = list(range(n))
    if shape == "sorted" or n < 2:
        # nothing to shuffle on 0 or 1 elements, whatever the shape asked for
        return base
    if shape == "reversed":
        return base[::-1]
    if shape == "random":
        a = base[:]
        random.Random(13).shuffle(a)
        return a
    if shape == "adjacent-50":
        a = base[:]
        rnd = random.Random(7)
        for _ in range(50):
            i = rnd.randint(0, n - 2)
            a[i], a[i + 1] = a[i + 1], a[i]
        return a
    if shape == "far-50":
        a = base[:]
        rnd = random.Random(11)
        for _ in range(50):
            i = rnd.randint(0, n - 1)
            j = rnd.randint(0, n - 1)
            a[i], a[j] = a[j], a[i]
        return a
    raise ValueError(f"unknown sort shape: {shape!r}")


def square_matrices(n: int, seed: int = 5) -> tuple:
    """A pair of ``n x n`` float matrices."""
    rnd = random.Random(seed)
    a = [[rnd.random() for _ in range(n)] for _ in range(n)]
    b = [[rnd.random() for _ in range(n)] for _ in range(n)]
    return a, b
