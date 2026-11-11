# Chấm phát âm & ngữ điệu (thử nghiệm)

Claude không nghe được âm thanh trực tiếp. Bộ công cụ mã nguồn mở này "nghe hộ", rồi gia sư đọc kết quả và nhận xét.

## Luồng
1. Tân thu âm (app ghi âm trên điện thoại, .m4a/.mp3/.wav), **đọc to đúng đoạn mẫu** trong bài.
2. Tải file lên repo: github.com/tannc28/english-tutor → thư mục `recordings/` → *Add file → Upload files*. Tên file: `YYYY-MM-DD_<mã-bài>.m4a`.
3. Nhắn gia sư "đã thu âm" (hoặc nộp bài trên web). Gia sư: `git pull` → `bash tools/speech/setup.sh` (lần đầu mỗi phiên/máy) → chạy `assess.py` → viết nhận xét vào bài + Progress Log (mục Pronunciation).

## Đo được gì
| Lớp | Công cụ | Cho biết |
|---|---|---|
| Độ dễ nghe | faster-whisper (Whisper small.en) | Máy có nhận ra đúng từ Tân định nói không; từ nào bị nghe nhầm |
| Âm vị | wav2vec2 `facebook/wav2vec2-lv-60-espeak-cv-ft` + espeak-ng | Âm bị thay/mất/thêm, đặc biệt **âm cuối** (s, t, d, k, l, z), th/sh/r, i dài/ngắn |
| Ngữ điệu, nhịp | Praat (parselmouth) | Cao độ, biên độ lên xuống (semitone), ngữ điệu cuối câu (lên/xuống), tốc độ (từ/phút), chỗ ngắt nghỉ, từ được nhấn mạnh nhất |

## Đã kiểm thử (11/11/2026, giọng tổng hợp espeak)
- Câu đọc **sai có chủ đích** (bỏ âm cuối: *wor, nigh, shif, she, hospitan*): bắt đúng hầu hết lỗi đã cài – mất /s/ trong *works, shifts*, mất /t/ trong *night*, mất /z/ trong *she's*, /l/ → /n/ trong *hospital*.
- Câu đọc **đúng**: vẫn báo nhầm ~13% âm vị (giọng máy kém tự nhiên, ranh giới từ *night shifts*). → **Chỉ báo lỗi lặp lại nhiều lần / ở nhiều câu**, không kết luận từ 1 âm lẻ.
- Ngữ điệu: chưa kiểm chứng được với giọng thật; giọng máy không có ngữ điệu tự nhiên.

## Giới hạn (nói thẳng)
- Không thay được tai giáo viên. Không chấm được "độ hay", cảm xúc, độ tự nhiên tổng thể.
- Trọng âm từ/câu chỉ có chỉ báo thô (cường độ). Ngữ điệu cuối câu là dấu hiệu thô.
- Model nhận dạng âm vị có thể sai, nhất là với âm thanh nhiễu → thu âm nơi yên tĩnh, điện thoại cách miệng ~20 cm.
- Trang web không ghi âm được (claude.ai chưa cấp quyền micro cho trang), nên phải tải file lên GitHub.

## Nguồn
- OpenPronounce (wav2vec2 + espeak, cùng hướng tiếp cận): https://github.com/Halleck45/OpenPronounce
- GOPT / speechocean762 (nghiên cứu chấm phát âm): https://github.com/YuanGongND/gopt
- Parselmouth (Praat cho Python), myprosody (đặc trưng ngữ điệu): https://github.com/Shahabks/myprosody
