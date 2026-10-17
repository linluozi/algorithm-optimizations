"""Minimum and maximum of a sequence, four ways.

The classic exercise: finding both in one pass costs 2(n-1) comparisons, and
comparing elements in pairs first brings that down to 3*floor(n/2), a 25%
reduction. Both numbers are real -- ``benchmarks/count_comparisons.py`` counts
them exactly.

What does *not* survive is the implied speedup. On CPython the pair-wise version
transcribed with an index-based ``while`` loop is ~1.6x **slower** than the
naive loop, because a comparison costs about as much as the surrounding bytecode
and the pairwise version pays for indexing, tuple packing and loop bookkeeping.

Express the same algorithm with iterators instead of indexing and it wins
(``min_max_pairwise``). The algorithm was never wrong; the transcription was.
See ``benchmarks/RESULTS.md`` for every number quoted here.
"""

from __future__ import annotations

from collections.abc import Sequence


def min_max_naive(arr: Sequence) -> tuple:
    """One pass, two comparisons per element: exactly ``2(n-1)`` comparisons.

    ``arr[1:]`` copies the tail; at 3M elements that is ~24 MB of pointers, or
    roughly 5% of the runtime. ``min_max_naive_nocopy`` exists so you can check
    that removing the copy does not change the ranking.
    """
    if not arr:
        raise ValueError("min_max of an empty sequence")
    mn = mx = arr[0]
    for x in arr[1:]:
        if x < mn:
            mn = x
        if x > mx:
            mx = x
    return mn, mx


def min_max_naive_nocopy(arr: Sequence) -> tuple:
    """``min_max_naive`` without the tail copy. Control for the baseline."""
    n = len(arr)
    if not n:
        raise ValueError("min_max of an empty sequence")
    mn = mx = arr[0]
    for i in range(1, n):
        x = arr[i]
        if x < mn:
            mn = x
        if x > mx:
            mx = x
    return mn, mx


def min_max_pairwise_indexed(arr: Sequence) -> tuple:
    """Pairwise comparison, transcribed with an index-based ``while`` loop.

    Exactly ``3*floor(n/2)`` comparisons. This is the version that looks like the
    textbook and measures *slower* than the naive loop -- kept as the negative
    result the README is about.
    """
    n = len(arr)
    if not n:
        raise ValueError("min_max of an empty sequence")
    if n == 1:
        return arr[0], arr[0]

    if arr[0] < arr[1]:
        mn, mx = arr[0], arr[1]
    else:
        mn, mx = arr[1], arr[0]

    i = 2
    while i < n - 1:
        a, b = arr[i], arr[i + 1]
        if a < b:
            if a < mn:
                mn = a
            if b > mx:
                mx = b
        else:
            if b < mn:
                mn = b
            if a > mx:
                mx = a
        i += 2

    if i < n:  # odd length: one element left over
        x = arr[i]
        if x < mn:
            mn = x
        elif x > mx:
            mx = x

    return mn, mx


def min_max_pairwise(arr: Sequence) -> tuple:
    """Same pairwise algorithm, iterated with ``zip(it, it)``.

    Identical comparison count, no indexing, no tuple packing per pair: about
    2x faster than ``min_max_pairwise_indexed``. Requires a sequence (not a bare
    iterable) so the odd tail can be read without an extra ``next()``.
    """
    n = len(arr)
    if not n:
        raise ValueError("min_max of an empty sequence")
    if n == 1:
        return arr[0], arr[0]

    it = iter(arr)
    first = next(it)
    second = next(it)
    if first < second:
        mn, mx = first, second
    else:
        mn, mx = second, first

    for a, b in zip(it, it):
        if a < b:
            if a < mn:
                mn = a
            if b > mx:
                mx = b
        else:
            if b < mn:
                mn = b
            if a > mx:
                mx = a

    if n % 2:  # zip() dropped the unpaired last element
        x = arr[-1]
        if x < mn:
            mn = x
        elif x > mx:
            mx = x

    return mn, mx


def min_max_builtin(arr: Sequence) -> tuple:
    """Two C-level passes. The answer you should actually use."""
    if not arr:
        raise ValueError("min_max of an empty sequence")
    return min(arr), max(arr)
