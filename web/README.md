# Web lớp học + quy trình dữ liệu

Link: https://claude.ai/artifact/LX12NEhBjqgC3qv5bvqAC2 (riêng tư, chỉ Tân mở được)

## Nguyên tắc: GitHub là nguồn dữ liệu DUY NHẤT
- Mọi thứ gia sư viết (bài, điểm, hồ sơ, tiến độ) nằm trong **`data/`** của repo, dạng JSON.
- Web **chỉ hiển thị**: `web/index.html` được publish kèm các file `data/*.json` (đọc bằng `fetch` tương đối).
- `tutor/02_PROGRESS_LOG.md` được **sinh tự động** từ `data/` bằng `python3 tools/sync.py`. Không sửa tay.
- Database của artifact **chỉ giữ dữ liệu Tân nhập**: bài nộp (`submissions/<id>`, `inbox/<id>`) và **nháp đang làm** (`drafts/<id>`, chỉ chủ sở hữu đọc/ghi; trang tự lưu 2 giây sau khi ngừng gõ + nút 💾 Lưu; bản trên máy luôn lưu tức thì; mở bài lấy bản mới hơn giữa máy và mây; xoá khi nộp). Khi chấm, bài nộp được chép vào `data/submissions/`.
→ Sửa một chỗ (JSON trong `data/`), chạy `sync.py`, push, publish. Không có hai bản để lệch nhau.

## Cấu trúc `data/`
| File | Nội dung |
|---|---|
| `days.json` | `{days:[{id, date, dayNo, type:"day", title, minutes, status:"open|graded", listenPct, readPct, difficulty, minutesActual, extraMinutes, note}]}`. Một entry mỗi ngày học; chỉ số do gia sư đánh giá khi chấm |
| `profile.json` | Hồ sơ học sinh = Learner model: `cefr{overall,listening,reading,vocab,grammar}`, `levels{…}`, `strengths[]`, `weaknesses[]`, `interests[]`, `habits`, `teacher_md`, `focus_md`, `decisions[{date,text}]`, `story`, `chunk_bank[]`, `pronunciation[]`, `orientation[]`, `week`, `streak`, `coach{summary_md, weekly_target_hours, target_why, recommendations[{title,why,how}]}`; `weaknesses` là object `{area, detail, evidence, plan}` |
| `lessons/<id>.json` | Nội dung bài: `{intro_md, parts:[{kind, title, md, listen?:[{who, voice:"buttery|airy|glassy|rounded", text≤2000}], rate?:0.75–1.1, audio?:"data/audio/<id>/p<i>.mp3", questions:[{id, q, type:"text|short|choice|dictation|recording", options?, placeholder?, read?}]}]}` |
| `grades/<id>.json` | `{score, summary_md, answers_md, next_md, gradedAt, items:{qid:{verdict:"correct|partial|wrong|unsure|skipped", note_md}}}` – `items` hiện dưới từng câu (bắt buộc, Tutor Guide 6e) |
| `submissions/<id>.json` | Bản chép bài làm của Tân (từ DB web; được publish để bài đã chấm luôn hiện câu trả lời), gồm `log` = nhật ký quá trình: `sessions[{s,e,at,kind,os,app,vw}]` (giây từ lúc mở bài; `at` giờ bắt đầu thật (UTC); `kind` computer/phone/tablet, `os`, `app` (đoán từ trình duyệt), `vw` bề rộng màn hình), `parts{pi:{ms}}` (thời gian tương tác mỗi phần), `q{qid:{first, ms, edits, changes[{t,from,to}]}}`, `listen{pi:{plays, rates[], revealAt, answeredBeforeReveal}}` |
| `keys/<id>.json` | Đáp án trắc nghiệm, **không** publish |
| `plan.json` | Bài nghe gia sư chọn theo ngày (tab 📅 Plan): `{days:{"YYYY-MM-DD":{note, listen:[{slot:"walk|morning|evening|weekend|any", time, title, source, minutes, level, apple?, youtube?, url?, transcript?, why}]}}}` – job 05:55 thêm ngày hôm nay |
| `resources.json` | Thư viện nghe tự do (tab 🎧 Listen): `{how_md, tiers:[{name, level, note, items:[{name, type, url, alt?, topics, why}]}]}` – chỉ link đã kiểm tra |

- **id**: `YYYY-MM-DD-day` (Day 1 giữ id cũ `2026-11-11-main`). Danh sách trên web sắp theo id giảm dần, hiển thị "Ngày N".
- `listen` → trang hiện trình nghe (Claude đọc, chỉnh tốc độ, lời ẩn tới khi bấm). `recording` → nút thu âm (xem `tools/speech/README.md`). `choice` luôn có thêm, tách riêng dưới các đáp án, nút "🤔 Mình không chắc" + ô ghi chú (đáp án lưu dạng `"Unsure: <ghi chú>"`; bài cũ có thể là `"Khác: …"`) và nút Bỏ chọn. Feedback bắt buộc (độ khó, chỗ khó nhất, phút) do trang tự thêm.

## Web có gì
- **📚 Bài học**: danh sách theo ngày ("Ngày N"), vở làm bài, trình nghe, thu âm, nộp bài, kết quả chấm.
- **👤 Hồ sơ**: CEFR ước lượng từng kỹ năng, giáo viên nhận xét, điểm mạnh / cần cải thiện, sở thích, đang tập trung, nhật ký quyết định ("vì sao bài lại như vậy").
- **📈 Tiến độ** (bảng huấn luyện): bức tranh hiện tại, gia sư khuyên, giờ học mỗi tuần so với mục tiêu, đang yếu gì + kế hoạch, dự báo tới C1 (chọn giờ/tuần để xem thay đổi), làm được gì ở mỗi mức, biểu đồ mức hiểu, bảng đánh giá từng ngày.

## Quy trình RA BÀI (job 05:55 mỗi ngày)
1. `git pull`; đọc `CLAUDE.md`, file này, `tutor/00_TUTOR_GUIDE.md`, `tutor/01_ROADMAP.md`, `data/profile.json`, `data/days.json`.
2. `ArtifactData list inbox` → nếu có bài chưa chấm: làm **Quy trình CHẤM** trước.
3. Bài ngày gần nhất còn `status:"open"` (Tân chưa nộp) → **không ra bài mới** (không dồn bài), chỉ nhắc nhẹ.
4. Quyết định bài hôm nay từ hồ sơ (vòng lặp thích ứng, `tutor/01_ROADMAP.md`). Ghi `data/lessons/<id>.json`, thêm entry vào `data/days.json`, thêm 1 dòng `profile.decisions`.
4b. **Audio MP3 cho phần nghe (bắt buộc – app Claude trên iPhone không phát được giọng `tts`):** `bash tools/audio_setup.sh` (container mới) → `python3 tools/audio.py <id>` → sinh `data/audio/<id>/p<i>.mp3` (Piper TTS, giọng Anh nam/nữ + Mỹ) và ghi `part.audio`. Trang ưu tiên MP3 (tua, chỉnh tốc độ), không có mới dùng `tts`.
5. `python3 tools/sync.py` → commit + push `main` → `Artifact publish web/index.html` với `files` = nội dung `web/publish_files.json`.
6. Báo Tân 2–3 dòng + link + PushNotification.

## Lịch Google Calendar
- Connector Google Calendar (tài khoản của Tân). Connector **không tạo được calendar mới** → dùng lịch **Personal** (`calendarId` = email chính), sự kiện tên bắt đầu **"📚 English · "**, `colorId: "9"`. Nếu Tân tự tạo lịch "English", chuyển sang dùng `calendarId` của lịch đó (`list_calendars`).
- Các buổi học là **chuỗi sự kiện lặp lại** (id trong `profile.schedule.calendar.recurring`). **Không tạo sự kiện mới mỗi ngày.**
- **Khi RA BÀI:** cập nhật **phiên bản của hôm nay** trong chuỗi (`list_events` hôm nay, lọc "📚 English" → `update_event` đúng id của phiên bản đó): tên = `📚 English · Day N – <tên bài> (sáng/tối)`, mô tả HTML: phần cần làm ở buổi đó + số phút + mục tiêu + link web.
- **Khi CHẤM xong:** cập nhật phiên bản buổi tối (cuối tuần: buổi bài 9:00) của ngày đó: thêm "✅" vào tên, mô tả = kết quả ngắn + điểm cần ôn + giờ học thực (từ log).
- Dùng `notificationLevel: "NONE"`; nhắc 10 phút trước cho buổi sắp tới (`overrideReminders` popup 10).

## Quy trình CHẤM (khi có comment "📥 Nộp bài <id>" hoặc job dự phòng)
1. `git pull`. Nếu `data/grades/<id>.json` đã có → không chấm lại.
2. `ArtifactData get submissions/<id>` (+ `data/lessons/<id>.json`, `data/keys/<id>.json`). Có câu `recording` → lấy asset, chấm phát âm (`tools/speech/README.md`), xong xoá asset.
3. Chấm theo Tutor Guide; đọc thêm `log` để phân tích quá trình (Tutor Guide 6d). Ghi `data/submissions/<id>.json` (bản chép), `data/grades/<id>.json`; cập nhật `data/days.json` (status `graded`, `listenPct`, `readPct`, `difficulty`, `minutesActual`, `extraMinutes` = feedback.extra, `note` ngắn) và `data/profile.json` (cefr/levels, strengths, weaknesses, interests, teacher_md, focus_md, decisions, chunk_bank, streak, updatedAt, **coach**, weaknesses có bằng chứng – xem Tutor Guide 6c).
4. `python3 tools/sync.py` → commit + push → publish (như trên) → `ArtifactData delete inbox/<id>`.
5. Trả lời trong thread comment + resolve (nếu đến qua comment), hoặc 1–2 dòng trong chat.

## Báo bài nộp về gia sư
- Chính: trang gửi comment **Send to Claude** "📥 Nộp bài <id>" → đánh thức phiên chính (đã kiểm chứng ~3 giây).
- Dự phòng (sau 8 giây không gửi được): `fire_trigger` Routine `trig_01AN7RrytvZ5BmXiymy5Ym5M`.
- Trang ghi kết quả báo vào `submissions/<id>.notify` để chẩn đoán.

## Quyền của trang
`db` (`submissions`, `inbox`, `drafts`), `comments` (Send to Claude), `mcp` → Claude Code Remote `fire_trigger`, `assets` (bản thu âm base64), `tts` (đọc bài nghe), `user`.
