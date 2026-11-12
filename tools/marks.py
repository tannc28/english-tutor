#!/usr/bin/env python3
"""Mốc thời gian từng đoạn (marks) cho phần nghe → web cho bấm nghe lại đúng đoạn trong transcript.

  python3 tools/marks.py <lessonId>…   |   --all

- Bài TTS (audio.py): đã có marks ước lượng → "bắt" vào khoảng lặng gần nhất trong MP3 (giữa các dòng có ~0,7 s im lặng).
- Bài nghe thật (VOA, keep_audio): chia thời lượng theo số ký tự từng đoạn lời → bắt vào khoảng lặng gần nhất (±2,5 s).
Ghi p["marks"] = [giây bắt đầu của từng dòng listen].
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def duration(f):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f],
                       capture_output=True, text=True).stdout
    return float(r or 0)


def silence_ends(f, db=-38, d=0.25):
    r = subprocess.run(['ffmpeg', '-i', f, '-af', f'silencedetect=n={db}dB:d={d}', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r)]


def snap(t, ends, win):
    c = [e for e in ends if abs(e - t) <= win]
    return min(c, key=lambda e: abs(e - t)) if c else t


def fix(lid):
    path = os.path.join(ROOT, 'data', 'lessons', lid + '.json')
    L = json.load(open(path))
    changed = False
    for pi, p in enumerate(L.get('parts', [])):
        lines = p.get('listen') or []
        a = p.get('audio')
        if len(lines) < 2 or not a or not os.path.exists(os.path.join(ROOT, a)):
            continue
        f = os.path.join(ROOT, a)
        dur, ends = duration(f), silence_ends(f)
        if not p.get('keep_audio'):
            # TTS: giữa các dòng có đúng ~0,7 s im lặng → khoảng lặng dài ≥0,6 s chính là ranh giới dòng
            gaps = [e for e in silence_ends(f, -45, 0.6) if e < dur - 0.3]
            if len(gaps) == len(lines) - 1:
                p['marks'] = [0.0] + [round(max(0, e - 0.1), 2) for e in gaps]
                changed = True
                print(f'{lid} part {pi + 1}: {len(lines)} marks (exact, dur {dur:.1f}s)')
                continue
        n = [max(1, len(str(x.get('text', '')))) for x in lines]
        tot, acc, est = sum(n), 0, []
        for k in n:
            est.append(dur * acc / tot); acc += k
        if not p.get('keep_audio') and p.get('marks') and len(p['marks']) == len(lines):
            est = p['marks']
        marks, last = [0.0], 0.0
        for t in est[1:]:
            s = round(max(last + 0.3, snap(t, ends, 2.5)), 2)
            marks.append(s); last = s
        p['marks'] = marks
        changed = True
        print(f'{lid} part {pi + 1}: {len(marks)} marks (dur {dur:.1f}s)')
    if changed:
        json.dump(L, open(path, 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    ids = sys.argv[1:]
    if ids == ['--all']:
        ids = [f[:-5] for f in sorted(os.listdir(os.path.join(ROOT, 'data', 'lessons'))) if f.endswith('.json')]
    for i in ids:
        fix(i)
