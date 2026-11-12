// Đo khung bao (bbox) thật của icon đạo cụ: node tools/kit_bbox.js < in.json > out.json
// in: {name: {body, w, h}} → out: {name: [x, y, w, h]}
const {chromium} = require('playwright');
let s = ''; process.stdin.on('data', d => s += d).on('end', async () => {
  const items = JSON.parse(s); const b = await chromium.launch(); const p = await b.newPage();
  const out = await p.evaluate(items => {
    const o = {};
    for (const [k, v] of Object.entries(items)) {
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', `0 0 ${v.w} ${v.h}`); svg.setAttribute('width', v.w); svg.setAttribute('height', v.h);
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g'); g.innerHTML = v.body; svg.appendChild(g);
      document.body.appendChild(svg); const r = g.getBBox(); o[k] = [r.x, r.y, r.width, r.height].map(x => +x.toFixed(2)); svg.remove();
    }
    return o;
  }, items);
  process.stdout.write(JSON.stringify(out)); await b.close();
});
