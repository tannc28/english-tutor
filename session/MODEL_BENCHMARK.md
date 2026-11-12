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
