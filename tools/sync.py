#!/usr/bin/env python3
"""Đồng bộ: repo (data/) → các bản hiển thị.

Nguồn dữ liệu DUY NHẤT là thư mục data/:
  data/weeks.json          kế hoạch theo TUẦN: chủ đề, mục tiêu, word wall, bài nghe tự do, chủ đề các tuần tới
  data/lessons.json        danh sách bài (mỗi bài thuộc 1 tuần) + chỉ số mỗi bài (listenPct, readPct, difficulty, minutesActual, note, status)
  data/profile.json        hồ sơ học sinh (Learner model, nhật ký quyết định, chunk bank, phát âm…)
  data/lessons/<id>.json   nội dung bài
  data/grades/<id>.json    kết quả chấm
  data/submissions/<id>.json  bài làm của Tân (chép từ web khi chấm)
  data/keys/<id>.json      đáp án (KHÔNG xuất bản lên web)

Script này:
  1. Kiểm tra JSON hợp lệ và lessons.json trỏ tới file bài có thật.
  2. Sinh lại tutor/02_PROGRESS_LOG.md từ profile.json + weeks.json + lessons.json (đừng sửa tay file đó).
  3. In ra danh sách file cần xuất bản kèm web (map `files` cho Artifact publish) → web/publish_files.json

Dùng: python3 tools/sync.py   (rồi publish web/index.html với files trong web/publish_files.json)
"""
import sys, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, "data", *p)

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def pct(v):
    return "–" if v in (None, "") else f"{round(float(v))}%"

def build_studylog():
    """Giờ học THẬT từ nhật ký phiên trong bài nộp (log.sessions + log.parts) → data/studylog.json.
    Mỗi phiên: bắt đầu (giờ VN), phút hoạt động (chia theo tỉ lệ thời gian mở, tổng = thời gian hoạt động thật của bài),
    gộp các phiên cách nhau < 10 phút thành 1 khối học."""
    import glob, datetime as dt
    tz = dt.timezone(dt.timedelta(hours=7))
    L = {l["id"]: l for l in json.load(open(D("lessons.json")))["lessons"]}
    ses = []
    for f in glob.glob(D("submissions", "*.json")):
        lid = os.path.basename(f)[:-5]; s = json.load(open(f)); lg = s.get("log") or {}
        ss = [x for x in lg.get("sessions", []) if "s" in x and "e" in x]
        if not ss or not lg.get("t0"): continue
        active = sum(v.get("ms", 0) for v in (lg.get("parts") or {}).values()) / 60000
        opened = sum(max(0, x["e"] - x["s"]) for x in ss) / 60 or 1
        k = min(1, active / opened) if active else 1
        for x in ss:
            m = max(0, x["e"] - x["s"]) / 60 * k
            if m < 0.5: continue
            st = dt.datetime.fromtimestamp(lg["t0"] / 1000 + x["s"], tz)
            ses.append({"start": st.isoformat(timespec="minutes"), "min": round(m, 1), "lesson": lid,
                        "title": L.get(lid, {}).get("title", lid), "kind": L.get(lid, {}).get("kind", ""), "device": x.get("kind", "")})
    ses.sort(key=lambda x: x["start"])
    blocks = []
    for x in ses:
        st = dt.datetime.fromisoformat(x["start"])
        if blocks and (st - dt.datetime.fromisoformat(blocks[-1]["end"])).total_seconds() < 600:
            b = blocks[-1]; b["min"] = round(b["min"] + x["min"], 1)
            b["end"] = max(b["end"], (st + dt.timedelta(minutes=x["min"])).isoformat(timespec="minutes"))
            if x["title"] not in b["lessons"]: b["lessons"].append(x["title"])
        else:
            blocks.append({"start": x["start"], "end": (st + dt.timedelta(minutes=x["min"])).isoformat(timespec="minutes"),
                           "min": x["min"], "lessons": [x["title"]]})
    days = {}
    for b in blocks:
        d = b["start"][:10]; days.setdefault(d, {"min": 0, "blocks": []})
        days[d]["min"] = round(days[d]["min"] + b["min"], 1); days[d]["blocks"].append(b)
    out = {"_note": "Sinh tự động bởi tools/sync.py từ log bài nộp – giờ học thật (phút hoạt động).", "sessions": ses, "days": days}
    json.dump(out, open(D("studylog.json"), "w"), ensure_ascii=False, indent=1)
    return out


def main():
    days = load(D("lessons.json"))["lessons"]
    weeks = load(D("weeks.json"))["weeks"]
    levels = load(D("levels.json"))["levels"]; mastery = load(D("mastery.json"))
    ids = {i["id"] for l in levels for sec in l["sections"] for i in sec["items"]}
    bad = [k for k in mastery.get("items", {}) if k not in ids]
    if bad: print("LỖI: mastery.json có id không tồn tại trong levels.json:", bad); sys.exit(1)
    wids = {w["no"] for w in weeks}
    for d in days:
        if d.get("week") not in wids: print(f"LỖI: {d['id']} thuộc tuần {d.get('week')} không có trong weeks.json"); sys.exit(1)
    prof = load(D("profile.json"))
    errors = []
    for d in days:
        if not os.path.exists(D("lessons", d["id"] + ".json")):
            errors.append(f"thiếu data/lessons/{d['id']}.json")
        if d.get("status") == "graded" and not os.path.exists(D("grades", d["id"] + ".json")):
            errors.append(f"{d['id']} status=graded nhưng thiếu data/grades/{d['id']}.json")
    for sub in ("lessons", "grades", "submissions", "keys"):
        for fn in os.listdir(D(sub)):
            if fn.endswith(".json"):
                load(D(sub, fn))  # raise nếu JSON hỏng
    if errors:
        print("LỖI:\n- " + "\n- ".join(errors)); sys.exit(1)

    # ---- Progress Log (sinh tự động)
    days_sorted = sorted(days, key=lambda d: (d.get("week", 0), d.get("order", 0)))
    graded = [d for d in days_sorted if d.get("status") == "graded"]
    L = []
    L.append("# PROGRESS LOG – Tân\n")
    L.append("> ⚠️ **File này được SINH TỰ ĐỘNG** từ `data/profile.json` + `data/weeks.json` + `data/lessons.json` bằng `python3 tools/sync.py`. Đừng sửa tay, hãy sửa file JSON.\n")
    L.append("## Trạng thái hiện tại")
    L.append(f"- Mục tiêu: {prof.get('goal','')}")
    L.append(f"- Trọng tâm: {prof.get('focus_now','')}")
    L.append(f"- Tuần: {prof.get('week','')} · Streak: {prof.get('streak',0)} ngày · Đã chấm: {len(graded)}/{len(days)} bài")
    L.append(f"- Mức hiểu mục tiêu: {prof.get('comprehension_target','')}")
    L.append(f"- Cập nhật hồ sơ: {prof.get('updatedAt','')}\n")
    L.append("## Learner model (hồ sơ – nguồn quyết định bài kế tiếp)")
    L.append("| Kỹ năng | CEFR ước lượng | Ghi chú |\n|---|---|---|")
    for k, name in [("overall","Tổng thể"),("listening","Nghe"),("reading","Đọc"),("vocab","Từ vựng"),("grammar","Ngữ pháp & từ nối")]:
        L.append(f"| {name} | {prof.get('cefr',{}).get(k) or '–'} | {prof.get('levels',{}).get(k,'')} |")
    L.append("")
    for key, title in [("strengths","Điểm mạnh"),("interests","Sở thích")]:
        items = prof.get(key) or []
        L.append(f"**{title}:** " + ("; ".join(items) if items else "chưa có"))
    L.append("\n**Cần cải thiện & kế hoạch:**")
    for w in prof.get("weaknesses") or []:
        if isinstance(w, str): L.append(f"- {w}")
        else: L.append(f"- [{w.get('area','')}] **{w.get('detail','')}** – dấu hiệu: {w.get('evidence','')} → {w.get('plan','')}")
    co = prof.get("coach") or {}
    if co:
        L.append(f"\n**Mục tiêu thời gian:** {co.get('weekly_target_hours','?')} giờ/tuần ({co.get('target_why','')})")
        if co.get("summary_md"): L.append(f"\n**Bức tranh hiện tại:** {co['summary_md']}")
        L.append("\n**Gia sư khuyên:**")
        for r in co.get("recommendations", []): L.append(f"- **{r.get('title','')}** – {r.get('how','')}")
    if prof.get("habits"): L.append(f"\n**Thói quen tiếp xúc tiếng Anh:** {prof['habits']}")
    if prof.get("teacher_md"): L.append(f"\n**Giáo viên nhận xét:**\n\n{prof['teacher_md']}")
    if prof.get("focus_md"): L.append(f"\n**Đang tập trung:** {prof['focus_md']}")
    L.append("\n### Nhật ký quyết định (vì sao bài lại như vậy)")
    L.append("| Ngày | Quyết định |\n|---|---|")
    for x in prof.get("decisions", []): L.append(f"| {x.get('date','')} | {x.get('text','')} |")
    L.append("\n## Checklist trình độ (data/levels.json + data/mastery.json)")
    L.append("| Level | ✅ Got it | 🌱 Learning | ⬜ Not yet | Chưa kiểm tra |\n|---|---|---|---|---|")
    for lv in levels:
        its = [i for sec in lv["sections"] for i in sec["items"] if not i.get("later")]
        st = [mastery.get("items", {}).get(i["id"], {}).get("tutor", "unknown") for i in its]
        L.append(f"| {lv['id']} | {st.count('got_it')}/{len(its)} | {st.count('learning')} | {st.count('not_yet')} | {st.count('unknown')} |")
    L.append("\n## Kế hoạch theo tuần")
    L.append("| Tuần | Ngày | Chủ đề | Trạng thái | Bài |\n|---|---|---|---|---|")
    for w in weeks:
        n = [d for d in days if d.get("week") == w["no"]]
        L.append(f"| {w['no']} | {w.get('start','')} → {w.get('end','')} | {w.get('theme','')} | {w.get('status','')} | {sum(1 for d in n if d.get('status')=='graded')}/{len(n)} đã chấm |")
    L.append("\n## Lịch sử bài học")
    L.append("| Tuần · Bài | Ngày làm | Bài | Trạng thái | Nghe | Đọc | Độ khó | Phút bài | Phút thêm | Nhận xét |\n|---|---|---|---|---|---|---|---|---|---|")
    for d in days_sorted:
        L.append(f"| T{d.get('week','')} · B{d.get('order','')} | {d.get('date') or '–'} | {d.get('title','')} | {d.get('status','')} | {pct(d.get('listenPct'))} | {pct(d.get('readPct'))} | {d.get('difficulty') or '–'} | {d.get('minutesActual') or '–'} | {d.get('extraMinutes') or '–'} | {d.get('note','')} |")
    st = prof.get("story") or {}
    if st:
        L.append(f"\n## Truyện dài kỳ: {st.get('title','')}")
        L.append(f"- Nhân vật: {st.get('characters','')}")
        L.append("- Đã có: " + "; ".join(st.get("episodes", [])))
    L.append("\n## Chunk Bank (gặp lại trong input mới theo lịch 1–3–7–14 ngày)")
    L.append("| Chunk | Nghĩa | Học | Gặp lại | Trạng thái |\n|---|---|---|---|---|")
    for c in prof.get("chunk_bank", []):
        L.append(f"| {c.get('chunk','')} | {c.get('meaning','')} | {c.get('learned','')} | {c.get('next','')} | {c.get('status','')} |")
    L.append("\n## Pronunciation (bản thu, tools/speech – chỉ khi Tân muốn)")
    pr = prof.get("pronunciation") or []
    if pr:
        L.append("| Ngày | Dễ nghe % | Khớp âm vị % | Từ/phút | Lỗi ưu tiên | Ngữ điệu |\n|---|---|---|---|---|---|")
        for p in pr: L.append(f"| {p.get('date','')} | {p.get('intelligibility','')} | {p.get('phoneme','')} | {p.get('wpm','')} | {p.get('issues','')} | {p.get('prosody','')} |")
    else:
        L.append("(chưa có)")
    L.append("\n## Thay đổi định hướng")
    for o in prof.get("orientation", []): L.append(f"- {o}")
    with open(os.path.join(ROOT, "tutor", "02_PROGRESS_LOG.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    # ---- Thư viện ôn tập (tab 🧠 Review): gom mọi thứ đã học từ data/ → data/library.json (sinh tự động)
    plan = {i: ds for w in weeks for ds, d in (w.get("days") or {}).items() for i in d.get("lessons", [])}
    lib = {"words": [], "grammar": [], "story": [], "mistakes": [], "generated": "auto – tools/sync.py"}
    seen = set()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from ipa import ipa as _ipa
    except Exception: _ipa = None
    changed = False
    for w in weeks:  # điền IPA (UK + US) cho word wall nếu thiếu – ghi thẳng vào weeks.json
        for x in w.get("words") or []:
            if _ipa and not x.get("ipa"): x["ipa"], x["ipa_us"] = _ipa(x["w"]), _ipa(x["w"], "us"); changed = True
    if changed:
        with open(D("weeks.json"), "w", encoding="utf-8") as f: json.dump({"weeks": weeks}, f, ensure_ascii=False, indent=1)
    for w in weeks:
        for x in w.get("words") or []:
            lib["words"].append({**x, "week": w["no"], "type": x.get("type", "word")}); seen.add(x["w"].lower())
    # kho Words (data/words.json): mọi từ/cụm/từ nối/phrasal verb/idiom đã dạy – có def, ex, vi, img, audio; IPA tự điền
    wp = D("words.json"); WJ = load(wp) if os.path.exists(wp) else {"words": []}; ch = False
    for x in WJ["words"]:
        if _ipa and not x.get("ipa"): x["ipa"], x["ipa_us"] = _ipa(x["w"]), _ipa(x["w"], "us"); ch = True
        if x["w"].lower() not in seen:
            lib["words"].append({k: v for k, v in x.items() if k != "prompt"}); seen.add(x["w"].lower())
    if ch:
        with open(wp, "w", encoding="utf-8") as f: json.dump(WJ, f, ensure_ascii=False, indent=1)
    lib["words"] = [w if os.path.exists(D("..", w["img"])) or not w.get("img") else {**w, "img": None} for w in lib["words"]]
    lib["words"] = [w if not w.get("audio") or os.path.exists(D("..", w["audio"])) else {**w, "audio": None} for w in lib["words"]]
    gp_ = D("grammar.json"); lib["grammar"] = load(gp_)["grammar"] if os.path.exists(gp_) else []
    for d in days_sorted:
        try: body = load(D("lessons", d["id"] + ".json"))
        except Exception: continue
        for pi, p in enumerate(body.get("parts", [])):
            ref = {"lesson": d["id"], "part": pi, "week": d.get("week"), "order": d.get("order"), "date": plan.get(d["id"], d.get("date")), "status": d.get("status")}
            if "Hope Street" in (p.get("title") or ""): lib["story"].append({**ref, "title": p.get("title", "")})
        gp = D("grades", d["id"] + ".json")
        if os.path.exists(gp):
            for c in load(gp).get("cards") or []: lib["mistakes"].append({**c, "lesson": d["id"], "date": d.get("date")})
    with open(D("library.json"), "w", encoding="utf-8") as f:
        json.dump(lib, f, ensure_ascii=False, indent=1)

    # ---- Danh sách file xuất bản kèm web (không có keys/)
    files = {f"data/{n}": f"data/{n}" for n in ("weeks.json", "lessons.json", "profile.json", "resources.json", "levels.json", "mastery.json", "library.json", "studylog.json")}
    for fn in sorted(os.listdir(D("vocab"))):
        if fn.endswith(".json"): files[f"data/vocab/{fn}"] = f"data/vocab/{fn}"
    for sub in ("lessons", "grades", "submissions"):
        for fn in sorted(os.listdir(D(sub))):
            if fn.endswith(".json"):
                files[f"data/{sub}/{fn}"] = f"data/{sub}/{fn}"
    for sub, exts in (("audio", (".mp3",)), ("img", (".webp", ".jpg", ".png", ".svg"))):
        for dp, _, fns in os.walk(D(sub)):
            for fn in sorted(fns):
                if fn.endswith(exts):
                    rel = os.path.relpath(os.path.join(dp, fn), ROOT)
                    files[rel] = rel
    with open(os.path.join(ROOT, "web", "publish_files.json"), "w", encoding="utf-8") as f:
        json.dump(files, f, ensure_ascii=False, indent=1)
    print(f"OK – {len(weeks)} tuần, {len(days)} bài, {len(graded)} đã chấm. Progress Log đã sinh lại. {len(files)} file cần xuất bản (web/publish_files.json).")

if __name__ == "__main__":
    build_studylog()
    main()
    # Tự soát sổ gia sư (Tân 12/11: "đây là cuốn sổ của bạn, phải tự biết cần thêm gì")
    import subprocess
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "check.py")])
