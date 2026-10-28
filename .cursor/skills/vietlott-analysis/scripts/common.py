"""Tải và nạp dữ liệu kết quả Vietlott (nguồn: github.com/vietvudanh/vietlott-data)."""
import json
import os
import urllib.request
from datetime import date
from pathlib import Path

import numpy as np

DATA = Path(os.environ.get("VIETLOTT_DATA", "/tmp/vietlott_data"))
BASE = "https://raw.githubusercontent.com/vietvudanh/vietlott-data/main/data/"

# tên -> (file, số bóng chính k, tổng số n)
GAMES = {
    "645": ("power645.jsonl", 6, 45),
    "655": ("power655.jsonl", 6, 55),
    "535": ("power535.jsonl", 5, 35),
    "keno": ("keno.jsonl", 20, 80),
}
TIER_ORDER = ["Giải Đặc biệt", "Giải Nhất", "Giải Nhì", "Giải ba"]


def fetch(force=False):
    DATA.mkdir(parents=True, exist_ok=True)
    for fn in ["power645", "power655", "power535", "keno", "bingo18", "3d", "3d_pro"]:
        dest = DATA / f"{fn}.jsonl"
        if force or not dest.exists() or dest.stat().st_size == 0:
            urllib.request.urlretrieve(BASE + fn + ".jsonl", dest)
    return DATA


def read(fn):
    path = DATA / fn
    if not path.exists():
        fetch()
    return [json.loads(line) for line in open(path)]


def load_set(game):
    """Trả về (draws[T,k] đã sort, weekday[T], dates, k, n)."""
    fn, k, n = GAMES[game]
    rows = read(fn)
    rows.sort(key=lambda r: (r["date"], int(r["id"].lstrip("#"))))
    draws = np.array([sorted(r["result"][:k]) for r in rows], dtype=np.int16)
    wd = np.array([date.fromisoformat(r["date"]).weekday() for r in rows])
    return draws, wd, [r["date"] for r in rows], k, n


def indicator(draws, n):
    M = np.zeros((len(draws), n), dtype=np.int8)
    M[np.arange(len(draws))[:, None], draws - 1] = 1
    return M


def load_3d(fn):
    """Mỗi kỳ -> (date, danh sách 20 số 3 chữ số theo thứ tự giải Đặc biệt, Nhất, Nhì, Ba)."""
    rows = read(fn)
    rows.sort(key=lambda r: (r["date"], int(r["id"])))
    out = []
    for r in rows:
        nums = [x for t in TIER_ORDER for x in r["result"].get(t, [])]
        out.append((r["date"], nums))
    return out
