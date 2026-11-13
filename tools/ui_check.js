#!/usr/bin/env node
// Tự soát GIAO DIỆN (Tân 13/11: "chướng mắt mà phải để tôi nói") – chạy sau MỌI thay đổi web/index.html:
//   node tools/ui_check.js [lessonId…]      (mặc định: mọi bài trong data/lessons.json)
// Mở trang thật bằng Chromium ở 2 cỡ (desktop 1600 · điện thoại 390) và báo:
//   • đáp án xếp lưới có HÀNG LẺ MỒ CÔI (hàng cuối ít ô hơn hàng trên)
//   • trang tràn ngang (cuộn ngang trên điện thoại)
//   • chữ trong nút/đáp án bị cắt
//   • KHOẢNG TRỐNG: thẻ (.card) rộng ≥1000px mà nội dung chỉ chiếm < 60% bề ngang (desktop)
// Exit 1 nếu có lỗi.
const {chromium} = require('playwright'); const http = require('http'); const fs = require('fs'); const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const srv = http.createServer((q, r) => { let p = decodeURIComponent(q.url.split('?')[0]); if (p === '/') p = '/index.html';
  const f = p === '/index.html' ? path.join(ROOT, 'web/index.html') : path.join(ROOT, p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
  const body = fs.readFileSync(f); r.writeHead(200, {'content-type': f.endsWith('.html') ? 'text/html; charset=utf-8' : f.endsWith('.json') ? 'application/json' : 'application/octet-stream'});
  r.end(p === '/index.html' ? Buffer.concat([Buffer.from('<meta charset="utf-8">'), body]) : body); });
(async () => {
  await new Promise(ok => srv.listen(0, ok)); const base = `http://localhost:${srv.address().port}/index.html`;
  let ids = process.argv.slice(2);
  if (!ids.length) ids = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/lessons.json'))).lessons.map(l => l.id);
  const b = await chromium.launch(); const bad = [];
  for (const vp of [{width:1600, height:1000, n:'desktop'}, {width:390, height:844, n:'phone'}]) {
    const p = await b.newPage({viewport: vp}); const errs = []; p.on('pageerror', e => errs.push(e.message));
    for (const id of ['', ...ids]) {
      await p.goto(base + (id ? '#' + id : ''), {waitUntil: 'load'}); await p.waitForTimeout(id ? 1200 : 2000);
      const r = await p.evaluate(() => {
        const out = [];
        if (document.documentElement.scrollWidth > innerWidth + 2) out.push(`tràn ngang ${document.documentElement.scrollWidth}px > ${innerWidth}px`);
        document.querySelectorAll('.opts').forEach(g => { const it = [...g.querySelectorAll(':scope > .opt')].filter(x => x.offsetParent); if (it.length < 2) return;
          const rows = {}; it.forEach(x => { const t = Math.round(x.getBoundingClientRect().top); rows[t] = (rows[t] || 0) + 1; });
          const c = Object.keys(rows).sort((a, b) => a - b).map(k => rows[k]);
          if (c.length > 1 && c[c.length - 1] < c[0]) out.push(`đáp án mồ côi ${c.join('+')} ở ${g.closest('.q')?.id || '?'}`); });
        document.querySelectorAll('button:not(.wcard), .opt, .tbtn, .mic-tab').forEach(x => { if (x.offsetParent && x.scrollWidth > x.clientWidth + 2 && getComputedStyle(x).overflow !== 'visible') out.push(`chữ bị cắt: "${x.textContent.trim().slice(0, 30)}"`); });
        if (innerWidth >= 1400) document.querySelectorAll('main .card, #main .card, .view .card').forEach(c => { if (!c.offsetParent) return; const cr = c.getBoundingClientRect(); if (cr.width < 1000 || cr.height < 120) return;
          let r = cr.left; c.querySelectorAll('*').forEach(e => { if (!e.offsetParent || e.children.length) return; const b = e.getBoundingClientRect(); if (b.width && b.height) r = Math.max(r, b.right); });
          const used = (r - cr.left) / cr.width; if (used < 0.6) out.push(`khoảng trống: thẻ "${(c.querySelector('.label,h2,h3')?.textContent || '').trim().slice(0, 40)}" chỉ dùng ${Math.round(used * 100)}% bề ngang`); });
        return out; });
      r.forEach(x => bad.push(`[${vp.n}] ${id || 'trang chủ'}: ${x}`));
    }
    errs.forEach(e => bad.push(`[${vp.n}] lỗi JS: ${e}`));
    await p.close();
  }
  await b.close(); srv.close();
  if (bad.length) { console.log('❌ UI:\n' + [...new Set(bad)].slice(0, 60).join('\n')); process.exit(1); }
  fs.writeFileSync(path.join(ROOT, 'web/.ui_ok'), new Date().toISOString() + '\n');
  console.log('✅ ui_check: không thấy lỗi bố cục');
})();
