// Render một file HTML (thẻ lỗi, báo cáo tuần…) thành PNG – dùng cho Telegram.
// node tools/render_card.js in.html out.png [width=540]
const { chromium } = require("playwright");
const [inp, out, w] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: Number(w) || 540, height: 400 }, deviceScaleFactor: 2 });
  await p.goto("file://" + require("path").resolve(inp));
  await p.waitForTimeout(200);
  await p.locator("#card").screenshot({ path: out });
  await b.close();
})();
