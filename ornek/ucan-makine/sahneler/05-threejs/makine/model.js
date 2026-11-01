// KOPYA: LeoOS/600-Kanal/Teardown/ucan-makine/ortak (degismedi).
// Leonardo'nun kanatli ucan makinesi (ornitopter), kodla yeniden kurgu. TEK GIRDI: krank acisi phi (radyan).
// Her parca, her gosterge ve her etiket buradaki pose(phi) fonksiyonunu okur; elle canlandirilan bir sey yok.
// Olculer metre. Leonardo olcu birakmadi; buradaki olculer referans cizimin oranlarindan alinmis yeniden kurgu.
//
// Eksenler: x = kanat acikligi (sag +), y = yukari, z = burun yonu (+). Krank mili x boyunca, krank y-z duzleminde doner.
//
// Zincir:  pedal kolu (ayak) <- itme cubugu <- orta krank   (dort cubuk: krank-kol)
//          orta krank mili -> yan kranklar -> iki biyel -> boyunduruk (dikey kizak)
//          boyunduruk -> iki kol -> kanat kok kaldiraci -> kanat menteşesi (z ekseni) -> kanat acisi theta

const D2R = Math.PI / 180;

export const OLCU = {
  C: {y: 0.34, z: 0.3}, // krank mili ekseni
  rc: 0.15, // yan krank yaricapi (boyunduruk icin)
  L: 0.75, // yan biyel boyu
  xYan: 0.34, // yan kranklarin ve biyellerin x konumu (pilotun iki yaninda)
  rp: 0.1, // orta krank yaricapi (pedal icin)
  T: {y: 0.22, z: -0.95}, // pedal kolu mafsali
  rt: 0.25, // pedal kolunda itme cubugunun baglandigi nokta
  rAyak: 0.45, // pedal kolunda uzengi (ayak) noktasi
  lp: 1.25, // itme cubugu boyu
  H: {x: 0.55, y: 1.55}, // sag kanat menteşesi (sol ayna)
  zH: 0.3,
  rl: 0.3, // kanat kok kaldiraci
  delta: 15 * D2R, // kaldiracin kanada gore dirsek acisi
  a: 0.25, // boyunduruk pimlerinin x konumu
  yukOfs: 0.1, // boyunduruk capraz kirisi biyel ucunun bu kadar ustunde
  R: 4.6, // menteşeden kanat ucuna
  kutle: {pilot: 70, makine: 80}, // kg; makine kutlesi TAHMIN (ahsap + keten, 10 m aciklik)
  rho: 1.225, // deniz seviyesi hava yogunlugu kg/m3
  g: 9.81,
  insanW: 250, // saatlerce degil, dakikalarca surdurulebilir iyi bir sporcu gucu (W)
  atW: 745, // 1 beygir gucu (W)
};

const O = OLCU;
// boyunduruk orta konumdayken kaldirac yatay (theta - delta = 0) olacak sekilde kol boyu
const ysOrta = O.C.y + O.L;
export const L2 = Math.hypot(O.H.x - O.rl - O.a, O.H.y - (ysOrta + O.yukOfs));

/** iki cemberin kesisimi; ust = true ise y'si buyuk olan (2B: [u, v]) */
function kesisim(c0, r0, c1, r1, sec) {
  const dx = c1[0] - c0[0];
  const dy = c1[1] - c0[1];
  const d = Math.hypot(dx, dy);
  const a = (r0 * r0 - r1 * r1 + d * d) / (2 * d);
  const h = Math.sqrt(Math.max(0, r0 * r0 - a * a));
  const mx = c0[0] + (a * dx) / d;
  const my = c0[1] + (a * dy) / d;
  const p1 = [mx + (h * dy) / d, my - (h * dx) / d];
  const p2 = [mx - (h * dy) / d, my + (h * dx) / d];
  return sec(p1, p2) ? p1 : p2;
}

/** kanat acisi (sag kanat, yataydan yukari +) ve tum mafsal noktalari, krank acisi phi'nin fonksiyonu */
export function pose(phi) {
  const s = Math.sin(phi);
  const c = Math.cos(phi);
  // yan krank pimi (z, y) ve boyunduruk: tam kizak-krank denklemi
  const pimYan = {z: O.C.z + O.rc * s, y: O.C.y + O.rc * c};
  const ys = O.C.y + O.rc * c + Math.sqrt(O.L * O.L - O.rc * O.rc * s * s);
  const biyelAci = Math.asin((O.rc * s) / O.L); // biyelin dikeyle acisi (y-z duzlemi)
  const Ky = ys + O.yukOfs;
  // kaldirac pimi Q: H merkezli rl ve K merkezli L2 cemberlerinin kesisimi, ustteki
  const Q = kesisim([O.H.x, O.H.y], O.rl, [O.a, Ky], L2, (p, q) => p[1] > q[1]);
  const theta = Math.atan2(O.H.y - Q[1], O.H.x - Q[0]) + O.delta;
  // orta krank pimi ve pedal kolu (dort cubuk): T merkezli rt ile pim merkezli lp kesisimi, ustteki
  const pimOrta = {z: O.C.z + O.rp * s, y: O.C.y + O.rp * c};
  const P = kesisim([O.T.z, O.T.y], O.rt, [pimOrta.z, pimOrta.y], O.lp, (p, q) => p[1] > q[1]);
  const psi = Math.atan2(P[0] - O.T.z, P[1] - O.T.y); // pedal kolunun dikeyle acisi (+ ileri)
  const ayak = {z: O.T.z + O.rAyak * Math.sin(psi), y: O.T.y + O.rAyak * Math.cos(psi)};
  return {phi, pimYan, ys, biyelAci, Ky, Q: {x: Q[0], y: Q[1]}, theta, pimOrta, pedalPim: {z: P[0], y: P[1]}, psi, ayak};
}

// ------------------------------------------------------------ bir tur boyunca tablo: kanat acisi ve hizi
const N = 720;
export const TABLO = [];
for (let i = 0; i <= N; i++) TABLO.push(pose((i / N) * 2 * Math.PI).theta);
const thMin = Math.min(...TABLO);
const thMax = Math.max(...TABLO);
export const GENLIK = thMax - thMin; // tepeden tepeye kanat yayi (radyan)
export const TH_MIN = thMin;
export const TH_MAX = thMax;
const DTH = TABLO.map((_, i) => (TABLO[(i + 1) % N] - TABLO[(i - 1 + N) % N]) / ((2 * 2 * Math.PI) / N));
const DTH_MAX = Math.max(...DTH.map(Math.abs));
/** d(theta)/d(phi) */
export const egim = (phi) => {
  const u = ((((phi / (2 * Math.PI)) % 1) + 1) % 1) * N;
  const i = Math.floor(u);
  return DTH[i] + (DTH[(i + 1) % N] - DTH[i]) * (u - i);
};
/** kapakcik acikligi 0..1: kanat yukari kalkarken hava ustten bastirir, kapakciklar acilir */
export const kapakcik = (phi) => {
  const k = egim(phi) / DTH_MAX;
  const x = Math.min(1, Math.max(0, (k - 0.05) / 0.35));
  return x * x * (3 - 2 * x);
};

// ------------------------------------------------------------ neden ucamadi: ideal momentum teorisi (en iyimser sinir)
// Kanatlarin supurdugu alan A, havayi asagi iten ideal bir disk gibi dusunulur. Gercek kanat bundan kotudur.
export const AGIRLIK = (O.kutle.pilot + O.kutle.makine) * O.g; // N
export const ALAN = O.R * O.R * GENLIK; // iki kanat: 2 x (1/2 R^2 x yay)
export const GEREKEN_W = Math.pow(AGIRLIK, 1.5) / Math.sqrt(2 * O.rho * ALAN);
/** P watt gucle ideal olarak kaldirilabilecek kuvvet (N) */
export const kaldirma = (P) => Math.cbrt(P * P * 2 * O.rho * ALAN);
/** guc -> kanat cirpma frekansi (Hz). Aerodinamik guc hizin kupuyle buyur; 250 W = saniyede 1 cirpma kabulu. */
export const frekans = (P) => Math.cbrt(Math.max(0, P) / O.insanW);
/** kalkis yuksekligi hedefi (m): kaldirma agirligi gecerse makine yukselir, gecmezse yerde kalir */
export const yukseklik = (P) => Math.min(3, Math.max(0, (kaldirma(P) / AGIRLIK - 1) * 20));
export const kg = (N_) => N_ / O.g;
