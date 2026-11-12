#!/usr/bin/env python3
"""Vẽ minh hoạ bằng FLUX.1 Schnell trên Cloudflare Workers AI (~2 giây/ảnh, free 10.000 neuron/ngày ≈ 170 ảnh;
token do proxy gắn vào api.cloudflare.com, account id ở data/profile.json → image_gen.cf_account).

  python3 tools/flux.py "<mô tả cảnh>" data/img/w2/l1-cover.webp [-n 3] [--cast nam,linh]
  python3 tools/flux.py --batch jobs.json [-j 4]  # {"data/img/w2/x.webp": {"scene": "...", "cast": ["nam"], "n": 2}, ...}

- Tự thêm STYLE chung + mô tả nhân vật cố định (data/flux_cast.json) để ảnh đồng bộ giữa các tuần.
- n > 1: lưu thêm biến thể x.v2.webp, x.v3.webp… → gia sư (Opus) XEM từng ảnh, chọn bản đúng nghĩa nhất,
  đổi tên bản chọn thành x.webp và xoá các bản còn lại.
- Ảnh lưu WebP 768×576 (cắt 4:3 từ ảnh vuông). Thất bại → exit code 2: dùng dự phòng SVG (Sonnet cho bìa/cảnh, Haiku cho thẻ từ).
- Câu lệnh chỉ mô tả cảnh – KHÔNG đưa tên thật/thông tin cá nhân của Tân vào prompt.
"""
import base64, io, json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLE = ("Flat vector illustration, children's book style, soft warm colors, clean simple shapes, "
         "friendly expressive faces, no text, no letters, no watermark, wide landscape composition with the main "
         "subjects in the centre. ")
CF = json.load(open(os.path.join(ROOT, 'data', 'profile.json'))).get('image_gen', {})


def cast_text(names):
    if not names:
        return ''
    cast = json.load(open(os.path.join(ROOT, 'data', 'flux_cast.json')))
    return ' '.join(cast[n] for n in names if n in cast) + ' '


def save_webp(raw, path, w=768, h=576):
    from PIL import Image
    im = Image.open(io.BytesIO(raw)).convert('RGB')
    W, H = im.size
    if W / H > w / h:   # quá rộng → cắt 2 bên
        nw = int(H * w / h); im = im.crop(((W - nw) // 2, 0, (W - nw) // 2 + nw, H))
    else:               # quá cao → cắt trên/dưới (giữ phần giữa, lệch lên chút để không mất đầu)
        nh = int(W * h / w); top = int((H - nh) * .4); im = im.crop((0, top, W, top + nh))
    im.resize((w, h), Image.LANCZOS).save(path, 'WEBP', quality=82)


def cloudflare(prompt, out, n, seed=None, steps=6):
    if not CF.get('cf_account'):
        return []
    url = (f"https://api.cloudflare.com/client/v4/accounts/{CF['cf_account']}/ai/run/"
           f"{CF.get('cf_model', '@cf/black-forest-labs/flux-1-schnell')}")
    base, ext = os.path.splitext(out)
    saved, t0 = [], time.time()
    for i in range(n):
        body = {'prompt': prompt[:2000], 'steps': steps}
        if seed is not None:
            body['seed'] = int(seed) + i
        r = subprocess.run(['curl', '-sS', '-m', '90', url, '-H', 'Authorization: Bearer proxy-injected',
                            '-H', 'Content-Type: application/json', '-d', json.dumps(body)],
                           capture_output=True, text=True).stdout
        try:
            d = json.loads(r)
        except ValueError:
            d = {'errors': [r[:200]]}
        if not d.get('success'):
            print('✗ Cloudflare:', d.get('errors'), file=sys.stderr)
            break
        path = out if i == 0 else f'{base}.v{i + 1}{ext}'
        os.makedirs(os.path.dirname(os.path.abspath(path)) or '.', exist_ok=True)
        save_webp(base64.b64decode(d['result']['image']), path)
        saved.append(path)
    if saved:
        print(f'✓ {len(saved)} ảnh (Cloudflare, {round(time.time() - t0)}s):', ' '.join(saved))
    return saved


def generate(scene, out, n=1, cast=None, seed=None):
    return cloudflare(STYLE + cast_text(cast) + scene, out, n, seed)


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
