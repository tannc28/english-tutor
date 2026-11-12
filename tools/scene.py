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
 "furniture": [{"type": "table", "x": 192, "top": 212, "w": 260}],   # table|desk|counter|shelf (+ "behind": true)
 "props": [{"icon": "hot-beverage", "on": "table", "x": 150},      # đáy chạm mặt bàn ("on": "floor" = sàn)
           {"icon": "closed-umbrella", "hold": "nam", "hand": "right", "grip": "top"},  # trong tay: vẽ đè lại bàn tay lên đồ (layer: grip|front|behind)
           {"icon": "luggage", "on": "floor", "x": 250},
           {"icon": "key", "x": 300, "y": 80, "size": 30, "rot": 0, "back": true}],
 # Kích thước đạo cụ tự tính theo cm thật (REAL_CM) so với người; "k" phóng to/thu nhỏ, "size" ép px.
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
FULL_UNITS = 3120  # người đứng (đỉnh tóc → gót) ≈ 170 cm


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
    hands = sorted((x + flip * s * (hx - nx), neck_y + s * (hy - ny)) for hx, hy in P[bkey].get('hands', []))
    info = {'hands': hands, 'px_per_cm': s * FULL_UNITS / 170, 'x': x, 'y': y, 'hand_r': 75 * s}
    svg = shadow + f'<g transform="translate({x} {neck_y:.1f}) scale({flip * s:.5f} {s:.5f})">' + ''.join(g) + '</g>'
    return svg, info


def _bbox(props, names):
    import subprocess
    inp = {n: props[n] for n in names}
    r = subprocess.run(['node', os.path.join(ROOT, 'tools', 'kit_bbox.js')], input=json.dumps(inp),
                       capture_output=True, text=True, cwd=os.path.join(ROOT, 'tools'))
    if r.returncode == 0:
        for n, bb in json.loads(r.stdout).items():
            props[n]['bb'] = bb


def icon(name):
    props = load('props.json', {})
    if name in props:
        if 'bb' not in props[name]:
            _bbox(props, [name])
            json.dump(props, open(os.path.join(KIT, 'props.json'), 'w'), indent=0, sort_keys=True)
        return props[name]
    for base in [os.path.join(ROOT, 'tools', 'node_modules'), *os.environ.get('NODE_PATH', '').split(':')]:
        p = os.path.join(base, '@iconify-json', 'fluent-emoji-flat', 'icons.json')
        if base and os.path.exists(p):
            d = json.load(open(p))
            if name in d['icons']:
                ic = d['icons'][name]
                props[name] = {'body': ic['body'], 'w': ic.get('width', d.get('width', 32)),
                               'h': ic.get('height', d.get('height', 32))}
                _bbox(props, [name])
                json.dump(props, open(os.path.join(KIT, 'props.json'), 'w'), indent=0, sort_keys=True)
                return props[name]
            raise SystemExit(f'không có icon "{name}" trong fluent-emoji-flat')
    raise SystemExit(f'icon "{name}" chưa có trong data/kit/props.json; cài: cd tools && npm i @iconify-json/fluent-emoji-flat')


# Kích thước thật (cm, theo chiều lớn nhất) của đạo cụ hay dùng – để tỉ lệ đúng với người
REAL_CM = {'hot-beverage': 11, 'teacup-without-handle': 9, 'cup-with-straw': 18, 'croissant': 14, 'sandwich': 14,
           'closed-umbrella': 90, 'umbrella': 100, 'luggage': 60, 'handbag': 30, 'backpack': 45, 'school-backpack': 45,
           'laptop': 33, 'mobile-phone': 15, 'books': 18, 'blue-book': 22, 'key': 7, 'potted-plant': 45,
           'package': 45, 'alarm-clock': 10, 'pizza': 30, 'bowl-with-spoon': 16, 'steaming-bowl': 18,
           'desktop-computer': 50, 'newspaper': 35, 'shopping-bags': 40, 'wrapped-gift': 30, 'cookie': 8,
           'green-apple': 8, 'red-apple': 8, 'bread': 25, 'wine-glass': 20, 'glass-of-milk': 13, 'pot-of-food': 25}

# Điểm cầm mặc định (tỉ lệ trong khung icon) + góc xoay khi cầm
GRIP = {'closed-umbrella': ([.15, .12], 30, .8), 'luggage': ([.5, .04], 0, 1), 'handbag': ([.5, .1], 0, 1),
        'shopping-bags': ([.5, .1], 0, 1), 'hot-beverage': ([.75, .5], 0, 1), 'mobile-phone': ([.5, .6], 0, 1)}

SURF = {}   # mặt phẳng: id → (x0, x1, y_top)
CHARS = {}  # id nhân vật → info (tay, tỉ lệ)
HAND_USED = []


def furniture(f):
    t, x, top, w = f['type'], f['x'], f['top'], f.get('w', 120)
    floor = f.get('floor', 262)
    c = f.get('color', {'table': '#8A5C3C', 'desk': '#B98B63', 'counter': '#A87450', 'shelf': '#9B6B47'}.get(t, '#8A5C3C'))
    if t == 'table':  # bàn tròn 1 chân
        svg = (f'<rect x="{x - w / 2}" y="{top}" width="{w}" height="8" rx="4" fill="{c}"/>'
               f'<rect x="{x - 4}" y="{top + 8}" width="8" height="{floor - top - 12}" fill="{c}" opacity=".85"/>'
               f'<ellipse cx="{x}" cy="{floor - 3}" rx="{w * .16}" ry="4" fill="{c}"/>')
    elif t == 'desk':
        svg = (f'<rect x="{x - w / 2}" y="{top}" width="{w}" height="9" rx="3" fill="{c}"/>'
               f'<rect x="{x - w / 2 + 10}" y="{top + 9}" width="7" height="{floor - top - 9}" fill="{c}" opacity=".85"/>'
               f'<rect x="{x + w / 2 - 17}" y="{top + 9}" width="7" height="{floor - top - 9}" fill="{c}" opacity=".85"/>')
    elif t == 'counter':
        svg = (f'<rect x="{x - w / 2}" y="{top + 6}" width="{w}" height="{floor - top - 6}" fill="{c}"/>'
               f'<rect x="{x - w / 2 - 4}" y="{top}" width="{w + 8}" height="8" rx="2" fill="{c}" style="filter:brightness(.8)"/>')
    elif t == 'shelf':
        svg = f'<rect x="{x - w / 2}" y="{top}" width="{w}" height="5" rx="2" fill="{c}"/>'
    else:
        raise SystemExit(f'không có đồ nội thất "{t}" (table|desk|counter|shelf)')
    SURF[f.get('id', t)] = (x - w / 2, x + w / 2, top)
    return svg


def prop(p, scale):
    """Đặt đạo cụ: tự do (x,y) | 'on': mặt phẳng (đáy chạm mặt) | 'hold': nhân vật (khớp vào tay)."""
    ic = icon(p['icon'])
    bx, by, bw, bh = ic.get('bb', [0, 0, ic['w'], ic['h']])
    ref = CHARS.get(p.get('hold')) or scale
    if p.get('hold') and p['icon'] in GRIP:
        g0, r0, k0 = GRIP[p['icon']]
        p = {'grip': g0, 'rot': r0, 'k': k0, **p}
    if 'size' in p:
        sz = p['size']
    else:
        sz = REAL_CM.get(p['icon'], 30) * p.get('k', 1) * (ref['px_per_cm'] if ref else 1.1)
    sc = sz / max(bw, bh)
    if p.get('hold'):
        hs = CHARS[p['hold']]['hands']
        if not hs:
            raise SystemExit(f'tư thế của {p["hold"]} không có tay để cầm – đổi body')
        hand = p.get('hand', 'right')
        hx, hy = hs[-1] if hand == 'right' else hs[0] if hand == 'left' else hs[int(hand)]
        HAND_USED.append((hx, hy))
        grip = p.get('grip', 'center')  # điểm trên đồ vật nằm trong lòng bàn tay
        if isinstance(grip, list):  # [fx, fy] tỉ lệ trong khung đồ vật, VD tay cầm ô ở góc trên trái
            gx, gy = bx + bw * grip[0], by + bh * grip[1]
        else:
            gx = bx + bw / 2
            gy = {'top': by + bh * .08, 'center': by + bh / 2, 'bottom': by + bh * .9}.get(grip, by + bh / 2)
        ax, ay = hx + p.get('dx', 0), hy + p.get('dy', 0)
    elif p.get('on'):
        x0, x1, top = SURF.get(p['on'], (0, W, p.get('floor', 262))) if p['on'] != 'floor' else (0, W, p.get('floor', 262))
        gx, gy = bx + bw / 2, by + bh
        ax, ay = p['x'], top + p.get('dy', 0)
    else:
        gx, gy = bx + bw / 2, by + bh / 2
        ax, ay = p['x'], p['y']
    rot = f' rotate({p["rot"]})' if p.get('rot') else ''
    fl = ' scale(-1 1)' if p.get('flip') else ''
    shadow = ''
    if p.get('on') and not p.get('noshadow'):
        shadow = f'<ellipse cx="{ax}" cy="{ay}" rx="{bw * sc * .42:.1f}" ry="{max(1.2, bw * sc * .06):.1f}" fill="#000" opacity=".15"/>'
    return shadow + (f'<g transform="translate({ax:.1f} {ay:.1f}){rot}{fl} scale({sc:.4f}) '
                     f'translate({-gx:.2f} {-gy:.2f})">{ic["body"]}</g>')


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
    SURF.clear(); CHARS.clear()
    chars = sorted(spec.get('chars', []), key=lambda c: c.get('y', 262))
    built = []
    for i, c in enumerate(chars):
        svg, info = character(c, cast)
        info['svg'] = svg
        CHARS[c.get('id', c.get('cast', str(i)))] = info
        built.append((c, svg))
    scale = next(iter(CHARS.values()), None)
    props = spec.get('props', [])
    behind = [f for f in spec.get('furniture', []) if f.get('behind')]
    front_f = [f for f in spec.get('furniture', []) if not f.get('behind')]
    out += [furniture(f) for f in behind]
    out += [prop(p, scale) for p in props if p.get('back')]
    for c, svg in built:
        cid = c.get('id', c.get('cast'))
        # đồ cầm "behind": vẽ trước người → bàn tay/ngón đè lên, trông như đang nắm
        out += [prop(p, scale) for p in props if p.get('hold') == cid and p.get('layer') == 'behind']
        out.append(svg)
    out += [furniture(f) for f in front_f]
    if spec.get('svg'):
        out.append(spec['svg'])
    n = 0
    for p in props:
        if p.get('back') or (p.get('hold') and p.get('layer') == 'behind'):
            continue
        out.append(prop(p, scale))
        if p.get('hold') and p.get('layer', 'grip') == 'grip':
            # vẽ đè lại riêng bàn tay lên đồ vật → ngón tay nắm quanh đồ
            ch = CHARS[p['hold']]
            hx, hy = HAND_USED[-1]
            n += 1
            out.append(f'<clipPath id="hand{n}"><circle cx="{hx:.1f}" cy="{hy:.1f}" r="{ch["hand_r"] * p.get("hr", 1):.1f}"/></clipPath>'
                       f'<g clip-path="url(#hand{n})">{ch["svg"]}</g>')
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
