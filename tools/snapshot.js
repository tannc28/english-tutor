// Chụp ảnh dài một bài (đã chấm) ở khổ iPhone → JPG, để gửi Tân qua Telegram.
// Dùng: node tools/snapshot.js <lessonId> <out.jpg>   (phục vụ web/ + data/ cục bộ, không cần đăng nhập)
const http = require("http"), fs = require("fs"), path = require("path");
const { chromium, devices } = require("playwright");
const ROOT = path.resolve(__dirname, ".."), [id, out] = process.argv.slice(2);
const TYPES = {".html":"text/html; charset=utf-8", ".json":"application/json", ".webp":"image/webp", ".svg":"image/svg+xml", ".mp3":"audio/mpeg", ".jpg":"image/jpeg", ".png":"image/png"};
const srv = http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split("?")[0]);
  let f = p === "/" || p === "/index.html" ? path.join(ROOT, "web/index.html") : path.join(ROOT, p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  let body = fs.readFileSync(f);
  if (f.endsWith("index.html")) body = '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' + body;
  res.writeHead(200, {"content-type": TYPES[path.extname(f)] || "application/octet-stream"}); res.end(body);
}).listen(0, async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({...devices["iPhone 13"], deviceScaleFactor: 2});
  const p = await ctx.newPage();
  await p.goto(`http://localhost:${srv.address().port}/index.html#${id}`);
  await p.waitForSelector(".grade, .part", {timeout: 15000}); await p.waitForTimeout(1500);
  await p.evaluate(() => {
    document.querySelectorAll(".player audio, .pl-row, .toc").forEach(e => e.style.display = "none");
    // câu trả lời dài: thay ô nhập bằng khối chữ để hiện đầy đủ
    document.querySelectorAll('.book input[type=text], .book input[type=number], .book textarea, .bookcol input[type=text], .bookcol input[type=number], .bookcol textarea').forEach(el => {
      if (el.hidden || el.offsetParent === null) return;
      const d = document.createElement("div"); d.textContent = el.value || "—";
      d.style.cssText = "white-space:pre-wrap;padding:10px 12px;border:1px solid #d0d7e2;border-radius:10px;background:#f7f9fc;font:inherit;min-height:1.4em";
      el.replaceWith(d);
    });
  });
  // Trình duyệt không chụp nổi 1 ảnh quá cao → chụp từng đoạn 3000px rồi ghép (tools/notify.py dùng PIL)
  const box = await p.locator(".bookcol").boundingBox(), sy = await p.evaluate(() => window.scrollY);
  const top = box.y + sy, segs = [];
  for (let y = 0, i = 0; y < box.height; y += 3000, i++){
    const h = Math.min(3000, box.height - y), f = `${out}.part${String(i).padStart(2,"0")}.png`;
    await p.screenshot({path: f, fullPage: true, clip: {x: box.x, y: top + y, width: box.width, height: h}}); segs.push(f);
  }
  await b.close(); srv.close(); console.log(JSON.stringify(segs));
});
