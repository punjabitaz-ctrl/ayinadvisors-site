/* AYiN Advisors - Home hero iris, WebGL edition (Phase 2d).
   Built by tools/hero3d/build.mjs into assets/hero3d.js (committed; the site has no build step on the host).

   Contract with the page:
   - The 2D canvas #iris (assets/site.js) is the baseline and the fallback. This script runs only on desktop-class
     devices (>= 720px, hover or fine pointer, no reduced motion, no data saver). Anything that goes wrong
     (no WebGL, an exception, a lost context) removes our canvas and hands the hero back to the 2D canvas.
   - Colours are never written here: they are read from the CSS roles --accent-fill, --ink and --surface of the
     surface the canvas sits on, at start and on every `themechange`.
   - Rendering is on demand. A frame is scheduled only while the pointer or scroll moves the scene or while the
     scene is still easing toward its target; then requestAnimationFrame stops. The one-off entrance lasts 1.8 s
     (under the WCAG 2.2.2 limit of 5 s). Nothing moves by itself afterwards. */
import {
  BufferGeometry, CircleGeometry, Color, Float32BufferAttribute, Group, LineBasicMaterial, LineDashedMaterial,
  LineLoop, LineSegments, Mesh, MeshBasicMaterial, PerspectiveCamera, Scene, WebGLRenderer,
} from "three";

const ENTRANCE_MS = 1800;
const EASE = 6;            // 1/s, pointer and scroll easing rate
const SETTLE = 0.0015;     // stop rendering once every eased value is this close to its target
const MAX_YAW = 0.3, MAX_PITCH = 0.18, MAX_CAM = 0.28;   // pointer bounds (radians / scene units)

const supported = () => {
  const mm = (q) => window.matchMedia && window.matchMedia(q).matches;
  if (mm("(prefers-reduced-motion: reduce)")) return false;
  if (window.innerWidth < 720) return false;
  if (!mm("(pointer: fine)") && !mm("(hover: hover)")) return false;
  const c = navigator.connection;
  if (c && c.saveData) return false;
  return true;
};

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

function rng(seed) {               // small deterministic PRNG so the node layout is the same on every visit
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function circlePoints(r, n) {
  const p = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    p[i * 3] = Math.cos(a) * r;
    p[i * 3 + 1] = Math.sin(a) * r;
  }
  return p;
}
const loopGeometry = (r, n = 144) => {
  const g = new BufferGeometry();
  g.setAttribute("position", new Float32BufferAttribute(circlePoints(r, n), 3));
  return g;
};

function start() {
  const hero = document.querySelector(".hero");
  const flat = document.getElementById("iris");
  if (!hero || !flat || !supported()) return;

  const canvas = document.createElement("canvas");
  canvas.id = "iris3d";
  canvas.setAttribute("aria-hidden", "true");
  canvas.setAttribute("role", "presentation");

  let renderer;
  try {
    renderer = new WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: "low-power" });
  } catch (e) {
    return;                        // no WebGL: the 2D canvas keeps running untouched
  }

  /* ---------- colours from the page's CSS roles ---------- */
  const probe = document.createElement("canvas").getContext("2d");
  const role = (name) => {
    const v = getComputedStyle(flat).getPropertyValue(name).trim();
    if (!v) throw new Error("missing CSS role " + name);
    probe.fillStyle = v;
    return new Color(probe.fillStyle);
  };
  const gold = new Color(), ink = new Color(), surface = new Color();
  const readColours = () => {
    gold.copy(role("--accent-fill"));
    ink.copy(role("--ink"));
    surface.copy(role("--surface"));
  };

  /* ---------- scene ---------- */
  const scene = new Scene();
  const camera = new PerspectiveCamera(38, 1, 0.1, 60);
  camera.position.set(0, 0, 9);
  const iris = new Group();
  scene.add(iris);

  const R = 2.35;
  const layers = [];               // { obj, z, push } : push = how far the layer spreads with scroll
  const disposables = [];
  const mat = (Material, color, opacity, extra) => {
    const m = new Material(Object.assign({ transparent: true, opacity, depthWrite: false }, extra || {}));
    m.userData.base = opacity;
    m.userData.role = color;       // "gold" | "ink" | "surface"
    disposables.push(m);
    return m;
  };
  const add = (obj, z, push, geometry) => {
    obj.position.z = z;
    iris.add(obj);
    layers.push({ obj, z, push });
    if (geometry) disposables.push(geometry);
    return obj;
  };

  // concentric rings at different depths
  const RINGS = 7;
  for (let i = 1; i <= RINGS; i++) {
    const g = loopGeometry((R * i) / RINGS);
    add(new LineLoop(g, mat(LineBasicMaterial, "gold", 0.2 + (i / RINGS) * 0.34)), (i - 4) * 0.42, 1, g);
  }
  // dashed ring (turns with the scroll and pointer, never on its own)
  const dashG = loopGeometry(R * 0.74, 200);
  const dashed = new LineLoop(dashG, mat(LineDashedMaterial, "gold", 0.6, { dashSize: 0.03, gapSize: 0.17 }));
  dashed.computeLineDistances();
  add(dashed, 0.35, 0.8, dashG);
  // ripple rings, further out and further back
  [1.1, 1.26, 1.45].forEach((k, i) => {
    const g = loopGeometry(R * k, 160);
    add(new LineLoop(g, mat(LineBasicMaterial, "ink", 0.13 - i * 0.03)), -1.4 - i * 0.7, 1.6 + i * 0.4, g);
  });
  // iris core: two thin rings and the pupil (lines only; no tinted fills behind the text)
  const coreRingG = loopGeometry(R * 0.27, 96);
  add(new LineLoop(coreRingG, mat(LineBasicMaterial, "gold", 0.85)), 0.55, 0.5, coreRingG);
  const coreRing2G = loopGeometry(R * 0.2, 80);
  add(new LineLoop(coreRing2G, mat(LineBasicMaterial, "gold", 0.45)), 0.62, 0.45, coreRing2G);
  const pupilG = new CircleGeometry(R * 0.095, 48);
  add(new Mesh(pupilG, mat(MeshBasicMaterial, "surface", 1)), 0.7, 0.4, pupilG);
  const pupilRingG = loopGeometry(R * 0.095, 64);
  add(new LineLoop(pupilRingG, mat(LineBasicMaterial, "gold", 0.9)), 0.72, 0.4, pupilRingG);
  // orbiting nodes and their spokes (static; they sit at different depths)
  const rand = rng(1714);
  const nodeG = new CircleGeometry(0.045, 14);
  disposables.push(nodeG);
  const spokes = [];
  for (let i = 0; i < 14; i++) {
    const a = rand() * Math.PI * 2;
    const r = R * (0.5 + rand() * 0.52);
    const z = (rand() - 0.5) * 2.4;
    const dot = new Mesh(nodeG, mat(MeshBasicMaterial, "gold", 0.45 + rand() * 0.5));
    dot.position.set(Math.cos(a) * r, Math.sin(a) * r, 0);
    add(dot, z, 1.2);
    spokes.push(0, 0, 0, Math.cos(a) * r, Math.sin(a) * r, 0);
  }
  const spokeG = new BufferGeometry();
  spokeG.setAttribute("position", new Float32BufferAttribute(spokes, 3));
  add(new LineSegments(spokeG, mat(LineBasicMaterial, "gold", 0.1)), 0, 0.3, spokeG);

  const tint = () => {
    const by = { gold, ink, surface };
    disposables.forEach((m) => { if (m.isMaterial) m.color.copy(by[m.userData.role]); });
  };

  /* ---------- state ---------- */
  const T = { px: 0, py: 0, sp: 0 };     // targets: pointer x/y (-1..1), scroll progress (0..1)
  const C = { px: 0, py: 0, sp: 0 };     // eased current values
  let born = 0, last = 0, raf = 0, visible = true, inView = true, dead = false, frames = 0, dashTurn = 0, heroH = 1;

  const place = () => {                  // sit the iris on the right so the headline keeps a calm field
    const vh = 2 * Math.tan((camera.fov * Math.PI) / 360) * camera.position.z;
    iris.position.x = vh * camera.aspect * 0.26;
  };
  const resize = () => {
    const w = Math.max(1, hero.clientWidth), h = Math.max(1, hero.clientHeight);
    heroH = h;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    place();
    invalidate();
  };

  const apply = (e) => {
    const s = C.sp;
    iris.rotation.y = C.px * MAX_YAW;
    iris.rotation.x = C.py * MAX_PITCH;
    iris.scale.setScalar(0.9 + 0.1 * e + s * 0.06);
    camera.position.x = C.px * MAX_CAM;
    camera.position.y = -C.py * MAX_CAM * 0.6;
    camera.lookAt(0, 0, 0);
    const fade = 1 - Math.pow(s, 1.1) * 0.95;
    layers.forEach((l) => {
      l.obj.position.z = l.z * (0.1 + 0.9 * e) * (1 + s * 1.7 * l.push);
      const m = l.obj.material;
      m.opacity = m.userData.base * e * fade;
      l.obj.visible = m.opacity > 0.002;
    });
    dashed.rotation.z = dashTurn;
  };

  function frame(now) {
    raf = 0;
    if (dead) return;
    try {
      const dt = last ? Math.min(0.05, (now - last) / 1000) : 1 / 60;
      last = now;
      const k = 1 - Math.exp(-dt * EASE);
      C.px += (T.px - C.px) * k;
      C.py += (T.py - C.py) * k;
      C.sp += (T.sp - C.sp) * k;
      dashTurn = C.sp * 2.4 + C.px * 0.5;
      const e0 = clamp((now - born) / ENTRANCE_MS, 0, 1);
      apply(1 - Math.pow(1 - e0, 3));
      renderer.render(scene, camera);
      frames++;
      const moving = e0 < 1 || Math.abs(T.px - C.px) > SETTLE || Math.abs(T.py - C.py) > SETTLE || Math.abs(T.sp - C.sp) > SETTLE;
      if (moving && visible) raf = requestAnimationFrame(frame);
      else last = 0;
    } catch (err) {
      teardown(err);
    }
  }
  function invalidate() {
    if (dead || raf || !visible) return;
    if (!born) born = performance.now();
    raf = requestAnimationFrame(frame);
  }

  /* ---------- input ---------- */
  const onPointer = (e) => {
    if (e.pointerType === "touch") return;
    const r = hero.getBoundingClientRect();
    T.px = clamp(((e.clientX - r.left) / r.width - 0.5) * 2, -1, 1);
    T.py = clamp(((e.clientY - r.top) / r.height - 0.5) * 2, -1, 1);
    invalidate();
  };
  const onLeave = () => { T.px = 0; T.py = 0; invalidate(); };
  const onScroll = () => {
    const p = clamp(window.scrollY / (heroH * 0.9), 0, 1);
    if (p !== T.sp) { T.sp = p; invalidate(); }
  };
  const onTheme = () => { try { readColours(); tint(); invalidate(); } catch (e) { teardown(e); } };
  const onLost = (e) => { e.preventDefault(); teardown(); };
  const onVis = () => { visible = !document.hidden && inView; if (visible) invalidate(); };
  let io = null, ro = null;       // created inside the guarded start-up below so a failure tears everything down

  function teardown(why) {
    if (dead) return;
    dead = true;
    if (why instanceof Error) console.debug("hero3d: falling back to the 2D hero:", why);
    if (raf) cancelAnimationFrame(raf);
    hero.removeEventListener("pointermove", onPointer);
    hero.removeEventListener("pointerleave", onLeave);
    window.removeEventListener("scroll", onScroll);
    window.removeEventListener("themechange", onTheme);
    document.removeEventListener("visibilitychange", onVis);
    window.removeEventListener("pagehide", teardown);
    canvas.removeEventListener("webglcontextlost", onLost);
    if (io) io.disconnect();
    if (ro) ro.disconnect();
    try {
      disposables.forEach((d) => d.dispose());
      renderer.dispose();
      renderer.forceContextLoss();
    } catch (e) { /* already gone */ }
    canvas.remove();
    delete hero.dataset.iris;
    delete flat.dataset.engine;
    delete window.__ayinHero3d;
    window.dispatchEvent(new CustomEvent("iris3d:off"));   // site.js restarts the 2D canvas
  }

  /* ---------- go ---------- */
  try {
    io = new IntersectionObserver((entries) => {
      inView = entries[entries.length - 1].isIntersecting;
      onVis();
    });
    ro = new ResizeObserver(resize);
    readColours();
    tint();
    canvas.addEventListener("webglcontextlost", onLost);
    flat.after(canvas);
    resize();
    hero.addEventListener("pointermove", onPointer, { passive: true });
    hero.addEventListener("pointerleave", onLeave, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("themechange", onTheme);
    document.addEventListener("visibilitychange", onVis);
    window.addEventListener("pagehide", teardown);
    io.observe(hero);
    ro.observe(hero);
    onScroll();
    hero.dataset.iris = "webgl";
    flat.dataset.engine = "webgl";          // site.js stops drawing the 2D canvas
    // read-only probe for the tests and for debugging in the console
    window.__ayinHero3d = {
      snapshot: () => ({
        rotY: iris.rotation.y, rotX: iris.rotation.x, spread: C.sp, frames, dead,
        gold: gold.getHexString(), ink: ink.getHexString(), surface: surface.getHexString(),
        ring: layers[RINGS - 1].obj.material.color.getHexString(),
        ringZ: layers.slice(0, RINGS).map((l) => l.obj.position.z),
        camX: camera.position.x,
      }),
    };
    invalidate();
    requestAnimationFrame(() => { canvas.dataset.ready = ""; });
  } catch (err) {
    teardown(err);
  }
}

try { start(); } catch (e) { console.debug("hero3d: not started:", e); }
