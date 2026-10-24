"""
The statistics the benchmark reports. Standard library only, so the package runs anywhere.

Two choices here differ from the authors' earlier grader check, and both are deliberate:

- **Rounding is half-up**, as the research harness's `metrics.ts` does (`Math.round`). Python's
  `round` is half-to-even, which bins a machine mark of 2.5 as 2 and 3.5 as 4; the harness bins both
  up. On integer marks the two agree.
- **The human ceiling is one order per rater pair**, rater A against rater B, as the harness and
  Paper VI compute it. `grader_check.py` pools both orders, which pools the two raters' marginals and
  reads lower: on Mohler's 1,727 kept rows it gives 0.503 where the harness and the release give
  0.519. Same items, different number, so the benchmark uses the release's.

Every interval is a percentile bootstrap over the unit the probe was applied to: the response. The
interval must contain its own point estimate (`shared/stats.py`'s rule); one that does not is a bug,
and it raises rather than printing.
"""

import math
import random


def half_up(x):
    return math.floor(x + 0.5)


def qwk(a, b, lo, hi):
    """Quadratic weighted kappa on integer bins lo..hi; marks are rounded half-up first."""
    n = int(half_up(hi - lo)) + 1
    if n < 2 or not a:
        return float("nan")
    idx = lambda x: min(n - 1, max(0, int(half_up(x - lo))))
    obs = [[0.0] * n for _ in range(n)]
    ha, hb = [0.0] * n, [0.0] * n
    for x, y in zip(a, b):
        i, j = idx(x), idx(y)
        obs[i][j] += 1
        ha[i] += 1
        hb[j] += 1
    tot = float(len(a))
    num = den = 0.0
    for i in range(n):
        for j in range(n):
            w = (i - j) ** 2 / (n - 1) ** 2
            num += w * obs[i][j]
            den += w * ha[i] * hb[j] / tot
    return 1.0 - num / den if den else float("nan")


def pearson(a, b):
    n = len(a)
    if n < 2:
        return float("nan")
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((y - mb) ** 2 for y in b) ** 0.5
    return num / (da * db) if da and db else float("nan")


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def sd(xs):
    xs = list(xs)
    if len(xs) < 2:
        return float("nan")
    m = mean(xs)
    return (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5


def quantile(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    pos = q * (len(xs) - 1)
    lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def bootstrap(units, stat, reps=2000, seed=7):
    """(point, lo, hi) for stat(list_of_units), resampling units with replacement."""
    point = stat(units)
    if not units or point != point:
        return point, float("nan"), float("nan")
    rng = random.Random(seed)
    k = len(units)
    draws = []
    for _ in range(reps):
        v = stat([units[rng.randrange(k)] for _ in range(k)])
        if v == v:
            draws.append(v)
    lo, hi = quantile(draws, 0.025), quantile(draws, 0.975)
    # A degenerate statistic (all draws equal) can sit a float's width outside; anything more is a bug.
    eps = 1e-9 * max(1.0, abs(point))
    if not (lo - eps <= point <= hi + eps):
        raise AssertionError(f"bootstrap interval [{lo}, {hi}] does not contain its point {point}")
    return point, lo, hi


def interval(point, lo, hi):
    return {"estimate": point, "ci95": [lo, hi]}


def excludes_zero(iv):
    lo, hi = iv["ci95"]
    return lo == lo and hi == hi and (lo > 0 or hi < 0)
