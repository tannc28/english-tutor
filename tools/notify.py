#!/usr/bin/env python3
"""Gửi thông báo Telegram cho Tân (bot @CtanEnglishTutorBot).

Token (bí mật – KHÔNG để trong repo): biến môi trường TELEGRAM_BOT_TOKEN, nếu không có thì file /root/.telegram_token.
Chat id: data/profile.json → notify.telegram_chat_id (lấy bằng --setup sau khi Tân bấm Start với bot).

Dùng:
  python3 tools/notify.py "✅ Đã chấm Lesson 2 – 8/10 …"          # gửi (HTML: <b>, <i>, <a href>)
  python3 tools/notify.py --setup                                   # tìm chat id từ tin nhắn /start, lưu vào profile
  echo "**markdown**" | python3 tools/notify.py --md          # gửi markdown (đổi sang HTML Telegram)
  python3 tools/notify.py --inbox                                   # in tin Tân nhắn cho bot (job sáng đọc: xin nghỉ, góp ý…)
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

def send(text):
    r = api("sendMessage", chat_id=chat_id(), text=text, parse_mode="HTML", disable_web_page_preview="true")
    print("sent" if r.get("ok") else r)

if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--setup"]: setup()
    elif a == ["--inbox"]: inbox()
    elif a[:1] == ["--md"]: send(md2html(sys.stdin.read() if len(a) == 1 else " ".join(a[1:])))
    elif a: send(" ".join(a))
    else: print(__doc__)
