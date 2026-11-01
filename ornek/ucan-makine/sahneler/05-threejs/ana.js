// Sahne 5 (Three.js): kagit ustundeki yan gorunus eskizine ayni aciyla 3D makine oturur, eskiz cekilir,
// kamera ~120 derece doner, kanatlar krankla cirpar. Zaman yalniz kare numarasindan (zaman.js).
import {surucu} from '/ortak/surucu.js';
import {sahneKur} from './makine/sahne.js';
import {KARE, FOV, kamAt, phiAt, acilis, eskizO} from './zaman.js';

const W = 1920;
const H = 1080;
const PR = 1.2; // sahne 1600x900 css pikselinde kurulu (tarama sikligi ona gore); 1.2 ile 1920x1080 cizer
const D2R = Math.PI / 180;

// tohumlu sozde rastgele (Math.random yok)
function tohum(a) {
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const tuval = (w, h) => Object.assign(document.createElement('canvas'), {width: w, height: h});

let st, out, ctx, bos, eskiz, maske, mctx, mVeri, mAlan, kat, off, octx;
// eskizdeki iki dayanak (piksel): burun ucu ve kuyruk yelpazesinin orta kaburga ucu
const REF_A = [40, 750];
const REF_B = [1505, 718];

async function kur() {
  const gl = tuval(W, H);
  st = sahneKur({canvas: gl});
  st.resize(1600, 900, PR);
  st.camera.fov = FOV;
  st.camera.updateProjectionMatrix();
  st.kalite({samples: 4, shadow: 4096});
  st.gl = gl;

  out = tuval(W, H);
  ctx = out.getContext('2d');
  off = tuval(W, H);
  octx = off.getContext('2d');
  document.body.appendChild(out);

  // bos kagit: ayni murekkep gecisinden, makine gizli (doku ekran uzayinda sabit, her karenin zemini bu)
  st.makine.kok.visible = false;
  cizSahne(0);
  bos = tuval(W, H);
  bos.getContext('2d').drawImage(gl, 0, 0);
  st.makine.kok.visible = true;

  eskiz = new Image();
  eskiz.src = './eskiz-cizgi.png';
  await eskiz.decode();

  // murekkep yikamasi maskesi: dusuk cozunurluklu tohumlu gurultu + soldan saga egim (burundan kuyruga)
  const MW = 240, MH = 135;
  maske = tuval(MW, MH);
  mctx = maske.getContext('2d');
  mVeri = mctx.createImageData(MW, MH);
  const r = tohum(305);
  const G = 9, GH = 6;
  const izgara = Array.from({length: (G + 1) * (GH + 1)}, () => r());
  const vn = (x, y) => {
    const gx = (x / MW) * G, gy = (y / MH) * GH;
    const i = Math.min(G - 1, Math.floor(gx)), j = Math.min(GH - 1, Math.floor(gy));
    let fx = gx - i, fy = gy - j;
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy);
    const v = (a, b) => izgara[b * (G + 1) + a];
    return (v(i, j) * (1 - fx) + v(i + 1, j) * fx) * (1 - fy) + (v(i, j + 1) * (1 - fx) + v(i + 1, j + 1) * fx) * fy;
  };
  mAlan = new Float32Array(MW * MH);
  for (let y = 0; y < MH; y++) for (let x = 0; x < MW; x++) mAlan[y * MW + x] = 0.74 * Math.min(1, Math.max(0, (x / MW - 0.18) / 0.66)) + 0.26 * vn(x, y);

  // kagit katmani (carpma): kenar kararmasi + birkac soluk leke, sabit
  kat = tuval(W, H);
  const k = kat.getContext('2d');
  k.fillStyle = '#fff';
  k.fillRect(0, 0, W, H);
  const rg = k.createRadialGradient(W / 2, H / 2, H * 0.42, W / 2, H / 2, W * 0.62);
  rg.addColorStop(0, 'rgba(255,255,255,0)');
  rg.addColorStop(1, 'rgba(196,176,146,1)');
  k.fillStyle = rg;
  k.fillRect(0, 0, W, H);
  const lr = tohum(1485);
  for (let i = 0; i < 9; i++) {
    const x = lr() * W, y = lr() * H, rr = 60 + lr() * 220;
    const g = k.createRadialGradient(x, y, 0, x, y, rr);
    g.addColorStop(0, `rgba(214,192,156,${0.18 + lr() * 0.2})`);
    g.addColorStop(0.7, `rgba(226,208,176,${0.06 + lr() * 0.06})`);
    g.addColorStop(1, 'rgba(255,255,255,0)');
    k.fillStyle = g;
    k.fillRect(x - rr, y - rr, rr * 2, rr * 2);
  }
}

function cizSahne(f) {
  const kam = kamAt(f);
  st.frame({phi: phiAt(f), ayrik: 0, bezSaydam: 0.15, kapakVurgu: 0, yukseklik: 0}, {...kam, az: kam.az * D2R, el: kam.el * D2R});
}

function maskeGuncelle(r) {
  const e = -0.12 + r * 1.24;
  const d = mVeri.data;
  for (let i = 0; i < mAlan.length; i++) {
    const u = Math.min(1, Math.max(0, (e - mAlan[i]) / 0.12 + 0.5));
    d[i * 4] = d[i * 4 + 1] = d[i * 4 + 2] = 255;
    d[i * 4 + 3] = Math.round(255 * u * u * (3 - 2 * u));
  }
  mctx.putImageData(mVeri, 0, 0);
}

async function kare(f) {
  cizSahne(f);
  ctx.globalCompositeOperation = 'source-over';
  ctx.globalAlpha = 1;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.drawImage(bos, 0, 0);

  // 3D: murekkep yikamasiyla belirir
  const r = acilis(f);
  if (r >= 0.999) ctx.drawImage(st.gl, 0, 0);
  else if (r > 0.001) {
    maskeGuncelle(r);
    octx.globalCompositeOperation = 'source-over';
    octx.clearRect(0, 0, W, H);
    octx.drawImage(st.gl, 0, 0);
    octx.globalCompositeOperation = 'destination-in';
    octx.imageSmoothingEnabled = true;
    octx.imageSmoothingQuality = 'high';
    octx.drawImage(maske, 0, 0, W, H);
    ctx.drawImage(off, 0, 0);
  }

  // eskiz: 3D makinenin burun ve kuyruk ucuna kilitli (kamera kipirdasa da ustunde kalir), sonra cekilir
  const eo = eskizO(f);
  if (eo > 0.001) {
    const a = st.project(0, 0.55, 2.15);
    const b = st.project(0, 0.55, -3.55);
    const A = [a[0] * PR, a[1] * PR], B = [b[0] * PR, b[1] * PR];
    const v = [REF_B[0] - REF_A[0], REF_B[1] - REF_A[1]];
    const v2 = [B[0] - A[0], B[1] - A[1]];
    const s = Math.hypot(...v2) / Math.hypot(...v);
    const rot = Math.atan2(v2[1], v2[0]) - Math.atan2(v[1], v[0]);
    // cekilirken hafifce geri cekilip kuculur (kagittan kalkiyor gibi)
    const geri = 1 - eo;
    const cs = Math.cos(rot) * s * (1 - 0.03 * geri), sn = Math.sin(rot) * s * (1 - 0.03 * geri);
    ctx.globalAlpha = Math.pow(eo, 1.3);
    ctx.globalCompositeOperation = 'multiply';
    ctx.setTransform(cs, sn, -sn, cs, A[0] - (cs * REF_A[0] - sn * REF_A[1]) + 10 * geri, A[1] - (sn * REF_A[0] + cs * REF_A[1]) - 6 * geri);
    ctx.drawImage(eskiz, 0, 0);
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha = 1;
  }

  ctx.globalCompositeOperation = 'multiply';
  ctx.drawImage(kat, 0, 0);
  ctx.globalCompositeOperation = 'source-over';
  return out;
}

// onizleme: ?ornek=0,60,150 yalniz o kareleri sirayla cizer (0000.png, 0001.png ...)
const ornek = new URLSearchParams(location.search).get('ornek');
if (ornek) {
  const L = ornek.split(',').map(Number);
  surucu(kur, (i) => kare(L[i]), L.length);
} else surucu(kur, kare, KARE);
