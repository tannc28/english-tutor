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
| `weeks.json` | **Kế hoạch theo tuần** `{weeks:[{no, start, end, status:"current|planned|done", theme, title, why_md, goals[], how_md, target_hours, cover, days:{"YYYY-MM-DD":{lessons:[id…] (≤2/ngày), listen?:<chỉ số trong listen>, note}}, words:[{w, img, def, ex, vi?, audio}], listen:[{title, source, minutes, level, apple?, youtube?, url?, transcript?, why}], review_md?}]}` – tuần hiện tại có đủ chi tiết; các tuần tới chỉ có chủ đề + mục tiêu |
| `lessons.json` | Danh sách bài `{lessons:[{id, week, order, kind:"Listening|Reading|Mixed|Review|Assessment", title, minutes, cover, status:"open|graded", date (ngày làm, ghi khi chấm), listenPct, readPct, difficulty, strain, minutesActual, extraMinutes, note}]}` – mỗi bài nộp riêng; chỉ số do gia sư ghi khi chấm |
| `profile.json` | Hồ sơ học sinh = Learner model: `cefr{overall,listening,reading,vocab,grammar}`, `levels{…}`, `strengths[]`, `weaknesses[]`, `interests[]`, `habits`, `teacher_md`, `focus_md`, `decisions[{date,text}]`, `story`, `chunk_bank[]`, `pronunciation[]`, `orientation[]`, `week`, `streak`, `coach{summary_md, weekly_target_hours, target_why, recommendations[{title,why,how}]}`; `weaknesses` là object `{area, detail, evidence, plan}` |
| `lessons/<id>.json` | Nội dung bài: `{intro_md, parts:[{kind, title, md, listen?:[{who, voice:"buttery|airy|glassy|rounded", text≤2000}], rate?:0.75–1.1, audio?:"data/audio/<id>/p<i>.mp3", learn?:true, practice?:true, questions:[{id, q, type:"text|short|choice|dictation|recording", options?, placeholder?, read?, check?:{answer, why}}]}]}` – `check` = câu luyện, trang chấm ngay (không tính điểm, không cần trong keys) |
| `grades/<id>.json` | `{score, summary_md, answers_md, next_md, gradedAt, items:{qid:{verdict:"correct|partial|wrong|unsure|skipped", note_md}}}` – `items` hiện dưới từng câu (bắt buộc, Tutor Guide 6e) |
| `submissions/<id>.json` | Bản chép bài làm của Tân (từ DB web; được publish để bài đã chấm luôn hiện câu trả lời), gồm `log` = nhật ký quá trình: `sessions[{s,e,at,kind,os,app,vw}]` (giây từ lúc mở bài; `at` giờ bắt đầu thật (UTC); `kind` computer/phone/tablet, `os`, `app` (đoán từ trình duyệt), `vw` bề rộng màn hình), `parts{pi:{ms}}` (thời gian tương tác mỗi phần), `q{qid:{first, ms, edits, changes[{t,from,to}]}}`, `listen{pi:{plays, rates[], revealAt, answeredBeforeReveal}}` |
| `keys/<id>.json` | Đáp án trắc nghiệm, **không** publish |
| `img/w<N>/…` | Minh hoạ (webp từ `tools/illustrate.py`, svg tự vẽ). Trong bài: `![alt](data/img/…)` trong md, `cover` cho thẻ bài |
| `audio/<id>/p<i>.mp3`, `audio/w<N>/words/*.mp3` | Audio bài nghe + word wall (`tools/audio.py`) |
| `resources.json` | Thư viện nghe tự do (tab 🎧 Listen): `{how_md, tiers:[{name, level, note, items:[{name, type, url, alt?, topics, why}]}]}` – chỉ link đã kiểm tra |

- **id**: `w<N>-l<số>` (3 bài đầu giữ id cũ). Web gom theo tuần, hiển thị "Week N · Lesson M". Khung bài: Learn → Try it → Input → Check (Tutor Guide mục 4).
- `listen` → trang hiện trình nghe (Claude đọc, chỉnh tốc độ, lời ẩn tới khi bấm). `recording` → nút thu âm (xem `tools/speech/README.md`). `choice` luôn có thêm, tách riêng dưới các đáp án, nút "🤔 Mình không chắc" + ô ghi chú (đáp án lưu dạng `"Unsure: <ghi chú>"`; bài cũ có thể là `"Khác: …"`) và nút Bỏ chọn. Feedback bắt buộc (độ khó, chỗ khó nhất, phút) do trang tự thêm.

## Web có gì
- **🗓 This week** (trang chủ): **📍 Today** (việc hôm nay theo giờ: bài sáng/tối + podcast; bài lỡ tự dời sang hôm nay, tối đa 2 bài/ngày, phần thừa ghi "no rush"), **dải 7 ngày** (✅ xong · ▶ hôm nay · ↪ lỡ), **Your journey** (mọi tuần, số bài đã xong, bấm để xem lại – không bao giờ xoá); chủ đề tuần + ảnh bìa, vì sao chủ đề này, mục tiêu can-do, tiến độ tuần, nút "Continue" (bài chưa làm kế tiếp), thẻ bài có hình (làm thứ tự tuỳ ý), word wall (chạm để lật: nghĩa + ví dụ + audio), bài nghe tự do cùng chủ đề, dải các tuần tới.
- **📚 Bài học**: danh sách gom theo tuần, vở làm bài, trình nghe MP3, nộp bài, kết quả chấm. Feedback có thêm **độ căng não** (😌 relaxed / 🙂 some / 😵 hard).
- **👤 Hồ sơ**: CEFR ước lượng từng kỹ năng, giáo viên nhận xét, điểm mạnh / cần cải thiện, sở thích, đang tập trung, nhật ký quyết định ("vì sao bài lại như vậy").
- **📈 Tiến độ** (bảng huấn luyện): bức tranh hiện tại, gia sư khuyên, giờ học mỗi tuần so với mục tiêu, đang yếu gì + kế hoạch, dự báo tới C1 (chọn giờ/tuần để xem thay đổi), làm được gì ở mỗi mức, biểu đồ mức hiểu, bảng đánh giá từng ngày.

## Quy trình LÊN KẾ HOẠCH TUẦN (job Chủ nhật 17:43) – suy nghĩ sâu, dùng Opus
1. `git pull`; đọc `CLAUDE.md`, file này, Tutor Guide, Roadmap, `profile.json` (input_level, weaknesses, decisions, chunk_bank), `weeks.json`, `lessons.json`, grades + submissions của tuần (nhất là phần "Look back" của bài ôn cuối tuần, cột strain).
2. `ArtifactData list inbox` → chấm bài tồn trước.
3. Đánh giá tuần: cập nhật `profile` (input_level lên/xuống, weaknesses, coach) + `weeks[tuần này].review_md`, status `done`.
4. Tuần tới (`status: current`): chọn/điều chỉnh chủ đề (theo feedback + sở thích; tiếng Anh phổ thông), viết why_md, goals, how_md, **~6 bài** (Learn → Try it → Input → Check, bài cuối = ôn tập + Look back), **lịch gợi ý từng ngày `days`** (ngày thường 1–2 bài theo khung 7:45/20:30, cuối tuần 1 bài 9:00 + podcast, có ngày nghỉ; khớp `profile.schedule`), truyện dài kỳ nối tiếp, word wall ~12 từ có hình, 6–8 bài nghe tự do cùng chủ đề (Apple Podcasts/YouTube, đã kiểm tra link). Bài tuần trước chưa làm vẫn để nguyên – không dồn, không áp lực; tuần mới có thể ít bài hơn. Thêm 1 tuần `planned` ở cuối để luôn thấy trước 3 tuần.
5. Minh hoạ: spec → `python3 tools/illustrate.py spec.json` (bìa tuần, bìa từng bài, cảnh truyện, word wall); bản đồ/sơ đồ → SVG tự vẽ. Audio: `python3 tools/audio.py <id>…` + `--words <N>`.
6. `python3 tools/sync.py` → commit + push `main` → `Artifact publish web/index.html` với `files` = `web/publish_files.json`.
7. Báo Tân 2–3 dòng + link + PushNotification.

## Job hằng ngày 05:55 – theo dõi nhẹ nhàng
1. `git pull`; `ArtifactData list inbox` → chấm bài tồn.
2. Xem `days`: Tân lỡ nhiều → dàn lại lịch các ngày còn lại (vẫn ≤2 bài/ngày, có thể bỏ bớt bài phụ). Điều chỉnh **bài chưa làm** của tuần theo feedback mới nhất (😵 → hạ độ khó/độ dài; 😌 + ≥90% liền → nâng nhẹ). Tân làm hết bài tuần → thêm 1–2 bài bonus cùng chủ đề.
3. Cập nhật lịch hôm nay: gợi ý bài kế tiếp (link `#<id>`) cho buổi sáng/tối.
4. Chỉ nhắc khi 2 ngày không học, giọng nhẹ nhàng – không thúc ép. Không có gì mới → không gửi thông báo.

## Lịch Google Calendar
- Connector Google Calendar (tài khoản của Tân). Connector **không tạo được calendar mới** → dùng lịch **Personal** (`calendarId` = email chính), sự kiện tên bắt đầu **"📚 English · "**, `colorId: "9"`. Nếu Tân tự tạo lịch "English", chuyển sang dùng `calendarId` của lịch đó (`list_calendars`).
- Các buổi học là **chuỗi sự kiện lặp lại** (id trong `profile.schedule.calendar.recurring`). **Không tạo sự kiện mới mỗi ngày.**
- **Khi RA BÀI:** cập nhật **phiên bản của hôm nay** trong chuỗi (`list_events` hôm nay, lọc "📚 English" → `update_event` đúng id của phiên bản đó): tên = `📚 English · W<N> – <bài gợi ý>`, mô tả HTML: chủ đề tuần + bài gợi ý + phút + link `#<id>`.
- **Khi CHẤM xong:** cập nhật phiên bản buổi tối (cuối tuần: buổi bài 9:00) của ngày đó: thêm "✅" vào tên, mô tả = kết quả ngắn + điểm cần ôn + giờ học thực (từ log).
- Dùng `notificationLevel: "NONE"`; nhắc 10 phút trước cho buổi sắp tới (`overrideReminders` popup 10).

## Quy trình CHẤM (khi có comment "📥 Nộp bài <id>" hoặc job dự phòng)
1. `git pull`. Nếu `data/grades/<id>.json` đã có → không chấm lại.
2. `ArtifactData get submissions/<id>` (+ `data/lessons/<id>.json`, `data/keys/<id>.json`). Có câu `recording` → lấy asset, chấm phát âm (`tools/speech/README.md`), xong xoá asset.
3. Chấm theo Tutor Guide; đọc thêm `log` để phân tích quá trình (Tutor Guide 6d). Ghi `data/submissions/<id>.json` (bản chép), `data/grades/<id>.json`; cập nhật `data/lessons.json` (status `graded`, `date` = ngày nộp, `listenPct`, `readPct`, `difficulty`, `strain` = feedback.strain, `minutesActual`, `extraMinutes` = feedback.extra, `note` ngắn) và `data/profile.json` (cefr/levels, strengths, weaknesses, interests, teacher_md, focus_md, decisions, chunk_bank, streak, updatedAt, **coach**, weaknesses có bằng chứng – xem Tutor Guide 6c).
4. `python3 tools/sync.py` → commit + push → publish (như trên) → `ArtifactData delete inbox/<id>`.
5. Trả lời trong thread comment + resolve (nếu đến qua comment), hoặc 1–2 dòng trong chat.

## Báo bài nộp về gia sư
- Chính: trang gửi comment **Send to Claude** "📥 Nộp bài <id>" → đánh thức phiên chính (đã kiểm chứng ~3 giây).
- Dự phòng (sau 8 giây không gửi được): `fire_trigger` Routine `trig_01AN7RrytvZ5BmXiymy5Ym5M`.
- Trang ghi kết quả báo vào `submissions/<id>.notify` để chẩn đoán.

## Quyền của trang
`db` (`submissions`, `inbox`, `drafts`), `comments` (Send to Claude), `mcp` → Claude Code Remote `fire_trigger`, `assets` (bản thu âm base64), `tts` (đọc bài nghe), `user`.
