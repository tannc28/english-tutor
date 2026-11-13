#!/usr/bin/env python3
"""Telegram cho việc HỌC (Tân chọn 12/11: tin 4 dòng + thẻ lỗi + quiz ôn lại + báo cáo tuần).

  python3 tools/tg.py graded <lessonId>   # sau khi chấm: tin 4 dòng (grade.tg) + thẻ lỗi (grade.cards, ≤3) + đưa quiz (grade.quiz) vào hàng ôn
  python3 tools/tg.py quiz                # job sáng: gửi quiz đến hạn (data/review.json), đọc kết quả quiz đã làm
  python3 tools/tg.py weekly <weekNo>     # Chủ nhật: ảnh báo cáo tuần
  python3 tools/tg.py words               # job sáng: ≤4 thẻ từ có hình (ôn đến hạn + từ mới) + 1 file audio
Dữ liệu gia sư viết khi chấm (grades/<id>.json):
  tg:    {"win": "...", "fix": "..."}                       – mỗi dòng ≤ 90 ký tự, tiếng Việt/Anh đơn giản
  cards: [{"q": "...", "yours": "...", "right": "...", "tip": "..."}]   – tối đa 3 lỗi quan trọng nhất (❌→✅→💡)
  quiz:  [{"q": "...", "options": ["..",".."], "answer": 0, "why": "..."}]  – 2–3 câu ôn đúng chỗ sai (q ≤ 300, option ≤ 100, why ≤ 200 ký tự)
Lịch ôn: ngày hôm sau → +3 ngày → +7 ngày (nếu sai thì lặp lại từ đầu).
"""
import json, os, sys, html, subprocess, tempfile, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import notify
ROOT = notify.ROOT; D = lambda *p: os.path.join(ROOT, "data", *p)
CLASS = notify.CLASS
load = lambda p: json.load(open(p, encoding="utf-8"))
def save(p, o): json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
E = lambda s: html.escape(str(s or ""), quote=False)
today = lambda: dt.date.today().isoformat()
CSS = """<meta charset="utf-8"><style>
body{margin:0;background:#eef2f7;font-family:-apple-system,'Segoe UI',Roboto,'Noto Sans',sans-serif;color:#1c2333}
#card{margin:0;padding:26px 26px 22px;background:#fff;border-radius:0;display:flex;flex-direction:column;gap:14px}
.k{font:600 13px/1 ui-monospace,Menlo,monospace;letter-spacing:.08em;text-transform:uppercase;color:#6b7690}
.q{font-size:19px;line-height:1.45;font-weight:600}
.row{display:grid;grid-template-columns:34px 1fr;gap:10px;align-items:start;font-size:19px;line-height:1.45;padding:12px 14px;border-radius:12px}
.no{background:#fdecec}.no b{color:#b42318;text-decoration:line-through;text-decoration-thickness:2px}
.ok{background:#e8f6ee}.ok b{color:#157347}
.tip{background:#eef3ff;font-size:17px}
.big{font-size:22px}
</style>"""

def render(htmlbody, out, width=540):
    f = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8"); f.write(CSS + htmlbody); f.close()
    subprocess.run(["node", os.path.join(ROOT, "tools", "render_card.js"), f.name, out, str(width)], check=True)
    os.remove(f.name); return out

def lesson_meta(lid):
    return next((l for l in load(D("lessons.json"))["lessons"] if l["id"] == lid), {})

def next_lesson():
    idx = load(D("lessons.json"))["lessons"]; W = load(D("weeks.json"))["weeks"]
    plan = {i: ds for w in W for ds, d in (w.get("days") or {}).items() for i in d.get("lessons", [])}
    open_ = sorted([l for l in idx if l.get("status") == "open"], key=lambda l: (plan.get(l["id"], "9"), l.get("order", 0)))
    return open_[0] if open_ else None, plan

def send_photos(paths, caption=""):
    import uuid
    b = uuid.uuid4().hex
    media = [{"type": "photo", "media": f"attach://f{i}", **({"caption": caption, "parse_mode": "HTML"} if i == 0 and caption else {})} for i in range(len(paths))]
    body = f'--{b}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{notify.chat_id()}\r\n--{b}\r\nContent-Disposition: form-data; name="media"\r\n\r\n{json.dumps(media, ensure_ascii=False)}\r\n'.encode()
    for i, p in enumerate(paths):
        body += f'--{b}\r\nContent-Disposition: form-data; name="f{i}"; filename="{os.path.basename(p)}"\r\nContent-Type: image/png\r\n\r\n'.encode() + open(p, "rb").read() + b"\r\n"
    body += f"--{b}--\r\n".encode()
    import urllib.request
    method = "sendMediaGroup" if len(paths) > 1 else None
    if method is None:  # 1 ảnh → sendPhoto
        b2 = uuid.uuid4().hex
        body = (f'--{b2}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{notify.chat_id()}\r\n'
                f'--{b2}\r\nContent-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n--{b2}\r\nContent-Disposition: form-data; name="parse_mode"\r\n\r\nHTML\r\n'
                f'--{b2}\r\nContent-Disposition: form-data; name="photo"; filename="card.png"\r\nContent-Type: image/png\r\n\r\n').encode() + open(paths[0], "rb").read() + f"\r\n--{b2}--\r\n".encode()
        b, method = b2, "sendPhoto"
    req = urllib.request.Request(f"https://api.telegram.org/bot{notify.token()}/{method}", data=body, headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=90) as r: print(method, json.load(r).get("ok"))

# ---------- 1 + 4: sau khi chấm
def graded(lid):
    g = load(D("grades", lid + ".json")); m = lesson_meta(lid); tg = g.get("tg") or {}
    nxt, plan = next_lesson()
    nx = f'<a href="{CLASS}#{nxt["id"]}">{E(nxt["title"])}</a>' + (" (" + dt.date.fromisoformat(plan[nxt["id"]]).strftime('%a %d/%m') + ")" if nxt and nxt["id"] in plan else "") if nxt else "hết bài tuần này 🎉"
    msg = (f'✅ <b>Đã chấm: {E(m.get("title", lid))}</b>\n'
           f'📊 {E(tg.get("score") or g.get("score", ""))}\n'
           f'👍 {E(tg.get("win", ""))}\n'
           f'🔧 {E(tg.get("fix", ""))}\n'
           f'➡️ Tiếp theo: {nx}\n'
           f'<a href="{CLASS}#{lid}">Xem chi tiết trên web</a>')
    # có tin "⏳ Đang chấm…" (notify.py --start grade-<id>) → sửa chính tin đó thành kết quả; không có thì gửi mới
    notify.status_end(f"grade-{lid}", msg.split("\n", 1)[1], title=msg.split("\n", 1)[0].replace("✅ ", ""))
    g["tg_sent"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")   # check.py: bài đã chấm phải có tg_sent (Tân 13/11)
    save(D("grades", lid + ".json"), g)
    cards = (g.get("cards") or [])[:3]
    if cards:
        outs = []
        for i, c in enumerate(cards):
            body = f'''<div id="card"><div class="k">🔧 Fix {i+1}/{len(cards)} · {E(m.get("title", lid))}</div>
              <div class="q">{E(c["q"])}</div>
              <div class="row no"><span class="big">❌</span><span>{E(c["yours"]) and f"<b>{E(c['yours'])}</b>"}</span></div>
              <div class="row ok"><span class="big">✅</span><span><b>{E(c["right"])}</b></span></div>
              <div class="row tip"><span class="big">💡</span><span>{E(c["tip"])}</span></div></div>'''
            outs.append(render(body, os.path.join(tempfile.gettempdir(), f"fix-{lid}-{i}.png")))
        send_photos(outs, "🔧 <b>Chỗ cần sửa</b> – lướt qua là đủ. Sáng mai mình hỏi lại bằng quiz 😉")
    if g.get("quiz"):
        R = load(D("review.json")) if os.path.exists(D("review.json")) else {"items": []}
        have = {x["id"] for x in R["items"]}
        start = (dt.date.today() + dt.timedelta(days=1)).isoformat()
        for i, q in enumerate(g["quiz"]):
            qid = f"{lid}-q{i}"
            if qid not in have: R["items"].append({"id": qid, "lesson": lid, **q, "due": start, "step": 0, "history": []})
        save(D("review.json"), R); print("quiz queued:", len(g["quiz"]))

# ---------- 6: quiz ôn lại (spaced: +1 → +3 → +7)
STEPS = [1, 3, 7]
def collect_answers(R):
    try: ups = notify.api("getUpdates", allowed_updates='["message","poll_answer"]').get("result", [])
    except Exception: return
    by_poll = {x.get("poll_id"): x for x in R["items"] if x.get("poll_id")}
    for u in ups:
        a = u.get("poll_answer")
        if not a or a.get("poll_id") not in by_poll: continue
        x = by_poll[a["poll_id"]]; ok = a.get("option_ids", [None])[0] == x["answer"]
        if x.get("answered_poll") == a["poll_id"]: continue
        x["answered_poll"] = a["poll_id"]; x["history"].append({"date": today(), "ok": ok})
        if ok: x["step"] += 1
        else: x["step"] = 0
        x["due"] = None if x["step"] >= len(STEPS) else (dt.date.today() + dt.timedelta(days=STEPS[x["step"]])).isoformat()
        x.pop("poll_id", None)

def quiz(force=False):
    p = D("review.json")
    if not os.path.exists(p): print("no review queue"); return
    R = load(p); collect_answers(R)
    for x in R["items"]:  # quiz gửi > 2 ngày mà Tân chưa làm → gửi lại sau
        if x.get("poll_id") and x.get("sent") and (dt.date.today() - dt.date.fromisoformat(x["sent"])).days >= 2:
            x.pop("poll_id"); x["due"] = today()
    due = [x for x in R["items"] if x.get("due") and (force or x["due"] <= today()) and not x.get("poll_id")][:3]
    if due: notify.send(f"🧠 <b>Ôn lại {len(due)} câu</b> – chọn đáp án, Telegram hiện giải thích ngay.")
    for x in due:
        r = notify.api("sendPoll", chat_id=notify.chat_id(), question=x["q"][:300], options=json.dumps([o[:100] for o in x["options"]], ensure_ascii=False),
                       type="quiz", correct_option_id=x["answer"], explanation=x.get("why", "")[:200], is_anonymous="false")
        if r.get("ok"): x["poll_id"] = r["result"]["poll"]["id"]; x["sent"] = today()
    save(p, R); print("sent", len(due), "quiz")

# ---------- 7: thẻ từ vựng có hình (mỗi ngày ≤4 thẻ: từ đến hạn ôn trước, rồi từ mới của word wall; ôn sau 1 → 3 → 7 → 14 ngày)
WSTEPS = [1, 3, 7, 14]
def words(n=4):
    lib = load(D("library.json"))["words"]
    p = D("review.json"); R = load(p) if os.path.exists(p) else {"items": []}
    S = R.setdefault("words", {})
    due = [w for w in lib if w["w"] in S and S[w["w"]].get("due") and S[w["w"]]["due"] <= today()]
    new = [w for w in lib if w["w"] not in S and w.get("img")]
    pick = (due + new)[:n]
    if not pick: print("no word cards today"); return
    outs, auds = [], []
    for i, w in enumerate(pick):
        img = f'<img src="file://{os.path.join(ROOT, w["img"])}" style="width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:14px">' if w.get("img") else ""
        body = f'''<div id="card">{img}<div class="k">{"🔁 review" if w in due else "✨ new word"} · Week {E(w.get("week",""))}</div>
          <div style="font-size:34px;font-weight:800;line-height:1.1">{E(w["w"])}</div>
          {f'<div style="font-size:21px;color:#2b6de0">🇬🇧 {E(w.get("ipa"))}' + (f' &nbsp;·&nbsp; 🇺🇸 {E(w.get("ipa_us"))}' if w.get("ipa_us") and w.get("ipa_us") != w.get("ipa") else "") + '</div>' if w.get("ipa") else ""}
          {f'<div class="q" style="font-weight:500">{E(w.get("def"))}</div>' if w.get("def") else ""}
          {f'<div class="row tip"><span class="big">💬</span><span><i>{E(w.get("ex"))}</i></span></div>' if w.get("ex") else ""}
          {f'<div style="font-size:17px;color:#6b7690">🇻🇳 {E(w.get("vi"))}</div>' if w.get("vi") else ""}</div>'''
        outs.append(render(body, os.path.join(tempfile.gettempdir(), f"word-{i}.png")))
        if w.get("audio") and os.path.exists(os.path.join(ROOT, w["audio"])): auds.append(os.path.join(ROOT, w["audio"]))
        st = S.get(w["w"], {"step": -1}); step = min(st["step"] + 1, len(WSTEPS) - 1)
        S[w["w"]] = {"step": step, "due": (dt.date.today() + dt.timedelta(days=WSTEPS[step])).isoformat(), "sent": today()}
    send_photos(outs, f'🃏 <b>{len(pick)} thẻ từ hôm nay</b> – nhìn hình, đoán nghĩa, rồi đọc ví dụ. <a href="{CLASS}#on-tap">Ôn thêm trên web</a>')
    if auds:  # ghép audio các từ thành 1 file để nghe liền
        lst = os.path.join(tempfile.gettempdir(), "words.txt"); out = os.path.join(tempfile.gettempdir(), f"words-{today()}.mp3")
        open(lst, "w").write("".join(f"file '{a}'\n" for a in auds))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
        import uuid, urllib.request
        b = uuid.uuid4().hex
        body = (f'--{b}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{notify.chat_id()}\r\n--{b}\r\nContent-Disposition: form-data; name="title"\r\n\r\nWords {today()}\r\n'
                f'--{b}\r\nContent-Disposition: form-data; name="audio"; filename="words.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n').encode() + open(out, "rb").read() + f"\r\n--{b}--\r\n".encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{notify.token()}/sendAudio", data=body, headers={"Content-Type": f"multipart/form-data; boundary={b}"})
        with urllib.request.urlopen(req, timeout=60) as r: print("audio", json.load(r).get("ok"))
    save(p, R)

# ---------- 8: báo cáo tuần
def weekly(no):
    W = next(w for w in load(D("weeks.json"))["weeks"] if w["no"] == no)
    ls = sorted([l for l in load(D("lessons.json"))["lessons"] if l.get("week") == no], key=lambda l: l.get("order", 0))
    done = [l for l in ls if l.get("status") == "graded"]
    mins = sum((l.get("minutesActual") or 0) + (l.get("extraMinutes") or 0) for l in done)
    M = load(D("mastery.json"))["items"]; LV = load(D("levels.json"))["levels"]
    txt = {i["id"]: i["text"] for l in LV for s in l["sections"] for i in s["items"]}
    up = [k for k, v in M.items() if v.get("tutor") == "got_it" and not v.get("baseline") and W["start"] <= v.get("date", "") <= W["end"]]
    tg = [k for k in W.get("targets", [])]
    face = {"relaxed": "😌", "some": "🙂", "hard": "😵"}
    bars = "".join(f'''<div style="display:flex;flex-direction:column;align-items:center;gap:4px;flex:1">
        <div style="height:110px;width:100%;display:flex;align-items:flex-end;gap:3px;justify-content:center">
          <div title="listen" style="width:14px;height:{(l.get('listenPct') or 0)*1.1}px;background:#e0892b;border-radius:4px 4px 0 0"></div>
          <div title="read" style="width:14px;height:{(l.get('readPct') or 0)*1.1}px;background:#2b6de0;border-radius:4px 4px 0 0"></div></div>
        <span style="font-size:13px;color:#6b7690">L{l.get('order')}</span><span style="font-size:16px">{face.get(l.get('strain'), '·') if l.get('status')=='graded' else '○'}</span></div>''' for l in ls)
    tile = lambda big, small: f'<div style="flex:1;background:#f4f6fa;border-radius:12px;padding:12px"><div style="font-size:26px;font-weight:800">{big}</div><div style="font-size:14px;color:#6b7690">{small}</div></div>'
    body = f'''<div id="card"><div class="k">📊 Weekly report · Week {no} · {E(W["theme"])}</div>
      <div style="display:flex;gap:10px">{tile(f"{len(done)}/{len(ls)}", "lessons done")}{tile(f"{round(mins/60,1)} h", "in lessons")}{tile(f"+{len(up)}", "new checklist ✅ this week")}</div>
      <div><div class="k" style="margin-bottom:8px">Understanding per lesson · <span style="color:#e0892b">■ listening</span> <span style="color:#2b6de0">■ reading</span> · effort</div><div style="display:flex;gap:6px">{bars}</div></div>
      <div><div class="k" style="margin-bottom:6px">This week's targets</div>{"".join(f'<div style="font-size:15px;line-height:1.5">{"✅" if M.get(t,{}).get("tutor")=="got_it" else "🌱" if M.get(t,{}).get("tutor")=="learning" else "⬜"} {E(txt.get(t,t))}</div>' for t in tg)}</div>
      {f'<div class="row tip"><span class="big">➡️</span><span>{E(W.get("next_focus",""))}</span></div>' if W.get("next_focus") else ""}</div>'''
    out = render(body, os.path.join(tempfile.gettempdir(), f"week{no}.png"))
    send_photos([out], f'📊 <b>Báo cáo tuần {no}</b> · <a href="{CLASS}">mở lớp học</a>')

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["graded"]: graded(a[1])
    elif a[:1] == ["quiz"]: quiz(force="--now" in a)
    elif a[:1] == ["weekly"]: weekly(int(a[1]))
    elif a[:1] == ["words"]: words()
    else: print(__doc__)
