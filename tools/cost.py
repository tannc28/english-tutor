#!/usr/bin/env python3
"""Chi phí AI của lớp học (Tân 13/11: "biết lớp tiêu tốn thế nào theo ngày/tuần/tháng").

  python3 tools/cost.py        # đọc nhật ký phiên Claude Code (~/.claude/projects/*english-tutor*/) → data/costs.json

- Tính theo GIÁ API công khai (USD / 1 triệu token) – "chi phí tương đương API". Nếu Tân dùng gói thuê bao,
  hoá đơn thật là phí gói; con số này cho biết lớp "đáng giá" bao nhiêu và việc nào tốn nhất.
- Mỗi tin nhắn đếm 1 lần (gộp theo message.id). Gồm phiên chính (Opus) + subagent (Sonnet/Haiku).
- Giữ lịch sử: ngày đã có trong data/costs.json mà nhật ký không còn (container mới) thì giữ nguyên.
- Cloudflare FLUX (ảnh) và Telegram miễn phí → 0.
"""
import json, os, glob, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'costs.json')
TZ = dt.timezone(dt.timedelta(hours=7))
# USD / 1M token: input, output, cache read  (cache write 5 phút = 1,25× input, 1 giờ = 2× input)
RATES = {'opus': (4.0, 20.0, 0.20), 'sonnet': (2.0, 10.0, 0.10), 'haiku': (0.10, 0.50, 0.01), 'fable': (8.0, 40.0, 0.20)}
VND_PER_USD = 26000

def fam(model):
    m = (model or '').lower()
    for k in RATES:
        if k in m: return k
    return None

def scan():
    msgs = {}
    for f in glob.glob(os.path.expanduser('~/.claude/projects/*english-tutor*/**/*.jsonl'), recursive=True):
        try:
            with open(f, errors='ignore') as fh:
                for line in fh:
                    if '"usage"' not in line: continue
                    try: d = json.loads(line)
                    except Exception: continue
                    m = d.get('message')
                    if not isinstance(m, dict) or not m.get('usage'): continue
                    k = fam(m.get('model'))
                    if not k: continue
                    mid = m.get('id') or (f + str(d.get('uuid')))
                    u = m['usage']; cc = u.get('cache_creation') or {}
                    rec = {'ts': d.get('timestamp'), 'fam': k, 'in': u.get('input_tokens', 0) or 0, 'out': u.get('output_tokens', 0) or 0,
                           'cr': u.get('cache_read_input_tokens', 0) or 0,
                           'cw5': cc.get('ephemeral_5m_input_tokens', 0) or 0, 'cw1h': cc.get('ephemeral_1h_input_tokens', 0) or 0,
                           'sub': '/subagents/' in f}
                    if not cc and u.get('cache_creation_input_tokens'): rec['cw5'] = u['cache_creation_input_tokens']
                    old = msgs.get(mid)
                    if not old or rec['out'] >= old['out']: msgs[mid] = rec
        except OSError:
            pass
    return msgs.values()

def cost(r):
    i, o, c = RATES[r['fam']]
    return (r['in'] * i + r['cw5'] * i * 1.25 + r['cw1h'] * i * 2 + r['cr'] * c + r['out'] * o) / 1e6

def main():
    days = {}
    for r in scan():
        if not r['ts']: continue
        day = dt.datetime.fromisoformat(r['ts'].replace('Z', '+00:00')).astimezone(TZ).date().isoformat()
        D = days.setdefault(day, {'usd': 0.0, 'by': {}, 'calls': 0})
        B = D['by'].setdefault(r['fam'], {'usd': 0.0, 'in': 0, 'out': 0, 'cache_read': 0, 'cache_write': 0, 'calls': 0})
        c = cost(r); D['usd'] += c; D['calls'] += 1
        B['usd'] += c; B['in'] += r['in']; B['out'] += r['out']; B['cache_read'] += r['cr']; B['cache_write'] += r['cw5'] + r['cw1h']; B['calls'] += 1
    old = json.load(open(OUT)) if os.path.exists(OUT) else {}
    merged = dict(old.get('days', {}))
    for d, v in days.items():   # ngày còn trong nhật ký → số mới; ngày cũ mất nhật ký → giữ số đã lưu
        if d not in merged or v['usd'] >= merged[d].get('usd', 0) * 0.98: merged[d] = v
    for v in merged.values():
        v['usd'] = round(v['usd'], 3)
        for b in v['by'].values(): b['usd'] = round(b['usd'], 3)
    out = {'_note': 'Sinh bởi tools/cost.py – chi phí AI tương đương giá API (USD), theo ngày giờ VN. FLUX/Telegram miễn phí.',
           'updated': dt.datetime.now(TZ).isoformat(timespec='minutes'), 'vnd_per_usd': VND_PER_USD,
           'rates_usd_per_mtok': {k: {'input': a, 'output': b, 'cache_read': c} for k, (a, b, c) in RATES.items()},
           'days': dict(sorted(merged.items()))}
    json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
    tot = sum(v['usd'] for v in merged.values())
    print(f'costs: {len(merged)} ngày, tổng ≈ ${tot:.2f} (~{tot * VND_PER_USD:,.0f} đ) → data/costs.json')

if __name__ == '__main__':
    main()
