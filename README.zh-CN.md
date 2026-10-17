# algorithm-optimizations

[English](README.md) · **中文**

<img src="assets/banner.png" alt="Five implementations of min/max: the pairwise version is 1.58x slower than the naive loop" width="100%">

四个教科书级优化。实测过，不是声称的。

**其中有两个在 CPython 上不成立** —— 而不成立的这两个，恰好是纸面上最可信的两个。

| # | 优化 | 纸面上 | 本机实测 | 判定 |
|---|---|---|---|---|
| 1 | 成对比较求 min/max | `2(n-1)` → `3⌊n/2⌋`，少 25% 比较 | 比朴素循环**慢 1.58 倍** | ✗ |
| 2 | 矩阵分块（cache blocking） | 提高局部性、减少 cache miss | **1.01–1.25 倍**（从无收益） | ✗ |
| 3 | 冒泡 → 鸡尾酒排序 | 双向 + 早停，轮次更少 | 已排序 **929×**，逆序 **0.97×** | ~ |
| 4 | 朴素递归 → DP → 矩阵快速幂 | `O(φⁿ)` → `O(n)` → `O(log n)` | 282 ms → 0.028 ms → 0.0066 ms | ✓ |

全部数据：CPython 3.13.14 / Windows 11 / Ryzen 7 H 255，独立进程、best of 5。
完整表格见 [`benchmarks/RESULTS.md`](benchmarks/RESULTS.md)，原始数据见
[`benchmarks/results.json`](benchmarks/results.json)。每条结论对应哪条命令，
见 [`docs/claims.md`](docs/claims.md)。

## 有意思的那个失败：成对比较求 min/max

同时求最小值与最大值，朴素做法要 `2(n-1)` 次比较。先把元素两两配对比一次，
再分别与当前 min / max 比 —— 一共 `3⌊n/2⌋` 次，大约少 25%。

**比较次数是真的。** 这个仓库不靠相信，直接数
（`benchmarks/count_comparisons.py`，单元格 = 实测 / 精确值）：

```
       n |            min_max_naive | min_max_pairwise_indexed |         min_max_pairwise
     100 |        198 / 198        ok |        148 / 148        ok |        148 / 148        ok
    1001 |      2,000 / 2,000      ok |      1,500 / 1,500      ok |      1,500 / 1,500      ok
  100000 |    199,998 / 199,998    ok |    149,998 / 149,998    ok |    149,998 / 149,998    ok
```

少 25% 的比较，多 **58% 的墙钟时间**（300 万个整数）：

| 实现 | 最优 ms | 比值 | 成本在哪 |
|---|---|---|---|
| `min_max_naive` | 80.82 | 1.00 | 每元素 2 次比较，直线循环 |
| `min_max_naive_nocopy` | 88.08 | 1.09 | 同上，去掉尾部拷贝 —— *对照组* |
| `min_max_pairwise_indexed` | 127.73 | **1.58** | 成对 + `while` + `arr[i]` / `arr[i+1]` |
| `min_max_pairwise` | 60.10 | **0.74** | 同一算法，改用 `zip(it, it)` |
| `min_max_builtin` | 38.54 | **0.48** | `min(arr), max(arr)` |

第三行为什么输：一次比较只是一个字节码，而两个操作数本来就在缓存里。
`arr[i]` 和 `arr[i+1]` 各是一条取下标字节码，配对还要打包、解包，
`while` 每轮再判一次。**省下一次比较，付出四条字节码**，
而 CPython 的时间就是花在字节码条数上的。

第四行为什么赢：算法从来没错，错的是转写方式。用 `zip(it, it)` 迭代，
配对循环留在 C 里，取下标完全消失 —— 比较次数一样，比索引版快约 2.1 倍，
也比它本该打败的朴素循环更快。

还有一个诚实的脚注：`min_max_naive_nocopy` 比带 `arr[1:]` 拷贝的版本**更慢**。
拷贝 24 MB 指针很便宜，丢掉快速列表迭代器才是贵的。去掉拷贝救不了这个基线。

## 第二个失败：解释器里的 cache blocking

矩阵乘法的内积循环在 CPython 里每一步大约 100 ns，而一次 L2 cache miss 只值
几纳秒。当解释器比 cache miss 贵 20 倍时，重排循环省下的访存时间不可能回本。

| 规模 | 朴素 | 分块-8 | 分块-32 | 分块-64 | `zip` + `sum(map(mul))` |
|---|---|---|---|---|---|
| n = 128 | 69.49 ms | — | 81.83 ms (1.18×) | — | 51.79 ms (**0.75×**) |
| n = 160 | 149.27 ms | 187.21 ms (1.25×) | 153.45 ms (1.03×) | 150.47 ms (1.01×) | 99.00 ms (**0.66×**) |
| n = 192 | 242.46 ms | — | 271.12 ms (1.12×) | 252.81 ms (1.04×) | 159.75 ms (**0.66×**) |

分块的收益既不随块大小变化，也不随矩阵规模变化 —— 这是「噪声 + 循环开销」的
特征，不是 cache 复用的特征。真正有效的是把内积交给 C：转置一次 `B`，
再用 `sum(map(mul, row, col))` 让整行在 C 里算完。同样的 `O(n³)` 工作量，
时间少 1.3–1.5 倍。

（顺带一提，它在浮点上还更准一点：从 CPython 3.12 起 `sum()` 对浮点做
Neumaier 补偿求和，所以 `matmul_zip` 的舍入和朴素的 `+=` 累加器不同。）

## 真正成立的两条

### 排序：两处改动，治的是两种数据

「冒泡排序 vs 鸡尾酒排序（带早停）」这个对比藏了一件事：它同时改了两处。
把它们拆开：

| 输入（n = 2000） | `bubble_sort` | `bubble_sort_early` | `cocktail_sort` |
|---|---|---|---|
| 已排序 | 66.46 ms | 0.0716 ms — **929×** | 0.0718 ms — **926×** |
| 相邻交换 50 次 | 66.00 ms | 0.1430 ms — **462×** | 0.1741 ms — **379×** |
| 远距离交换 50 次 | 68.55 ms | 69.56 ms — 1.0× | 6.82 ms — **10.1×** |
| 随机 | 111.87 ms | 114.52 ms — 1.0× | 102.40 ms — **1.09×** |
| 完全逆序 | 150.30 ms | 151.17 ms — 1.0× | 155.28 ms — **0.97×** |

`×` 表示比 `bubble_sort` 快多少倍；`1.0×` 表示没有变化，小于 1 表示更慢。

- **只加早停**，在真正接近有序的数据上就能拿到全部收益：已排序 929×，
  双向一遍在上面加不出任何东西。
- **只加双向**，救的是「逆序对很少、但离得很远」这种情况：远距离交换形态下
  10.1×，而早停在这里一分不值（1.0×）。
- **完全逆序**时鸡尾酒版反而慢 3%：每一轮都在交换每一对，第二趟扫描纯属白跑。
- 随机数据上两者相差在 ±10% 以内，也就是这台机器的噪声底。

大多数 benchmark 里被标成「接近有序」的是第三行 —— 50 次任意两点交换，
位移可达整个数组长度。它在算法意义上不是接近有序，这也正是同一份代码
既能被引用成 10× 又能被引用成 900× 的原因。

### Fibonacci：复杂度阶梯是真的，墙钟不是线性的

| n | `fib_naive` | n | `fib_dp` | `fib_matrix` |
|---|---|---|---|---|
| 25 | 9.64 ms | 100 | 0.0022 ms | 0.0026 ms |
| 28 | 38.34 ms | 1 000 | 0.0277 ms | 0.0066 ms |
| 30 | 107.46 ms | 10 000 | 0.9147 ms | 0.2271 ms |
| 32 | 282.35 ms | 100 000 | 63.42 ms | 7.96 ms |

朴素版每加 1 大约乘 1.6（黄金比），所以 n = 40 确实跑不动。
矩阵版在 n = 100 到 1000 之间反超 DP —— n = 100 时 DP 还领先 18%，
到 n = 1000 时矩阵版领先 4.2 倍。

但要看增长，不能只看指数。n 从 1000 到 100000（100 倍），
DP 涨了 **2290 倍**，矩阵版涨了 **1206 倍**。两者都远超声线性：
循环次数是降下来了，可数字本身在变大，而 Python 的大整数不免费。
`O(log n)` 次「越来越大的整数乘法」不等于 `O(log n)` 的时间。

## 复现

```bash
git clone https://github.com/linluozi/algorithm-optimizations
cd algorithm-optimizations

python -m benchmarks.run_all --json benchmarks/results.json --markdown benchmarks/RESULTS.md
python -m benchmarks.run_all --mode interleaved   # 比值复核，见下
python benchmarks/count_comparisons.py            # 只数比较次数，不计时
python -m unittest discover -s tests -t .         # 31 个测试
```

`python -m benchmarks.run_all --quick` 用同样一套 harness 跑小规模，约 5 秒 ——
CI 用的就是它。

## 方法，以及为什么这么啰嗦

- **每个（用例, 变体）一个子进程。** 一个分配了 300 万个整数的变体会留下不同的堆，
  接下来跑的东西就是在更脏的机器上被测。这个仓库里影响不大；
  在另一个仓库里，一个一次分配 57 MB 的 CSV 读取器让**下一个**算法凭空慢了 2.4 倍。
- **取最优，不取平均。** 干扰只会让某一次变慢，不会让它变快，所以最小值是受污染
  最少的估计。`median_ms` 也一并给出，但结论引用 `best_ms`。
- **固定种子。** 所有输入都来自 `algopt/data.py`。这个 benchmark 的第一版用裸的
  `random.randint`，同一条命令跑出了两个不同结论。
- **交错模式用来核对比值。** 这台笔记本的绝对耗时在两次运行之间能漂 40%
  （同一个朴素循环，一小时前 123 ms、一小时后 173 ms）。而同一轮内的**比值**
  不受影响，因为漂移对所有变体一视同仁。所以：绝对数字引用 isolated 模式，
  下结论之前用 `--mode interleaved` 复核。
- **护栏。** 计时前每个变体先在小输入上验一遍，benchmark 不可能悄悄测一个坏函数。

细节见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。如果某个「简化」让上面任何一条不再成立，
那它就不是简化。

## 目录

```
algopt/
  sorting.py      bubble_sort, bubble_sort_early, cocktail_sort
  min_max.py      naive, naive_nocopy, pairwise_indexed（陷阱）, pairwise, builtin
  fibonacci.py    fib_naive, fib_dp, fib_matrix
  matmul.py       matmul_naive, matmul_blocked（负结果）, matmul_zip
  data.py         带种子的输入生成器
  bench.py        harness：isolated / interleaved，输出 markdown + json
benchmarks/
  run_all.py            python -m benchmarks.run_all
  count_comparisons.py  数 < 和 >，不数纳秒
  RESULTS.md            生成的表格
tests/                  31 个 unittest
docs/claims.md          每条 README 结论 → 支撑它的用例
```

## 这仓库不是什么

不是「Python vs C」的横评，也不是说这些算法不好。它们是正确的，而且在它们被设计
出来的硬件上 —— 在那种机器上「一次比较」和「一次 cache miss」都是昂贵操作 ——
它们就是正确答案。这里讲的是另一步：当论文结论被转写成 Python，
底下的成本模型悄悄换了。

## 许可证

MIT，见 [LICENSE](LICENSE)。
