# Kết quả phân tích (cập nhật 28/10/2026)

Dữ liệu: github.com/vietvudanh/vietlott-data, đến 25-28/10/2026. Mega 6/45 1.383 kỳ, Power 6/55 1.416, Lotto 5/35 972,
Keno 89.849, Bingo18 97.527, Max 3D 1.150, Max 3D Pro 797.

## Kết luận chung
Các giải số khớp với quay số ngẫu nhiên. Không phương pháp nào dự đoán được kỳ sau hơn ngẫu nhiên.

## Phương pháp đã thử và kết quả

| Phương pháp (script) | Kết quả |
|---|---|
| 10 kiểm định cố định + null Monte Carlo + Holm (`core_tests.py`) | Không có tín hiệu ở Mega, Power, Keno, Bingo18. Lotto 5/35 chẵn/lẻ p=0,005 (Holm trong giải 0,05; Bonferroni 30 kiểm định 0,15). |
| Backtest 5 chiến lược (nóng, lạnh, lâu chưa ra, lặp kỳ trước) | Mọi z trong khoảng -1,0 đến +1,3, ngang ngẫu nhiên. |
| Học máy walk-forward: logistic + gradient boosting, 9 đặc trưng (`alt_methods.py ml`) | AUC 0,496-0,502; log-loss không cải thiện (p 0,06-0,86); top-k trúng không hơn ngẫu nhiên (z -0,06..+1,33). |
| Kiểm tra NIST: monobit, runs, spectral, ApEn, Ljung-Box, độ nén (`nist`) | 76 p-value, p nhỏ nhất 0,0003 (tổng chẵn/lẻ Lotto 5/35), Holm 0,025. Còn lại là nhiễu. |
| Bayes factor Dirichlet-multinomial (`bayes`) | Tần suất số: log10 BF -28 đến -163 (a=1), ủng hộ đều rất mạnh. 3D chữ số cuối: phụ thuộc tiên nghiệm (a=1: -5,6 / -9,9; Beta(10,90) cho ô chữ số 6: +3,0 / +3,2, nhưng ô được chọn sau khi thấy dữ liệu). |
| Phổ tần số (chu kỳ ẩn), hoán vị (`spectral`) | Không có (p 0,12-0,80). |
| Phụ thuộc chéo giữa kỳ t và t+lag (bảng n×n) (`crossdraw`) | Không có (16 phép; p nhỏ nhất 0,033 ở 5/35 lag 2, nhiễu). |
| Lịch: ngày/tháng quay có trùng số (`calendar`) | Không có (p 0,12-1,0). Tỉ lệ số <= 31 đúng lý thuyết. |
| Cấu trúc trong số 3D (`struct3d`) | Các chữ số độc lập nhau; tổng chữ số, va chạm số trong kỳ đúng lý thuyết; dư chữ số 6 phân tán đều theo giải, vị trí quay và (Max 3D) theo năm. |

## Giả thuyết "ngoài khuôn" (`out_of_box.py`, 28/10/2026)

| Giả thuyết | Kết quả |
|---|---|
| "Có người trúng nhiều lần nên có quy luật ẩn" (`winners`) | Không cần quy luật. 1 dòng Max 3D Pro trúng ít nhất 1 giải ~3,9%/kỳ: chơi đều đặn 1 năm kỳ vọng ~6 lần trúng (5 dòng/kỳ: ~30 lần). Trúng jackpot 2 lần bằng 1 vé/kỳ gần như không xảy ra; nếu có thì thường do mua nhiều vé/dãy "bao" hoặc góp vé. Thiên lệch chọn lọc: chỉ thấy người trúng. |
| Tổ hợp lặp lại giữa các kỳ (`overlap`: mọi cặp kỳ, phân phối số trùng so với siêu bội) | Không dày đuôi ở Mega, Lotto 5/35, Keno. Power 6/55 có 1 cặp trùng cả 6 số (#00647 16/11/2021 và #00993 06/02/2024, đã đối chiếu nguồn ngoài: 08-19-27-34-46-51, số phụ 02 và 24); kỳ vọng 0,035 cặp, P(>=1)=3,4%: trùng hợp hiếm, không phải quy luật. |
| Liên hệ giữa các giải (`crossgame`) | Không có (Holm nhỏ nhất 0,07). |
| Mã kỳ quay mod m liên quan số xuất hiện (`drawid`) | Không có sau làm sạch dữ liệu (Holm nhỏ nhất 0,12). Lotto 5/35 quay 2 lần/ngày, mã lẻ = buổi 1: tổng lẻ ở cả hai buổi (54,1% và 57,4%). |
| Dấu vết bộ sinh số giả ngẫu nhiên (`prng`: độ phức tạp tuyến tính Berlekamp-Massey) | L ≈ n/2 đúng lý thuyết ở Bingo18, Keno, 3D (p 0,14-0,49): không có dấu vết LFSR. |
| Tương đồng chữ số trong một kỳ 3D (`within3d`, null xáo trộn theo khối 100 kỳ) | Max 3D z=+2,8 (p=0,015), 3D Pro z=+0,6: không nhất quán giữa hai giải, không đủ sau hiệu chỉnh. |

Lưu ý chất lượng dữ liệu: file Power 6/55 có 1 bản ghi của Mega 6/45 lẫn vào (2022-09-23, mã 00944, chỉ 6 số);
`common.rows_for` đã loại. Luôn kiểm tra mã kỳ liên tục và số lượng số mỗi kỳ trước khi phân tích.

## Hai ứng viên cần theo dõi (chưa xác nhận)

1. Max 3D / 3D Pro, chữ số cuối = 6: 10,89% / 11,09% (CI95 10,5-11,3% / 10,6-11,6%), p ~1e-5 trên toàn dữ liệu.
   Kiểm chứng tiến (kỳ sau 15/10/2026): 6/100 và 13/100, quá ít để kết luận. Cần ~6.200 số mới (~150 kỳ mỗi giải).
   Chưa loại trừ lỗi của kho dữ liệu; nên đối chiếu với vietlott.vn.
2. Lotto 5/35, tổng lẻ: 55,8% (542/972) so với 50,0%, p=0,0004, nhất quán ở mọi quý (53-58%, đồng nhất p=0,72), không có
   ở Mega/Power. 26 kỳ sau 14/10/2026: 19 lẻ (73%), p một phía=0,015. Hạn chế: giả thuyết chọn sau khi thấy dữ liệu, nằm trong
   họ ~150 kiểm định (Bonferroni ~0,05), và mẫu mới nhỏ. Nếu thật, mỗi tổ hợp tổng lẻ có xác suất cao hơn khoảng 11%,
   vẫn không đủ để có kỳ vọng dương.

## Tỉ lệ trả thưởng kỳ vọng (ước tính, bỏ qua trùng giải)
Max 3D ~55%, Max 3D Pro ~55%, Max 3D+ ~45%. Nếu thiên lệch chữ số 6 là thật: Pro ~64%, Max 3D ~60%. Tất cả < 100%.
