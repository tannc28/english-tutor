#!/usr/bin/env python3
"""Vẽ minh hoạ bằng FLUX.1 Schnell qua AI Horde (mạng GPU tình nguyện, miễn phí, không cần key).

  python3 tools/flux.py "<mô tả cảnh>" data/img/w2/l1-cover.webp [-n 3] [--cast nam,linh]
  python3 tools/flux.py --batch jobs.json [-j 4]  # {"data/img/w2/x.webp": {"scene": "...", "cast": ["nam"], "n": 2}, ...}

- Tự thêm STYLE chung + mô tả nhân vật cố định (data/flux_cast.json) để ảnh đồng bộ giữa các tuần.
- n > 1: lưu thêm biến thể x.v2.webp, x.v3.webp… → gia sư (Opus) XEM từng ảnh, chọn bản đúng nghĩa nhất,
  đổi tên bản chọn thành x.webp và xoá các bản còn lại.
- Thất bại (hết giờ chờ, Horde lỗi) → exit code 2: dùng dự phòng SVG (Sonnet cho bìa/cảnh, Haiku cho thẻ từ).
- Câu lệnh chỉ mô tả cảnh – KHÔNG đưa tên thật/thông tin cá nhân của Tân vào prompt.
"""
import json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://aihorde.net/api/v2'
MODEL = 'Flux.1-Schnell fp8 (Compact)'
STYLE = ("Flat vector illustration, children's book style, soft warm colors, clean simple shapes, "
         "friendly expressive faces, no text, no letters, no watermark. ")
HDR = ['-H', 'apikey: ' + os.environ.get('HORDE_API_KEY', '0000000000'), '-H', 'Content-Type: application/json',
       '-H', 'Client-Agent: english-tutor-illustrations:1:anon']


def api(method, path, body=None):
    a = ['curl', '-sS', '-m', '60', '-X', method, API + path] + HDR
    if body is not None:
        a += ['-d', json.dumps(body)]
    out = subprocess.run(a, capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except ValueError:
        return {'message': out[:300] or 'không có phản hồi'}


def cast_text(names):
    if not names:
        return ''
    cast = json.load(open(os.path.join(ROOT, 'data', 'flux_cast.json')))
    return ' '.join(cast[n] for n in names if n in cast) + ' '


def generate(scene, out, n=1, cast=None, w=768, h=576, wait=600, seed=None):
    prompt = STYLE + cast_text(cast) + scene
    params = {'width': w, 'height': h, 'steps': 4, 'cfg_scale': 1, 'sampler_name': 'k_euler', 'n': n}
    if seed is not None:
        params['seed'] = str(seed)
    job = api('POST', '/generate/async', {'prompt': prompt, 'params': params, 'models': [MODEL],
                                          'nsfw': False, 'censor_nsfw': True, 'r2': True})
    if 'id' not in job:
        print('✗ Horde từ chối:', job.get('message'), file=sys.stderr)
        return []
    t0 = time.time()
    while True:
        s = api('GET', '/generate/check/' + job['id'])
        if s.get('done'):
            break
        if s.get('faulted') or s.get('is_possible') is False or time.time() - t0 > wait:
            print('✗ Horde không xong:', s, file=sys.stderr)
            return []
        print(f"  … chờ ~{s.get('wait_time')}s, hàng đợi {s.get('queue_position')}", flush=True)
        time.sleep(10)
    gens = api('GET', '/generate/status/' + job['id']).get('generations', [])
    os.makedirs(os.path.dirname(os.path.abspath(out)) or '.', exist_ok=True)
    base, ext = os.path.splitext(out)
    saved = []
    for i, g in enumerate(gens):
        if g.get('censored'):
            continue
        path = out if i == 0 else f'{base}.v{i + 1}{ext}'
        subprocess.run(['curl', '-sS', '-m', '120', '-o', path, g['img']], check=False)
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            saved.append(path)
    print(f'✓ {len(saved)} ảnh sau {round(time.time() - t0)}s:', ' '.join(saved))
    return saved


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(1)
    if a[0] == '--batch':
        from concurrent.futures import ThreadPoolExecutor
        jobs = json.load(open(a[1]))
        par = int(a[a.index('-j') + 1]) if '-j' in a else 4   # số ảnh gửi song song
        with ThreadPoolExecutor(par) as ex:
            res = dict(zip(jobs, ex.map(lambda kv: generate(kv[1]['scene'], kv[0], kv[1].get('n', 1), kv[1].get('cast'),
                                                            seed=kv[1].get('seed')), jobs.items())))
        fails = [p for p, r in res.items() if not r]
        if fails:
            print('✗ cần dự phòng SVG:', ' '.join(fails), file=sys.stderr)
            sys.exit(2)
    else:
        n, cast = 1, None
        if '-n' in a:
            n = int(a[a.index('-n') + 1])
        if '--cast' in a:
            cast = a[a.index('--cast') + 1].split(',')
        sys.exit(0 if generate(a[0], a[1], n, cast) else 2)
