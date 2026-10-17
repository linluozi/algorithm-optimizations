# Measured results

Generated 2026-10-17 11:03 UTC in `isolated` mode.

- Platform: `Windows-11-10.0.26300-SP0`
- Processor: `AMD64 Family 25 Model 117 Stepping 2, AuthenticAMD`
- Python: `3.13.14` (CPython)
- CPUs: 16

`best` is the fastest of N runs. `ratio` is variant / baseline of the same
case (smaller is faster; below 1.00 means the variant wins).

## sorting

| case | variant | best ms | median ms | ratio |
|---|---|---|---|---|
| `sort/sorted/2000` | naive | 66.4576 | 66.9466 | 1.000 |
| `sort/sorted/2000` | early | 0.0716 | 0.0721 | 0.001 |
| `sort/sorted/2000` | cocktail | 0.0718 | 0.0726 | 0.001 |
| `sort/adjacent-50/2000` | naive | 66.0013 | 67.5589 | 1.000 |
| `sort/adjacent-50/2000` | early | 0.1430 | 0.1433 | 0.002 |
| `sort/adjacent-50/2000` | cocktail | 0.1741 | 0.1850 | 0.003 |
| `sort/far-50/2000` | naive | 68.5496 | 69.9861 | 1.000 |
| `sort/far-50/2000` | early | 69.5639 | 69.9970 | 1.015 |
| `sort/far-50/2000` | cocktail | 6.8196 | 6.9105 | 0.099 |
| `sort/random/2000` | naive | 111.8697 | 114.5452 | 1.000 |
| `sort/random/2000` | early | 114.5223 | 116.2080 | 1.024 |
| `sort/random/2000` | cocktail | 102.4030 | 104.1658 | 0.915 |
| `sort/reversed/2000` | naive | 150.3034 | 159.6050 | 1.000 |
| `sort/reversed/2000` | early | 151.1735 | 154.9844 | 1.006 |
| `sort/reversed/2000` | cocktail | 155.2761 | 158.2126 | 1.033 |

## min-max

| case | variant | best ms | median ms | ratio |
|---|---|---|---|---|
| `min-max/3000k` | naive | 80.8228 | 85.2770 | 1.000 |
| `min-max/3000k` | naive-nocopy | 88.0800 | 91.5132 | 1.090 |
| `min-max/3000k` | pairwise-indexed | 127.7295 | 130.7742 | 1.580 |
| `min-max/3000k` | pairwise | 60.0983 | 61.7569 | 0.744 |
| `min-max/3000k` | builtin | 38.5387 | 39.1656 | 0.477 |

## fibonacci

| case | variant | best ms | median ms | ratio |
|---|---|---|---|---|
| `fib/naive/25` | naive | 9.6368 | 9.8725 | 1.000 |
| `fib/naive/28` | naive | 38.3419 | 38.4862 | 1.000 |
| `fib/naive/30` | naive | 107.4637 | 116.7494 | 1.000 |
| `fib/naive/32` | naive | 282.3489 | 290.5762 | 1.000 |
| `fib/dp/100` | dp | 0.0022 | 0.0024 | 1.000 |
| `fib/dp/1000` | dp | 0.0277 | 0.0299 | 1.000 |
| `fib/dp/10000` | dp | 0.9147 | 0.9367 | 1.000 |
| `fib/dp/100000` | dp | 63.4231 | 64.9246 | 1.000 |
| `fib/matrix/100` | matrix | 0.0026 | 0.0030 | 1.000 |
| `fib/matrix/1000` | matrix | 0.0066 | 0.0071 | 1.000 |
| `fib/matrix/10000` | matrix | 0.2271 | 0.3352 | 1.000 |
| `fib/matrix/100000` | matrix | 7.9624 | 8.0180 | 1.000 |

## matmul

| case | variant | best ms | median ms | ratio |
|---|---|---|---|---|
| `matmul/128` | naive | 69.4879 | 71.1399 | 1.000 |
| `matmul/128` | blocked-32 | 81.8326 | 83.2802 | 1.178 |
| `matmul/128` | zip | 51.7903 | 53.3769 | 0.745 |
| `matmul/160` | naive | 149.2743 | 157.1317 | 1.000 |
| `matmul/160` | blocked-8 | 187.2060 | 192.0951 | 1.254 |
| `matmul/160` | blocked-32 | 153.4476 | 157.6185 | 1.028 |
| `matmul/160` | blocked-64 | 150.4682 | 157.0903 | 1.008 |
| `matmul/160` | zip | 98.9964 | 104.8917 | 0.663 |
| `matmul/192` | naive | 242.4618 | 252.4054 | 1.000 |
| `matmul/192` | blocked-32 | 271.1159 | 274.4646 | 1.118 |
| `matmul/192` | blocked-64 | 252.8063 | 254.8883 | 1.043 |
| `matmul/192` | zip | 159.7486 | 163.1482 | 0.659 |
