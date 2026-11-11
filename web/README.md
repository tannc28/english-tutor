# Web lớp học

Link: https://claude.ai/artifact/LX12NEhBjqgC3qv5bvqAC2 (riêng tư, chỉ Tân xem được)
Nguồn trang: `web/index.html`. Muốn cập nhật trang thì publish lại file này vào đúng URL trên.

## Luồng làm việc
1. Đến giờ, Routine gửi tin vào phiên chính → gia sư soạn bài, ghi vào DB (`lessons/<id>`) + lưu file `lessons/` trong repo.
2. Tân mở web, làm bài lúc nào tiện, bấm **Nộp bài** → trang lưu `submissions/<id>` rồi báo gia sư:
   - Cách chính: **Send to Claude** (comment ở đầu bài, nội dung `📥 Nộp bài <id> …`) → đánh thức phiên chính (phiên đang theo dõi artifact). **Đã kiểm chứng 11/11 (bài thử 4): tin đến phiên chính sau ~3 giây.** Gia sư chấm, ghi `grades/<id>`, rồi trả lời + resolve thread bằng ArtifactComments.
   - Dự phòng: `fire_trigger` của Routine "Tân nộp bài (web)" (`trig_01AN7RrytvZ5BmXiymy5Ym5M`). Lưu ý: lượt này chạy **ngoài** transcript phiên chính và không push repo → lần chạy lịch kế tiếp phải đồng bộ điểm từ `grades/` vào Progress Log.
   - Trang ghi kết quả báo vào `submissions/<id>.notify` (via, canSend, mã lỗi) để chẩn đoán.
3. Gia sư chấm → ghi `grades/<id>`, set `lessons/<id>.status="graded"`, cập nhật `meta/progress` + Progress Log, push `main`. Kết quả hiện ngay trên web.
4. Nếu trang không tự báo được (thiếu quyền connector), Tân nhắn "nộp bài <id>" trong phiên chat; gia sư đọc `submissions/<id>` bằng ArtifactData.

## Schema (ghi bằng ArtifactData)
- **id**: `YYYY-MM-DD-<walk|main|weekly|sunday>` (chỉ chữ, số, gạch ngang). Danh sách sắp xếp theo `id` giảm dần.
- `lessons/<id>`:
  ```json
  {"id":"2026-11-11-main","date":"2026-11-11","type":"main","title":"Day 1 – Đánh giá đầu vào",
   "minutes":50,"status":"open","intro_md":"...",
   "parts":[{"kind":"Reading","title":"...","md":"markdown (bài đọc để trong > blockquote; chunk dùng <mark>)",
             "questions":[{"id":"r1","q":"câu hỏi","type":"text|short|choice|dictation","options":["A","B"],"placeholder":"..."}]}]}
  ```
  Phần FEEDBACK bắt buộc (độ khó 1–5, chỗ khó nhất, số phút) do trang tự thêm, không cần ghi vào `parts`.
- `submissions/<id>`: `{lessonId, answers:{qid:text}, feedback:{difficulty, hardest, minutes}, submittedAt}` (trang ghi).
- `grades/<id>`: `{score:"Reading 7/10 · Listening 6/10 · Dictation 80%", summary_md, answers_md, next_md, gradedAt}`.
- `meta/progress`: `{phase:"1 · Input", week, streak, next, updatedAt}`.
