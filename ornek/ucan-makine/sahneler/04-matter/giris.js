import { surucu } from "/ortak/surucu.js";
const { Engine, Bodies, Body, Composite, Events, Common } = Matter;
const KARE = 240, W = 1920, H = 1080, MASA_Y = 840;
const cv = document.getElementById("c"), g = cv.getContext("2d");
// tohumlu rastgele
const rng = (s) => () => (s = (s * 16807) % 2147483647) / 2147483647;
Common._seed = 4242; Math.random = rng(777);
const R = rng(2026);
// kağıt (bir kez, sabit)
const kagit = document.createElement("canvas"); kagit.width = W; kagit.height = H;
(function () {
  const k = kagit.getContext("2d"), r = rng(31);
  k.fillStyle = "#E8D9B8"; k.fillRect(0, 0, W, H);
  for (let i = 0; i < 260; i++) { const x = r() * W, y = r() * H, rad = 20 + r() * 120;
    const gr = k.createRadialGradient(x, y, 0, x, y, rad); const a = 0.03 + r() * 0.04;
    gr.addColorStop(0, `rgba(150,110,60,${a})`); gr.addColorStop(1, "rgba(150,110,60,0)"); k.fillStyle = gr; k.fillRect(x - rad, y - rad, rad * 2, rad * 2); }
  for (let i = 0; i < 5000; i++) { k.fillStyle = `rgba(80,55,30,${0.03 + r() * 0.05})`; k.fillRect(r() * W, r() * H, 1 + r() * 2, 1 + r() * 2); }
  const v = k.createRadialGradient(W / 2, H / 2, 400, W / 2, H / 2, 1150);
  v.addColorStop(0, "rgba(70,40,15,0)"); v.addColorStop(1, "rgba(70,40,15,0.38)"); k.fillStyle = v; k.fillRect(0, 0, W, H);
})();
const INK = "#2b1d12", SOFT = "#6b5640", RED = "#b3261e";
// fizik
const eng = Engine.create({ gravity: { x: 0, y: 0.7 }, positionIterations: 10, velocityIterations: 8 });
const zemin = Bodies.rectangle(W / 2, MASA_Y + 100, 3000, 200, { isStatic: true, label: "masa", friction: 0.8, restitution: 0.08 });
const duvarL = Bodies.rectangle(-100 + 220, 600, 200, 3000, { isStatic: true, label: "duvar" });
const duvarR = Bodies.rectangle(W + 100 - 220, 600, 200, 3000, { isStatic: true, label: "duvar" });
Composite.add(eng.world, [zemin, duvarL, duvarR]);
const parca = [];
function ekle(tur, x, y, w, h, aci, vx = 0, vav = 0) {
  const opt = { friction: 0.6, frictionStatic: 0.9, restitution: 0.12, density: 0.002, angle: aci, label: tur };
  let b, ek = {};
  if (tur === "krank") {
    const mil = Bodies.rectangle(0, 0, 150, 18), kol = Bodies.rectangle(66, 40, 18, 90), top = Bodies.circle(-66, 0, 26);
    b = Body.create({ parts: [mil, kol, top], ...opt }); Body.setPosition(b, { x, y }); Body.setAngle(b, aci);
    ek.mil = [150, 18]; 
  } else if (tur === "pedal") { b = Bodies.rectangle(x, y, w, h, { ...opt, chamfer: { radius: 6 } }); }
  else if (tur === "bez") { b = Bodies.trapezoid(x, y, w, h, 0.25, opt); }
  else b = Bodies.rectangle(x, y, w, h, opt);
  Body.setVelocity(b, { x: vx, y: vav }); Body.setAngularVelocity(b, (R() - 0.5) * 0.06);
  Composite.add(eng.world, b);
  parca.push({ b, tur, w, h, js: R() * 1000 });
}
// kadro: ilk karede çoğu havada görünür
const L = [];
for (let i = 0; i < 4; i++) L.push(["cubuk", 260 + R() * 80, 22, 0]);
for (let i = 0; i < 6; i++) L.push(["kaburga", 180 + R() * 90, 14, 0]);
L.push(["krank"], ["krank"]); L.push(["pedal", 150, 46], ["pedal", 130, 42]);
for (let i = 0; i < 4; i++) L.push(["bez", 210 + R() * 60, 110 + R() * 30]);
L.push(["cubuk", 380, 26], ["cubuk", 340, 24], ["kaburga", 220, 14], ["bez", 260, 140]);
L.forEach((p, i) => {
  const x = 420 + R() * 1080, y = (i < 12 ? 60 + R() * 420 : -150 - (i - 12) * 420 - R() * 150);
  ekle(p[0], x, y, p[1], p[2], R() * Math.PI * 2, (R() - 0.5) * 3, 1 + R() * 2);
});
// çarpma olayları
let f = 0; const ev = [];
Events.on(eng, "collisionStart", (e) => e.pairs.forEach((p) => {
  const a = p.bodyA, b = p.bodyB, va = a.velocity, vb = b.velocity;
  const hiz = Math.hypot(va.x - vb.x, va.y - vb.y);
  if (hiz < 2.2) return;
  const masa = a.label === "masa" || b.label === "masa";
  if (a.label === "duvar" || b.label === "duvar") return;
  const guc = Math.min(1, hiz / 16);
  ev.push({ kare: f, tur: masa ? (guc > 0.45 ? "dusme" : "vurus") : (guc > 0.3 ? "vurus" : "tik"), guc: +guc.toFixed(2) });
}));
function olayYaz() {
  ev.sort((x, y) => y.guc - x.guc);
  const secili = []; 
  for (const o of ev) { if (secili.length >= 24) break; if (secili.some((s) => Math.abs(s.kare - o.kare) < 3)) continue; secili.push(o); }
  secili.sort((x, y) => x.kare - y.kare);
  return secili;
}
// el çizimi yardımcıları
const sal = (s, i, a) => Math.sin(s * 12.9898 + i * 78.233) * a;
function kontur(poly, js, kalin) {
  const n = poly.length;
  for (let pass = 0; pass < 2; pass++) {
    g.beginPath();
    for (let i = 0; i <= n; i++) { const p = poly[i % n], q = poly[(i + 1) % n];
      const x = p.x + sal(js, i + pass * 7, 1.4), y = p.y + sal(js, i + 3 + pass * 7, 1.4);
      if (i === 0) g.moveTo(x, y); else g.lineTo(x, y);
    }
    g.lineWidth = kalin - pass * 0.8; g.strokeStyle = INK; g.lineJoin = "round"; g.lineCap = "round"; g.stroke();
  }
}
function tara(poly, ac, aralik) {
  g.save(); g.beginPath(); poly.forEach((p, i) => i ? g.lineTo(p.x, p.y) : g.moveTo(p.x, p.y)); g.closePath(); g.clip();
  g.strokeStyle = SOFT; g.lineWidth = 1.3; g.globalAlpha = 0.7; g.beginPath();
  const c = Math.cos(ac), s = Math.sin(ac);
  for (let t = -400; t < 400; t += aralik) { g.moveTo(poly[0].x + (-600) * c - t * s, poly[0].y + (-600) * s + t * c); g.lineTo(poly[0].x + 600 * c - t * s, poly[0].y + 600 * s + t * c); }
  g.stroke(); g.restore();
}
function ciz(p) {
  const b = p.b;
  const parts = b.parts.length > 1 ? b.parts.slice(1) : [b];
  if (p.tur === "bez") {
    const poly = b.vertices; tara(poly, 0.7 + b.angle * 0, 9); tara(poly, -0.8, 14); kontur(poly, p.js, 2.6);
  } else {
    parts.forEach((q, i) => {
      const poly = q.circleRadius ? Array.from({ length: 14 }, (_, k) => ({ x: q.position.x + Math.cos(k / 14 * 6.2832 + b.angle) * q.circleRadius, y: q.position.y + Math.sin(k / 14 * 6.2832 + b.angle) * q.circleRadius })) : q.vertices;
      tara(poly, 0.9, p.tur === "kaburga" ? 7 : 8); kontur(poly, p.js + i * 3, p.tur === "kaburga" ? 2.2 : 2.8);
    });
  }
  if (p.tur === "krank") { // kırmızı menteşe halkası
    const q = b.parts[3]; g.beginPath(); g.arc(q.position.x, q.position.y, 13, 0, 6.2832); g.strokeStyle = RED; g.lineWidth = 3.2; g.stroke();
  }
  if (p.tur === "cubuk" || p.tur === "pedal") { // vida çentiği
    const v = b.vertices, m1 = { x: (v[0].x + v[3].x) / 2, y: (v[0].y + v[3].y) / 2 }, m2 = { x: (v[1].x + v[2].x) / 2, y: (v[1].y + v[2].y) / 2 };
    [m1, m2].forEach((m, k) => { const t = 0.08; const c = { x: m.x + (k ? -1 : 1) * (m2.x - m1.x) * t, y: m.y + (k ? -1 : 1) * (m2.y - m1.y) * t };
      g.beginPath(); g.arc(c.x, c.y, 3, 0, 6.2832); g.strokeStyle = INK; g.lineWidth = 1.6; g.stroke(); });
  }
}
function sahne(fr) {
  g.drawImage(kagit, 0, 0);
  // masa çizgisi + tarama
  g.strokeStyle = INK; g.lineWidth = 3;
  g.beginPath(); for (let x = 0; x <= W; x += 40) { const y = MASA_Y + sal(x, 2, 1.5); x ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke();
  g.lineWidth = 1.2; g.strokeStyle = SOFT; g.globalAlpha = 0.7; g.beginPath();
  for (let x = -40; x < W; x += 14) { g.moveTo(x, MASA_Y + 10); g.lineTo(x + 36, MASA_Y + 80 + sal(x, 5, 6)); } g.stroke(); g.globalAlpha = 1;
  g.lineWidth = 1.6; g.beginPath(); g.moveTo(0, MASA_Y + 96); for (let x = 0; x <= W; x += 60) g.lineTo(x, MASA_Y + 96 + sal(x, 8, 2)); g.stroke();
  parca.forEach(ciz);
  g.fillStyle = INK; g.font = "76px Fell"; g.textBaseline = "alphabetic";
  g.fillText("PARÇALAR".toLocaleUpperCase("tr"), 90, 130);
  g.fillStyle = SOFT; g.font = "italic 38px Garamond"; g.fillText("makine masaya dökülünce", 92, 182);
  return cv;
}
async function kare(fr) {
  f = fr;
  if (fr > 0) for (let i = 0; i < 2; i++) Engine.update(eng, 1000 / 60);
  if (fr === KARE - 1) { await fetch("/olay", { method: "POST", body: JSON.stringify(olayYaz()) }).catch(() => {}); fetch("/log", { method: "POST", body: "OLAYLAR " + JSON.stringify(olayYaz()) }); }
  return sahne(fr);
}
surucu(async () => {}, kare, KARE);
