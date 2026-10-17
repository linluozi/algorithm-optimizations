"""Fibonacci numbers: exponential recursion, linear DP, logarithmic matrix power.

The complexity ladder is real -- the naive version roughly multiplies by 1.6 per
increment of n (golden ratio). At n = 100 the DP is still 18% ahead; at n = 1000
the matrix version is 4.2x ahead. The crossover is somewhere between the two.

But read the wall-clock table, not just the exponents: Python's
big integers make *both* fast versions grow faster than their loop count
suggests, because the numbers themselves grow.

Measured tables: ``benchmarks/RESULTS.md``.
"""

from __future__ import annotations


def _check(n: int) -> int:
    """Reject the inputs that used to fail silently (``fib(-5) == -5``)."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(f"n must be an int, got {type(n).__name__}")
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    return n


def fib_naive(n: int) -> int:
    """Naive recursion, O(phi^n). n = 32 already takes ~200 ms."""
    n = _check(n)

    def go(k: int) -> int:
        return k if k < 2 else go(k - 1) + go(k - 2)

    return go(n)


def fib_dp(n: int) -> int:
    """Bottom-up DP with two rolling variables: O(n) additions, O(1) space."""
    n = _check(n)
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _mat_mul(a: tuple, b: tuple) -> tuple:
    """Multiply two 2x2 matrices stored as flat 4-tuples."""
    a00, a01, a10, a11 = a
    b00, b01, b10, b11 = b
    return (
        a00 * b00 + a01 * b10,
        a00 * b01 + a01 * b11,
        a10 * b00 + a11 * b10,
        a10 * b01 + a11 * b11,
    )


def _mat_pow(m: tuple, e: int) -> tuple:
    result = (1, 0, 0, 1)  # identity
    while e:
        if e & 1:
            result = _mat_mul(result, m)
        m = _mat_mul(m, m)
        e >>= 1
    return result


def fib_matrix(n: int) -> int:
    """Matrix fast power: O(log n) 2x2 multiplications.

    [[1,1],[1,0]] ** n == [[F(n+1), F(n)], [F(n), F(n-1)]], so F(n) is the
    top-left entry of the (n-1)-th power.
    """
    n = _check(n)
    if n < 2:
        return n
    return _mat_pow((1, 1, 1, 0), n - 1)[0]
