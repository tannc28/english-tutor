#!/usr/bin/env python3
"""Chấm phát âm + ngữ điệu cho một bản ghi đọc to (read-aloud) so với câu mẫu.

Cách dùng:
    python assess.py <audio> "<câu/đoạn mẫu>" [--out report.json]

Pipeline (toàn bộ mã nguồn mở, chạy CPU):
  1. ffmpeg           → chuẩn hoá 16 kHz mono
  2. faster-whisper   → nhận dạng từ + thời điểm + độ tin cậy từng từ
                        (máy có "nghe ra" đúng từ Tân định nói không = độ dễ nghe)
  3. wav2vec2 (facebook/wav2vec2-lv-60-espeak-cv-ft)
                      → nhận dạng ÂM VỊ thực tế Tân phát ra (IPA)
     espeak-ng        → âm vị CHUẨN của câu mẫu (IPA)
     so khớp          → âm bị thay / bị mất / thêm, đặc biệt âm cuối
  4. Praat (parselmouth) → cao độ (F0), cường độ, tốc độ nói, ngắt nghỉ,
                        ngữ điệu cuối câu (lên/xuống), độ "phẳng" của giọng

Giới hạn: đây là công cụ hỗ trợ, không thay tai giáo viên. Âm vị do model
nhận dạng có thể sai; ngữ điệu chỉ đo được các dấu hiệu thô.
"""
import argparse, difflib, json, os, re, subprocess, sys, tempfile, unicodedata

def to_wav(src):
    fd, dst = tempfile.mkstemp(suffix=".wav"); os.close(fd)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-ac", "1", "-ar", "16000", dst], check=True)
    return dst

def norm_words(s):
    return re.findall(r"[a-z']+", s.lower().replace("’", "'"))

# ---------- 1. ASR (word level) ----------
def asr(wav, ref_text):
    from faster_whisper import WhisperModel
    model = WhisperModel(os.environ.get("WHISPER_MODEL", "small.en"), device="cpu", compute_type="int8")
    # Không đưa câu mẫu vào prompt: muốn biết máy nghe "thật" ra gì
    segs, _ = model.transcribe(wav, language="en", word_timestamps=True, beam_size=5, vad_filter=False,
                               condition_on_previous_text=False)
    words = []
    for s in segs:
        for w in s.words or []:
            words.append({"w": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2), "p": round(w.probability, 2)})
    return words

def align_words(ref, hyp_words):
    hyp = [re.sub(r"[^a-z']", "", w["w"].lower()) for w in hyp_words]
    sm = difflib.SequenceMatcher(a=ref, b=hyp, autojunk=False)
    rows = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                h = hyp_words[j1 + k]
                rows.append({"ref": ref[i1 + k], "heard": h["w"], "ok": True, "p": h["p"], "start": h["start"], "end": h["end"]})
        else:
            refs, hyps = ref[i1:i2], hyp_words[j1:j2]
            for k in range(max(len(refs), len(hyps))):
                r = refs[k] if k < len(refs) else None
                h = hyps[k] if k < len(hyps) else None
                rows.append({"ref": r, "heard": h["w"] if h else None, "ok": False, "p": h["p"] if h else None,
                             "start": h["start"] if h else None, "end": h["end"] if h else None,
                             "type": "missing" if h is None else ("extra" if r is None else "different")})
    return rows

# ---------- 2. Phonemes ----------
IGN = set("ˈˌːˑ‿ .,?!-'")
def ipa_tokens(s):
    s = unicodedata.normalize("NFD", s)
    out, i = [], 0
    two = {"tʃ", "dʒ", "aɪ", "aʊ", "eɪ", "oʊ", "ɔɪ", "əʊ", "ɪə", "eə", "ʊə", "ɜː"}
    s = "".join(c for c in s if c not in "ˈˌ‿")
    while i < len(s):
        if s[i] in IGN or s[i].isspace() or unicodedata.category(s[i]) == "Mn": i += 1; continue
        if s[i:i + 2] in two: out.append(s[i:i + 2]); i += 2; continue
        out.append(s[i]); i += 1
    return out

def ref_phonemes_by_word(text):
    words = norm_words(text)
    res = []
    for w in words:
        p = subprocess.run(["espeak-ng", "-q", "--ipa", "-v", "en-us", w], capture_output=True, text=True).stdout.strip()
        res.append((w, ipa_tokens(p)))
    return res

def recognized_phonemes(wav):
    import torch, soundfile as sf
    from transformers import AutoProcessor, AutoModelForCTC
    name = os.environ.get("PHONEME_MODEL", "facebook/wav2vec2-lv-60-espeak-cv-ft")
    proc = AutoProcessor.from_pretrained(name); model = AutoModelForCTC.from_pretrained(name).eval()
    audio, sr = sf.read(wav)
    inp = proc(audio, sampling_rate=16000, return_tensors="pt")
    with torch.no_grad():
        ids = model(inp.input_values).logits.argmax(-1)
    txt = proc.batch_decode(ids)[0]
    return ipa_tokens(txt.replace(" ", ""))

# Nhóm âm hay gặp lỗi với người Việt → nhãn giải thích
VN_HINTS = {
    "θ": "âm th vô thanh (think) – đặt đầu lưỡi giữa hai hàm răng, thổi hơi",
    "ð": "âm th hữu thanh (this) – lưỡi giữa răng, rung cổ",
    "ʃ": "âm sh (she) – môi tròn, không phải s",
    "ʒ": "âm như trong measure",
    "z": "âm z hữu thanh – hay bị đọc thành s",
    "v": "âm v – răng trên chạm môi dưới",
    "dʒ": "âm j (job) – không phải z hay ch",
    "tʃ": "âm ch tiếng Anh (church) – bật hơi mạnh hơn ch Việt",
    "ɹ": "âm r tiếng Anh – lưỡi cong, không rung",
    "l": "âm l cuối từ (feel) – hay bị nuốt",
    "s": "âm s cuối (works, cats) – hay bị bỏ",
    "t": "âm t cuối (night) – hay bị bỏ hoặc nuốt",
    "d": "âm d cuối (cold) – hay bị bỏ",
    "k": "âm k cuối (work) – hay bị bỏ",
    "iː": "i dài (sheep) – phân biệt với ɪ ngắn (ship)",
    "ɪ": "i ngắn (ship)",
    "æ": "a bẹt (cat) – miệng mở rộng sang hai bên",
}

def phoneme_report(ref_by_word, rec):
    ref_flat, owner = [], []
    for wi, (w, ps) in enumerate(ref_by_word):
        for pi, p in enumerate(ps):
            ref_flat.append(p); owner.append((wi, pi == len(ps) - 1))
    sm = difflib.SequenceMatcher(a=ref_flat, b=rec, autojunk=False)
    issues, matched = [], 0
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal": matched += i2 - i1; continue
        for k in range(i1, i2):
            wi, is_final = owner[k]
            got = "".join(rec[j1:j2]) if op == "replace" else ""
            issues.append({"word": ref_by_word[wi][0], "expected": ref_flat[k], "got": got or "(mất)",
                           "final": is_final, "hint": VN_HINTS.get(ref_flat[k], "")})
    score = round(100 * matched / max(1, len(ref_flat)))
    return score, issues, "".join(ref_flat), "".join(rec)

# ---------- 3. Prosody ----------
def prosody(wav, words):
    import parselmouth, numpy as np
    snd = parselmouth.Sound(wav)
    pitch = snd.to_pitch(time_step=0.01, pitch_floor=70, pitch_ceiling=400)
    f0 = pitch.selected_array["frequency"]; t = pitch.xs()
    voiced = f0 > 0
    out = {"duration_s": round(snd.duration, 2)}
    if voiced.sum() > 10:
        st = 12 * np.log2(f0[voiced] / np.median(f0[voiced]))
        out["pitch_median_hz"] = round(float(np.median(f0[voiced])), 1)
        out["pitch_range_semitones"] = round(float(np.percentile(st, 95) - np.percentile(st, 5)), 1)
        # Cuối câu: so 300 ms cuối có tiếng với đoạn trước đó
        vt = t[voiced]; vf = st
        end = vt[-1]
        tail = vf[vt > end - 0.3]; before = vf[(vt > end - 0.9) & (vt <= end - 0.3)]
        if len(tail) > 3 and len(before) > 3:
            d = float(np.mean(tail) - np.mean(before))
            out["final_contour"] = "lên ↗" if d > 1.5 else ("xuống ↘" if d < -1.5 else "ngang →")
            out["final_change_semitones"] = round(d, 1)
    if words:
        speak = words[-1]["end"] - words[0]["start"]
        out["words_per_min"] = round(60 * len(words) / max(speak, 0.1))
        gaps = [round(words[i + 1]["start"] - words[i]["end"], 2) for i in range(len(words) - 1)]
        out["pauses"] = [{"after": words[i]["w"], "s": g} for i, g in enumerate(gaps) if g >= 0.3]
        # Nhấn từ: cường độ trung bình từng từ (dB), để thấy giọng có lên xuống nhấn nhá không
        inten = snd.to_intensity(time_step=0.01)
        per = []
        for w in words:
            seg = [inten.get_value(x) for x in np.arange(w["start"], w["end"], 0.01)]
            seg = [v for v in seg if v == v]
            if seg: per.append((w["w"], round(float(np.mean(seg)), 1)))
        if per:
            vals = np.array([v for _, v in per])
            out["word_loudness_spread_db"] = round(float(vals.std()), 1)
            top = sorted(per, key=lambda x: -x[1])[:3]
            out["most_stressed_words"] = [w for w, _ in top]
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("audio"); ap.add_argument("reference"); ap.add_argument("--out")
    ap.add_argument("--no-phonemes", action="store_true")
    a = ap.parse_args()
    wav = to_wav(a.audio)
    ref = norm_words(a.reference)
    words = asr(wav, a.reference)
    rows = align_words(ref, words)
    intellig = round(100 * sum(r["ok"] for r in rows if r["ref"]) / max(1, len(ref)))
    report = {"reference": a.reference, "heard": " ".join(w["w"] for w in words),
              "intelligibility_pct": intellig, "words": rows, "prosody": prosody(wav, words)}
    if not a.no_phonemes:
        score, issues, refp, recp = phoneme_report(ref_phonemes_by_word(a.reference), recognized_phonemes(wav))
        report["phoneme_match_pct"] = score; report["phoneme_issues"] = issues
        report["ipa_expected"] = refp; report["ipa_heard"] = recp
    js = json.dumps(report, ensure_ascii=False, indent=1)
    if a.out: open(a.out, "w").write(js)
    print(js)

if __name__ == "__main__":
    main()
