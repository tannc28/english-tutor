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
| `levels.json` | **Checklist trình độ** A2 / B1 / B2 / C1: mỗi level có `summary_md, hours, proof[]` (cách biết đã đạt), `vocab` (danh sách từ), `sections` (listening, reading, grammar, linking, later) → `items[{id, text, ex?, later?}]`. Nguồn: CEFR Companion Volume, Core Inventory, CEFR-J |
| `mastery.json` | Gia sư đánh giá từng item: `items{id:{tutor:"got_it|learning|not_yet", evidence, date}}`, `vocab.estimate_md`. **Cập nhật mỗi lần chấm** (có bằng chứng từ bài) |
| `library.json` | **Tự sinh** bởi `sync.py`: `words` (word wall mọi tuần + chunk_bank), `learn` (phần ① Learn của mọi bài → link `#<id>/p<i>`), `story` (các tập Hope Street), `mistakes` (`grades[].cards`) – nguồn của tab 🧠 Review |
| `review.json` | Hàng ôn quiz Telegram (từ `grades[].quiz`): `items[{id, lesson, q, options, answer, why, due, step, history[{date, ok}], poll_id?}]` – do `tools/tg.py` quản lý |
| `vocab/<A1…C1>.json`, `vocab/pseudo.json` | Danh sách từ theo level (CEFR-J Wordlist 1.5 + Octanove C1) và từ giả cho bài kiểm tra từ vựng yes/no |
| `img/w<N>/…` | Minh hoạ (webp từ `tools/illustrate.py`, svg tự vẽ). Trong bài: `![alt](data/img/…)` trong md, `cover` cho thẻ bài |
| `audio/<id>/p<i>.mp3`, `audio/w<N>/words/*.mp3` | Audio bài nghe + word wall (`tools/audio.py`) |
| `resources.json` | Thư viện nghe tự do (tab 🎧 Listen): `{how_md, tiers:[{name, level, note, items:[{name, type, url, alt?, topics, why}]}]}` – chỉ link đã kiểm tra |

- **id**: `w<N>-l<số>` (3 bài đầu giữ id cũ). Web gom theo tuần, hiển thị "Week N · Lesson M". Khung bài: Learn → Try it → Input → Check (Tutor Guide mục 4).
- `listen` → trang hiện trình nghe (Claude đọc, chỉnh tốc độ, lời ẩn tới khi bấm). `recording` → nút thu âm (xem `tools/speech/README.md`). `choice` luôn có thêm, tách riêng dưới các đáp án, nút "🤔 Mình không chắc" + ô ghi chú (đáp án lưu dạng `"Unsure: <ghi chú>"`; bài cũ có thể là `"Khác: …"`) và nút Bỏ chọn. Feedback bắt buộc (độ khó, chỗ khó nhất, phút) do trang tự thêm.

## Web có gì
**Điều hướng: 3 tab chính + tab con** – 📅 Learn (🗓 This week · 📚 Lessons · 🎧 Listening library) · 🧠 Review · 📈 Progress (🎯 Levels · 📊 Stats · 👤 Profile). Hash cũ vẫn chạy (`#`, `#bai`, `#nghe`, `#on-tap`, `#level`, `#tien-do`, `#ho-so`, `#<lessonId>/p<i>`).

**Điện thoại (≤640px, thiết kế lại 12/11 vì Tân thấy bí):** đầu trang 1 dòng (số liệu & lộ trình ở tab Progress); **thanh tab chính ở đáy** (tầm ngón cái); làm bài = **toàn màn hình** với 1 thanh mỏng (← · Parts · tiến độ · 💾 · 📤), mục lục chuyển vào bảng trượt "Parts"; nội dung tràn hết bề ngang, bỏ khung lồng khung; câu hỏi không đóng hộp, đáp án là hàng ≥50px; chữ 16.5px, ô nhập 16px (iOS không tự phóng to).

**Làm bài (đọc/nghe + câu hỏi):** phần có bài dài (>600 ký tự) hoặc có audio và ≥2 câu hỏi được chia `.split`: máy tính ≥1100px → 2 cột, bài **ghim bên trái** (cuộn riêng), câu hỏi bên phải; điện thoại → nút nổi **📖 Text** (hiện khi bài đã cuộn khỏi màn hình) mở **bảng trượt** 62% màn hình với bài đọc; phần nghe → **trình phát gọn 1 dòng ghim** trên đầu khi cuộn câu hỏi. Danh sách bài bên trái mặc định thu gọn (☰ để mở).

- **🗓 This week** (trang chủ): **thời khoá biểu theo ngày** – dải 7 ngày (bấm 1 ngày để xem kế hoạch ngày đó), **📍 Today** (việc hôm nay theo giờ: bài sáng/tối + podcast; bài lỡ tự dời sang hôm nay, tối đa 2 bài/ngày, phần thừa ghi "no rush"), **dải 7 ngày** (✅ xong · ▶ hôm nay · ↪ lỡ), **Your journey** (mọi tuần, số bài đã xong, bấm để xem lại – không bao giờ xoá); chủ đề tuần + ảnh bìa, vì sao chủ đề này, mục tiêu can-do, tiến độ tuần, nút "Continue" (bài chưa làm kế tiếp), thẻ bài có hình (làm thứ tự tuỳ ý), word wall (chạm để lật: nghĩa + ví dụ + audio), bài nghe tự do cùng chủ đề, dải các tuần tới.
- **📚 Bài học**: danh sách gom theo tuần → ngày ("Thu, 12/11 · Morning"), vở làm bài, trình nghe MP3, nộp bài, kết quả chấm. Feedback có thêm **độ căng não** (😌 relaxed / 🙂 some / 😵 hard).
- **👤 Hồ sơ**: CEFR ước lượng từng kỹ năng, giáo viên nhận xét, điểm mạnh / cần cải thiện, sở thích, đang tập trung, nhật ký quyết định ("vì sao bài lại như vậy").
- **📈 Tiến độ** (bảng huấn luyện): bức tranh hiện tại, gia sư khuyên, giờ học mỗi tuần so với mục tiêu, đang yếu gì + kế hoạch, dự báo tới C1 (chọn giờ/tuần để xem thay đổi), làm được gì ở mỗi mức, biểu đồ mức hiểu, bảng đánh giá từng ngày.

## Quy trình LÊN KẾ HOẠCH TUẦN (job Chủ nhật 17:43) – suy nghĩ sâu, dùng Opus
1. `git pull`; đọc `CLAUDE.md`, file này, Tutor Guide, Roadmap, `profile.json` (input_level, weaknesses, decisions, chunk_bank), `weeks.json`, `lessons.json`, grades + submissions của tuần (nhất là phần "Look back" của bài ôn cuối tuần, cột strain).
2. `ArtifactData list inbox` → chấm bài tồn trước.
3. Đánh giá tuần: cập nhật `profile` (input_level lên/xuống, weaknesses, coach) + `weeks[tuần này].review_md`, status `done`.
4. Tuần tới (`status: current`): chọn/điều chỉnh chủ đề (theo feedback + sở thích; tiếng Anh phổ thông), viết why_md, goals, how_md, **~6 bài** (Learn → Try it → Input → Check, bài cuối = ôn tập + Look back), **lịch gợi ý từng ngày `days`** (ngày thường 1–2 bài theo khung 7:45/20:30, cuối tuần 1 bài 9:00 + podcast, có ngày nghỉ; khớp `profile.schedule`), truyện dài kỳ nối tiếp, word wall ~12 từ có hình, 6–8 bài nghe tự do cùng chủ đề (Apple Podcasts/YouTube, đã kiểm tra link). Bài tuần trước chưa làm vẫn để nguyên – không dồn, không áp lực; tuần mới có thể ít bài hơn. Thêm 1 tuần `planned` ở cuối để luôn thấy trước 3 tuần.
5. Minh hoạ: spec → `python3 tools/illustrate.py spec.json` (bìa tuần, bìa từng bài, cảnh truyện, word wall); bản đồ/sơ đồ → SVG tự vẽ. Audio: `python3 tools/audio.py <id>…` + `--words <N>`.
6. `python3 tools/sync.py` → commit + push `main` → `Artifact publish web/index.html` với `files` = `web/publish_files.json`.
7. Telegram: `weeks[N].next_focus` (1 câu) → `python3 tools/tg.py weekly <N>` (ảnh báo cáo tuần vừa xong) → `tools/notify.py`: chủ đề tuần mới + lịch Thứ 2 + link.

## Job hằng ngày 05:55 – theo dõi nhẹ nhàng
1. `git pull`; `ArtifactData list inbox` → chấm bài tồn.
2. Xem `days`: Tân lỡ nhiều → dàn lại lịch các ngày còn lại (vẫn ≤2 bài/ngày, có thể bỏ bớt bài phụ). Điều chỉnh **bài chưa làm** của tuần theo feedback mới nhất (😵 → hạ độ khó/độ dài; 😌 + ≥90% liền → nâng nhẹ). Tân làm hết bài tuần → thêm 1–2 bài bonus cùng chủ đề.
3. Cập nhật lịch hôm nay: gợi ý bài kế tiếp (link `#<id>`) cho buổi sáng/tối.
4. `python3 tools/tg.py quiz` – gửi quiz ôn đến hạn (ôn lại sau 1 → 3 → 7 ngày; sai thì làm lại từ đầu) và ghi kết quả quiz Tân đã làm vào `review.json` (lỗi vẫn sai sau 2 lần → thêm vào weaknesses + bài tuần tới). Đọc tin Tân nhắn bot (`tools/notify.py --inbox`) → xử lý. Thông báo qua **Telegram**: khi có chấm/đổi lịch; nhắc nhẹ khi 2 ngày không học (không thúc ép). Không có gì mới → không gửi.

## Lịch Google Calendar
- Connector Google Calendar (tài khoản của Tân). Connector **không tạo được calendar mới** → dùng lịch **Personal** (`calendarId` = email chính), sự kiện tên bắt đầu **"📚 English · "**, `colorId: "9"`. Nếu Tân tự tạo lịch "English", chuyển sang dùng `calendarId` của lịch đó (`list_calendars`).
- Các buổi học là **chuỗi sự kiện lặp lại** (id trong `profile.schedule.calendar.recurring`). **Không tạo sự kiện mới mỗi ngày.**
- **Khi RA BÀI:** cập nhật **phiên bản của hôm nay** trong chuỗi (`list_events` hôm nay, lọc "📚 English" → `update_event` đúng id của phiên bản đó): tên = `📚 English · W<N> – <bài gợi ý>`, mô tả HTML: chủ đề tuần + bài gợi ý + phút + link `#<id>`.
- **Khi CHẤM xong:** cập nhật phiên bản buổi tối (cuối tuần: buổi bài 9:00) của ngày đó: thêm "✅" vào tên, mô tả = kết quả ngắn + điểm cần ôn + giờ học thực (từ log).
- Dùng `notificationLevel: "NONE"`; nhắc 10 phút trước cho buổi sắp tới (`overrideReminders` popup 10).

## Quy trình CHẤM (khi có comment "📥 Nộp bài <id>" hoặc job dự phòng)
1. `git pull`. Nếu `data/grades/<id>.json` đã có → không chấm lại.
2. `ArtifactData get submissions/<id>` (+ `data/lessons/<id>.json`, `data/keys/<id>.json`). Có câu `recording` → lấy asset, chấm phát âm (`tools/speech/README.md`), xong xoá asset.
3. Chấm theo Tutor Guide; đọc thêm `log` để phân tích quá trình (Tutor Guide 6d). Ghi `data/submissions/<id>.json` (bản chép), `data/grades/<id>.json`; cập nhật `data/lessons.json` (status `graded`, `date` = ngày nộp, `listenPct`, `readPct`, `difficulty`, `strain` = feedback.strain, `minutesActual`, `extraMinutes` = feedback.extra, `note` ngắn) **`data/mastery.json`** (item checklist nào bài này cho bằng chứng → got_it/learning/not_yet + evidence; đọc thêm `drafts/selfcheck`) và `data/profile.json` (cefr/levels, strengths, weaknesses, interests, teacher_md, focus_md, decisions, chunk_bank, streak, updatedAt, **coach**, weaknesses có bằng chứng – xem Tutor Guide 6c).
4. `python3 tools/sync.py` → commit + push → publish (như trên) → `ArtifactData delete inbox/<id>`.
5. Trả lời trong thread comment + resolve (nếu đến qua comment), hoặc 1–2 dòng trong chat. **Telegram** (Tân chọn 12/11): ghi vào `grades/<id>.json` thêm `tg {score, win, fix}` (mỗi dòng ≤ 90 ký tự), `cards` (≤3 lỗi quan trọng nhất: q, yours, right, tip – ❌→✅→💡) và `quiz` (2–3 câu trắc nghiệm ôn đúng chỗ sai: q, options, answer, why) → `python3 tools/tg.py graded <id>` = tin 4 dòng + ảnh thẻ lỗi + đưa quiz vào hàng ôn `data/review.json`. Không gửi ảnh chụp dài, không viết lại nhận xét dài.

## Bài nghe VOA (tab con 🎧 Listening) – thay cho "nghe tự do" (Tân 12/11)
- Tân muốn **chỉ học trên web, không link sang trang khác**, và muốn nghe cũng được dẫn dắt + theo dõi. Nguồn: **VOA Learning English** (public domain, ~95–125 từ/phút, có lời). Chỉ lấy bài **VOA tự viết** (American Stories, Words and Their Stories, Ask a Teacher, Everyday Grammar…); `tools/voa.py` tự bỏ bài có AP/Reuters/AFP.
- `python3 tools/voa.py list <zone>` → chọn bài hợp chủ đề tuần + mức thoải mái → `python3 tools/voa.py get <url> voa-<tên>` (MP3 → `data/audio/voa/`, lời + từ vựng → `data/sources/voa/`).
- Soạn bài `w<N>-voa-<k>` (kind `Listening`, `extra: true`, ~15'): ① Before you listen (cụm từ + IPA + dự đoán) → ② Listen (part có `audio` = MP3 VOA, `keep_audio: true`, `listen` = các đoạn lời để hiện transcript) với 4–6 câu hỏi + % hiểu + từ còn khó. Đáp án vào `keys/`. Ghi `credit` (chữ, **không link**).
- Lịch: `weeks[].days[ngày].extra = "<id>"` → hiện ở Today (21:40 / 14:30) và dải 7 ngày (🎧). Chấm như bài thường. Không dùng link podcast bên ngoài nữa.

## Minh hoạ – FLUX là chính, SVG dự phòng (Tân chọn 12/11)
- **Chính: FLUX.1 Schnell qua AI Horde** – `python3 tools/flux.py "<cảnh>" data/img/wN/<tên>.webp -n 2 --cast nam,linh` (hoặc `--batch jobs.json`). Miễn phí, không key; ~1–4 phút/ảnh (hàng đợi) → chạy nền, nhiều ảnh cùng lúc. Dùng cho: ảnh bìa tuần, ảnh bìa bài, cảnh truyện, **thẻ từ cụ thể** (đồ vật, hành động, nơi chốn, tình huống).
  - Prompt = STYLE chung (flat, children's book, không chữ) + mô tả nhân vật cố định `data/flux_cast.json` + cảnh **theo câu ví dụ** (ai, làm gì, cầm gì, đặt ở đâu – viết rõ tay cầm, đồ đặt trên bàn). Không đưa thông tin cá nhân của Tân vào prompt.
  - `-n 2..3` → **Opus xem từng ảnh** (Read), chọn bản đúng nghĩa + tự nhiên nhất (tay cầm đúng, đồ không lơ lửng, không chữ lỗi) → đổi thành `<tên>.webp`, xoá `.vN`. Không bản nào đạt → vẽ lại 1 lần với prompt rõ hơn → vẫn sai → dự phòng.
- **Dự phòng SVG** (Horde lỗi/hết giờ, exit code 2, hoặc từ **trừu tượng** khó vẽ cảnh: *although, unless, however…* → sơ đồ/2 khung): **Sonnet** (subagent `model: "sonnet"`) cho bìa/cảnh truyện + từ trừu tượng; **Haiku** (`model: "haiku"`) cho thẻ từ đơn giản. SVG viewBox 384×288, flat pastel, cùng dàn nhân vật, không chữ, <12 KB; subagent **phải render PNG và tự xem lại, sửa ≤3 vòng** (tay cầm đúng, đồ đặt đúng mặt phẳng).
- Sau cùng: dựng ảnh tổng hợp kiểm tra bằng mắt trước khi publish. `img` trong `words.json`/`weeks.json`/`lessons.json` trỏ `.webp` hoặc `.svg` đều được.
- Không dùng: emoji ghép hình, ghép mảnh Open Peeps (Tân thấy chắp vá), Pollinations ẩn danh (kém), Gemini ảnh (free tier = 0), Figma generate_image (tốn credit – chỉ khi Tân đồng ý). `tools/illustrate.py` (SDXL CPU) chỉ khi mọi thứ khác hỏng.

## Tab 🧠 Review (ôn tập & tra cứu)
- Ô tìm kiếm chung; mục **Words & chunks** (thẻ có hình, chạm để xem nghĩa + nghe), **Grammar & skills** (mở thẳng phần Learn), **My mistakes** (❌→✅→💡), **Story** (đọc lại các tập), **What's next** (tuần tới, mục checklist còn lại, từ chưa biết trong word check).
- **🃏 Practise**: thẻ lật (hình → đoán → lật xem nghĩa + nghe) → *Again* / *Got it*; ôn lại sau 1 → 3 → 7 → 14 → 30 ngày. Lưu ở `drafts/selfcheck.srs` (gia sư đọc khi lên kế hoạch tuần: từ hay "Again" → đưa vào bài).
- Link sâu tới 1 phần bài: `#<lessonId>/p<số phần>`.
- Telegram mỗi sáng: `tools/tg.py words` gửi ≤4 thẻ từ có hình + 1 file audio (lịch riêng trong `review.json.words`).

## Checklist trình độ (tab 🎯 Levels)
- Mỗi level hiện % item ✅, số 🌱/⬜/chưa kiểm tra, "how we'll know you're there", ô từ vựng (bài **word check** 40 từ = 36 từ thật ngẫu nhiên + 4 từ giả, điểm đã trừ đoán bừa; hoặc duyệt toàn bộ danh sách).
- Tân tự đánh giá từng item + kết quả word check → DB `drafts/selfcheck` (chỉ chủ sở hữu). **Khi chấm / job tuần:** đọc `drafts/selfcheck`, so với bằng chứng từ bài → cập nhật `mastery.json` (ghi evidence ngắn, tiếng Anh). Tân tự chấm cao hơn gia sư → thêm item đó vào bài tuần tới để kiểm chứng.
- `weeks[].targets` = các item tuần đó đẩy lên; hiện ở trang tuần. Job tuần chọn targets từ các item 🌱/⬜ của level đang học.

## Quy trình XIN NGHỈ (Tân bấm "🙋 Can't study…" ở một ngày)
- Trang ghi `inbox/leave-<YYYY-MM-DD>` `{type:"leave", date, kind:"off|morning|evening|short", note}` + gửi comment "🙋 Day-off request …" (dự phòng: fire_trigger).
- Gia sư: sửa `weeks[].days` – ngày đó `off: "<lý do ngắn, tiếng Anh>"` (nghỉ cả ngày) hoặc bớt bài/rút ngắn; **dời bài sang ngày nhẹ sau đó** (≤2 bài/ngày, cuối tuần có thể bỏ bài phụ); cập nhật lịch Google ngày đó → sync → push → publish → `ArtifactData delete inbox/leave-<date>` → trả lời 1 dòng + resolve thread → **Telegram**: lịch mới của những ngày bị ảnh hưởng.
- Tân cũng có thể xin nghỉ bằng cách **nhắn bot Telegram** – job sáng đọc `tools/notify.py --inbox`.
- Bài lỡ mà **không** xin nghỉ: trang tự hiện ở Today với nhãn "missed"; job sáng xếp lại nếu dồn quá 2 bài.

## Báo bài nộp về gia sư
- Chính: trang gửi comment **Send to Claude** "📥 Nộp bài <id>" → đánh thức phiên chính (đã kiểm chứng ~3 giây).
- Dự phòng (sau 8 giây không gửi được): `fire_trigger` Routine `trig_01AN7RrytvZ5BmXiymy5Ym5M`.
- Trang ghi kết quả báo vào `submissions/<id>.notify` để chẩn đoán.

## Quyền của trang
`db` (`submissions`, `inbox`, `drafts`), `comments` (Send to Claude), `mcp` → Claude Code Remote `fire_trigger`, `assets` (bản thu âm base64), `tts` (đọc bài nghe), `user`.
