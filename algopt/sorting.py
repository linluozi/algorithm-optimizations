"""Bubble sort, in three increasingly clever versions.

The point of this module is that "clever" is two independent changes, and they
fix two different inputs:

* ``bubble_sort``        -- no early exit, always n(n-1)/2 comparisons.
* ``bubble_sort_early``  -- adds an early exit; wins big on data that is already
                            sorted or nearly sorted *by displacement*.
* ``cocktail_sort``      -- adds a backward pass; wins big when there are few
                            inversions but they are far apart (a small element
                            parked at the end), and loses on reversed input.

Measured numbers for all five input shapes are in ``benchmarks/RESULTS.md``.
"""

from __future__ import annotations

from collections.abc import Sequence


def bubble_sort(arr: Sequence) -> list:
    """Textbook bubble sort: no early exit.

    Always performs exactly ``n(n-1)/2`` comparisons, whatever the input looks
    like. Kept as the baseline the other two are measured against.
    """
    a = list(arr)
    n = len(a)
    for i in range(n):
        for j in range(n - i - 1):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
    return a


def bubble_sort_early(arr: Sequence) -> list:
    """Bubble sort with an early exit when a pass makes no swaps."""
    a = list(arr)
    n = len(a)
    for i in range(n):
        swapped = False
        last = n - i - 1
        for j in range(last):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:
            break
    return a


def cocktail_sort(arr: Sequence) -> list:
    """Bidirectional bubble sort (cocktail shaker) with an early exit.

    Each round sweeps right, then left, shrinking both bounds. A single element
    that has to travel the full width of the list is moved one step per *round*
    rather than one step per *pass*, so far-apart inversions are what this fixes.
    """
    a = list(arr)
    left, right = 0, len(a) - 1
    swapped = True
    while swapped and left < right:
        swapped = False
        for i in range(left, right):
            if a[i] > a[i + 1]:
                a[i], a[i + 1] = a[i + 1], a[i]
                swapped = True
        right -= 1

        if not swapped:
            break

        swapped = False
        for i in range(right, left, -1):
            if a[i] < a[i - 1]:
                a[i], a[i - 1] = a[i - 1], a[i]
                swapped = True
        left += 1
    return a
