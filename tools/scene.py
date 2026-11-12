#!/usr/bin/env python3
"""Scene kit: ghép ảnh SVG từ spec JSON ngắn (thay vì để model vẽ cả file SVG).

  python3 tools/scene.py spec.json out.svg         # 1 cảnh
  python3 tools/scene.py --batch specs.json        # {"data/img/w1/x.svg": spec, ...}
  python3 tools/scene.py --list                    # liệt kê nền, nhân vật, thân, mặt, đạo cụ

Spec (canvas 384x288):
{"bg": "street",                       # data/kit/bg/<bg>.svg
 "fx": ["rain"],                       # hiệu ứng phủ: rain | night | glow:x,y[,r]
 "chars": [{"cast": "nam",             # data/kit/cast.json (tóc, da, màu áo cố định)
            "body": "standing/WalkingColorTee",   # hoặc effigy/Coffee (nửa người), sitting/...
            "face": "Smile", "x": 190, "y": 262, "h": 190, "flip": false}],
 "props": [{"icon": "closed-umbrella", "x": 120, "y": 200, "size": 40, "rot": 0, "front": true}],
 "svg": "<rect .../>",                 # tuỳ chọn: chèn thêm hình thô (bàn, chữ...)
 "bubble": {"text": "Hi!", "x": 230, "y": 60}}

Nhân vật: Open Peeps (Pablo Stanley, CC0). Đạo cụ: Fluent Emoji Flat (Microsoft, MIT),
lưu sẵn trong data/kit/props.json; icon mới lấy từ npm @iconify-json/fluent-emoji-flat
(nếu đã cài trong tools/node_modules hoặc NODE_PATH) rồi tự lưu vào props.json.
"""
import json, os, re, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(ROOT, 'data', 'kit')
W, H = 384, 288
_peeps = None


def peeps():
    global _peeps
    if _peeps is None:
        _peeps = json.load(open(os.path.join(KIT, 'peeps.json')))
    return _peeps


def load(name, default):
    p = os.path.join(KIT, name)
    return json.load(open(p)) if os.path.exists(p) else default


def fill(key, colors):
    part = peeps()['parts'][key]
    vals = dict(part['def'])
    vals.update({k: v for k, v in colors.items() if v})
    s = part['svg']
    s = re.sub(r'(?<!\{)\{(\w+)\}(?!\})', lambda m: vals.get(m.group(1), '#ccc'), s)
    return s.replace('{{', '{').replace('}}', '}')


# Vị trí các mảnh đầu so với đỉnh cổ (theo Effigy của @opeepsfun/open-peeps)
HAIR, FACE, BEARD, ACC = (-265, -449), (-76, -273), (-112, -121), (-188, -218)
TOP = -560  # đỉnh tóc xấp xỉ so với cổ


def character(c, cast):
    who = dict(cast.get(c.get('cast', ''), {}))
    who.update({k: v for k, v in c.items() if k in ('head', 'beard', 'acc', 'colors', 'face')})
    colors = dict(who.get('colors', {}))
    body = c.get('body', who.get('body', 'standing/ShirtColorTee'))
    bkey = 'body/' + body
    P = peeps()['parts']
    if bkey not in P:
        raise SystemExit(f'không có thân "{body}" (xem --list)')
    nx, ny = P[bkey].get('neck', [460, 0])
    bh = float(P[bkey]['vb'].split()[3])
    full_h = (bh - ny) - TOP
    if body.startswith('effigy/'):
        full_h = 1130  # nửa người: chiều cao khung bust (cổ cách đỉnh 429)
    s = c.get('h', 190) / full_h
    head = who.get('head', 'ShortOne')
    ax, ay = peeps()['hair_adj'].get(head, [0, 0])
    g = [f'<g transform="translate({-nx} {-ny})">{fill(bkey, colors)}</g>',
         f'<g transform="translate({HAIR[0] + ax} {HAIR[1] + ay})">{fill("head/" + head, colors)}</g>',
         f'<g transform="translate({FACE[0]} {FACE[1]})">{fill("face/" + who.get("face", "Smile"), colors)}</g>']
    if who.get('beard'):
        g.append(f'<g transform="translate({BEARD[0]} {BEARD[1]})">{fill("beard/" + who["beard"], colors)}</g>')
    if who.get('acc'):
        g.append(f'<g transform="translate({ACC[0]} {ACC[1]})">{fill("accessory/" + who["acc"], colors)}</g>')
    x, y = c.get('x', 192), c.get('y', 262)
    top = y - c.get('h', 190)  # vị trí đỉnh đầu
    neck_y = top - TOP * s if not body.startswith("effigy/") else top + 429 * s
    flip = -1 if c.get('flip') else 1
    shadow = '' if body.startswith('effigy/') or c.get('noshadow') else \
        f'<ellipse cx="{x}" cy="{y}" rx="{c.get("h", 190) * .2:.1f}" ry="{c.get("h", 190) * .025:.1f}" fill="#000" opacity=".12"/>'
    return shadow + f'<g transform="translate({x} {neck_y:.1f}) scale({flip * s:.5f} {s:.5f})">' + ''.join(g) + '</g>'


def icon(name):
    props = load('props.json', {})
    if name in props:
        return props[name]
    for base in [os.path.join(ROOT, 'tools', 'node_modules'), *os.environ.get('NODE_PATH', '').split(':')]:
        p = os.path.join(base, '@iconify-json', 'fluent-emoji-flat', 'icons.json')
        if base and os.path.exists(p):
            d = json.load(open(p))
            if name in d['icons']:
                ic = d['icons'][name]
                props[name] = {'body': ic['body'], 'w': ic.get('width', d.get('width', 32)),
                               'h': ic.get('height', d.get('height', 32))}
                json.dump(props, open(os.path.join(KIT, 'props.json'), 'w'), indent=0, sort_keys=True)
                return props[name]
            raise SystemExit(f'không có icon "{name}" trong fluent-emoji-flat')
    raise SystemExit(f'icon "{name}" chưa có trong data/kit/props.json; cài: cd tools && npm i @iconify-json/fluent-emoji-flat')


def prop(p):
    ic = icon(p['icon'])
    sz = p.get('size', 40)
    sc = sz / max(ic['w'], ic['h'])
    rot = f' rotate({p["rot"]})' if p.get('rot') else ''
    fl = ' scale(-1 1)' if p.get('flip') else ''
    return (f'<g transform="translate({p["x"]} {p["y"]}){rot}{fl} scale({sc:.4f}) '
            f'translate({-ic["w"] / 2} {-ic["h"] / 2})">{ic["body"]}</g>')


def fx(kind):
    if kind == 'rain':
        lines = ''.join(f'<path d="M{(i * 37) % 384} {(i * 53) % 280}l-5 14"/>' for i in range(70))
        return f'<g stroke="#FFFFFF" stroke-width="1.3" opacity=".55" stroke-linecap="round">{lines}</g>'
    if kind == 'night':
        return '<rect width="384" height="288" fill="#1B2140" opacity=".35"/>'
    if kind.startswith('glow:'):
        x, y, *r = kind[5:].split(',')
        return f'<circle cx="{x}" cy="{y}" r="{r[0] if r else 30}" fill="#FFE7A0" opacity=".35"/>'
    return ''


def bubble(b):
    t = html.escape(b['text'])
    w = max(28, 7 * len(b['text']) + 16)
    x, y = b['x'], b['y']
    tail = b.get('tail', [x - w / 2 + 14, y + 26])
    return (f'<g><path d="M{x - w / 2 + 8} {y + 14}L{tail[0]} {tail[1]}L{x - w / 2 + 22} {y + 14}Z" fill="#fff" stroke="#333" stroke-width="1.2"/>'
            f'<rect x="{x - w / 2}" y="{y - 14}" width="{w}" height="28" rx="12" fill="#fff" stroke="#333" stroke-width="1.2"/>'
            f'<rect x="{x - w / 2 + 6}" y="{y + 10}" width="22" height="6" fill="#fff"/>'
            f'<text x="{x}" y="{y + 5}" font-family="Comic Sans MS,Segoe Print,sans-serif" font-size="13" text-anchor="middle" fill="#222">{t}</text></g>')


def render(spec):
    cast = load('cast.json', {})
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">']
    if spec.get('bg'):
        out.append(open(os.path.join(KIT, 'bg', spec['bg'] + '.svg')).read())
    if spec.get('svg_back'):
        out.append(spec['svg_back'])
    out += [prop(p) for p in spec.get('props', []) if not p.get('front')]
    for c in sorted(spec.get('chars', []), key=lambda c: c.get('y', 262)):
        out.append(character(c, cast))
    if spec.get('svg'):
        out.append(spec['svg'])
    out += [prop(p) for p in spec.get('props', []) if p.get('front')]
    out += [fx(k) for k in spec.get('fx', [])]
    if spec.get('bubble'):
        out.append(bubble(spec['bubble']))
    out.append('</svg>')
    return '\n'.join(out)


def listing():
    P = peeps()['parts']
    groups = {}
    for k in P:
        g, n = k.rsplit('/', 1)
        groups.setdefault(g, []).append(n)
    print('bg:', ' '.join(f[:-4] for f in sorted(os.listdir(os.path.join(KIT, 'bg')))))
    print('cast:', ' '.join(load('cast.json', {}).keys()))
    for g, ns in groups.items():
        if g.startswith('body/'):
            print(f'{g}:')
            for n in ns:
                print(f'   {n:28}', ' '.join(sorted(set(P[g + "/" + n]['def']) - {'outlineColor', 'skinColor'})))
        else:
            print(f'{g}:', ' '.join(ns))
    print('props (đã lưu):', ' '.join(sorted(load('props.json', {}))))


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] == '--list':
        listing()
    elif a[0] == '--batch':
        for path, spec in json.load(open(a[1])).items():
            open(os.path.join(ROOT, path) if not os.path.isabs(path) else path, 'w').write(render(spec))
            print('✓', path)
    else:
        spec = json.loads(a[0]) if a[0].lstrip().startswith('{') else json.load(open(a[0]))
        svg = render(spec)
        if len(a) > 1:
            open(a[1], 'w').write(svg)
        else:
            print(svg)
