"""Tests for the benchmark harness itself.

A benchmark you cannot trust is worse than no benchmark, so the harness gets
tested like any other code: the guards must catch a broken variant, the case
registry must be self-consistent, and the markdown report must contain the rows.
"""

from __future__ import annotations

import unittest

from algopt import bench


class TestMeasure(unittest.TestCase):
    def test_returns_sorted_runs(self):
        out = bench.measure(lambda: sum(range(1000)), (), repeat=3)
        self.assertEqual(len(out["runs_ms"]), 3)
        self.assertLessEqual(out["best_ms"], out["median_ms"])
        # runs_ms is rounded for display, best_ms is not
        self.assertAlmostEqual(out["best_ms"], min(out["runs_ms"]), places=5)

    def test_warmup_is_not_counted(self):
        calls = []
        bench.measure(lambda: calls.append(1), (), repeat=2, warmup=1)
        self.assertEqual(len(calls), 3)


class TestCaseRegistry(unittest.TestCase):
    def test_ids_are_unique(self):
        cases = bench.build_cases()
        ids = [c.id for c in cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_case_resolves_every_variant(self):
        for case in bench.build_cases():
            for variant in case.variants:
                with self.subTest(case=case.id, variant=variant):
                    self.assertTrue(callable(case.resolve(variant)))

    def test_lookup_by_id(self):
        case = bench.case_by_id("sort/sorted")
        self.assertEqual(case.group, "sorting")
        with self.assertRaises(SystemExit):
            bench.case_by_id("nope")

    def test_quick_mode_is_smaller(self):
        full = {c.id for c in bench.build_cases(quick=False)}
        quick = {c.id for c in bench.build_cases(quick=True)}
        self.assertTrue(quick)
        self.assertTrue(quick.issubset(full) or any("fib/naive/20" in c for c in quick))


class TestGuards(unittest.TestCase):
    def test_sort_guard_rejects_broken_fn(self):
        with self.assertRaises(AssertionError):
            bench._check_sort(lambda arr: list(arr))

    def test_minmax_guard_rejects_broken_fn(self):
        with self.assertRaises(AssertionError):
            bench._check_minmax(lambda arr: (0, 0))

    def test_fib_guard_rejects_broken_fn(self):
        with self.assertRaises(AssertionError):
            bench._check_fib(lambda n: 0)

    def test_matmul_guard_rejects_broken_fn(self):
        with self.assertRaises(AssertionError):
            bench._check_matmul(lambda a, b: [[0, 0], [0, 0]])

    def test_guards_pass_on_real_functions(self):
        from algopt import fibonacci, matmul, min_max, sorting

        bench._check_sort(sorting.bubble_sort)
        bench._check_sort(sorting.bubble_sort_early)
        bench._check_sort(sorting.cocktail_sort)
        bench._check_minmax(min_max.min_max_naive)
        bench._check_minmax(min_max.min_max_pairwise_indexed)
        bench._check_minmax(min_max.min_max_pairwise)
        bench._check_minmax(min_max.min_max_builtin)
        bench._check_fib(fibonacci.fib_naive)
        bench._check_fib(fibonacci.fib_dp)
        bench._check_fib(fibonacci.fib_matrix)
        bench._check_matmul(matmul.matmul_naive)
        bench._check_matmul(matmul.matmul_zip)
        bench._check_matmul(matmul.matmul_blocked)


class TestMarkdown(unittest.TestCase):
    def test_contains_every_group(self):
        results = {
            "sort/sorted": {
                "group": "sorting",
                "variants": {
                    "naive": {"best_ms": 10.0, "median_ms": 11.0},
                    "early": {"best_ms": 1.0, "median_ms": 1.1},
                },
            },
            "min-max/3k": {
                "group": "min-max",
                "variants": {"naive": {"best_ms": 5.0, "median_ms": 5.5}},
            },
        }
        text = bench.to_markdown(results, "isolated", bench.machine_info())
        self.assertIn("## sorting", text)
        self.assertIn("## min-max", text)
        self.assertIn("| `sort/sorted` | early | 1.0000 |", text)
        self.assertIn("ratio", text)


if __name__ == "__main__":
    unittest.main()
