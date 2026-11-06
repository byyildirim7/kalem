// node ses/render.mjs <paket köküne göre olaylar.json> <cikis.wav>
import http from "http"; import fs from "fs"; import path from "path"; import puppeteer from "puppeteer-core";
const KOK = path.resolve(import.meta.dirname, "..");
const mime = { ".json": "application/json", ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript" };
const srv = http.createServer((q, r) => { const p = path.join(KOK, decodeURIComponent(q.url.split("?")[0])); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { "content-type": mime[path.extname(p)] || "application/octet-stream" }); r.end(d); } }); }).listen(0);
const port = srv.address().port;
// CHROME değişkeni > işletim sisteminin bilinen yolları (ortak/yakala.py ile aynı sıra)
const chrome = process.env.CHROME || {
  darwin: ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
  win32: ["PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"].map((v) => path.join(process.env[v] || "", "Google", "Chrome", "Application", "chrome.exe")),
  linux: ["/usr/bin/google-chrome", "/usr/bin/chromium"],
}[process.platform]?.find((a) => fs.existsSync(a));
if (!chrome) { console.error("Chrome bulunamadı; CHROME değişkeniyle yolunu ver"); process.exit(1); }
const br = await puppeteer.launch({ executablePath: chrome, headless: "new", args: ["--autoplay-policy=no-user-gesture-required"] });
try {
  const pg = await br.newPage(); pg.on("pageerror", (e) => console.log("[hata]", e.message));
  await pg.goto(`http://127.0.0.1:${port}/ses/ses.html?o=/${process.argv[2]}`); await pg.waitForFunction("window.hazir", { timeout: 20000 });
  const [L, R] = await pg.evaluate(() => window.render());
  const f = (b) => new Float32Array(new Uint8Array(Buffer.from(b, "base64")).buffer);
  const l = f(L), rr = f(R), n = l.length, out = Buffer.alloc(44 + n * 4);
  out.write("RIFF", 0); out.writeUInt32LE(36 + n * 4, 4); out.write("WAVEfmt ", 8); out.writeUInt32LE(16, 16); out.writeUInt16LE(1, 20); out.writeUInt16LE(2, 22);
  out.writeUInt32LE(44100, 24); out.writeUInt32LE(44100 * 4, 28); out.writeUInt16LE(4, 32); out.writeUInt16LE(16, 34); out.write("data", 36); out.writeUInt32LE(n * 4, 40);
  const c = (x) => Math.max(-32768, Math.min(32767, Math.round(x * 32767)));
  for (let i = 0; i < n; i++) { out.writeInt16LE(c(l[i]), 44 + i * 4); out.writeInt16LE(c(rr[i]), 46 + i * 4); }
  fs.writeFileSync(process.argv[3], out); console.log("ses", (n / 44100).toFixed(2), "sn");
} finally { await br.close(); srv.close(); }   // başsız Chrome öksüz kalmasın
