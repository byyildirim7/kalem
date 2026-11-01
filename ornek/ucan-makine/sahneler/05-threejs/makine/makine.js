// KOPYA: LeoOS/600-Kanal/Teardown/ucan-makine/ortak. Degisiklik: kirmizi #b3261e (brif).
// Ucan makinenin kodla kurulmus geometrisi (metre). guncelle(durum) her parcayi model.js'teki pose(phi)'den yerlestirir.
// Gorunum Leo defteri: duz toon boya + murekkep konturu ve tarama (sahne.js'teki murekkep gecisi).
import * as THREE from 'three';
import {OLCU as O, L2, pose, kapakcik} from './model.js';

const V3 = THREE.Vector3;
export const RENK = {
  agac: '#D2B587',
  agacKoyu: '#B8956A',
  keten: '#F4EAD3',
  pilot: '#E4D0AB',
  demir: '#6A543A',
  ip: '#8C7552',
  kir: '#b3261e',
};

// 3 kademeli toon gecisi: isik, yari golge, golge (tarama bu kademelere oturur)
const GRAD = (() => {
  const d = new Uint8Array([120, 120, 120, 255, 200, 200, 200, 255, 255, 255, 255, 255]);
  const t = new THREE.DataTexture(d, 3, 1, THREE.RGBAFormat);
  t.minFilter = t.magFilter = THREE.NearestFilter;
  t.needsUpdate = true;
  return t;
})();
const toon = (color, extra = {}) => new THREE.MeshToonMaterial({color, gradientMap: GRAD, ...extra});

const Y = new V3(0, 1, 0);
/** birim silindiri (y boyunca boy 1) a'dan b'ye yerlestirir */
export function yerlestir(m, a, b) {
  const d = new V3().subVectors(b, a);
  const l = d.length();
  m.position.copy(a).addScaledVector(d, 0.5);
  m.scale.set(1, Math.max(1e-4, l), 1);
  m.quaternion.setFromUnitVectors(Y, d.multiplyScalar(1 / Math.max(1e-6, l)));
}

export function makineKur() {
  const M = {
    agac: toon(RENK.agac),
    agacKoyu: toon(RENK.agacKoyu),
    keten: toon(RENK.keten, {side: THREE.DoubleSide, transparent: true, opacity: 1, emissive: '#5a4a30'}),
    kapak: toon(RENK.keten, {side: THREE.DoubleSide, emissive: '#5a4a30'}),
    pilot: toon(RENK.pilot),
    demir: toon(RENK.demir),
    ip: toon(RENK.ip),
    kir: toon(RENK.kir),
  };
  const kok = new THREE.Group();
  const tum = [];
  const ekle = (ebeveyn, geo, mat) => {
    const m = new THREE.Mesh(geo, mat);
    m.castShadow = true;
    m.receiveShadow = true;
    ebeveyn.add(m);
    tum.push(m);
    return m;
  };
  const silGeo = (r, seg = 7) => new THREE.CylinderGeometry(r, r, 1, seg, 1);
  const cubuk = (ebeveyn, a, b, r, mat, seg = 7) => {
    const m = ekle(ebeveyn, silGeo(r, seg), mat);
    yerlestir(m, a, b);
    return m;
  };
  const egri = (ebeveyn, pts, r, mat, n = 48, seg = 6) => ekle(ebeveyn, new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), n, r, seg, false), mat);
  const baglama = (ebeveyn, p, r = 0.05) => {
    const m = ekle(ebeveyn, new THREE.TorusGeometry(r, 0.012, 5, 12), M.ip);
    m.position.copy(p);
    return m;
  };

  // ------------------------------------------------------------ govde: kayik bicimli kafes
  const govde = new THREE.Group();
  kok.add(govde);
  const ZB = 2.15;
  const gen = (z, w) => w * Math.pow(Math.max(0, 1 - (z / ZB) ** 2), 0.6);
  const yAlt = (z) => 0.14 + 0.38 * (z / ZB) ** 2;
  const yUst = (z) => 1.0 - 0.42 * (z / ZB) ** 2;
  const burun = new V3(0, 0.55, ZB);
  const kuyrukKok = new V3(0, 0.55, -ZB);
  const ray = (wf, yf, s) => {
    const pts = [burun.clone()];
    for (let i = 1; i < 24; i++) {
      const z = ZB - (i / 24) * 2 * ZB;
      pts.push(new V3(s * gen(z, wf), yf(z), z));
    }
    pts.push(kuyrukKok.clone());
    return pts;
  };
  for (const s of [-1, 1]) {
    egri(govde, ray(0.45, yAlt, s), 0.04, M.agacKoyu, 64);
    egri(govde, ray(0.41, yUst, s), 0.034, M.agac, 64);
  }
  // capraz cerceveler
  for (const z of [1.55, 1.0, 0.3, -0.35, -0.95, -1.55]) {
    const wa = gen(z, 0.45);
    const wu = gen(z, 0.41);
    for (const s of [-1, 1]) {
      cubuk(govde, new V3(s * wa, yAlt(z), z), new V3(s * wu, yUst(z), z), 0.026, M.agac);
      baglama(govde, new V3(s * wu, yUst(z), z), 0.045);
    }
    cubuk(govde, new V3(-wa, yAlt(z), z), new V3(wa, yAlt(z), z), 0.028, M.agacKoyu);
    if (Math.abs(z - 0.3) > 0.01) cubuk(govde, new V3(-wu, yUst(z), z), new V3(wu, yUst(z), z), 0.022, M.agac);
  }
  // yere basan iki kizak ayagi
  for (const z of [1.0, -0.95]) {
    for (const s of [-1, 1]) cubuk(govde, new V3(s * gen(z, 0.45), yAlt(z), z), new V3(s * 0.5, 0.02, z), 0.024, M.agacKoyu);
  }
  for (const s of [-1, 1]) cubuk(govde, new V3(s * 0.5, 0.02, 1.3), new V3(s * 0.5, 0.02, -1.25), 0.03, M.agacKoyu);
  // pilot tahtasi
  const tahta = ekle(govde, new THREE.BoxGeometry(0.4, 0.035, 1.1), M.agacKoyu);
  tahta.position.set(0, 0.5, 0.45);
  for (const z of [0.0, 0.9]) cubuk(govde, new V3(0, 0.5, z), new V3(0, yAlt(z), z), 0.02, M.agac);
  // el tutamagi
  cubuk(govde, new V3(-gen(1.18, 0.41) * 0.95, 0.6, 1.18), new V3(gen(1.18, 0.41) * 0.95, 0.6, 1.18), 0.022, M.agac);
  // omuz kulesi: iki A cercevesi (on/arka), tepe kirisi, menteşe yataklari
  const zH = O.zH;
  for (const dz of [-0.12, 0.12]) {
    for (const s of [-1, 1]) cubuk(govde, new V3(s * gen(zH, 0.41), yUst(zH), zH + dz * 2.5), new V3(s * 0.6, 1.64, zH + dz), 0.03, M.agac);
    cubuk(govde, new V3(-0.66, 1.64, zH + dz), new V3(0.66, 1.64, zH + dz), 0.03, M.agac);
  }
  for (const s of [-1, 1]) {
    const ym = ekle(govde, new THREE.BoxGeometry(0.1, 0.16, 0.3), M.demir);
    ym.position.set(s * O.H.x, O.H.y + 0.06, zH);
    baglama(govde, new V3(s * 0.6, 1.64, zH + 0.12), 0.05);
    baglama(govde, new V3(s * 0.6, 1.64, zH - 0.12), 0.05);
  }
  // ust capraz kiris (z = 0.3) ve boyunduruk kilavuz yuvalari
  const wu3 = gen(zH, 0.41);
  cubuk(govde, new V3(-wu3, 0.98, zH), new V3(wu3, 0.98, zH), 0.03, M.agac);
  for (const s of [-1, 1]) {
    const yuva = ekle(govde, new THREE.CylinderGeometry(0.045, 0.045, 0.09, 10), M.demir);
    yuva.position.set(s * 0.4, 0.98, zH);
  }
  // makara ve halatlar (sus degil: kuyruk dumenine giden ip yolu)
  const makara = ekle(govde, new THREE.CylinderGeometry(0.11, 0.11, 0.05, 20), M.agacKoyu);
  makara.rotation.z = Math.PI / 2;
  makara.position.set(0, 1.18, -0.55);
  cubuk(govde, new V3(0, yUst(-0.55), -0.55), new V3(0, 1.1, -0.55), 0.022, M.agac);
  cubuk(govde, new V3(0, 1.29, -0.55), new V3(0, 1.62, zH - 0.12), 0.006, M.ip, 4);
  cubuk(govde, new V3(0, 1.07, -0.55), new V3(0, 0.6, -ZB - 0.05), 0.006, M.ip, 4);

  // ------------------------------------------------------------ krank mili ve kranklar (tek girdi burada doner)
  const krank = new THREE.Group();
  krank.position.set(0, O.C.y, O.C.z);
  kok.add(krank);
  const mil = ekle(krank, silGeo(0.028, 10), M.demir);
  mil.rotation.z = Math.PI / 2;
  mil.scale.y = 0.9;
  for (const [x, r] of [[-O.xYan, O.rc], [0, O.rp], [O.xYan, O.rc]]) {
    for (const dx of [-0.03, 0.03]) {
      const kol = ekle(krank, new THREE.BoxGeometry(0.022, r + 0.07, 0.07), M.kir);
      kol.position.set(x + dx, r / 2, 0);
    }
    const pim = ekle(krank, silGeo(0.02, 8), M.demir);
    pim.rotation.z = Math.PI / 2;
    pim.scale.y = 0.1;
    pim.position.set(x, r, 0);
  }
  for (const s of [-1, 1]) {
    const yat = ekle(govde, new THREE.BoxGeometry(0.06, 0.12, 0.1), M.demir);
    yat.position.set(s * 0.43, O.C.y, O.C.z);
    cubuk(govde, new V3(s * 0.43, O.C.y - 0.06, O.C.z), new V3(s * 0.43, yAlt(O.C.z), O.C.z), 0.02, M.agac);
  }

  // ------------------------------------------------------------ biyeller, boyunduruk, kollar
  const mekan = new THREE.Group(); // patlatmada birlikte hareket edenler
  kok.add(mekan);
  const biyel = [-1, 1].map(() => ekle(mekan, silGeo(0.024, 7), M.agacKoyu));
  const ysOrta = O.C.y + O.L;
  const boy = new THREE.Group();
  mekan.add(boy);
  // boyunduruk: iki dikey kizak cubugu (x = +-0.40) + capraz kiris + biyel ucu pimleri
  for (const s of [-1, 1]) {
    cubuk(boy, new V3(s * 0.4, ysOrta - 0.25, zH), new V3(s * 0.4, ysOrta + O.yukOfs + 0.03, zH), 0.026, M.agac);
    cubuk(boy, new V3(s * O.xYan, ysOrta, zH), new V3(s * 0.42, ysOrta, zH), 0.016, M.demir);
  }
  cubuk(boy, new V3(-0.44, ysOrta + O.yukOfs, zH), new V3(0.44, ysOrta + O.yukOfs, zH), 0.032, M.agac);
  for (const s of [-1, 1]) {
    const p = ekle(boy, silGeo(0.018, 8), M.demir);
    p.rotation.x = Math.PI / 2;
    p.scale.y = 0.12;
    p.position.set(s * O.a, ysOrta + O.yukOfs, zH);
  }
  const kol = [-1, 1].map(() => ekle(mekan, silGeo(0.022, 7), M.agacKoyu));

  // ------------------------------------------------------------ pedal kolu, itme cubugu
  const pedal = new THREE.Group();
  pedal.position.set(0, O.T.y, O.T.z);
  mekan.add(pedal);
  cubuk(pedal, new V3(0, 0, 0), new V3(0, O.rAyak + 0.04, 0), 0.026, M.agacKoyu);
  cubuk(pedal, new V3(-0.2, O.rAyak, 0), new V3(0.2, O.rAyak, 0), 0.02, M.demir);
  for (const s of [-1, 1]) {
    const u = ekle(pedal, new THREE.TorusGeometry(0.06, 0.012, 5, 12, Math.PI), M.demir);
    u.position.set(s * 0.12, O.rAyak, 0);
    u.rotation.y = Math.PI / 2;
  }
  const pedalYatak = ekle(govde, new THREE.BoxGeometry(0.12, 0.06, 0.08), M.demir);
  pedalYatak.position.set(0, O.T.y - 0.03, O.T.z);
  cubuk(govde, new V3(0, O.T.y - 0.06, O.T.z), new V3(0, yAlt(O.T.z), O.T.z), 0.02, M.agac);
  const itme = ekle(mekan, silGeo(0.02, 7), M.agacKoyu);

  // ------------------------------------------------------------ kanatlar (sag kurulur, sol ayna)
  // kanat yerel ekseni: x aciklik (menteşeden disa), z kiris (on +), y kanat normali
  const ON = [[0.0, 0.05], [0.9, 0.3], [1.8, 0.42], [2.7, 0.4], [3.5, 0.28], [4.2, 0.05], [4.7, -0.5]];
  const KABURGA = [[[0.05, 0.05], [0.2, -1.25]], [[0.9, 0.3], [1.0, -1.5]], [[1.8, 0.42], [1.9, -1.6]], [[2.7, 0.4], [2.85, -1.45]], [[3.5, 0.28], [3.7, -1.15]], [[4.2, 0.05], [4.45, -0.8]]];
  const KAPAK = [];
  for (const [x0, x1] of [[1.97, 2.31], [2.36, 2.68], [2.93, 3.19], [3.23, 3.47]])
    for (const [z0, z1] of [[-0.14, -0.54], [-0.6, -0.98]]) KAPAK.push({x0, x1, z0, z1});
  const kanatSekli = () => {
    const sh = new THREE.Shape();
    sh.moveTo(ON[0][0], ON[0][1]);
    const on = new THREE.CatmullRomCurve3(ON.map(([x, z]) => new V3(x, z, 0))).getPoints(40);
    for (const p of on) sh.lineTo(p.x, p.y);
    // firfirli arka kenar: kaburga uclari arasi iceri kavis
    const uc = [[4.7, -0.5], ...KABURGA.slice().reverse().map((k) => k[1])];
    for (let i = 0; i < uc.length - 1; i++) {
      const [ax, az] = uc[i];
      const [bx, bz] = uc[i + 1];
      const mx = (ax + bx) / 2;
      const mz = (az + bz) / 2;
      const nx = -(bz - az);
      const nz = bx - ax;
      const nl = Math.hypot(nx, nz);
      const derin = 0.16 + 0.04 * i;
      sh.quadraticCurveTo(mx - (nx / nl) * derin * -1, mz - (nz / nl) * derin * -1, bx, bz);
    }
    sh.lineTo(ON[0][0], ON[0][1]);
    for (const k of KAPAK) {
      const h = new THREE.Path();
      h.moveTo(k.x0, k.z0);
      h.lineTo(k.x0, k.z1);
      h.lineTo(k.x1, k.z1);
      h.lineTo(k.x1, k.z0);
      h.closePath();
      sh.holes.push(h);
    }
    const g = new THREE.ShapeGeometry(sh, 16);
    g.rotateX(Math.PI / 2);
    return g;
  };
  const kanatGeo = kanatSekli();
  const kanatlar = [1, -1].map((sx) => {
    const ayna = new THREE.Group();
    ayna.scale.x = sx;
    kok.add(ayna);
    const k = new THREE.Group();
    k.position.set(O.H.x, O.H.y, zH);
    ayna.add(k);
    const bez = ekle(k, kanatGeo, M.keten);
    bez.userData.bez = true;
    bez.position.y = -0.01;
    // on kiris (kalin), kaburgalar (ince), kok kaldiraci (dirsekli)
    egri(k, ON.map(([x, z], i) => new V3(x, 0.03 * Math.sin((i / (ON.length - 1)) * Math.PI), z)), 0.045, M.agacKoyu, 60);
    for (const [[ax, az], [bx, bz]] of KABURGA) cubuk(k, new V3(ax, 0.01, az), new V3(bx, 0, bz), 0.016, M.agac, 5);
    // kapakcik cubuklari (her kapak sirasinin on kenarinda menteşe cubugu)
    for (const k2 of KAPAK) cubuk(k, new V3(k2.x0 - 0.02, 0.012, k2.z0 + 0.02), new V3(k2.x1 + 0.02, 0.012, k2.z0 + 0.02), 0.01, M.agac, 5);
    const Ql = new V3(-O.rl * Math.cos(O.delta), O.rl * Math.sin(O.delta), 0);
    cubuk(k, new V3(0, 0, 0), Ql, 0.034, M.agacKoyu);
    const mp = ekle(k, silGeo(0.03, 10), M.demir);
    mp.rotation.x = Math.PI / 2;
    mp.scale.y = 0.34;
    const kp = ekle(k, silGeo(0.016, 8), M.demir);
    kp.rotation.x = Math.PI / 2;
    kp.scale.y = 0.1;
    kp.position.copy(Ql);
    // kapakciklar: on kenarindan menteşeli
    const kapaklar = KAPAK.map((k2) => {
      const g = new THREE.PlaneGeometry(k2.x1 - k2.x0 - 0.01, k2.z0 - k2.z1 - 0.01);
      g.rotateX(-Math.PI / 2);
      g.translate((k2.x1 + k2.x0) / 2, 0, -(k2.z0 - k2.z1) / 2);
      const m = ekle(k, g, M.kapak);
      m.position.set(0, 0.004, k2.z0);
      m.userData.kapak = true;
      return m;
    });
    return {ayna, k, kapaklar, bez};
  });

  // ------------------------------------------------------------ kuyruk: dikey yelpaze dumen
  const kuyruk = new THREE.Group();
  kuyruk.position.copy(kuyrukKok);
  kok.add(kuyruk);
  cubuk(kuyruk, new V3(0, 0, 0.05), new V3(0, 0, -0.35), 0.035, M.agacKoyu);
  {
    const K0 = new V3(0, 0, -0.35);
    const n = 7;
    const uc = [];
    for (let i = 0; i < n; i++) {
      const a = (-55 + (110 * i) / (n - 1)) * (Math.PI / 180);
      const p = new V3(0, Math.sin(a) * 1.05, -0.35 - Math.cos(a) * 1.05);
      uc.push(p);
      cubuk(kuyruk, K0, p, 0.014, M.agac, 5);
    }
    // sekil duzlemi (u = -z, v = y): kok -> uc0 -> kavisli kenarlar -> kok
    const sh = new THREE.Shape();
    sh.moveTo(0.35, 0);
    sh.lineTo(-uc[0].z, uc[0].y);
    for (let i = 1; i < n; i++) {
      const p = uc[i];
      const q = uc[i - 1];
      const mu = (-p.z - q.z) / 2;
      const mv = (p.y + q.y) / 2;
      sh.quadraticCurveTo(0.35 + (mu - 0.35) * 0.86, mv * 0.86, -p.z, p.y);
    }
    sh.lineTo(0.35, 0);
    const g = new THREE.ShapeGeometry(sh, 10);
    // sekil (u, v) -> (x 0, y v, z -u)
    g.rotateY(Math.PI / 2);
    const m = ekle(kuyruk, g, M.keten);
    m.userData.bez = true;
  }

  // ------------------------------------------------------------ pilot: tahta manken, yuzustu
  const pilot = new THREE.Group();
  kok.add(pilot);
  const kure = (p, r) => {
    const m = ekle(pilot, new THREE.SphereGeometry(r, 14, 10), M.pilot);
    m.position.copy(p);
    return m;
  };
  const uzuv = (a, b, r) => {
    const m = ekle(pilot, new THREE.CapsuleGeometry(r, 1, 4, 10), M.pilot);
    yerlestir(m, a, b);
    // kapsulun yuvarlak uclari boyla olceklenmesin
    m.scale.y = Math.max(0.01, a.distanceTo(b) - 2 * r);
    return m;
  };
  kure(new V3(0, 0.8, 0.86), 0.11);
  uzuv(new V3(0, 0.77, 0.74), new V3(0, 0.75, 0.66), 0.045);
  const govdeP = ekle(pilot, new THREE.CapsuleGeometry(0.15, 0.5, 4, 12), M.pilot);
  govdeP.rotation.x = Math.PI / 2;
  govdeP.scale.set(1.25, 1, 0.85);
  govdeP.position.set(0, 0.67, 0.33);
  const omuz = [-1, 1].map((s) => new V3(s * 0.2, 0.72, 0.6));
  const el = [-1, 1].map((s) => new V3(s * 0.22, 0.62, 1.15));
  for (let i = 0; i < 2; i++) {
    const dirsek = omuz[i].clone().lerp(el[i], 0.5).add(new V3(0, -0.09, 0));
    uzuv(omuz[i], dirsek, 0.042);
    uzuv(dirsek, el[i], 0.038);
    kure(el[i], 0.045);
  }
  kure(new V3(0, 0.64, -0.08), 0.13).scale.set(1.35, 0.8, 1);
  const bacak = [-1, 1].map(() => ({uyluk: uzuv(new V3(), new V3(0, 0.1, 0), 0.06), baldir: uzuv(new V3(), new V3(0, 0.1, 0), 0.05), diz: kure(new V3(), 0.05), ayak: kure(new V3(), 0.05)}));
  const KALCA_Z = -0.15;
  const UY = 0.48;
  const BA = 0.5;

  // ------------------------------------------------------------ guncelle
  const KIR = new THREE.Color(RENK.kir);
  const KIR_E = new THREE.Color('#6a1c10');
  const tmpA = new V3();
  const tmpB = new V3();
  const sonPose = {p: pose(0)};
  const durum0 = {phi: 0, ayrik: 0, bezSaydam: 0, kapakVurgu: 0};
  const guncelle = (d = durum0) => {
    const p = pose(d.phi);
    sonPose.p = p;
    const e = d.ayrik ?? 0;
    // patlatma: parcalar kendi yonlerinde acilir
    pilot.position.set(0, 0.95 * e, 0.15 * e);
    mekan.position.set(0, 0, 0);
    kuyruk.position.set(0, kuyrukKok.y + 0.15 * e, kuyrukKok.z - 0.8 * e);
    krank.position.set(0, O.C.y - 0.45 * e, O.C.z);
    krank.rotation.x = p.phi;
    const yk = 0.6 * e; // boyunduruk + kollar yukari
    boy.position.y = p.ys - ysOrta + yk;
    for (let i = 0; i < 2; i++) {
      const s = i ? 1 : -1;
      // biyel: krank pimi -> boyunduruk biyel ucu (patlatmada uzar: iki parcanin ayrildigini gosterir)
      tmpA.set(s * O.xYan, p.pimYan.y - 0.45 * e, p.pimYan.z);
      tmpB.set(s * O.xYan, p.ys + yk, O.C.z);
      yerlestir(biyel[i], tmpA, tmpB);
      tmpA.set(s * O.a, p.Ky + yk, O.zH);
      tmpB.set(s * (p.Q.x + 0.5 * e), p.Q.y + 0.3 * e, O.zH);
      yerlestir(kol[i], tmpA, tmpB);
    }
    // kanatlar
    for (const kn of kanatlar) {
      kn.k.position.set(O.H.x + 0.5 * e, O.H.y + 0.3 * e, O.zH);
      kn.k.rotation.z = p.theta;
      const ac = kapakcik(p.phi) * (70 * Math.PI) / 180;
      for (const m of kn.kapaklar) m.rotation.x = -ac;
    }
    // pedal ve itme cubugu
    pedal.position.set(0, O.T.y - 0.3 * e, O.T.z - 0.3 * e);
    pedal.rotation.x = p.psi;
    tmpA.set(0, p.pimOrta.y - 0.45 * e, p.pimOrta.z);
    tmpB.set(0, p.pedalPim.y - 0.3 * e, p.pedalPim.z - 0.3 * e);
    yerlestir(itme, tmpA, tmpB);
    // bacaklar: kalca -> uzengi, iki kemikli ters kinematik, diz asagi
    for (let i = 0; i < 2; i++) {
      const s = i ? 1 : -1;
      const kalca = new V3(s * 0.1, 0.64, KALCA_Z);
      // patlatmada pilot butun olarak kalkar, bacak durusu ayni kalir (pilotun yerel uzayi)
      const ayak = new V3(s * 0.12, p.ayak.y + 0.03, p.ayak.z);
      const dz = ayak.z - kalca.z;
      const dy = ayak.y - kalca.y;
      const dist = Math.min(UY + BA - 1e-3, Math.hypot(dz, dy));
      const ang = Math.atan2(dy, dz); // y-z duzleminde: aci z ekseninden
      const cosA = (UY * UY + dist * dist - BA * BA) / (2 * UY * dist);
      const a = Math.acos(Math.max(-1, Math.min(1, cosA)));
      // iki cozum: dizi asagida olani sec (yuzustu yatan biri ayagiyla geri iterken diz yere bakar)
      const d1 = ang + a;
      const d2 = ang - a;
      const yy = (q) => kalca.y + UY * Math.sin(q);
      const q = yy(d1) < yy(d2) ? d1 : d2;
      const diz = new V3(s * 0.11, kalca.y + UY * Math.sin(q), kalca.z + UY * Math.cos(q));
      const b = bacak[i];
      b.uyluk.scale.set(1, 1, 1);
      yerlestir(b.uyluk, kalca, diz);
      b.uyluk.scale.y = Math.max(0.01, kalca.distanceTo(diz) - 0.12);
      yerlestir(b.baldir, diz, ayak);
      b.baldir.scale.y = Math.max(0.01, diz.distanceTo(ayak) - 0.1);
      b.diz.position.copy(diz);
      b.ayak.position.copy(ayak);
    }
    // gorunum modlari
    const sa = d.bezSaydam ?? 0;
    M.keten.opacity = 1 - 0.8 * sa;
    M.keten.depthWrite = sa < 0.5;
    M.pilot.transparent = sa > 0.01;
    M.pilot.opacity = 1 - 0.78 * sa;
    M.pilot.depthWrite = sa < 0.5;
    const kv = d.kapakVurgu ?? 0;
    M.kapak.color.set(RENK.keten).lerp(KIR, 0.9 * kv);
    M.kapak.emissive.set('#5a4a30').lerp(KIR_E, kv);
    return p;
  };
  guncelle();
  return {kok, guncelle, M, tum, kanatlar, pilot, krank, boy, pedal, kuyruk, govde, sonPose, zemin: 0};
}
