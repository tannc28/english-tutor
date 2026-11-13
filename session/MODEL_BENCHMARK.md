# Benchmark Haiku vs Sonnet cho lớp học (12/11/2026)

Cùng đề, cùng file đầu vào (`scratchpad/bench`), gia sư (Opus) chấm theo đáp án chuẩn.

| Việc | Haiku | Sonnet | Ghi chú |
|---|---|---|---|
| T1 · Thẻ từ (12 mục, có bẫy nghĩa) | **10/12** đúng – *unless* định nghĩa ngược ("except in the case that … does not happen"), *punt* chọn nghĩa Anh "liều thử" không khớp bài | **12/12** đúng, ghi chú hữu ích (table it Anh ≠ Mỹ, I'd = I had) | Sai nghĩa = dạy sai → không giao Haiku |
| T2 · Ra 5 câu hỏi đọc hiểu + 1 câu chép chính tả | 4,5/5 – đúng, trả lời được từ bài; phân bố dạng câu hơi lệch (thiếu 1 câu chi tiết) | 5/5 – đúng phân bố gist/chi tiết/nghĩa/suy luận | Cả hai dùng được làm bản nháp |
| T3 · Chấm bài (5 câu có đáp án) | Phán định **5/5 khớp** gia sư; nhận xét ngắn, 1 chỗ bắt bẻ thừa (many/some), **không giải thích *chew*** dù Tân hỏi | Phán định **5/5 khớp**; nhận xét rõ, có tiếng Việt đúng chỗ, giải thích *chew* | Chấm vẫn do Opus (quy tắc) |
| Thời gian / token | 77 s · ~89k token | 60 s · ~79k token | Sonnet nhanh và gọn hơn ở việc viết |
| Chi phí ước tính (giá API) | ~1,5 cent | ~25 cent | Gói Max: trừ hạn mức, tỷ lệ tương tự |

**Kết luận:** Haiku = vẽ SVG + việc máy móc. Sonnet = nội dung cần đúng nghĩa khi giao ra ngoài (Opus xem lại). Opus = soạn bài, chấm, lên kế hoạch.

## Vẽ SVG: Haiku vs Sonnet (12/11/2026, cùng 8 hình, cùng đề)

| | Haiku | Sonnet |
|---|---|---|
| Thời gian | 102 s | 207 s |
| Token (cả phiên agent) | ~95k | ~99k |
| Chi phí ước tính (giá API) | ~1,4 cent (≈0,2 cent/hình) | ~27 cent (≈3,4 cent/hình) |
| Chất lượng (gia sư chấm từng cặp) | thắng 1/8 (*unless* tương phản ngày/đêm rõ hơn) | **thắng 6/8**, hoà 1 (*tram*): bố cục tự nhiên, nhiều chi tiết, đúng cảnh hơn (*overwhelmed*, *spread yourself too thin*, ảnh bìa Manchester, Mr Patel bê TV) |

Cả hai đều đúng nghĩa ở mức dùng được; *move the goalposts* cả hai còn yếu.

## Sonnet vs Opus cho việc của lớp (13/11/2026, cùng đề, chạy song song, gia sư chấm)

| Việc | Sonnet | Opus | Nhận xét |
|---|---|---|---|
| A · Chấm bài 06 (nghe, Tân hỏi về dẫn chuyện) | Đúng 2/2, đọc log đúng (dòng 1 nghe lại 12×), trả lời có cơ sở, giữ B1 đúng luật. Gợi ý *shadowing* (= nói, lệch quy tắc chỉ-input) | Như Sonnet + **tự tính tốc độ dẫn chuyện 180–197 wpm so với đọc 124** → lý giải sắc hơn; nhận lỗi thiết kế bài. Xưng "bạn" (lệch quy tắc mình–Tân) | Gần ngang; Opus sâu hơn một bậc |
| B · Soạn bài đọc Ep. 4 (B1+, 3 câu check) | 236 từ, tự nhiên, đúng mức, 3 câu đúng; 1 dòng chú giải lủng củng (*Give it a week*) | 269 từ, tự nhiên hơn, cụm in đậm trong bài, chú giải chuẩn, có tiếng Việt chỗ khó | Cả hai dùng được; Opus nhỉnh hơn chút |
| C · Lên lịch thứ Bảy (10 bài + lý do + lời nhắn) | Đủ luật, lý do bám dữ liệu; **1 lỗi đọc số liệu** (so 121 đọc lại với 124 bài mới → "chưa tiến bộ", thực ra +20%); không xét bài 13/11 còn dở | Đủ luật, **tự phát hiện bài 13/11 còn dở + xung đột Weekly Test với góp ý của Tân**, xử lý hợp lý | Opus rõ hơn ở phán đoán |
| Thời gian | 29–37 s / việc | 33–77 s / việc | Sonnet nhanh ~1,5–2× |
| Token | ~80k / việc | ~81–89k / việc | gần bằng |
| Chi phí (giá API) | ~1/5 Opus | 1× | theo bảng giá hiện hành |

**Kết luận:** Sonnet đủ tốt cho việc *viết nội dung theo khuôn* (truyện, câu hỏi, chú giải, chấm bài nhỏ chỉ có câu chọn). Opus vẫn cần cho việc *phán đoán thích ứng* (lên lịch ngày/tuần, quyết định nâng/hạ mức, trả lời góp ý của Tân, thư tuần) – nơi Sonnet hay sót bối cảnh/đọc sai số liệu.
