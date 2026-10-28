---
name: vietlott-analysis
description: Phân tích thống kê kết quả xổ số Vietlott (Mega 6/45, Power 6/55, Lotto 5/35, Keno, Bingo18, Max 3D, Max 3D Pro). Tải dữ liệu mới nhất, chạy kiểm định tính ngẫu nhiên với null Monte Carlo + hiệu chỉnh Holm, backtest walk-forward, kiểm chứng tiến cho giả thuyết chữ số cuối = 6 của Max 3D, và các phương pháp khác (học máy, NIST, Bayes, phổ tần số, phụ thuộc chéo, lịch, cấu trúc 3D, tổ hợp lặp, PRNG). Dùng khi người dùng muốn cập nhật/chạy lại phân tích Vietlott, kiểm tra "quy luật" số trúng, hoặc đánh giá một chiến lược chọn số.
license: MIT
---

# Phân tích kết quả Vietlott

Kết luận hiện tại (cập nhật 28/10/2026): kết quả các giải số khớp với quay số ngẫu nhiên; không chiến lược dự đoán nào
(số nóng, số lạnh, số lâu chưa ra, lặp kỳ trước, học máy) hơn ngẫu nhiên. Ngoại lệ cần theo dõi: chữ số cuối = 6 ở Max 3D
và Max 3D Pro (~10,9-11,1% thay vì 10%), chưa được kiểm chứng tiến đủ lớn. Xem `reference/findings.md`.

Luôn kết hợp với skill `statistical-analysis` (chọn test, hiệu chỉnh đa lần, effect size) và `statistical-power`.

## Chuẩn bị

```bash
pip install numpy scipy statsmodels scikit-learn pandas
cd .cursor/skills/vietlott-analysis/scripts
python -c "import common; common.fetch(force=True)"   # tải dữ liệu mới nhất vào $VIETLOTT_DATA (mặc định /tmp/vietlott_data)
```

Nguồn dữ liệu: https://github.com/vietvudanh/vietlott-data (vietlott.vn chặn truy cập tự động, HTTP 403).
Dữ liệu có thể được hiệu chỉnh/bù kỳ thiếu về sau, nên số kỳ có thể tăng nhiều hơn số kỳ mới.

## Quy trình

1. `python core_tests.py --games 645 655 535 --mc 1500 --forward-since YYYY-MM-DD`
   10 kiểm định cố định mỗi giải (tần suất, lặp từ kỳ trước, tự tương quan, chẵn/lẻ, tổng, cặp liền kề, nhóm chục,
   cặp số, thứ trong tuần), null Monte Carlo, Holm; backtest walk-forward 5 chiến lược; Bingo18; chữ số cuối 3D.
   Thêm `keno` vào `--games` (chậm, vài phút).
   Đặt `--forward-since` là ngày của lần phân tích trước để có kiểm chứng tiến chỉ trên kỳ mới.
2. `python alt_methods.py all` (hoặc từng phần: `ml nist bayes spectral crossdraw calendar struct3d sumparity`).
   `ml` và `spectral` cho Keno chạy vài phút; `nist` mất ~3 phút do phép đo độ nén.
3. `python out_of_box.py all` (hoặc `winners overlap crossgame drawid prng within3d`): giả thuyết ngoài khuôn,
   gồm trả lời câu "có người trúng nhiều lần thì phải có quy luật" bằng tính toán theo ngẫu nhiên thuần.
4. Báo cáo: nêu số kiểm định, p thô nhỏ nhất, Bonferroni/Holm trên cả họ, và kiểm chứng tiến.

## Quy tắc diễn giải (bắt buộc)

- Kiểm tra chất lượng dữ liệu trước (mã kỳ liên tục, đủ số mỗi kỳ, không lẫn game khác).
- Xác định họ giả thuyết TRƯỚC, đếm số kiểm định, hiệu chỉnh cả họ. p thô ~0,01-0,05 trong hàng chục kiểm định là nhiễu.
- Chi-square thường giả định bốc có hoàn lại; với 6/45, 6/55, Keno hãy dùng null Monte Carlo (đã có sẵn).
- Phát hiện sau khi nhìn dữ liệu chỉ là giả thuyết. Chỉ tính là xác nhận khi đúng ô/giả thuyết đó được kiểm trên kỳ MỚI.
- Báo công suất: dữ liệu lotto chỉ phát hiện lệch tương đối ~28-33% mỗi số; Keno ~2,5%; Bingo18 ~1,6%.
- Không gợi ý tăng tiền cược. Tỉ lệ trả thưởng kỳ vọng của Max 3D/3D Pro ~55%, Max 3D+ ~45%; nếu thiên lệch chữ số 6
  là thật thì 3D Pro lên khoảng 64%, vẫn dưới 100%.

## Điểm cần kiểm chứng tiếp

- Max 3D / Max 3D Pro: chữ số cuối = 6. Cần ~6.200 số mới (~150 kỳ mỗi giải, ~1 năm) để đủ công suất.
  Chạy `python core_tests.py --forward-since 2026-10-15` định kỳ.
- Lotto 5/35, tổng lẻ ~55,8% thay vì 50% (p=0,0004, nhất quán theo quý, không có ở Mega/Power): chạy
  `python alt_methods.py sumparity` định kỳ; giả thuyết chọn sau khi thấy dữ liệu nên cần kiểm chứng tiến.
