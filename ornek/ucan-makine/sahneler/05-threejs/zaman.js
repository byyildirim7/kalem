// Sahne 5 zaman cizelgesi: her sey kare numarasinin (f) saf fonksiyonu. Sayfa ve olaylar.mjs ayni dosyayi okur.
import {pose} from './makine/model.js';

export const KARE = 300;
export const FPS = 30;

const sm = (x) => {
  const u = Math.min(1, Math.max(0, x));
  return u * u * u * (u * (u * 6 - 15) + 10);
};
export const ss = (a, b, f) => sm((f - a) / (b - a));

// ------------------------------------------------------------ akis
export const ACILIS = [12, 74]; // 3D murekkep yikamasiyla belirir (kare)
export const ESKIZ_CEK = [36, 100]; // eskiz cekilir
const CIRP = {bas: 84, tam: 124, yavas: 242, dur: 284}; // kanat cirpma: baslar, tam hiz, yavaslar, durur
const DON = [92, 282]; // kamera donusu

export const acilis = (f) => ss(ACILIS[0], ACILIS[1], f);
export const eskizO = (f) => 1 - ss(ESKIZ_CEK[0], ESKIZ_CEK[1], f);

// ------------------------------------------------------------ krank acisi: hiz profili toplanir, tam sayi tur atar
// PHI0: kanat ~20 derece yukarida, asagi inerken (eskizdeki durusa en yakin aci). Butun tur sayisi: son kare ayni durus.
const profil = (f) => ss(CIRP.bas, CIRP.tam, f) * (1 - ss(CIRP.yavas, CIRP.dur, f));
const ALT = 8; // kare basina alt adim (integral)
const BIRIKIM = [0];
for (let f = 0; f < KARE + 1; f++) {
  let s = 0;
  for (let k = 0; k < ALT; k++) s += profil(f + (k + 0.5) / ALT);
  BIRIKIM.push(BIRIKIM[f] + s / ALT);
}
const HEDEF_HZ = 0.95;
export const TUR = Math.round((HEDEF_HZ / FPS) * BIRIKIM[KARE]);
const OLCEK = TUR / BIRIKIM[KARE]; // tur / (profil-kare)
export const frekans = (f) => profil(f) * OLCEK * FPS; // Hz
export const PHI0 = 4.63;
export const phiAt = (f) => PHI0 + 2 * Math.PI * OLCEK * BIRIKIM[Math.max(0, Math.min(KARE, f))];
export const thetaAt = (f) => pose(phiAt(f)).theta;

// ------------------------------------------------------------ kamera (derece). az 90 = tam yan (burun solda, eskizle ayni)
export const FOV = 15; // dar aci: yandan bakista yakin kanat dev gorunmesin (eskiz neredeyse ortografik)
export function kamAt(f) {
  const k = ss(DON[0], DON[1], f);
  const yak = ss(0, ACILIS[1] + 30, f); // acilista cok hafif yaklasma
  const pay = ss(70, 130, f); // kanat cirpmaya baslarken ust bosluk acilir (kanat ucu kadraja sigsin)
  return {
    tx: 0,
    ty: 2.0 + 0.62 * pay - 0.3 * k + 0.2 * Math.sin(Math.PI * k),
    tz: -0.7 + 0.7 * k,
    az: 80 - 120 * k,
    el: 6 + 12 * k,
    d: 22 - 0.6 * yak + 1.6 * pay + 3.1 * k + 1.5 * Math.sin(Math.PI * k),
    sx: 0,
    sy: 0,
  };
}

// ------------------------------------------------------------ ses olaylari
export function olaylar() {
  const out = [{kare: ACILIS[0], tur: 'hisirti', guc: 0.55}];
  for (let f = 1; f < KARE - 1; f++) {
    const a = thetaAt(f - 1);
    const b = thetaAt(f);
    const c = thetaAt(f + 1);
    // asagi vurus baslangici: kanat tepede, inmeye basliyor
    if (b >= a && b > c + 1e-6 && frekans(f) > 0.15) {
      const g = Math.min(1, frekans(f + 4) / HEDEF_HZ);
      out.push({kare: f, tur: 'kanat', guc: Math.round((0.35 + 0.6 * g) * 100) / 100});
    }
  }
  return out;
}
