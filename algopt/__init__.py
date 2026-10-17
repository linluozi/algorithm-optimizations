"""Four textbook optimizations, kept honest by a benchmark harness.

Two of the four classical "wins" do not survive contact with CPython. Both
negative results are preserved here on purpose: they are the reason this
repository exists. See ``README.md`` and ``docs/claims.md``.
"""

__version__ = "1.0.0"

__all__ = ["sorting", "min_max", "fibonacci", "matmul", "data", "bench"]
