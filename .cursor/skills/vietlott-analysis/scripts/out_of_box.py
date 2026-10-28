"""Các giả thuyết "ngoài khuôn": tổ hợp lặp lại, liên hệ giữa các giải, mã kỳ quay, dấu vết PRNG,
tương đồng bên trong một kỳ 3D, và xác suất "có người trúng nhiều lần" theo ngẫu nhiên.

Dùng:  python out_of_box.py {winners,overlap,crossgame,drawid,prng,within3d,all}
"""
import math
import sys
from bisect import bisect_left

import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

from common import indicator, load_3d, load_set, read, rows_for

rng = np.random.default_rng(20261028)
LOTTO = ["645", "655", "535"]


def hdr(t):
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


# --------------------------------------------------------------------------------------
def run_winners():
    hdr("A. 'CÓ NGƯỜI TRÚNG NHIỀU LẦN' CÓ CẦN QUY LUẬT ẨN KHÔNG? (tính theo ngẫu nhiên thuần)")
    from scipy.stats import binom, poisson
    # Max 3D Pro: một dòng 2 bộ ba số, xác suất trúng ít nhất 1 giải nhỏ mỗi kỳ
    q = 1 - (1 - 1 / 1000) ** 20
    p_line = 1 - (1 - q) ** 2 + 0.0  # xấp xỉ: ít nhất 1 trong 2 bộ số xuất hiện trong 20 số trúng
    print(f"  Max 3D Pro: xác suất 1 dòng trúng ít nhất 1 giải mỗi kỳ ≈ {p_line:.3%}")
    for lines_per_draw, draws_per_week, weeks in [(1, 3, 52), (5, 3, 52), (5, 3, 4)]:
        L = lines_per_draw * draws_per_week * weeks
        e = L * p_line
        print(f"    {lines_per_draw} dòng/kỳ, {draws_per_week} kỳ/tuần, {weeks} tuần ({L} dòng): kỳ vọng {e:.1f} lần trúng, "
              f"P(trúng >= 2 lần) = {binom.sf(1, L, p_line):.3f}, P(>= 5 lần) = {binom.sf(4, L, p_line):.3f}")
    print("  => Trúng giải nhỏ nhiều lần là điều BÌNH THƯỜNG với người chơi đều đặn; không cần quy luật.")
    # Jackpot Power 6/55
    print("\n  Jackpot (giả định minh hoạ, không phải số liệu thật về số người chơi):")
    for name, odds in [("Power 6/55", 28_989_675), ("Mega 6/45", 8_145_060)]:
        for players in (200_000, 1_000_000):
            tickets_per_player_draw = 1
            draws = 1400
            p_player = 1 - (1 - 1 / odds) ** (draws * tickets_per_player_draw)
            exp1 = players * p_player
            exp2 = players * binom.sf(1, draws, 1 / odds)
            print(f"    {name}, {players:,} người mua 1 vé/kỳ suốt {draws} kỳ: kỳ vọng {exp1:.1f} người từng trúng jackpot, "
                  f"{exp2:.4f} người trúng 2 lần")
    print("  => Trúng jackpot 2 lần bằng 1 vé/kỳ gần như không xảy ra; nếu có thì thường là người mua rất nhiều vé/dãy "
          "('bao' số) hoặc nhóm góp vé. Số tổ hợp mua nhiều thì xác suất tăng đúng bằng tỉ lệ số vé, không do số 'hay ra'.")
    print("  Thiên lệch chọn lọc: ta chỉ nghe về người trúng, không nghe về hàng triệu người mua không trúng.")


# --------------------------------------------------------------------------------------
def overlap_hist(M, kmax):
    O = M.astype(np.float32) @ M.astype(np.float32).T
    iu = np.triu_indices(len(M), 1)
    return np.bincount(O[iu].astype(int), minlength=kmax + 1)


def run_overlap():
    hdr("B. TỔ HỢP LẶP LẠI: số cặp kỳ có chung >= m số so với lý thuyết (siêu bội)\n"
        "   Nếu có 'bộ số hay xuất hiện', đuôi phân phối (trùng nhiều số) sẽ dày hơn ngẫu nhiên. Null Monte Carlo.")
    for g in LOTTO + ["keno"]:
        d, _, _, k, n = load_set(g)
        if g == "keno":
            d = d[-4000:]
        T = len(d)
        M = indicator(d, n)
        obs = overlap_hist(M, k)
        npairs = T * (T - 1) / 2
        pm = np.array([math.comb(k, o) * math.comb(n - k, k - o) / math.comb(n, k) for o in range(k + 1)])
        B = 40 if g == "keno" else 150
        sims = []
        for _ in range(B):
            s = np.sort(rng.random((T, n)).argpartition(k, axis=1)[:, :k] + 1, axis=1)
            sims.append(overlap_hist(indicator(s, n), k))
        sims = np.array(sims, dtype=float)
        print(f"\n-- {g}: {T} kỳ, {int(npairs):,} cặp kỳ (chung số: quan sát | kỳ vọng | z so với null MC)")
        tail_rows = []
        top = range(max(0, k // 2), k + 1)
        for o in top:
            mu, sd = sims[:, o].mean(), sims[:, o].std(ddof=1)
            z = (obs[o] - mu) / sd if sd > 0 else float("nan")
            tail_rows.append(z)
            print(f"   chung {o}: {obs[o]:>10d} | {npairs * pm[o]:>12.1f} | z={z:+.2f}")
        for m in (k - 2, k - 1, k):
            ob = obs[m:].sum()
            sm = sims[:, m:].sum(1)
            mu, sd = sm.mean(), sm.std(ddof=1)
            print(f"   chung >= {m}: {ob} (kv {mu:.2f}); p MC={(1 + (sm >= ob).sum()) / (B + 1):.3f}")


# --------------------------------------------------------------------------------------
def run_crossgame():
    hdr("C. LIÊN HỆ GIỮA CÁC GIẢI: bộ số của giải A có liên quan tới bộ số gần nhất trước đó của giải B?\n"
        "   Thống kê: số trùng trung bình; null = dịch vòng chuỗi B (giữ nguyên cấu trúc, phá cặp).")
    data = {g: load_set(g) for g in LOTTO}
    pairs = [("645", "655"), ("655", "645"), ("645", "535"), ("535", "645"), ("655", "535"), ("535", "655")]
    ps = []
    for a, b in pairs:
        da, _, dates_a, ka, na = data[a]
        db, _, dates_b, kb, nb = data[b]
        Mb = indicator(db, nb)
        Ma = indicator(da, na)
        m = min(na, nb)
        idx = []
        for i, ds in enumerate(dates_a):
            j = bisect_left(dates_b, ds) - 1
            idx.append(j)
        idx = np.array(idx)
        ok = idx >= 0
        A = Ma[ok][:, :m].astype(float)
        jj = idx[ok]
        def stat(shift):
            B_ = Mb[(jj + shift) % len(Mb)][:, :m].astype(float)
            return (A * B_).sum(1).mean()
        obs = stat(0)
        null = np.array([stat(int(rng.integers(30, len(Mb) - 30))) for _ in range(500)])
        z = (obs - null.mean()) / null.std()
        p = (1 + (np.abs(null - null.mean()) >= abs(obs - null.mean())).sum()) / 501
        ps.append(p)
        print(f"  {a} <- {b} (kỳ gần nhất trước đó): trùng TB {obs:.4f} vs null {null.mean():.4f}, z={z:+.2f}, p={p:.3f}")
    print(f"  Holm nhỏ nhất: {multipletests(ps, method='holm')[1].min():.3f}")


# --------------------------------------------------------------------------------------
def run_drawid():
    hdr("D. MÃ KỲ QUAY: số thứ tự kỳ (mod m) có liên quan tới số xuất hiện không? (null hoán vị nhãn)")
    for g in LOTTO:
        d, _, _, k, n = load_set(g)
        rows = rows_for(g)
        ids = np.array([int(r["id"]) for r in rows])
        M = indicator(d, n).astype(float)
        out = []
        for m in (2, 3, 4, 5, 6, 7, 8, 10, 12):
            lab = ids % m
            def stat(labels):
                W = np.array([M[labels == c].sum(0) for c in range(m)])
                E = W.sum(1, keepdims=True) * W.sum(0, keepdims=True) / W.sum()
                return ((W - E) ** 2 / E).sum()
            obs = stat(lab)
            null = np.array([stat(rng.permutation(lab)) for _ in range(300)])
            out.append((m, (1 + (null >= obs).sum()) / 301))
        h = multipletests([p for _, p in out], method="holm")[1]
        print(f"  {g}: " + "  ".join(f"mod{m}: p={p:.2f}" for m, p in out) + f"  | Holm nhỏ nhất {h.min():.2f}")


# --------------------------------------------------------------------------------------
def berlekamp_massey(s):
    n = len(s)
    c = np.zeros(n + 1, dtype=np.uint8)
    b = np.zeros(n + 1, dtype=np.uint8)
    c[0] = b[0] = 1
    L, m = 0, -1
    for i in range(n):
        d = (s[i] + int(np.dot(c[1:L + 1], s[i - L:i][::-1]) if L else 0)) % 2
        if d:
            t = c.copy()
            sh = i - m
            c[sh:] ^= b[: n + 1 - sh]
            if 2 * L <= i:
                L, m, b = i + 1 - L, i, t
    return L


def run_prng():
    hdr("E. DẤU VẾT BỘ SINH SỐ GIẢ NGẪU NHIÊN: độ phức tạp tuyến tính (Berlekamp-Massey)\n"
        "   Chuỗi ngẫu nhiên thật có L ≈ n/2; bộ sinh tuyến tính (LFSR/Mersenne Twister) có L thấp hơn nhiều.")
    rows = sorted(read("bingo18.jsonl"), key=lambda r: (r["date"], int(r["id"])))
    s = np.array([sum(r["result"]) for r in rows])
    streams = {"bingo18 Lớn/Nhỏ": (s >= 11).astype(np.uint8), "bingo18 tổng chẵn/lẻ": (s % 2).astype(np.uint8)}
    for fn, nm in [("3d_pro.jsonl", "3D Pro chữ số cuối > 4")]:
        streams[nm] = (np.array([int(x[2]) for _, ns in load_3d(fn) for x in ns]) > 4).astype(np.uint8)
    d, _, _, k, n = load_set("keno")
    streams["keno tổng > TB"] = (d.sum(1) > k * (n + 1) / 2).astype(np.uint8)
    N = 1500
    for name, b in streams.items():
        Ls = []
        for w in range(min(12, len(b) // N)):
            Ls.append(berlekamp_massey(b[w * N:(w + 1) * N]))
        Ls = np.array(Ls)
        e0 = N / 2 + (4 + (1 if N % 2 == 0 else -1)) / 18
        t = stats.ttest_1samp(Ls - e0, 0.0)
        print(f"  {name:28s}: {len(Ls)} cửa sổ x {N} bit, L TB={Ls.mean():.1f} (kỳ vọng {e0:.2f}), "
              f"min={Ls.min()}, p={t.pvalue:.3f}")


# --------------------------------------------------------------------------------------
def run_within3d():
    hdr("F. TƯƠNG ĐỒNG BÊN TRONG MỘT KỲ 3D: các số cùng kỳ có chung chữ số cùng vị trí nhiều hơn ngẫu nhiên?\n"
        "   Null: xáo trộn chữ số trong từng vị trí giữa các số TRONG KHỐI 100 kỳ (giữ nguyên phân bố biên theo thời gian, kể cả dư chữ số 6).")
    import itertools
    for fn in ["3d.jsonl", "3d_pro.jsonl"]:
        rows = [ns for _, ns in load_3d(fn) if len(ns) == 20]
        A = np.array([[[int(c) for c in x] for x in ns] for ns in rows])
        T = len(A)
        iu = np.triu_indices(20, 1)
        def stat(X):
            eq = (X[:, iu[0], :] == X[:, iu[1], :])
            return eq.sum(axis=(1, 2)).mean(), np.bincount(eq.sum(2).ravel(), minlength=4)
        obs, hist = stat(A)
        BLK = 100
        null = []
        for _ in range(200):
            F = A.copy()
            for b0 in range(0, T, BLK):
                blk = F[b0:b0 + BLK].reshape(-1, 3)
                for p in range(3):
                    blk[:, p] = rng.permutation(blk[:, p])
                F[b0:b0 + BLK] = blk.reshape(-1, 20, 3)
            null.append(stat(F)[0])
        null = np.array(null)
        z = (obs - null.mean()) / null.std()
        print(f"  {fn}: số vị trí trùng TB mỗi kỳ (190 cặp) = {obs:.3f} vs null {null.mean():.3f}, z={z:+.2f}, "
              f"p={(1 + (np.abs(null - null.mean()) >= abs(obs - null.mean())).sum()) / 201:.3f}")
        print(f"     phân bố số vị trí trùng của cặp (0..3): {hist.tolist()}")


COMMANDS = {"winners": run_winners, "overlap": run_overlap, "crossgame": run_crossgame,
            "drawid": run_drawid, "prng": run_prng, "within3d": run_within3d}

if __name__ == "__main__":
    which = sys.argv[1:] or ["all"]
    if "all" in which:
        which = list(COMMANDS)
    for w in which:
        COMMANDS[w]()
