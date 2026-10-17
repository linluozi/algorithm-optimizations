"""Correctness tests. Performance claims are only worth reading if these pass."""

from __future__ import annotations

import math
import unittest

from algopt import data, fibonacci, matmul, min_max, sorting

SORT_CASES = [
    [],
    [1],
    [2, 1],
    [1, 2],
    [3, 3, 3],
    [5, 4, 3, 2, 1],
    list(range(10)),
    [0, -1, 5, -3, 2, 2, 0],
    [64, 34, 25, 12, 22, 11, 90],
]


class TestSorting(unittest.TestCase):
    def test_against_sorted(self):
        for case in SORT_CASES:
            for fn in (sorting.bubble_sort, sorting.bubble_sort_early, sorting.cocktail_sort):
                with self.subTest(fn=fn.__name__, case=case):
                    self.assertEqual(fn(case), sorted(case))

    def test_all_shapes(self):
        for shape in data.SORT_SHAPES:
            arr = data.sort_data(shape, 200)
            expected = sorted(arr)
            for fn in (sorting.bubble_sort, sorting.bubble_sort_early, sorting.cocktail_sort):
                with self.subTest(fn=fn.__name__, shape=shape):
                    self.assertEqual(fn(arr), expected)

    def test_does_not_mutate_input(self):
        arr = [3, 1, 2]
        for fn in (sorting.bubble_sort, sorting.bubble_sort_early, sorting.cocktail_sort):
            fn(arr)
            self.assertEqual(arr, [3, 1, 2])

    def test_accepts_tuple(self):
        self.assertEqual(sorting.cocktail_sort((3, 1, 2)), [1, 2, 3])


class TestMinMax(unittest.TestCase):
    FUNCS = (
        min_max.min_max_naive,
        min_max.min_max_naive_nocopy,
        min_max.min_max_pairwise_indexed,
        min_max.min_max_pairwise,
        min_max.min_max_builtin,
    )

    def test_lengths_one_to_forty(self):
        # covers every odd/even parity and the "one element left over" branch
        for n in range(1, 41):
            arr = data.int_list(n, seed=n)
            expected = (min(arr), max(arr))
            for fn in self.FUNCS:
                with self.subTest(fn=fn.__name__, n=n):
                    self.assertEqual(fn(arr), expected)

    def test_odd_tail_is_not_dropped(self):
        # the zip(it, it) version must still see the unpaired last element
        for n in (3, 5, 7, 9):
            arr = [5] * (n - 1) + [-100]
            self.assertEqual(min_max.min_max_pairwise(arr), (-100, 5))

    def test_equal_values(self):
        self.assertEqual(min_max.min_max_pairwise([7, 7]), (7, 7))
        self.assertEqual(min_max.min_max_pairwise_indexed([7, 7]), (7, 7))

    def test_empty_raises(self):
        for fn in self.FUNCS:
            with self.subTest(fn=fn.__name__):
                with self.assertRaises(ValueError):
                    fn([])


class TestFibonacci(unittest.TestCase):
    @staticmethod
    def reference(n):
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        return a

    def test_matches_reference(self):
        for n in list(range(0, 60)) + [200, 500, 1000]:
            expected = self.reference(n)
            with self.subTest(n=n):
                self.assertEqual(fibonacci.fib_dp(n), expected)
                self.assertEqual(fibonacci.fib_matrix(n), expected)
                if n <= 30:
                    self.assertEqual(fibonacci.fib_naive(n), expected)

    def test_known_values(self):
        self.assertEqual(fibonacci.fib_dp(0), 0)
        self.assertEqual(fibonacci.fib_dp(1), 1)
        self.assertEqual(fibonacci.fib_matrix(10), 55)
        self.assertEqual(fibonacci.fib_naive(20), 6765)

    def test_negative_raises(self):
        for fn in (fibonacci.fib_naive, fibonacci.fib_dp, fibonacci.fib_matrix):
            with self.subTest(fn=fn.__name__):
                with self.assertRaises(ValueError):
                    fn(-5)

    def test_non_integer_raises(self):
        for fn in (fibonacci.fib_naive, fibonacci.fib_dp, fibonacci.fib_matrix):
            for bad in (2.5, "10", None, True):
                with self.subTest(fn=fn.__name__, bad=bad):
                    with self.assertRaises(TypeError):
                        fn(bad)


class TestMatmul(unittest.TestCase):
    @staticmethod
    def reference(a, b):
        """Explicit += accumulation.

        Deliberately not ``sum(...)``: since CPython 3.12 ``sum()`` applies
        Neumaier compensation to floats, so it rounds differently from a plain
        accumulator. The difference is in the last bits, which is why the float
        comparison below uses ``isclose`` instead of ``==``.
        """
        n = len(a)
        out = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                s = 0.0
                for k in range(n):
                    s += a[i][k] * b[k][j]
                out[i][j] = s
        return out

    def assert_matrices_close(self, got, expected):
        self.assertEqual(len(got), len(expected))
        for row_got, row_exp in zip(got, expected):
            self.assertEqual(len(row_got), len(row_exp))
            for g, e in zip(row_got, row_exp):
                self.assertTrue(math.isclose(g, e, rel_tol=1e-12, abs_tol=1e-12), f"{g} != {e}")

    def test_small_sizes(self):
        for n in (1, 2, 3, 4, 5, 7, 8, 16, 17):
            a, b = data.square_matrices(n, seed=n)
            expected = self.reference(a, b)
            for fn in (
                matmul.matmul_naive,
                matmul.matmul_zip,
                lambda x, y: matmul.matmul_blocked(x, y, 1),
                lambda x, y: matmul.matmul_blocked(x, y, 3),
                lambda x, y: matmul.matmul_blocked(x, y, 32),
                lambda x, y: matmul.matmul_blocked(x, y, 64),
            ):
                with self.subTest(n=n, fn=getattr(fn, "__name__", "blocked")):
                    self.assert_matrices_close(fn(a, b), expected)

    def test_integer_matrices(self):
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        self.assertEqual(matmul.matmul_naive(a, b), [[19, 22], [43, 50]])
        self.assertEqual(matmul.matmul_zip(a, b), [[19, 22], [43, 50]])
        self.assertEqual(matmul.matmul_blocked(a, b, 1), [[19, 22], [43, 50]])

    def test_non_square_raises(self):
        with self.assertRaises(ValueError):
            matmul.matmul_naive([[1, 2, 3], [4, 5, 6]], [[1], [2], [3]])
        with self.assertRaises(ValueError):
            matmul.matmul_blocked([[1, 2, 3], [4, 5, 6]], [[1], [2], [3]])

    def test_bad_block_size(self):
        a, b = data.square_matrices(4)
        for bad in (0, -3):
            with self.subTest(block_size=bad):
                with self.assertRaises(ValueError):
                    matmul.matmul_blocked(a, b, bad)


class TestDataGenerators(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(data.int_list(50), data.int_list(50))
        self.assertNotEqual(data.int_list(50, seed=1), data.int_list(50, seed=2))
        self.assertEqual(data.sort_data("random", 100), data.sort_data("random", 100))

    def test_shapes_are_what_they_claim(self):
        self.assertEqual(data.sort_data("sorted", 20), list(range(20)))
        self.assertEqual(data.sort_data("reversed", 20), list(range(19, -1, -1)))
        adjacent = data.sort_data("adjacent-50", 100)
        self.assertEqual(sorted(adjacent), list(range(100)))
        # every element stays within a few slots of home after neighbour swaps
        self.assertTrue(all(abs(i - v) <= 60 for i, v in enumerate(adjacent)))

    def test_unknown_shape(self):
        with self.assertRaises(ValueError):
            data.sort_data("almost-sorted", 10)


if __name__ == "__main__":
    unittest.main()
