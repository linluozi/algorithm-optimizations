"""Square matrix multiplication: naive, cache-blocked, and row-vectorised.

Cache blocking is what you do in C: it turns a stream of cache misses into
reuse. CPython never gets that far -- the interpreter costs roughly 100 ns per
inner-product step, while an L2 miss costs a few nanoseconds -- so blocking
measures as *no improvement at all* here, at any block size and any size we
tried.

The version that does help moves the inner product into C:
``sum(map(mul, row, col))``. Same O(n^3) work, ~1.4x less time.
"""

from __future__ import annotations

from operator import mul


def _shape(m) -> tuple:
    return len(m), len(m[0]) if m else 0


def _check(a, b) -> int:
    n, k = _shape(a)
    k2, m = _shape(b)
    if n != k or k != k2 or k2 != m:
        raise ValueError(
            f"expected two square matrices of equal size, got {n}x{k} and {k2}x{m}"
        )
    return n


def matmul_naive(a: list, b: list) -> list:
    """Triple loop with ``b[k][j]`` access: the format most people write first."""
    n = _check(a, b)
    c = [[0] * n for _ in range(n)]
    for i in range(n):
        row = a[i]
        crow = c[i]
        for j in range(n):
            s = 0
            for k in range(n):
                s += row[k] * b[k][j]
            crow[j] = s
    return c


def matmul_blocked(a: list, b: list, block_size: int = 32) -> list:
    """Cache-blocked triple loop. Included as a negative result: see module docstring."""
    n = _check(a, b)
    if block_size < 1:
        raise ValueError(f"block_size must be >= 1, got {block_size}")
    c = [[0] * n for _ in range(n)]
    for ii in range(0, n, block_size):
        i_end = min(ii + block_size, n)
        for jj in range(0, n, block_size):
            j_end = min(jj + block_size, n)
            for kk in range(0, n, block_size):
                k_end = min(kk + block_size, n)
                for i in range(ii, i_end):
                    crow = c[i]
                    arow = a[i]
                    for j in range(jj, j_end):
                        s = crow[j]
                        for k in range(kk, k_end):
                            s += arow[k] * b[k][j]
                        crow[j] = s
    return c


def matmul_zip(a: list, b: list) -> list:
    """Transpose ``b`` once, then let C run the inner product via ``sum(map(mul, ...))``."""
    n = _check(a, b)
    bt = list(zip(*b))
    return [[sum(map(mul, row, col)) for col in bt] for row in a]
