# SESSION HISTORY – Khởi tạo khoá học (11/11/2026)

Toàn bộ thông tin & quyết định khi thiết lập khoá học. Lớp học diễn ra trong **một phiên Claude Code duy nhất** gắn với repo này.

## 1. Yêu cầu ban đầu của Tân
- Cần một project học tiếng Anh hằng ngày, Claude là gia sư 1-1: kiểm tra mỗi ngày, đưa bài học.
- Trình độ B1, đọc ổn, có từ vựng nhưng không biết liên kết → biết nhiều mà vẫn khó hiểu.
- Tân, sinh 2001. Mục tiêu: nói chuyện được, đọc tài liệu và nghe hiểu phần lớn tiếng Anh.
- Lĩnh vực: Công nghệ / IT. Thời lượng: 45–60 phút/ngày.

## 2. Lịch sinh hoạt
- T2–T6 làm 8:30–19:30. Đi bộ 15' (8:30–8:45 hoặc 8:45–9:00) + đợi thang 15'. Ngủ ~23:15. Cuối tuần nghỉ.
- Đề xuất ngủ/dậy: ngủ 23:00–23:15, dậy ~7:00 (5 chu kỳ 90'). Ôn 2–3' trước ngủ. Cuối tuần dậy muộn tối đa ~1h (8:00). Không học bài chính sát giờ ngủ.

## 3. Lịch học
| Mốc | Nội dung |
|---|---|
| 08:15 T2–T6 | Walk Pack (nghe/nhẩm khi đi bộ) |
| 18:55 T2–T6 | Ra bài chính 45–60' (Tân làm lúc tiện) |
| 09:40 T7 | Weekly Test + Feedback tuần + Talk Time |
| 10:15 CN | Nhắc học + Sunday Input tuỳ chọn |

Lịch chạy bằng 4 Routine lặp cố định gửi về phiên chính (ID trong `tutor/02_PROGRESS_LOG.md`).

## 4. Các quyết định & thay đổi
1. Mọi bài học diễn ra trong **một phiên chính** (Claude Code, `session_01VzvjsE7Dz6m9heACFeiGmz`), không mở phiên mới mỗi lần. Lịch gửi bài là 4 Routine cron cố định về phiên này.
2. Định hướng: **Input trước (Reading + Listening thật kỹ, hiểu hết), Output sau** (Speaking + Writing ở Phase 2). Tutor tự nghiên cứu phương pháp, theo dõi tiến độ, bắt feedback, luyện nói cùng học viên, cuối tuần giục học.
3. (11/11) Đổi giờ bài tối 20:45 → 18:55 (ra bài trước, Tân tự chọn giờ làm). Làm **web lớp học** (artifact claude.ai): xem bài, nộp bài → gia sư tự chấm và lên bài tiếp.
4. (11/11 chiều) **Đổi trọng tâm:** Tân muốn học **tiếng Anh phổ thông chuẩn trước, IT là phụ**; chỉ khi đạt C1 mới học chuyên sâu IT. Phương pháp chính: **Comprehensible Input** (nạp nhiều input chuẩn, vừa đủ hiểu). Viết lại Tutor Guide v3 + Roadmap v3. Web có trình nghe (Claude đọc, chỉnh tốc độ, ẩn lời).
5. (11/11 tối) Tân: **hiện tại chỉ tập trung input**; lộ trình **không cứng nhắc**, gia sư tự đánh giá sau mỗi bài/feedback để ra bài tốt nhất (thích ứng). Roadmap v4 thành "la bàn"; thêm *Learner model* + nhật ký quyết định trong Progress Log. Thu âm/phát âm: có công cụ, chỉ dùng khi Tân muốn.
6. (11/11 tối) **1 job duy nhất 05:55 mỗi ngày** ra đủ bài của ngày (xoá job Walk Pack/Weekly/CN). Web có 3 tab: Bài học theo ngày · Hồ sơ học sinh · Tiến độ. **GitHub `data/` là nguồn dữ liệu duy nhất**; web chỉ hiển thị (publish kèm trang), DB chỉ nhận bài nộp; Progress Log tự sinh bằng `tools/sync.py`. Bỏ các thư mục trùng lặp lessons/, tests/, readings/, recordings/.
7. Repo GitHub là nơi lưu toàn bộ: CLAUDE.md, giáo án, bài đọc, audio, test, tiến độ. Claude có toàn quyền push thẳng `main`.

## 5. Phương pháp đã nghiên cứu (nguồn)
- Intensive + extensive reading: https://howwelearnlanguages.substack.com/p/reading-but-not-improving
- Extensive/intensive listening: https://benjamins.com/catalog/aila.22015.kar
- Vandergrift metacognitive listening: https://teslcanadajournal.ca/index.php/tesl/article/download/1134/953/1293
- Graham & Macaro (2008): https://gianfrancoconti.com/2025/04/25/the-impact-of-listening-strategy-instruction-on-lower-intermediate-students-in-graham-and-macaro-2008/
- Shadowing & dictation (JALT): https://jalt-publications.org/sites/default/files/pdf-article/36.1-art1.pdf
- Nguồn nghe: VOA Learning English – Technology Report; BBC Learning English – 6 Minute English; sau đó TED/TEDx tech talks.

## 6. Nơi lưu trữ
- Repo GitHub `tannc28/english-tutor` – nguồn duy nhất cho mọi tài liệu và tiến độ.
