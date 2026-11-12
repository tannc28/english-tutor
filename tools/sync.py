#!/usr/bin/env python3
"""Đồng bộ: repo (data/) → các bản hiển thị.

Nguồn dữ liệu DUY NHẤT là thư mục data/:
  data/days.json           danh sách ngày học + chỉ số mỗi ngày (listenPct, readPct, difficulty, minutesActual, note, status)
  data/profile.json        hồ sơ học sinh (Learner model, nhật ký quyết định, chunk bank, phát âm…)
  data/lessons/<id>.json   nội dung bài
  data/grades/<id>.json    kết quả chấm
  data/submissions/<id>.json  bài làm của Tân (chép từ web khi chấm)
  data/keys/<id>.json      đáp án (KHÔNG xuất bản lên web)

Script này:
  1. Kiểm tra JSON hợp lệ và days.json trỏ tới file bài có thật.
  2. Sinh lại tutor/02_PROGRESS_LOG.md từ profile.json + days.json (đừng sửa tay file đó).
  3. In ra danh sách file cần xuất bản kèm web (map `files` cho Artifact publish) → web/publish_files.json

Dùng: python3 tools/sync.py   (rồi publish web/index.html với files trong web/publish_files.json)
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, "data", *p)

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def pct(v):
    return "–" if v in (None, "") else f"{round(float(v))}%"

def main():
    days = load(D("days.json"))["days"]
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
    days_sorted = sorted(days, key=lambda d: d["date"])
    graded = [d for d in days_sorted if d.get("status") == "graded"]
    L = []
    L.append("# PROGRESS LOG – Tân\n")
    L.append("> ⚠️ **File này được SINH TỰ ĐỘNG** từ `data/profile.json` + `data/days.json` bằng `python3 tools/sync.py`. Đừng sửa tay, hãy sửa file JSON.\n")
    L.append("## Trạng thái hiện tại")
    L.append(f"- Mục tiêu: {prof.get('goal','')}")
    L.append(f"- Trọng tâm: {prof.get('focus_now','')}")
    L.append(f"- Tuần: {prof.get('week','')} · Streak: {prof.get('streak',0)} ngày · Đã chấm: {len(graded)}/{len(days)} ngày")
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
    L.append("\n## Lịch sử ngày học")
    L.append("| Ngày | Bài | Trạng thái | Nghe | Đọc | Độ khó | Phút bài | Phút thêm | Nhận xét |\n|---|---|---|---|---|---|---|---|---|")
    for d in days_sorted:
        L.append(f"| N{d.get('dayNo','')} · {d['date']} | {d.get('title','')} | {d.get('status','')} | {pct(d.get('listenPct'))} | {pct(d.get('readPct'))} | {d.get('difficulty') or '–'} | {d.get('minutesActual') or '–'} | {d.get('extraMinutes') or '–'} | {d.get('note','')} |")
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

    # ---- Danh sách file xuất bản kèm web (không có keys/)
    files = {"data/days.json": "data/days.json", "data/profile.json": "data/profile.json", "data/resources.json": "data/resources.json", "data/plan.json": "data/plan.json"}
    for sub in ("lessons", "grades", "submissions"):
        for fn in sorted(os.listdir(D(sub))):
            if fn.endswith(".json"):
                files[f"data/{sub}/{fn}"] = f"data/{sub}/{fn}"
    adir = D("audio")
    if os.path.isdir(adir):
        for lid in sorted(os.listdir(adir)):
            for fn in sorted(os.listdir(os.path.join(adir, lid))):
                if fn.endswith(".mp3"): files[f"data/audio/{lid}/{fn}"] = f"data/audio/{lid}/{fn}"
    with open(os.path.join(ROOT, "web", "publish_files.json"), "w", encoding="utf-8") as f:
        json.dump(files, f, ensure_ascii=False, indent=1)
    print(f"OK – {len(days)} ngày, {len(graded)} đã chấm. Progress Log đã sinh lại. {len(files)} file cần xuất bản (web/publish_files.json).")

if __name__ == "__main__":
    main()
