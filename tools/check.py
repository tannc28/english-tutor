#!/usr/bin/env python3
"""Tự soát "cuốn sổ" của gia sư – những việc hay quên sau khi chấm / soạn bài.

  python3 tools/check.py          # in danh sách ❌ lỗi phải sửa + ⚠️ nên xem
  python3 tools/check.py --hook   # dùng cho Stop hook: có ❌ → exit 2 (Claude phải làm nốt trước khi dừng)

Gọi tự động: cuối tools/sync.py và Stop hook trong .claude/settings.json.
Thêm luật mới vào đây mỗi khi Tân góp ý một điều "đáng lẽ gia sư phải tự biết".
"""
import json, os, re, sys, glob, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, 'data', *p)
J = lambda p: json.load(open(p))
TZ = dt.timezone(dt.timedelta(hours=7))
TODAY = dt.datetime.now(TZ).date().isoformat()

# Cụm từ cũ đã bỏ – không được còn trong phần Progress (Tân 12/11)
STALE = ['0.85', '🎧 Listen', 'TikTok', '📅 Plan', 'Plan picks', 'nghe tự do (tab', 'nghe kèm lời trước']

err, warn = [], []


def ts(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except Exception:
        return None


def main():
    P = J(D('profile.json'))
    L = {l['id']: l for l in J(D('lessons.json'))['lessons']}
    W = J(D('weeks.json'))['weeks']
    M = J(D('mastery.json'))

    # 1) Chấm xong phải cập nhật bài + Progress
    grades = {os.path.basename(f)[:-5]: J(f) for f in glob.glob(D('grades', '*.json'))}
    p_upd = ts(P.get('updatedAt'))
    last = None
    for gid, g in grades.items():
        t = ts(g.get('gradedAt'))
        if t and (not last or t > last[1]):
            last = (gid, t)
        if gid in L and L[gid].get('status') != 'graded':
            err.append(f'lessons.json: {gid} đã có grade nhưng status chưa "graded"')
        if gid in L and L[gid].get('strain') is None and not L[gid].get('micro'):
            warn.append(f'lessons.json: {gid} thiếu strain/chỉ số sau khi chấm')
        if not os.path.exists(D('submissions', gid + '.json')):
            err.append(f'thiếu bản chép data/submissions/{gid}.json')
        sub = J(D('submissions', gid + '.json')) if os.path.exists(D('submissions', gid + '.json')) else {}
        if any((r or {}).get('reads') for r in ((sub.get('log') or {}).get('read') or {}).values()):
            txt = json.dumps(g, ensure_ascii=False)
            if 'wpm' not in txt:
                warn.append(f'grades/{gid}: có số đo đọc (log.read) nhưng nhận xét chưa nêu – Tân 12/11: nói rõ đọc bao lâu, mấy lượt, tốc độ wpm so với mốc')
        if (sub.get('log') or {}).get('asks') and not g.get('asks_md'):
            err.append(f'grades/{gid}: Tân hỏi qua nút 💬 Ask ({len(sub["log"]["asks"])} câu) nhưng grade chưa có asks_md trả lời')
        if not (L.get(gid, {}).get('micro')) and not g.get('tg'):
            warn.append(f'grades/{gid}: thiếu tg (tin Telegram)')
    if last and p_upd and last[1] > p_upd:
        err.append(f'Progress chưa cập nhật sau khi chấm {last[0]}: profile.updatedAt ({P.get("updatedAt")}) cũ hơn grade – '
                   'cập nhật cefr/levels, teacher_md, focus_md, coach, weaknesses, strengths, streak rồi đổi updatedAt')
    if last and str(M.get('updated', '')) < last[1].astimezone(TZ).date().isoformat():
        warn.append(f'mastery.json "updated" ({M.get("updated")}) cũ hơn lần chấm {last[0]} – đã xét checklist chưa?')

    # 1b) Dự báo C1 cụ thể cho Tân (Tân 12/11: phải nói rõ còn bao nhiêu giờ, tiêu chuẩn, ngày dự kiến) – đo lại sau mỗi lần chấm
    fc = P.get('forecast') or {}
    if not fc.get('skills') or not fc.get('phases'):
        err.append('profile.forecast thiếu skills/phases – tab Progress cần "Your road to C1" cụ thể (giờ còn thiếu, tiêu chuẩn, mốc)')
    elif last and str(fc.get('updated', '')) < last[1].astimezone(TZ).date().isoformat():
        warn.append(f'profile.forecast.updated ({fc.get("updated")}) cũ hơn lần chấm {last[0]} – cập nhật "You now/evidence/gap" theo số đo mới')

    # 2) Không còn lời khuyên/kế hoạch đã bỏ trong Progress
    blob = json.dumps({k: P.get(k) for k in ('coach', 'focus_md', 'teacher_md', 'weaknesses', 'focus_now', 'schedule')}, ensure_ascii=False)
    for s in STALE:
        if s in blob:
            err.append(f'profile (tab Progress) còn nội dung cũ: "{s}" – viết lại theo phương pháp hiện tại')

    # 3) Ngày học từ hôm nay trở đi: bài nhỏ, đủ đọc + nghe, đủ thời lượng, có file
    for w in W:
        for ds, d in sorted((w.get('days') or {}).items()):
            if ds < TODAY or d.get('off'):
                continue
            ls = [L[i] for i in d.get('lessons', []) if i in L]
            miss = [i for i in d.get('lessons', []) if i not in L]
            if miss:
                err.append(f'{ds}: lessons.json không có {miss}')
            if not ls:
                continue
            if not all(l.get('micro') for l in ls):
                (err if ds == TODAY else warn).append(f'{ds}: còn bài khung cũ (chưa chia bài nhỏ): {[l["id"] for l in ls if not l.get("micro")]}')
                continue
            kinds = {l.get('kind') for l in ls}
            if 'Reading' not in kinds or 'Listening' not in kinds:
                err.append(f'{ds}: phải có cả 📖 Reading lẫn 🎧 Listening (đang có {sorted(kinds)})')
            mins = sum(int(l.get('minutes') or 0) for l in ls)
            if mins < 90:
                warn.append(f'{ds}: tổng ~{mins} phút – Tân muốn ~2–3 giờ/ngày')
            for l in ls:
                if len(l.get('title', '')) > 48:
                    warn.append(f'{l["id"]}: tên bài dài ({len(l["title"])} ký tự) – nên 3–6 từ')
                if int(l.get('minutes') or 0) > 25 and l.get('kind') == 'Listening':
                    warn.append(f'{l["id"]}: bài nghe {l["minutes"]}′ > 25′')
                f = D('lessons', l['id'] + '.json')
                if not os.path.exists(f):
                    err.append(f'thiếu data/lessons/{l["id"]}.json')
                    continue
                body = J(f)
                qn = 0
                for p in body.get('parts', []):
                    if p.get('transcript_open'):
                        err.append(f'{l["id"]}: transcript_open – lời phải ẩn mặc định để luyện tai')
                    if p.get('listen') and not p.get('keep_audio') and l.get('status') != 'graded':
                        longl = [i for i, x in enumerate(p['listen']) if len(str(x.get('text', ''))) > 160]
                        if longl:
                            warn.append(f'{l["id"]}: dòng nghe {longl} dài >160 ký tự – Tân 13/11: mỗi dòng 1 câu để bấm nghe lại đúng câu')
                    if p.get('listen'):
                        if not p.get('audio') or not os.path.exists(os.path.join(ROOT, p['audio'])):
                            err.append(f'{l["id"]}: phần nghe chưa có audio (tools/audio.py)')
                        elif len(p.get('marks') or []) != len(p['listen']):
                            err.append(f'{l["id"]}: thiếu/lệch marks (tools/marks.py) – không bấm nghe lại từng dòng được')
                    qn += len([q for q in p.get('questions', []) if not q.get('check') and q['id'] not in ('u1', 't', 'ask')])
                inp = [p for p in body.get('parts', []) if (p.get('listen') and sum(len(str(x.get('text', ''))) for x in p['listen']) >= 400) or (not p.get('listen') and re.search(r'(^|\n)>\s', p.get('md', '')))]
                if not inp and not l['id'].startswith('w1-voa') and l.get('status') != 'graded':
                    warn.append(f'{l["id"]}: không có input thật (đoạn đọc ">" hoặc bài nghe ≥400 ký tự) – Tân 13/11: bài chỉ Learn là thừa, gộp vào bài nghe/đọc thật')
                if qn > 1:
                    warn.append(f'{l["id"]}: {qn} câu hỏi tự luận – chỉ % hiểu + Ask me là tự luận; còn lại là câu chọn có đáp án ngay')
                nc = len([q for p in body.get('parts', []) for q in p.get('questions', []) if q.get('check')])
                lim = 3 if l.get('kind') == 'Reading' else 2
                if l.get('status') != 'graded' and (nc == 0 or nc > lim + 1):
                    warn.append(f'{l["id"]}: {nc} câu check – Tân 13/11: bài đọc ~3 câu ngắn, bài nghe 1–2 câu (chọn, có đáp án ngay)')
                if l.get('cover') and not os.path.exists(os.path.join(ROOT, l['cover'])):
                    err.append(f'{l["id"]}: ảnh bìa không tồn tại {l["cover"]}')

    # 3b) Giao diện: sửa web/index.html thì phải chạy tools/ui_check.js (Tân 13/11: bố cục chướng mắt, khoảng trống – phải tự biết)
    wi, ok = os.path.join(ROOT, 'web', 'index.html'), os.path.join(ROOT, 'web', '.ui_ok')
    if not os.path.exists(ok) or os.path.getmtime(wi) > os.path.getmtime(ok) + 1:
        err.append('web/index.html đã đổi nhưng chưa qua `node tools/ui_check.js` (mồ côi, tràn ngang, khoảng trống) – chạy rồi xem ảnh cả desktop lẫn điện thoại')

    # 4) Từ mới phải đủ để vào thư viện Review
    for x in J(D('words.json')).get('words', []):
        if not x.get('def') or not x.get('ex'):
            err.append(f'words.json: "{x.get("w")}" thiếu def/ex')
        if x.get('img') and not os.path.exists(os.path.join(ROOT, x['img'])):
            warn.append(f'words.json: "{x.get("w")}" ảnh không tồn tại')

    return err, warn


if __name__ == '__main__':
    e, w = main()
    for x in e:
        print('❌', x, file=sys.stderr if '--hook' in sys.argv else sys.stdout)
    for x in w:
        print('⚠️ ', x, file=sys.stderr if '--hook' in sys.argv else sys.stdout)
    if not e and not w:
        print('✅ check: sổ gia sư đầy đủ')
    if '--hook' in sys.argv and e:
        print('\n→ Sổ gia sư còn việc chưa làm (tools/check.py). Làm nốt rồi sync + commit + publish trước khi dừng.', file=sys.stderr)
        sys.exit(2)
