#!/usr/bin/env python3
"""Sinh file MP3 cho các phần nghe (part.listen) bằng Piper TTS (mã nguồn mở, chạy offline).

Vì sao: giọng đọc `tts` của trang không chạy trên app Claude điện thoại. File MP3 thì phát được ở mọi nơi
(iPhone, Chrome, app), có chỉnh tốc độ và tua.

Dùng:  python3 tools/audio.py <lesson-id> [...]   (hoặc --all; --words <số tuần> = audio cho word wall)
→ data/audio/<id>/p<số phần>.mp3 và ghi part["audio"] = đường dẫn đó vào data/lessons/<id>.json.
Giọng (thư mục PIPER_DIR, mặc định /root/piper; tải ở tools/audio_setup.sh):
  rounded → en_GB-alan (nam, Anh) · glassy → en_GB-alba (nữ, Anh) · buttery/airy → en_US-lessac (Mỹ)
"""
import io, json, os, re, subprocess, sys, wave
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPER = os.environ.get("PIPER_DIR", "/root/piper")
VOICE = {"rounded": "en_GB-alan-medium", "glassy": "en_GB-alba-medium", "buttery": "en_US-lessac-medium", "airy": "en_US-lessac-medium",
         "us_f": "en_US-lessac-medium", "us_m": "en_US-ryan-medium"}
# Tốc độ: chuẩn hoá mọi giọng về nhịp nói TỰ NHIÊN (~210–235 từ/phút khi đang nói, ~150–165 tính cả nghỉ) – 13/11: ryan mặc định ~290 wpm, nhanh hơn người thật
SCALE = {"en_US-lessac-medium": 1.25, "en_US-ryan-medium": 1.4, "en_GB-alba-medium": 1.05, "en_GB-alan-medium": 1.0}
# Mặc định giọng MỸ (Tân chọn 12/11): từ = us_f, câu ví dụ = us_m; bài không ghi voice → buttery (Mỹ).
_cache = {}

def voice(name):
    from piper import PiperVoice
    if name not in _cache: _cache[name] = PiperVoice.load(os.path.join(PIPER, name + ".onnx"))
    return _cache[name]

def pcm(text, vname):
    v = voice(vname); buf = io.BytesIO()
    from piper import SynthesisConfig
    with wave.open(buf, "wb") as w: v.synthesize_wav(text, w, syn_config=SynthesisConfig(length_scale=SCALE.get(vname, 1.0)))
    buf.seek(0)
    with wave.open(buf) as r: return r.getframerate(), r.readframes(r.getnframes())

def render(lid, marks_only=False):
    """marks = giây bắt đầu của từng dòng listen → web cho bấm nghe lại đúng đoạn đó.
    marks_only: chỉ đo lại mốc thời gian (tổng hợp lại để đo, không ghi MP3)."""
    path = os.path.join(ROOT, "data", "lessons", lid + ".json"); L = json.load(open(path))
    out = os.path.join(ROOT, "data", "audio", lid); os.makedirs(out, exist_ok=True)
    for pi, p in enumerate(L.get("parts", [])):
        if not p.get("listen") or p.get("keep_audio"): continue   # bài nghe thật (VOA…) giữ audio gốc – mốc do voa_marks.py
        rate, chunks, marks, pos = None, [], [], 0
        for x in p["listen"]:
            marks.append(round(pos / (rate or 22050), 2) if rate else 0.0)
            for para in [s for s in str(x["text"]).split("\n\n") if s.strip()]:
                sr, data = pcm(para.strip(), VOICE.get(x.get("voice"), VOICE["buttery"]))
                rate = rate or sr
                c = data + b"\0\0" * int(sr * (0.7 if len(p["listen"]) > 1 else 0.5))
                chunks.append(c); pos += len(c) // 2
        p["marks"] = marks
        if marks_only:
            print(f"{lid} part {pi+1}: {len(marks)} marks"); continue
        wav = os.path.join(out, f"p{pi}.wav"); mp3 = os.path.join(out, f"p{pi}.mp3")
        with wave.open(wav, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(b"".join(chunks))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-b:a", "64k", mp3], check=True)
        os.remove(wav)
        p["audio"] = f"data/audio/{lid}/p{pi}.mp3"
        print(f"{lid} part {pi+1}: {p['audio']} ({os.path.getsize(mp3)//1024} KB)")
    json.dump(L, open(path, "w"), ensure_ascii=False, indent=1)

def render_words(no, force=False):
    W = json.load(open(os.path.join(ROOT, "data", "weeks.json")))
    w = [x for x in W["weeks"] if x["no"] == no][0]
    extra = json.load(open(os.path.join(ROOT, "data", "words.json")))["words"] if os.path.exists(os.path.join(ROOT, "data", "words.json")) else []
    items = w.get("words", []) + [e for e in extra if e.get("week") == no]
    for x in items:
        if not x.get("audio"): continue
        if not x["audio"].endswith("-us.mp3"):   # đổi tên file khi đổi sang giọng Mỹ (tránh cache bản cũ)
            x["audio"] = x["audio"][:-4] + "-us.mp3"
        if os.path.exists(os.path.join(ROOT, x["audio"])) and not force: continue
        out = os.path.join(ROOT, x["audio"]); os.makedirs(os.path.dirname(out), exist_ok=True)
        sr, a = pcm(re.sub(r"\bsb\b", "somebody", re.sub(r"\bsth\b", "something", x["w"])).replace("+ V-ing", "").replace("…", "").replace("+ time", ""), VOICE["us_f"])
        _, b = pcm(x.get("ex", ""), VOICE["us_m"]) if x.get("ex") else (sr, b"")
        wav = out[:-4] + ".wav"
        with wave.open(wav, "wb") as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes(a + b"\0\0" * int(sr * 0.6) + b)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-af", "silenceremove=start_periods=1:start_threshold=-45dB",
                        "-ac", "1", "-b:a", "48k", out], check=True); os.remove(wav)
    json.dump(W, open(os.path.join(ROOT, "data", "weeks.json"), "w"), ensure_ascii=False, indent=1)
    if extra:
        WJ = json.load(open(os.path.join(ROOT, "data", "words.json"))); WJ["words"] = extra
        json.dump(WJ, open(os.path.join(ROOT, "data", "words.json"), "w"), ensure_ascii=False, indent=1)
    print(f"week {no}: {len(items)} word audios")

if __name__ == "__main__":
    ids = sys.argv[1:]
    if ids[:1] == ["--words"]: render_words(int(ids[1]), "--force" in ids); sys.exit()
    mo = "--marks" in ids; ids = [i for i in ids if i != "--marks"]
    if ids == ["--all"]: ids = [f[:-5] for f in sorted(os.listdir(os.path.join(ROOT, "data", "lessons"))) if f.endswith(".json")]
    for i in ids: render(i, mo)
