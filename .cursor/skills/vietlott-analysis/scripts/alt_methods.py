"""Các phương pháp phân tích khác: học máy, kiểm tra ngẫu nhiên kiểu NIST, Bayes, phổ tần số,
phụ thuộc giữa các kỳ, lịch/ngày, và cấu trúc bên trong số 3D.

Dùng:  python alt_methods.py {ml,nist,bayes,spectral,crossdraw,calendar,struct3d,sumparity,all}
"""
import math
import sys
import zlib
from datetime import date

import numpy as np
from scipy import stats
from scipy.special import erfc, gammainc, gammaln
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.multitest import multipletests

from common import GAMES, TIER_ORDER, indicator, load_3d, load_set, read

rng = np.random.default_rng(20261028)
LOTTO = ["645", "655", "535"]


def hdr(t):
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


# ----------------------------------------------------------------------------------------
# 1. Học máy walk-forward: dự đoán từng số có xuất hiện ở kỳ kế tiếp không
# ----------------------------------------------------------------------------------------
def build_features(M, wd, warm):
    T, n = M.shape
    cs = np.vstack([np.zeros((1, n), dtype=np.int32), np.cumsum(M, axis=0, dtype=np.int32)])
    idx = np.arange(warm, T)
    feats = []
    for w in (10, 50, 200):
        c = cs[idx] - cs[np.maximum(idx - w, 0)]
        feats.append(c / np.minimum(idx, w)[:, None])
    last = np.full((T + 1, n), -1)
    cur = np.full(n, -1)
    for t in range(T):
        last[t] = cur
        cur = np.where(M[t] == 1, t, cur)
    feats.append(np.minimum(idx[:, None] - last[idx], 200))
    feats.append(M[idx - 1])
    feats.append(M[idx - 2])
    num = np.tile(np.arange(1, n + 1), (len(idx), 1))
    feats.append(num / n)
    feats.append(num % 2)
    feats.append(np.tile(wd[idx][:, None], (1, n)) / 6.0)
    X = np.stack(feats, axis=2).astype(np.float32)
    return X, M[idx], idx


def run_ml():
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.preprocessing import StandardScaler

    hdr("1. HỌC MÁY WALK-FORWARD (train 60% đầu theo thời gian, test 40% sau)\n"
        "   Đặc trưng: tần suất 10/50/200 kỳ, khoảng cách từ lần ra gần nhất, ra ở t-1/t-2, số, chẵn/lẻ, thứ.\n"
        "   Kiểm định ở mức từng kỳ (độc lập): log-loss so với tỉ lệ nền, và số trúng của top-k so với ngẫu nhiên.")
    for g in LOTTO + ["keno"]:
        draws, wd, _, k, n = load_set(g)
        M = indicator(draws, n)
        warm = 200
        X, Y, idx = build_features(M, wd, warm)
        T = len(idx)
        cut = int(T * 0.6)
        Xtr, Ytr = X[:cut].reshape(-1, X.shape[2]), Y[:cut].reshape(-1)
        Xte, Yte = X[cut:].reshape(-1, X.shape[2]), Y[cut:].reshape(-1)
        if len(Ytr) > 1_500_000:
            sel = rng.choice(len(Ytr), 1_500_000, replace=False)
            Xtr, Ytr = Xtr[sel], Ytr[sel]
        base = Ytr.mean()
        sc = StandardScaler().fit(Xtr)
        models = {
            "logistic": LogisticRegression(max_iter=200).fit(sc.transform(Xtr), Ytr),
            "gradient boosting": HistGradientBoostingClassifier(max_iter=120, max_depth=3, learning_rate=0.05,
                                                                l2_regularization=1.0, random_state=0).fit(Xtr, Ytr),
        }
        print(f"\n-- {g}: train {cut} kỳ, test {T - cut} kỳ, tỉ lệ nền {base:.4f} (lý thuyết {k / n:.4f})")
        nte = T - cut
        for name, m in models.items():
            inp = sc.transform(Xte) if name == "logistic" else Xte
            p = np.clip(m.predict_proba(inp)[:, 1], 1e-6, 1 - 1e-6)
            P = p.reshape(nte, n)
            Yt = Yte.reshape(nte, n)
            ll_m = -(Yt * np.log(P) + (1 - Yt) * np.log(1 - P)).mean(1)
            ll_b = -(Yt * math.log(base) + (1 - Yt) * math.log(1 - base)).mean(1)
            d = ll_b - ll_m
            t = stats.ttest_1samp(d, 0)
            auc = roc_auc_score(Yte, p)
            pk = 10 if g == "keno" else k
            hits = np.take_along_axis(Yt, np.argsort(-P, 1)[:, :pk], 1).sum(1)
            m0 = pk * k / n
            v0 = pk * (k / n) * (1 - k / n) * (n - pk) / (n - 1)
            z = (hits.mean() - m0) / math.sqrt(v0 / nte)
            print(f"   {name:18s} AUC={auc:.4f} | cải thiện log-loss/kỳ={d.mean():+.2e} (t={t.statistic:+.2f}, p={t.pvalue:.3f})"
                  f" | top-{pk} trúng TB {hits.mean():.4f} vs {m0:.4f} (z={z:+.2f})")


# ----------------------------------------------------------------------------------------
# 2. Bộ kiểm tra tính ngẫu nhiên kiểu NIST SP 800-22 trên chuỗi bit
# ----------------------------------------------------------------------------------------
def monobit(b):
    n = len(b)
    return erfc(abs((2 * b.astype(int) - 1).sum()) / math.sqrt(n) / math.sqrt(2))


def runs_test(b):
    n = len(b)
    pi = b.mean()
    if abs(pi - .5) >= 2 / math.sqrt(n):
        return 0.0
    v = 1 + int((b[1:] != b[:-1]).sum())
    return erfc(abs(v - 2 * n * pi * (1 - pi)) / (2 * math.sqrt(2 * n) * pi * (1 - pi)))


def spectral(b):
    n = len(b)
    f = np.abs(np.fft.fft(2 * b.astype(float) - 1))[: n // 2]
    thr = math.sqrt(math.log(1 / 0.05) * n)
    n1 = (f < thr).sum()
    n0 = 0.95 * n / 2
    d = (n1 - n0) / math.sqrt(n * 0.95 * 0.05 / 4)
    return erfc(abs(d) / math.sqrt(2))


def apen(b, m=3):
    n = len(b)
    def phi(mm):
        ext = np.concatenate([b, b[: mm - 1]]) if mm > 1 else b
        codes = np.zeros(n, dtype=int)
        for i in range(mm):
            codes = codes * 2 + ext[i: i + n]
        c = np.bincount(codes, minlength=2 ** mm) / n
        c = c[c > 0]
        return (c * np.log(c)).sum()
    ap = phi(m) - phi(m + 1)
    chi = 2 * n * (math.log(2) - ap)
    return 1 - gammainc(2 ** (m - 1), chi / 2)


def compress_z(b, R=200):
    def size(x):
        return len(zlib.compress(x.astype(np.uint8).tobytes(), 9))
    obs = size(b)
    pi = b.mean()
    sims = [size((rng.random(len(b)) < pi).astype(np.uint8)) for _ in range(R)]
    sd = np.std(sims)
    if sd == 0:
        return float('nan'), float('nan')
    z = (obs - np.mean(sims)) / sd
    return 2 * stats.norm.sf(abs(z)), z


def streams():
    out = {}
    rows = sorted(read("bingo18.jsonl"), key=lambda r: (r["date"], int(r["id"])))
    s = np.array([sum(r["result"]) for r in rows])
    out["bingo18 Lớn/Nhỏ (tổng>=11)"] = (s >= 11).astype(np.uint8)
    out["bingo18 tổng chẵn/lẻ"] = (s % 2).astype(np.uint8)
    for g in ["keno"] + LOTTO:
        draws, _, _, k, n = load_set(g)
        sm = draws.sum(1)
        out[f"{g} tổng > trung bình"] = (sm > k * (n + 1) / 2).astype(np.uint8)
        out[f"{g} tổng chẵn/lẻ"] = (sm % 2).astype(np.uint8)
    for fn in ["3d.jsonl", "3d_pro.jsonl"]:
        seq = [int(x[2]) for _, ns in load_3d(fn) for x in ns]
        out[f"{fn} chữ số cuối > 4"] = (np.array(seq) > 4).astype(np.uint8)
        out[f"{fn} chữ số cuối = 6"] = (np.array(seq) == 6).astype(np.uint8)
    return out


def run_nist():
    hdr("2. KIỂM TRA NGẪU NHIÊN KIỂU NIST trên chuỗi bit rút từ kết quả\n"
        "   Monobit, Runs, Spectral (FFT), Approximate Entropy, Ljung-Box (lag 1..20), độ nén zlib so với chuỗi ngẫu nhiên")
    allp = []
    for name, b in streams().items():
        ps = {"monobit": monobit(b), "runs": runs_test(b), "spectral": spectral(b), "apen": apen(b),
              "ljung-box": acorr_ljungbox(b.astype(float) - b.mean(), lags=[20], return_df=True)["lb_pvalue"].iloc[0],
              "nén": compress_z(b)[0]}
        if name.endswith("= 6"):
            for key in ("monobit", "runs", "spectral", "apen"):
                ps.pop(key)
        allp += [v for v in ps.values() if v == v]
        print(f"-- {name} (n={len(b)}, tỉ lệ 1 = {b.mean():.4f})  " + "  ".join(f"{k}={v:.3f}" for k, v in ps.items()))
    h = multipletests(allp, method="holm")[1]
    print(f"\n   {len(allp)} p-value; nhỏ nhất {np.nanmin(allp):.4f}; Holm nhỏ nhất {h.min():.3f}")
    print("   (Chuỗi 'chữ số cuối = 6' có tỉ lệ 1 ≈ 0.11 nên chỉ xét Ljung-Box và độ nén.)")


# ----------------------------------------------------------------------------------------
# 3. Bayes factor Dirichlet-multinomial: đều vs lệch
# ----------------------------------------------------------------------------------------
def log10_bf(counts, a=1.0):
    K = len(counts)
    N = counts.sum()
    lm = gammaln(K * a) - gammaln(N + K * a) + (gammaln(counts + a) - gammaln(a)).sum()
    l0 = N * math.log(1 / K)
    return (lm - l0) / math.log(10)


def run_bayes():
    hdr("3. BAYES FACTOR (Dirichlet-multinomial, tiên nghiệm đối xứng)\n"
        "   log10 BF(lệch : đều).  < 0: bằng chứng ủng hộ ĐỀU;  > 0: ủng hộ có lệch.  |log10 BF| > 2 là mạnh.\n"
        "   Với các giải bốc không hoàn lại, mô hình multinomial hơi bảo thủ.")
    for g in LOTTO + ["keno"]:
        draws, _, _, k, n = load_set(g)
        c = np.bincount(draws.ravel(), minlength=n + 1)[1:]
        print(f"  {g:5s} tần suất số   : " + "  ".join(f"a={a}: {log10_bf(c, a):+.2f}" for a in (0.5, 1, 10, 100)))
    rows = sorted(read("bingo18.jsonl"), key=lambda r: (r["date"], int(r["id"])))
    R = np.array([r["result"] for r in rows])
    print("  bingo18 mặt xúc xắc : " + "  ".join(f"a={a}: {log10_bf(np.bincount(R.ravel(), minlength=7)[1:], a):+.2f}" for a in (0.5, 1, 10, 100)))
    for fn in ["3d.jsonl", "3d_pro.jsonl"]:
        allN = [x for _, ns in load_3d(fn) for x in ns]
        for pos in range(3):
            c = np.bincount([int(x[pos]) for x in allN], minlength=10)
            print(f"  {fn:13s} chữ số vị trí {pos + 1}: " + "  ".join(f"a={a}: {log10_bf(c, a):+.2f}" for a in (0.5, 1, 10, 100)))
    # BF cho giả thuyết điểm: P(cuối=6) = theta vs 0.1, theta ~ Beta(1,9)*... dùng Beta(a,b) tập trung quanh 0.1
    print("\n  Giả thuyết hẹp 'P(cuối = 6) khác 0.1' (tiên nghiệm theta ~ Beta(10,90), tập trung quanh 0.1):")
    for fn in ["3d.jsonl", "3d_pro.jsonl"]:
        allN = [x for _, ns in load_3d(fn) for x in ns]
        n = len(allN)
        k6 = sum(x[2] == "6" for x in allN)
        a, b = 10, 90
        lm = gammaln(a + b) - gammaln(a) - gammaln(b) + gammaln(k6 + a) + gammaln(n - k6 + b) - gammaln(n + a + b)
        l0 = k6 * math.log(.1) + (n - k6) * math.log(.9)
        print(f"    {fn}: log10 BF = {(lm - l0) / math.log(10):+.2f}")


# ----------------------------------------------------------------------------------------
# 4. Phổ tần số (chu kỳ ẩn)
# ----------------------------------------------------------------------------------------
def run_spectral():
    hdr("4. PHỔ TẦN SỐ: có chu kỳ ẩn trong chuỗi xuất hiện của từng số?\n"
        "   Thống kê: đỉnh lớn nhất của periodogram chuẩn hoá trên mọi (số, tần số); null bằng hoán vị thứ tự kỳ.")
    for g in LOTTO + ["keno"]:
        draws, _, _, k, n = load_set(g)
        M = indicator(draws, n).astype(np.float32)
        T = len(M)
        p = k / n
        def peaks(X):
            F = np.fft.rfft(X - p, axis=0)
            P = (np.abs(F) ** 2) / (T * p * (1 - p))
            P = P[1:-1]
            return P.max(), P.mean(1).max()
        mx, mm = peaks(M)
        R = 60 if g == "keno" else 300
        null = np.array([peaks(M[rng.permutation(T)]) for _ in range(R)])
        p1 = (1 + (null[:, 0] >= mx).sum()) / (R + 1)
        p2 = (1 + (null[:, 1] >= mm).sum()) / (R + 1)
        print(f"  {g:5s} T={T}: đỉnh riêng từng số {mx:.1f} (null TB {null[:, 0].mean():.1f}) p={p1:.3f} | "
              f"đỉnh trung bình các số {mm:.2f} (null TB {null[:, 1].mean():.2f}) p={p2:.3f}")


# ----------------------------------------------------------------------------------------
# 5. Phụ thuộc chéo giữa kỳ t và t+lag (mọi cặp số)
# ----------------------------------------------------------------------------------------
def run_crossdraw():
    hdr("5. PHỤ THUỘC CHÉO: số i ở kỳ t có kéo theo số j ở kỳ t+lag không? (bảng n×n, null hoán vị)")
    for g in LOTTO + ["keno"]:
        draws, _, _, k, n = load_set(g)
        M = indicator(draws, n).astype(np.float32)
        if g == "keno":
            M = M[-20000:]
        T = len(M)
        def stat(X, lag):
            A, B = X[:-lag], X[lag:]
            N = A.T @ B
            E = np.outer(A.sum(0), B.sum(0)) / len(A)
            return ((N - E) ** 2 / E).sum()
        for lag in (1, 2, 3, 7):
            obs = stat(M, lag)
            R = 40 if g == "keno" else 150
            null = np.array([stat(M[rng.permutation(T)], lag) for _ in range(R)])
            z = (obs - null.mean()) / null.std()
            p = (1 + (null >= obs).sum()) / (R + 1)
            print(f"  {g:5s} lag={lag}: chi2={obs:9.1f} null TB={null.mean():9.1f} z={z:+.2f} p={p:.3f}")


# ----------------------------------------------------------------------------------------
# 6. Quan hệ với ngày tháng
# ----------------------------------------------------------------------------------------
def run_calendar():
    hdr("6. LỊCH: ngày trong tháng / tháng của kỳ quay có xuất hiện trong bộ số nhiều hơn mức ngẫu nhiên?")
    for g in LOTTO:
        draws, _, dates, k, n = load_set(g)
        p = k / n
        for label, fn_, lim in (("ngày trong tháng", lambda d: d.day, 31), ("tháng", lambda d: d.month, 12)):
            hit = tot = 0
            for row, ds in zip(draws, dates):
                v = fn_(date.fromisoformat(ds))
                if v <= n:
                    tot += 1
                    hit += int(v in row)
            bt = stats.binomtest(hit, tot, p)
            print(f"  {g}: {label:17s} trùng {hit}/{tot} = {hit / tot:.4f} (kv {p:.4f}) p={bt.pvalue:.3f}")
        small = (draws <= 31).sum() / draws.size
        print(f"  {g}: tỉ lệ số <= 31: {small:.4f} (kv {31 / n:.4f})")


# ----------------------------------------------------------------------------------------
# 7. Cấu trúc bên trong số 3D
# ----------------------------------------------------------------------------------------
def chi_indep(a, b):
    tab = np.zeros((10, 10))
    np.add.at(tab, (a, b), 1)
    return stats.chi2_contingency(tab)[1]


def run_struct3d():
    hdr("7. CẤU TRÚC BÊN TRONG MAX 3D / 3D PRO (nơi duy nhất có bất thường)")
    pooled = {s: [0, 0] for s in range(20)}
    for fn in ["3d.jsonl", "3d_pro.jsonl"]:
        rows = load_3d(fn)
        nums = [x for _, ns in rows for x in ns]
        A = np.array([[int(c) for c in x] for x in nums])
        print(f"\n-- {fn}: {len(rows)} kỳ, {len(nums)} số")
        ps = [("chữ số d1 ⟂ d2", chi_indep(A[:, 0], A[:, 1])), ("d2 ⟂ d3", chi_indep(A[:, 1], A[:, 2])),
              ("d1 ⟂ d3", chi_indep(A[:, 0], A[:, 2]))]
        full = [(ns[i], ns[i + 1]) for _, ns in rows for i in range(len(ns) - 1)]
        a = np.array([int(x[2]) for x, _ in full])
        b = np.array([int(y[2]) for _, y in full])
        ps.append(("chữ số cuối số liền kề trong kỳ", chi_indep(a, b)))
        ds = np.bincount(A.sum(1), minlength=28)
        pr = np.array([sum(1 for x in range(10) for y in range(10) for z in range(10) if x + y + z == s) / 1000 for s in range(28)])
        ps.append(("tổng chữ số theo lý thuyết", stats.chisquare(ds, pr * len(A)).pvalue))
        dup = sum(1 for _, ns in rows if len(set(ns)) < len(ns))
        pnodup = np.prod([1 - i / 1000 for i in range(20)])
        ps.append(("số kỳ có số trùng (va chạm)", stats.binomtest(dup, len(rows), 1 - pnodup).pvalue))
        for name, p in ps:
            print(f"   {name:34s} p={p:.3f}")
        print(f"   (kỳ có số trùng: {dup}/{len(rows)} = {dup / len(rows):.3f}, kỳ vọng {1 - pnodup:.3f})")
        per_slot = np.zeros((20, 2))
        for _, ns in rows:
            if len(ns) == 20:
                for s, x in enumerate(ns):
                    per_slot[s] += (x[2] == "6", 1)
                    pooled[s][0] += x[2] == "6"
                    pooled[s][1] += 1
        r = per_slot[:, 0] / per_slot[:, 1]
        rho = stats.spearmanr(np.arange(20), r)
        c = stats.chi2_contingency(np.stack([per_slot[:, 0], per_slot[:, 1] - per_slot[:, 0]]))[1]
        print(f"   tỉ lệ cuối=6 theo vị trí quay (0..19): chi2 đồng nhất p={c:.3f}; Spearman với thứ tự rho={rho.statistic:+.2f} p={rho.pvalue:.3f}")
        by_tier = {}
        i = 0
        for t, cnt in zip(TIER_ORDER, (2, 4, 6, 8)):
            by_tier[t] = (sum(x[2] == "6" for _, ns in rows if len(ns) == 20 for x in ns[i:i + cnt]), len(rows) * cnt)
            i += cnt
        print("   theo giải: " + "; ".join(f"{t} {a / b:.3f}" for t, (a, b) in by_tier.items()))
        # theo năm
        yr = {}
        for d, ns in rows:
            y = d[:4]
            for x in ns:
                yr.setdefault(y, [0, 0])
                yr[y][0] += x[2] == "6"
                yr[y][1] += 1
        print("   theo năm: " + "; ".join(f"{y} {a / b:.3f}" for y, (a, b) in sorted(yr.items())))
        c = stats.chi2_contingency(np.array([[a, b - a] for a, b in yr.values()]))[1]
        print(f"   đồng nhất giữa các năm: p={c:.3f}")
    s = np.array([pooled[i] for i in range(20)])
    print("\n   Gộp 2 giải, theo vị trí quay: " + " ".join(f"{a / b:.3f}" for a, b in s))
    print(f"   gộp: tỉ lệ cuối=6 = {s[:, 0].sum() / s[:, 1].sum():.4f}")


# ----------------------------------------------------------------------------------------
# 8. Chẵn/lẻ của tổng (ứng viên: Lotto 5/35)
# ----------------------------------------------------------------------------------------
def run_sumparity(forward_since="2026-10-14"):
    hdr("8. CHẴN/LẺ CỦA TỔNG: tỉ lệ kỳ có tổng lẻ so với lý thuyết, đồng nhất theo quý, kiểm chứng tiến")
    import collections
    for g in LOTTO:
        d, _, dates, k, n = load_set(g)
        nodd = (n + 1) // 2
        pe = [math.comb(nodd, j) * math.comb(n - nodd, k - j) / math.comb(n, k) for j in range(k + 1)]
        p0 = sum(pe[j] for j in range(1, k + 1, 2))
        par = d.sum(1) % 2
        T = len(par)
        pv = stats.binomtest(int(par.sum()), T, p0).pvalue
        q = collections.OrderedDict()
        for ds, p in zip(dates, par):
            key = ds[:4] + "Q%d" % ((int(ds[5:7]) - 1) // 3 + 1)
            q.setdefault(key, [0, 0])
            q[key][0] += int(p)
            q[key][1] += 1
        full = [v for v in q.values() if v[1] >= 50]
        het = stats.chi2_contingency(np.array([[a, b - a] for a, b in full]))[1] if len(full) > 1 else float("nan")
        old = [p for p, ds in zip(par, dates) if ds <= forward_since]
        new = [p for p, ds in zip(par, dates) if ds > forward_since]
        line = f"  {g}: tổng lẻ {par.mean():.4f} (lý thuyết {p0:.4f}), T={T}, p={pv:.5f}, đồng nhất theo quý p={het:.3f}"
        if new:
            line += f" | trước {forward_since}: {np.mean(old):.3f} (n={len(old)}); sau: {np.mean(new):.3f} (n={len(new)}, p một phía={stats.binom.sf(int(sum(new)) - 1, len(new), p0):.3f})"
        print(line)


COMMANDS = {"ml": run_ml, "nist": run_nist, "bayes": run_bayes, "spectral": run_spectral,
            "crossdraw": run_crossdraw, "calendar": run_calendar, "struct3d": run_struct3d,
            "sumparity": run_sumparity}

if __name__ == "__main__":
    which = sys.argv[1:] or ["all"]
    if "all" in which:
        which = list(COMMANDS)
    for w in which:
        COMMANDS[w]()
