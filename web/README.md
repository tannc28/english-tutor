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

## Schema (ghi bằng ArtifactData) – thiết kế để không phình khi có hàng trăm bài
Nguyên tắc: **không bao giờ list/query cả collection lớn** (`lessonBodies`, `submissions`, `grades`) vào context. Chỉ `get` đúng 1 doc theo id. Việc cần làm lấy từ `inbox` (nhỏ, chỉ chứa bài chưa chấm).

| Collection | Ai ghi | Nội dung | Kích thước |
|---|---|---|---|
| `lessons/<id>` | gia sư | metadata cho danh sách: `{id,date,type,title,minutes,status}` (status: open → submitted → graded) | ~200 B/bài |
| `lessonBodies/<id>` | gia sư | `{intro_md, parts:[...]}` – trang chỉ tải khi mở bài | vài KB/bài |
| `submissions/<id>` | trang | `{lessonId, answers:{qid:text}, feedback:{difficulty,hardest,minutes}, submittedAt, notify}` | |
| `inbox/<id>` | trang tạo, gia sư **xoá sau khi chấm** | `{lessonId, submittedAt}` = hàng đợi bài chưa chấm | rỗng khi đã chấm hết |
| `grades/<id>` | gia sư | `{score, summary_md, answers_md, next_md, gradedAt}` | |
| `keys/<id>` | gia sư | đáp án trắc nghiệm (trang không tải) | |
| `meta/progress` | gia sư | `{phase, week, streak, next, updatedAt}` | 1 doc |

- **id**: `YYYY-MM-DD-<walk|main|weekly|sunday>` (chữ, số, gạch ngang). Danh sách sắp theo `id` giảm dần.
- `parts[]`: `{kind, title, md, listen?:[{who, voice:"buttery|airy|glassy|rounded", text≤2000 ký tự}], rate?:0.8–1.1, questions:[{id, q, type:"text|short|choice|dictation", options?, placeholder?}]}`. Có `listen` thì trang hiện trình nghe (Claude đọc), lời ẩn tới khi bấm. Bài đọc để trong `>` blockquote, chunk dùng `<mark>`. Feedback bắt buộc do trang tự thêm.
- **Đăng bài** = 1 batch: `set lessons/<id>` (metadata) + `set lessonBodies/<id>` (nội dung).
- **Chấm bài** = `get submissions/<id>` + `get lessonBodies/<id>` → batch: `set grades/<id>`, `update lessons/<id> {status:"graded"}`, `delete inbox/<id>`, `update meta/progress`.
- **Tìm bài chưa chấm** = `list inbox` (chỉ vài doc nhỏ).
- Bài thử cũ (`*-test*`) để nội dung ngay trong `lessons/<id>`; trang vẫn đọc được (tương thích ngược).
