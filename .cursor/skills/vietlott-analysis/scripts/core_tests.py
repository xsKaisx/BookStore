"""Bộ kiểm định cốt lõi: null Monte Carlo + Holm, backtest walk-forward, kiểm chứng tiến cho 3D.

Dùng:  python core_tests.py [--games 645 655 535 keno] [--mc 1500] [--forward-since YYYY-MM-DD]
"""
import argparse
import math

import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

from common import GAMES, indicator, load_3d, load_set, read

rng = np.random.default_rng(20261028)


def stat_vector(draws, wd, n, k, fast=False):
    T = len(draws)
    M = indicator(draws, n)
    cnt = M.sum(0).astype(float)
    e = T * k / n
    o = {"tần suất từng số": ((cnt - e) ** 2 / e).sum()}
    o["số lặp từ kỳ trước"] = (M[1:] & M[:-1]).sum(1).mean()
    Xc = M.astype(float) - M.mean(0)
    o["tự tương quan lag-1"] = (T * ((Xc[1:] * Xc[:-1]).sum(0) / (Xc ** 2).sum(0)) ** 2).sum()
    odd = ((draws % 2) == 1).sum(1)
    nodd = (n + 1) // 2
    pe = np.array([math.comb(nodd, j) * math.comb(n - nodd, k - j) / math.comb(n, k) for j in range(k + 1)])
    oc = np.bincount(odd, minlength=k + 1)
    keep = pe * T >= 5
    ee = pe[keep] * T
    o["chẵn/lẻ"] = ((oc[keep] - ee) ** 2 / ee).sum()
    s = draws.sum(1).astype(float)
    mu = k * (n + 1) / 2
    var = k * (n + 1) * (n - k) / 12
    o["tổng: trung bình"] = (s.mean() - mu) / math.sqrt(var / T)
    o["tổng: phương sai"] = s.var(ddof=1) / var
    o["cặp liền kề"] = (np.diff(draws, axis=1) == 1).sum(1).mean()
    gc = np.bincount(((draws - 1) // 10).ravel(), minlength=math.ceil(n / 10)).astype(float)
    sz = np.array([min(10, n - 10 * i) for i in range(len(gc))])
    ge = T * k * sz / n
    o["nhóm chục"] = ((gc - ge) ** 2 / ge).sum()
    if not fast:
        P = (M.T.astype(np.int32) @ M.astype(np.int32)).astype(float)
        pc = P[np.triu_indices(n, 1)]
        o["cặp số (phân tán)"] = pc.var(ddof=1) / pc.mean()
    W = np.array([M[wd == d].sum(0) for d in range(7) if (wd == d).any()], dtype=float)
    E = W.sum(1, keepdims=True) * W.sum(0, keepdims=True) / W.sum()
    o["thứ trong tuần × số"] = ((W - E) ** 2 / E).sum()
    return o


def monte_carlo(game, B, fast=False):
    draws, wd, dates, k, n = load_set(game)
    T = len(draws)
    obs = stat_vector(draws, wd, n, k, fast)
    sims = [
        stat_vector(np.sort(rng.random((T, n)).argpartition(k, axis=1)[:, :k] + 1, axis=1).astype(np.int16), wd, n, k, fast)
        for _ in range(B)
    ]
    rows = []
    for key in obs:
        v = np.array([s[key] for s in sims])
        z = (obs[key] - v.mean()) / v.std(ddof=1)
        rows.append((key, obs[key], v.mean(), z, 2 * stats.norm.sf(abs(z))))
    holm = multipletests([r[4] for r in rows], method="holm")[1]
    print(f"\n== {game}: {T} kỳ, {dates[0]} -> {dates[-1]} (MC B={B})")
    for r, h in zip(rows, holm):
        print(f"  {r[0]:24s} obs={r[1]:9.3f} exp={r[2]:9.3f} z={r[3]:+5.2f} p={r[4]:.3f} Holm={h:.3f}{'  <--' if h < .05 else ''}")
    return [r[4] for r in rows]


def backtest(game, window=100):
    draws, _, _, k, n = load_set(game)
    pickk = 10 if game == "keno" else k
    if game == "keno":
        window = 500
    T = len(draws)
    M = indicator(draws, n).astype(np.int32)
    idx = np.arange(min(200, T // 5), T)
    cs = np.vstack([np.zeros((1, n), dtype=np.int64), np.cumsum(M, axis=0)])
    allc = cs[idx]
    winc = cs[idx] - cs[np.maximum(idx - window, 0)]
    hit = lambda p: M[idx[:, None], p].sum(1)
    last = np.full((T + 1, n), -1)
    cur = np.full(n, -1)
    for t in range(T):
        last[t] = cur
        cur = np.where(M[t] == 1, t, cur)
    S = {
        "nóng": hit(np.argsort(-allc, 1)[:, :pickk]),
        f"nóng {window} kỳ": hit(np.argsort(-winc, 1)[:, :pickk]),
        "lạnh": hit(np.argsort(allc, 1)[:, :pickk]),
        "lâu chưa ra": hit(np.argsort(last[idx], 1)[:, :pickk]),
        "lặp kỳ trước": hit(np.argsort(-M[idx - 1], 1)[:, :pickk]),
    }
    p0 = k / n
    m0 = pickk * p0
    v0 = pickk * p0 * (1 - p0) * (n - pickk) / (n - 1)
    txt = "; ".join(f"{kk} {h.mean():.4f} (z={(h.mean() - m0) / math.sqrt(v0 / len(h)):+.2f})" for kk, h in S.items())
    print(f"  backtest {game}: {txt} | kỳ vọng {m0:.4f}")


def bingo18():
    rows = sorted(read("bingo18.jsonl"), key=lambda r: (r["date"], int(r["id"])))
    R = np.array([r["result"] for r in rows])
    T = len(R)
    s = R.sum(1)
    ps = np.array([sum(1 for a in range(1, 7) for b in range(1, 7) for c in range(1, 7) if a + b + c == t) / 216 for t in range(3, 19)])
    big = (s >= 11).astype(int)
    runs = 1 + (np.diff(big) != 0).sum()
    n1 = big.sum()
    mu = 2 * n1 * (T - n1) / T + 1
    var = (mu - 1) * (mu - 2) / (T - 1)
    t = [
        ("mặt đều", stats.chisquare(np.bincount(R.ravel(), minlength=7)[1:]).pvalue),
        ("tổng theo lý thuyết", stats.chisquare(np.bincount(s, minlength=19)[3:], ps * T).pvalue),
        ("tổng(t)-tổng(t-1)", stats.pearsonr(s[1:], s[:-1]).pvalue),
        ("runs Lớn/Nhỏ", 2 * stats.norm.sf(abs((runs - mu) / math.sqrt(var)))),
    ]
    h = multipletests([x[1] for x in t], method="holm")[1]
    print(f"\n== BINGO18: {T} kỳ | " + "; ".join(f"{a} p={p:.3f} (Holm {hh:.3f})" for (a, p), hh in zip(t, h)))


def digits_3d(forward_since=None):
    """Kiểm tra chữ số cuối = 6 ở MAX 3D / 3D Pro; kiểm chứng tiến nếu có --forward-since."""
    print("\n== MAX 3D / 3D PRO: chữ số cuối = 6")
    zs = []
    for fn in ["3d.jsonl", "3d_pro.jsonl"]:
        rows = load_3d(fn)
        allN = [x for _, ns in rows for x in ns]
        k6 = sum(x[2] == "6" for x in allN)
        n = len(allN)
        ci = stats.binomtest(k6, n).proportion_ci(0.95)
        print(f" {fn}: {n} số, P(cuối=6)={k6 / n:.4f} CI95=({ci.low:.4f},{ci.high:.4f}) p={stats.binomtest(k6, n, .1).pvalue:.1e}")
        for pos in range(3):
            c = np.bincount([int(x[pos]) for x in allN], minlength=10)
            print(f"   vị trí {pos + 1}: chi2 p={stats.chisquare(c).pvalue:.2e}")
        if forward_since:
            fw = [x for d, ns in rows if d > forward_since for x in ns]
            if fw:
                kf = sum(x[2] == "6" for x in fw)
                nf = len(fw)
                zf = (kf - nf / 10) / math.sqrt(nf * .09)
                zs.append(zf)
                print(f"   kiểm chứng tiến (> {forward_since}): {nf} số, cuối=6: {kf} (kv {nf / 10:.0f}), z={zf:+.2f}, p một phía={stats.norm.sf(zf):.3f}")
    if zs:
        z = sum(zs) / math.sqrt(len(zs))
        print(f" Stouffer 2 giải (kiểm chứng tiến): z={z:+.2f}, p một phía={stats.norm.sf(z):.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", nargs="*", default=["645", "655", "535"])
    ap.add_argument("--mc", type=int, default=1500)
    ap.add_argument("--forward-since", default="2026-10-15")
    a = ap.parse_args()
    allp = []
    for g in a.games:
        allp += monte_carlo(g, 40 if g == "keno" else a.mc, fast=(g == "keno"))
        backtest(g)
    bingo18()
    digits_3d(a.forward_since)
    if allp:
        print(f"\nSố kiểm định: {len(allp)} | p nhỏ nhất {min(allp):.4f} | Bonferroni {min(1, min(allp) * len(allp)):.3f}")


if __name__ == "__main__":
    main()
