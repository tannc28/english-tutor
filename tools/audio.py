#!/usr/bin/env python3
"""Sinh file MP3 cho các phần nghe (part.listen) bằng Piper TTS (mã nguồn mở, chạy offline).

Vì sao: giọng đọc `tts` của trang không chạy trên app Claude điện thoại. File MP3 thì phát được ở mọi nơi
(iPhone, Chrome, app), có chỉnh tốc độ và tua.

Dùng:  python3 tools/audio.py <lesson-id> [...]   (hoặc --all; --words <số tuần> = audio cho word wall)
→ data/audio/<id>/p<số phần>.mp3 và ghi part["audio"] = đường dẫn đó vào data/lessons/<id>.json.
Giọng (thư mục PIPER_DIR, mặc định /root/piper; tải ở tools/audio_setup.sh):
  rounded → en_GB-alan (nam, Anh) · glassy → en_GB-alba (nữ, Anh) · buttery/airy → en_US-lessac (Mỹ)
"""
import io, json, os, subprocess, sys, wave
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPER = os.environ.get("PIPER_DIR", "/root/piper")
VOICE = {"rounded": "en_GB-alan-medium", "glassy": "en_GB-alba-medium", "buttery": "en_US-lessac-medium", "airy": "en_US-lessac-medium"}
_cache = {}

def voice(name):
    from piper import PiperVoice
    if name not in _cache: _cache[name] = PiperVoice.load(os.path.join(PIPER, name + ".onnx"))
    return _cache[name]

def pcm(text, vname):
    v = voice(vname); buf = io.BytesIO()
    with wave.open(buf, "wb") as w: v.synthesize_wav(text, w)
    buf.seek(0)
    with wave.open(buf) as r: return r.getframerate(), r.readframes(r.getnframes())

def render(lid):
    path = os.path.join(ROOT, "data", "lessons", lid + ".json"); L = json.load(open(path))
    out = os.path.join(ROOT, "data", "audio", lid); os.makedirs(out, exist_ok=True)
    for pi, p in enumerate(L.get("parts", [])):
        if not p.get("listen"): continue
        rate, chunks = None, []
        for x in p["listen"]:
            for para in [s for s in str(x["text"]).split("\n\n") if s.strip()]:
                sr, data = pcm(para.strip(), VOICE.get(x.get("voice"), VOICE["buttery"]))
                rate = rate or sr
                chunks.append(data + b"\0\0" * int(sr * (0.7 if len(p["listen"]) > 1 else 0.5)))
        wav = os.path.join(out, f"p{pi}.wav"); mp3 = os.path.join(out, f"p{pi}.mp3")
        with wave.open(wav, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(b"".join(chunks))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-b:a", "64k", mp3], check=True)
        os.remove(wav)
        p["audio"] = f"data/audio/{lid}/p{pi}.mp3"
        print(f"{lid} part {pi+1}: {p['audio']} ({os.path.getsize(mp3)//1024} KB)")
    json.dump(L, open(path, "w"), ensure_ascii=False, indent=1)

def render_words(no):
    W = json.load(open(os.path.join(ROOT, "data", "weeks.json")))
    w = [x for x in W["weeks"] if x["no"] == no][0]
    for x in w.get("words", []):
        if not x.get("audio"): continue
        out = os.path.join(ROOT, x["audio"]); os.makedirs(os.path.dirname(out), exist_ok=True)
        sr, a = pcm(x["w"].replace("sb", "somebody").replace("+ V-ing", ""), VOICE["glassy"])
        _, b = pcm(x.get("ex", ""), VOICE["rounded"]) if x.get("ex") else (sr, b"")
        wav = out[:-4] + ".wav"
        with wave.open(wav, "wb") as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(sr); f.writeframes(a + b"\0\0" * int(sr * 0.6) + b)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-b:a", "48k", out], check=True); os.remove(wav)
    print(f"week {no}: {len(w.get('words', []))} word audios")

if __name__ == "__main__":
    ids = sys.argv[1:]
    if ids[:1] == ["--words"]: render_words(int(ids[1])); sys.exit()
    if ids == ["--all"]: ids = [f[:-5] for f in sorted(os.listdir(os.path.join(ROOT, "data", "lessons"))) if f.endswith(".json")]
    for i in ids: render(i)
