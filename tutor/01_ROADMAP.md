# ROADMAP (v4) – Định hướng mềm, thích ứng theo từng bài

> **12/11: Đơn vị kế hoạch là TUẦN** (chủ đề + ~6 bài, `data/weeks.json`). Vòng lặp thích ứng chạy ở 2 nhịp: sau mỗi bài (chỉnh bài chưa làm trong tuần) và cuối tuần (chọn chủ đề + mức cho tuần tới). Mức soạn bài = `profile.input_level` (mức thoải mái), không phải mức làm bài kiểm tra.

> Đây là **la bàn, không phải lịch trình.** Bài mỗi ngày được quyết định bởi **hồ sơ năng lực** (Learner model) trong `data/profile.json` (xem đẹp ở tab Hồ sơ trên web), tức là kết quả chấm gần nhất, feedback và sở thích của Tân. Không theo bảng tuần cố định.

## Đích đến
- Tiếng Anh **phổ thông** B1 → **C1**, theo **Comprehensible Input**.
- **Hiện tại: chỉ tập trung INPUT** (nghe + đọc thật nhiều, vừa đủ hiểu). Output, phát âm, thu âm: chỉ làm khi Tân muốn, hoặc khi hồ sơ cho thấy đã đến lúc (và hỏi Tân trước).
- IT chỉ là phụ. Chuyên sâu IT chỉ bắt đầu khi đạt C1.

## Vòng lặp thích ứng (sau MỖI bài được chấm)
1. **Đo:** điểm hiểu từng phần, % hiểu Tân tự báo, độ khó 1–5, chỗ khó nhất, thời gian thực tế, từ chưa hiểu.
2. **Cập nhật hồ sơ** (`data/profile.json`): mức đang vừa sức của từng kỹ năng, xu hướng, sở thích, điểm yếu, cái gì hiệu quả hay không.
3. **Quyết định bài kế tiếp:**
   - % hiểu bài rộng < ~90%, độ khó ≥ 4, hoặc quá giờ → **hạ mức / rút ngắn**.
   - % hiểu ≈ 100%, độ khó ≤ 2, Tân thấy chán → **nâng mức / dài hơn / nguồn thật hơn**.
   - Lỗi hiểu lặp lại (quy chiếu, từ nối, câu dài, âm nối…) → lồng thêm hỗ trợ đúng điểm đó vào input sau.
   - Chủ đề và nhân vật Tân thích → làm nhiều hơn (narrow input).
   - Feedback trực tiếp của Tân **luôn được ưu tiên** hơn kế hoạch cũ.
4. **Ghi lý do** chọn bài vào `profile.decisions` (1 dòng) để lần sau xem lại được.

## Mốc tham khảo (chỉ để định hướng, không bắt buộc)
| Giai đoạn | Dấu hiệu chuyển tiếp |
|---|---|
| Input B1 → B1+ | Đọc truyện graded B1 trôi (~98% từ quen); nghe hội thoại chậm hiểu ≥ 90% |
| Input B1+ → B2 | Đọc bài phổ thông thật (tin, blog đời sống) ≥ 90%; nghe podcast cho người học tốc độ tự nhiên |
| Thêm output dần | Khi Tân muốn, hoặc input B2 ổn định |
| B2 → C1 | Phim/podcast bản xứ, sách thật; thảo luận, viết |
| Chuyên sâu IT | Sau khi đạt C1 ổn định |

Đánh giá tổng quát lại khi có đủ dữ liệu (khoảng mỗi 3–4 tuần), không cần đúng lịch.

## Gợi ý chủ đề đời sống (chọn theo sở thích, không theo thứ tự)
Một ngày bình thường · gia đình, bạn bè, hàng xóm · ăn uống, nấu ăn · đi lại, du lịch · sức khoẻ, giấc ngủ · tiền bạc, mua sắm · phim, âm nhạc, thể thao · tâm lý, thói quen · tin tức đời sống · lịch sử, khoa học phổ thông. Xuyên suốt: truyện dài kỳ *Hope Street*.
