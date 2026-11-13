#!/usr/bin/env python3
"""Gửi thông báo Telegram cho Tân (bot @CtanEnglishTutorBot).

Token (bí mật – KHÔNG để trong repo): biến môi trường TELEGRAM_BOT_TOKEN, nếu không có thì file /root/.telegram_token.
Chat id: data/profile.json → notify.telegram_chat_id (lấy bằng --setup sau khi Tân bấm Start với bot).

Dùng:
  python3 tools/notify.py "✅ Đã chấm Lesson 2 – 8/10 …"          # gửi (HTML: <b>, <i>, <a href>)
  python3 tools/notify.py --setup                                   # tìm chat id từ tin nhắn /start, lưu vào profile
  echo "**markdown**" | python3 tools/notify.py --md          # gửi markdown (đổi sang HTML Telegram)
  python3 tools/notify.py --result <lessonId> "<caption HTML ngắn>"   # ảnh dài bài đã chấm + caption (CÁCH CHÍNH khi chấm xong)
  python3 tools/notify.py --file <path> "<caption>"            # gửi file
  python3 tools/notify.py --inbox                                   # in tin Tân nhắn cho bot (job sáng đọc: xin nghỉ, góp ý…)
TIN TRẠNG THÁI 1 TIN DUY NHẤT (Tân 13/11: "đang làm gì nhắn trước, xong thì cập nhật lại chính tin đó"):
  python3 tools/notify.py --start <key> "Đang chấm bài <b>…</b>"    # gửi "⏳ …", nhớ message_id theo key
  python3 tools/notify.py --step  <key> "Soạn xong 3/6 bài"         # thêm 1 dòng tiến độ vào CHÍNH tin đó
  python3 tools/notify.py --done  <key> "Kết quả …"                 # ⏳→✅ + kết quả, sửa CHÍNH tin đó
  python3 tools/notify.py --fail  <key> "Lỗi … – cần Tân …"         # ⏳→⚠️
  key: grade-<lessonId> · morning-<YYYY-MM-DD> · weekly-<N> · leave-<date> … (tg.py graded tự --done grade-<id>)
Khi nào gửi: chấm xong 1 bài · ra kế hoạch tuần mới · xử lý xin nghỉ / đổi lịch · nhắc nhẹ khi 2 ngày không học.
"""
import json, os, sys, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE = os.path.join(ROOT, "data", "profile.json")
CLASS = "https://claude.ai/artifact/LX12NEhBjqgC3qv5bvqAC2"

def token():
    t = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not t and os.path.exists("/root/.telegram_token"): t = open("/root/.telegram_token").read().strip()
    if not t: sys.exit("Không có token Telegram (TELEGRAM_BOT_TOKEN hoặc /root/.telegram_token).")
    return t

def api(method, **params):
    data = urllib.parse.urlencode(params).encode() if params else None
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token()}/{method}", data=data, timeout=20) as r:
        return json.load(r)

def chat_id():
    p = json.load(open(PROFILE))
    c = (p.get("notify") or {}).get("telegram_chat_id")
    if not c: sys.exit("Chưa có chat id – Tân cần bấm Start với @CtanEnglishTutorBot, rồi chạy --setup.")
    return c

def setup():
    ups = api("getUpdates").get("result", [])
    chats = [u["message"]["chat"] for u in ups if "message" in u and u["message"]["chat"]["type"] == "private"]
    if not chats: print("Chưa có tin nhắn nào gửi bot."); return False
    c = chats[-1]
    p = json.load(open(PROFILE)); p.setdefault("notify", {})["telegram_chat_id"] = c["id"]
    json.dump(p, open(PROFILE, "w"), ensure_ascii=False, indent=1)
    print("Đã lưu chat id cho", c.get("first_name", "")); return True

def inbox():
    ups = api("getUpdates").get("result", [])
    cid = chat_id()
    for u in ups:
        m = u.get("message") or {}
        if m.get("chat", {}).get("id") == cid and m.get("text") and m["text"] != "/start":
            print(m["date"], m["text"])

def md2html(t):
    """Markdown đơn giản (bài chấm) → HTML Telegram: **b**, *i*, [x](url), danh sách, tiêu đề."""
    import re, html
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    t = re.sub(r"(?m)^#+\s*(.+)$", r"<b>\1</b>", t)
    t = re.sub(r"(?m)^\s*[-•]\s+", "• ", t)
    return t

def send_file(path, caption=""):
    """Gửi file (ảnh dài/PDF) dạng document để Tân mở, phóng to, tự cuộn."""
    import uuid, mimetypes
    b = uuid.uuid4().hex; name = os.path.basename(path)
    parts = [f'--{b}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id()}\r\n',
             f'--{b}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n',
             f'--{b}\r\nContent-Disposition: form-data; name="parse_mode"\r\n\r\nHTML\r\n']
    body = "".join(parts).encode() + f'--{b}\r\nContent-Disposition: form-data; name="document"; filename="{name}"\r\nContent-Type: {mimetypes.guess_type(name)[0] or "application/octet-stream"}\r\n\r\n'.encode() + open(path, "rb").read() + f"\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token()}/sendDocument", data=body, headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=60) as r: print("sent file" if json.load(r).get("ok") else "failed")

def send_album(paths, caption=""):
    """Gửi nhiều file thành 1 album (document) – caption ở file đầu."""
    import uuid
    b = uuid.uuid4().hex
    media = [{"type": "document", "media": f"attach://f{i}", **({"caption": caption, "parse_mode": "HTML"} if i == 0 else {})} for i in range(len(paths))]
    body = f'--{b}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id()}\r\n--{b}\r\nContent-Disposition: form-data; name="media"\r\n\r\n{json.dumps(media, ensure_ascii=False)}\r\n'.encode()
    for i, p in enumerate(paths):
        body += f'--{b}\r\nContent-Disposition: form-data; name="f{i}"; filename="{os.path.basename(p)}"\r\nContent-Type: image/jpeg\r\n\r\n'.encode() + open(p, "rb").read() + b"\r\n"
    body += f"--{b}--\r\n".encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token()}/sendMediaGroup", data=body, headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=120) as r: print("sent album" if json.load(r).get("ok") else "failed")

def send_result(lid, caption):
    """Chụp ảnh dài bài đã chấm (tools/snapshot.js) rồi gửi kèm caption ngắn."""
    import subprocess, tempfile
    out = os.path.join(tempfile.gettempdir(), f"{lid}.jpg")
    r = subprocess.run(["node", os.path.join(ROOT, "tools", "snapshot.js"), lid, out], check=True, capture_output=True, text=True)
    segs = json.loads(r.stdout.strip().splitlines()[-1])
    from PIL import Image
    ims = [Image.open(x).convert("RGB") for x in segs]
    W, H, MAXH = max(i.width for i in ims), sum(i.height for i in ims), 16000
    full = Image.new("RGB", (W, H), "white"); y = 0
    for im in ims: full.paste(im, (0, y)); y += im.height
    for x in segs: os.remove(x)
    n = -(-H // MAXH); files = []
    for k in range(n):  # bài dài → nhiều ảnh (mỗi ảnh ≤16000px) gửi thành 1 album
        f = out.replace(".jpg", f"-{k+1}of{n}.jpg") if n > 1 else out
        full.crop((0, k*MAXH, W, min(H, (k+1)*MAXH))).save(f, "JPEG", quality=80, optimize=True); files.append(f)
    print(f"{W}x{H} → {n} ảnh")
    if n == 1: send_file(files[0], caption)
    else: send_album(files, caption)

def send(text):
    r = api("sendMessage", chat_id=chat_id(), text=text, parse_mode="HTML", disable_web_page_preview="true")
    print("sent" if r.get("ok") else r)
    return (r.get("result") or {}).get("message_id")

# ---- Tin trạng thái: 1 tin, sửa dần (start → step… → done/fail)
STATUS = os.path.join(os.environ.get("TMPDIR", "/tmp"), "tg_status.json")
def _st():
    try: return json.load(open(STATUS))
    except Exception: return {}
def _render(e, icon):
    return f"{icon} {e['title']}" + "".join(f"\n{x}" for x in e["lines"])
def _edit(e, icon):
    text = _render(e, icon)[:4000]
    try:
        r = api("editMessageText", chat_id=chat_id(), message_id=e["mid"], text=text, parse_mode="HTML", disable_web_page_preview="true")
        if r.get("ok"): print("edited"); return True
    except Exception as ex: print("edit failed:", ex)
    return False
def status_start(key, title):
    S = _st(); mid = send("⏳ " + title)
    S[key] = {"mid": mid, "title": title, "lines": []}; json.dump(S, open(STATUS, "w"), ensure_ascii=False)
    return mid
def status_step(key, line):
    S = _st(); e = S.get(key)
    if not e: return status_start(key, line)
    e["lines"].append("• " + line); json.dump(S, open(STATUS, "w"), ensure_ascii=False); _edit(e, "⏳")
def status_end(key, text, icon="✅", title=None):
    """Sửa tin trạng thái thành kết quả; không có tin nào theo key (hoặc sửa lỗi) → gửi tin mới."""
    S = _st(); e = S.get(key)
    if e:
        if title: e["title"] = title
        e["lines"].append(text); 
        if _edit(e, icon): S.pop(key); json.dump(S, open(STATUS, "w"), ensure_ascii=False); return True
    send(f"{icon} {title + chr(10) if title else ''}{text}"); return False

if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--setup"]: setup()
    elif a == ["--inbox"]: inbox()
    elif a[:1] == ["--file"]: send_file(a[1], " ".join(a[2:]))
    elif a[:1] == ["--result"]: send_result(a[1], " ".join(a[2:]))
    elif a[:1] == ["--start"]: status_start(a[1], " ".join(a[2:]))
    elif a[:1] == ["--step"]: status_step(a[1], " ".join(a[2:]))
    elif a[:1] == ["--done"]: status_end(a[1], " ".join(a[2:]))
    elif a[:1] == ["--fail"]: status_end(a[1], " ".join(a[2:]), icon="⚠️")
    elif a[:1] == ["--md"]: send(md2html(sys.stdin.read() if len(a) == 1 else " ".join(a[1:])))
    elif a: send(" ".join(a))
    else: print(__doc__)
