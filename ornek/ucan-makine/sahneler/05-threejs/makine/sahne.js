// KOPYA: LeoOS/600-Kanal/Teardown/ucan-makine/ortak. Degisiklik: murekkep #2b1d12 (brif), golge opakligi 0.3.
// Leo defteri sahnesi: duz parsomen zemin, toon boya, ustune murekkep gecisi (kontur + tarama + el titremesi + kagit dokusu).
// Kontur, ayri bir normal/derinlik cizimindeki kirilmalardan cikar; tarama, rengin koyulugundan.
import * as THREE from 'three';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {ShaderPass} from 'three/addons/postprocessing/ShaderPass.js';
import {makineKur} from './makine.js';

export const KAGIT = '#E8D9B8';
export const MUREKKEP = '#2b1d12';

const MUREKKEP_GECISI = {
  uniforms: {
    tDiffuse: {value: null},
    tNormal: {value: null},
    tDerin: {value: null},
    uRes: {value: new THREE.Vector2(1, 1)},
    uNear: {value: 0.1},
    uFar: {value: 100},
    uPr: {value: 1},
    uInk: {value: new THREE.Color(MUREKKEP)},
    uTarama: {value: 1},
  },
  vertexShader: /* glsl */ `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
  fragmentShader: /* glsl */ `
    uniform sampler2D tDiffuse; uniform sampler2D tNormal; uniform sampler2D tDerin;
    uniform vec2 uRes; uniform float uNear; uniform float uFar; uniform float uPr; uniform vec3 uInk; uniform float uTarama;
    varying vec2 vUv;
    float lin(float d){ float z = d * 2.0 - 1.0; return 2.0 * uNear * uFar / (uFar + uNear - z * (uFar - uNear)); }
    float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
    float vn(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
      return mix(mix(h21(i), h21(i + vec2(1.0, 0.0)), f.x), mix(h21(i + vec2(0.0, 1.0)), h21(i + vec2(1.0, 1.0)), f.x), f.y); }
    void main(){
      vec2 px = 1.0 / uRes;
      vec2 fc = vUv * uRes / uPr;               // CSS pikseli cinsinden: tarama sikligi cozunurlukten bagimsiz
      vec2 j = (vec2(vn(fc * 0.045), vn(fc * 0.045 + 17.3)) - 0.5) * 2.4 * uPr * px;   // el titremesi
      vec2 uv = vUv + j;
      vec3 n0 = texture2D(tNormal, uv).xyz * 2.0 - 1.0;
      float d0 = lin(texture2D(tDerin, uv).x);
      float en = 0.0;
      float ed = 0.0;
      float w = 1.15 * uPr;
      for (int k = 0; k < 8; k++) {
        float a = float(k) * 0.785398;
        vec2 o = vec2(cos(a), sin(a)) * w * px;
        vec3 n1 = texture2D(tNormal, uv + o).xyz * 2.0 - 1.0;
        float d1 = lin(texture2D(tDerin, uv + o).x);
        en = max(en, 1.0 - dot(n0, n1));
        ed = max(ed, (d1 - d0) / max(d0, 0.001));
      }
      float kontur = max(smoothstep(0.22, 0.55, en), smoothstep(0.01, 0.03, ed));
      kontur *= 0.75 + 0.25 * vn(fc * 0.3);    // murekkebin kalem baskisi
      vec3 c = texture2D(tDiffuse, vUv).rgb;
      float lum = dot(c, vec3(0.299, 0.587, 0.114));
      float sp = 5.0;
      float t1 = abs(fract((fc.x + fc.y + 3.0 * vn(fc * 0.02)) / sp) - 0.5) * 2.0;
      float t2 = abs(fract((fc.x - fc.y + 3.0 * vn(fc * 0.02 + 9.0)) / (sp * 1.15)) - 0.5) * 2.0;
      float c1 = 1.0 - smoothstep(0.2, 0.5, t1);
      float c2 = 1.0 - smoothstep(0.2, 0.5, t2);
      float kA = 1.0 - smoothstep(0.62, 0.74, lum);
      float kB = 1.0 - smoothstep(0.36, 0.5, lum);
      float tarama = max(c1 * kA, c2 * kB) * (0.55 + 0.45 * vn(fc * 0.06)) * uTarama;
      vec3 col = mix(c, uInk, tarama * 0.5);
      col = mix(col, uInk, kontur * 0.9);
      col *= 0.972 + 0.05 * vn(fc * 0.85) + 0.02 * vn(fc * 0.05);   // kagit dokusu
      gl_FragColor = vec4(col, 1.0);
    }`,
};

export function sahneKur({canvas}) {
  const renderer = new THREE.WebGLRenderer({canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance'});
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(KAGIT);
  const camera = new THREE.PerspectiveCamera(30, 16 / 9, 0.3, 80);

  // isik: tek gunes + yumusak ortam; toon boyasi bunu uc kademeye boler
  const GUNES = new THREE.Vector3(-0.45, 0.85, 0.35).normalize();
  const gunes = new THREE.DirectionalLight('#fff6e6', 2.4);
  gunes.castShadow = true;
  Object.assign(gunes.shadow.camera, {left: -7, right: 7, top: 7, bottom: -7, near: 1, far: 40});
  gunes.shadow.mapSize.set(2048, 2048);
  gunes.shadow.bias = -0.0006;
  gunes.shadow.normalBias = 0.02;
  gunes.position.copy(GUNES).multiplyScalar(18);
  scene.add(gunes, gunes.target);
  scene.add(new THREE.AmbientLight('#fff3dc', 1.05));

  // zemin: gorunmez, yalniz golge alir (golge taramaya doner)
  const golge = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.ShadowMaterial({color: '#5a4228', opacity: 0.3}));
  golge.rotation.x = -Math.PI / 2;
  golge.receiveShadow = true;
  scene.add(golge);

  const makine = makineKur();
  scene.add(makine.kok);

  // normal + derinlik hedefi (kontur icin)
  const ndHedef = new THREE.WebGLRenderTarget(4, 4, {type: THREE.HalfFloatType});
  ndHedef.depthTexture = new THREE.DepthTexture(4, 4);
  const normalMat = new THREE.MeshNormalMaterial({side: THREE.DoubleSide});

  const composer = new EffectComposer(renderer, new THREE.WebGLRenderTarget(4, 4, {type: THREE.HalfFloatType, samples: 4}));
  composer.addPass(new RenderPass(scene, camera));
  composer.addPass(new OutputPass());
  const murekkep = new ShaderPass(MUREKKEP_GECISI);
  composer.addPass(murekkep);

  const size = {w: 1600, h: 900, pr: 1};
  const resize = (w, h, pr) => {
    Object.assign(size, {w, h, pr});
    renderer.setPixelRatio(pr);
    renderer.setSize(w, h, false);
    composer.setPixelRatio(pr);
    composer.setSize(w, h);
    ndHedef.setSize(Math.round(w * pr), Math.round(h * pr));
    murekkep.uniforms.uRes.value.set(Math.round(w * pr), Math.round(h * pr));
    murekkep.uniforms.uPr.value = pr;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  };

  const tmp = new THREE.Vector3();
  const nd = new THREE.Color();
  /** d: makine durumu ({phi, ayrik, bezSaydam, kapakVurgu, yukseklik}); k: kamera ({tx,ty,tz, az, el (radyan), d, sx, sy}) */
  const frame = (d, k) => {
    const p = makine.guncelle(d);
    makine.kok.position.y = d.yukseklik ?? 0;
    camera.position.set(k.tx + k.d * Math.cos(k.el) * Math.sin(k.az), k.ty + k.d * Math.sin(k.el), k.tz + k.d * Math.cos(k.el) * Math.cos(k.az));
    camera.lookAt(k.tx, k.ty, k.tz);
    camera.setViewOffset(size.w, size.h, -(k.sx ?? 0), -(k.sy ?? 0), size.w, size.h);
    camera.updateMatrixWorld();
    // gunes golge kutusu makineyi izler
    tmp.set(0, (d.yukseklik ?? 0) + 1, 0);
    gunes.target.position.copy(tmp);
    gunes.position.copy(tmp).addScaledVector(GUNES, 18);
    gunes.target.updateMatrixWorld();
    // 1) normal + derinlik
    const eskiArka = scene.background;
    renderer.getClearColor(nd);
    const eskiA = renderer.getClearAlpha();
    golge.visible = false;
    const bezGizli = (d.bezSaydam ?? 0) > 0.5;
    for (const kn of makine.kanatlar) kn.bez.visible = !bezGizli;
    makine.pilot.visible = !bezGizli;
    scene.background = null;
    scene.overrideMaterial = normalMat;
    renderer.setClearColor(0x8080ff, 1);
    renderer.setRenderTarget(ndHedef);
    renderer.clear();
    renderer.render(scene, camera);
    renderer.setRenderTarget(null);
    scene.overrideMaterial = null;
    scene.background = eskiArka;
    renderer.setClearColor(nd, eskiA);
    golge.visible = true;
    for (const kn of makine.kanatlar) kn.bez.visible = true;
    makine.pilot.visible = true;
    murekkep.uniforms.tNormal.value = ndHedef.texture;
    murekkep.uniforms.tDerin.value = ndHedef.depthTexture;
    murekkep.uniforms.uNear.value = camera.near;
    murekkep.uniforms.uFar.value = camera.far;
    // 2) renk + murekkep
    composer.render();
    return p;
  };
  const pv = new THREE.Vector3();
  /** dunya noktasi -> 1600x900 sahne pikseli */
  const project = (x, y, z) => {
    pv.set(x, y, z).project(camera);
    if (pv.z > 1) return null;
    return [(pv.x * 0.5 + 0.5) * size.w, (-pv.y * 0.5 + 0.5) * size.h];
  };
  const kalite = ({samples, shadow}) => {
    if (samples !== undefined)
      for (const t of [composer.renderTarget1, composer.renderTarget2]) {
        t.samples = samples;
        t.dispose();
      }
    if (shadow !== undefined) {
      gunes.shadow.mapSize.set(shadow, shadow);
      gunes.shadow.map?.dispose();
      gunes.shadow.map = null;
    }
  };
  return {renderer, scene, camera, composer, makine, resize, frame, project, size, kalite};
}
