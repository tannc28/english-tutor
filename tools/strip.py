#!/usr/bin/env python3
"""Hình minh hoạ BẰNG VÍ DỤ cho từ trừu tượng (từ nối, cụm ngữ pháp): 2 khung truyện tranh + từ khoá ở giữa.
Tân 12/11: "dùng illustration bằng ví dụ… giúp tôi hiểu được chứ không phải random ảnh".
strip(out.svg, [(emoji, caption), (emoji, caption)], link="although", note="surprise!")
"""
import html
E = lambda s: html.escape(s, quote=True)
def strip(out, panels, link, note="", sym="→"):
    W, H = 384, 288
    pw, gap, top = 148, 60, 22
    xs = [14, W - 14 - pw]
    cols = ["#fff4e0", "#e6f4ea"]
    g = []
    for i, (emo, cap) in enumerate(panels[:2]):
        x = xs[i]
        g.append(f'<rect x="{x}" y="{top}" width="{pw}" height="200" rx="18" fill="{cols[i]}" stroke="#d6dbe4" stroke-width="2"/>')
        g.append(f'<text x="{x+pw/2}" y="{top+92}" font-size="50" text-anchor="middle">{E(emo)}</text>')
        words, lines, cur = cap.split(), [], ""
        for w in words:
            if len(cur + " " + w) > 15: lines.append(cur); cur = w
            else: cur = (cur + " " + w).strip()
        lines.append(cur)
        for j, ln in enumerate(lines[:3]):
            g.append(f'<text x="{x+pw/2}" y="{top+140+j*22}" font-size="16" font-weight="600" fill="#1c2333" text-anchor="middle">{E(ln)}</text>')
    cx = W / 2
    if sym == "→":
        g.append(f'<path d="M{cx-30} {top+100} L{cx+24} {top+100}" stroke="#2b6de0" stroke-width="4" stroke-linecap="round"/><path d="M{cx+16} {top+90} L{cx+28} {top+100} L{cx+16} {top+110}" fill="none" stroke="#2b6de0" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
    else:
        g.append(f'<text x="{cx}" y="{top+112}" font-size="34" font-weight="800" fill="#2b6de0" text-anchor="middle">{E(sym)}</text>')
    g.append(f'<rect x="40" y="{H-50}" width="{W-80}" height="38" rx="19" fill="#2b6de0"/><text x="{W/2}" y="{H-25}" font-size="18" font-weight="800" fill="#fff" text-anchor="middle">{E(link)}{(" · " + E(note)) if note else ""}</text>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="-apple-system,Segoe UI,Roboto,sans-serif"><rect width="{W}" height="{H}" fill="#f6f8fb"/>{"".join(g)}</svg>'
    open(out, "w", encoding="utf-8").write(svg)
