/* ============================================================
   AYiN Advisors — Shared interactions
   ============================================================ */
(function () {
  "use strict";
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Navbar scroll state ---------- */
  const nav = document.querySelector(".nav");
  const onScroll = () => {
    if (!nav) return;
    nav.classList.toggle("scrolled", window.scrollY > 40);
  };
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  /* ---------- Theme switch ----------
     Contract: html[data-theme="light"|"dark"], set before first paint by the inline script in <head>;
     the visitor's choice lives in localStorage["ayin-theme"] (every access guarded: storage may be
     blocked). With no stored choice the page follows the system preference live. */
  const THEME_KEY = "ayin-theme";
  const themeToggles = document.querySelectorAll(".theme-toggle");
  const themeMeta = document.querySelector('meta[name="theme-color"]');
  /* theme-color follows the active theme. Today navy in both themes, so both entries hold the value the page
     shipped with; change an entry here (or Task 2's palette work) to diverge them. */
  const THEME_COLOR = themeMeta ? { light: themeMeta.content, dark: themeMeta.content } : null;
  const readTheme = () => { try { const v = localStorage.getItem(THEME_KEY); return v === "light" || v === "dark" ? v : null; } catch (e) { return null; } };
  const systemDark = window.matchMedia("(prefers-color-scheme: dark)");
  const applyTheme = (theme, animate) => {
    const root = document.documentElement;
    if (root.dataset.theme === theme) return;
    if (animate && !reduce) {
      root.classList.add("theme-switching");
      clearTimeout(applyTheme.t);
      applyTheme.t = setTimeout(() => root.classList.remove("theme-switching"), 200);
    }
    root.dataset.theme = theme;
    themeToggles.forEach((b) => b.setAttribute("aria-pressed", theme === "dark" ? "true" : "false"));
    if (themeMeta && THEME_COLOR) themeMeta.setAttribute("content", THEME_COLOR[theme]);
    window.dispatchEvent(new CustomEvent("themechange", { detail: { theme } }));
  };
  if (themeToggles.length) {
    const current = document.documentElement.dataset.theme === "dark" ? "dark" : "light";
    themeToggles.forEach((b) => b.setAttribute("aria-pressed", current === "dark" ? "true" : "false"));
    if (themeMeta && THEME_COLOR) themeMeta.setAttribute("content", THEME_COLOR[current]);
    themeToggles.forEach((b) =>
      b.addEventListener("click", () => {
        const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        try { localStorage.setItem(THEME_KEY, next); } catch (e) { /* choice lasts for this visit only */ }
        applyTheme(next, true);
      })
    );
    const onSystem = (e) => { if (!readTheme()) applyTheme(e.matches ? "dark" : "light", true); };
    if (systemDark.addEventListener) systemDark.addEventListener("change", onSystem);
    else if (systemDark.addListener) systemDark.addListener(onSystem);
  }

  /* ---------- Mobile menu ---------- */
  const toggle = document.querySelector(".nav-toggle");
  const drawer = document.querySelector(".mobile-drawer");
  if (toggle && drawer) {
    const setOpen = (open, returnFocus) => {
      drawer.classList.toggle("open", open);
      toggle.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
      if (!open && returnFocus) toggle.focus();
    };
    toggle.addEventListener("click", () => setOpen(!drawer.classList.contains("open")));
    drawer.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => setOpen(false)));
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && drawer.classList.contains("open")) setOpen(false, true);
    });
  }

  /* ---------- Reveal on scroll ---------- */
  const revealEls = document.querySelectorAll(".reveal, .line-reveal");
  if (revealEls.length) {
    if (reduce || !("IntersectionObserver" in window)) {
      revealEls.forEach((el) => el.classList.add("in"));
    } else {
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((e) => {
            if (e.isIntersecting) {
              e.target.classList.add("in");
              io.unobserve(e.target);
            }
          });
        },
        { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
      );
      revealEls.forEach((el) => io.observe(el));

      // Fallback 1: reveal anything already within the viewport (covers
      // environments where IO doesn't fire for the initial frame).
      const checkInView = () => {
        const vh = window.innerHeight;
        revealEls.forEach((el) => {
          const r = el.getBoundingClientRect();
          if (r.top < vh * 0.96 && r.bottom > 0) el.classList.add("in");
        });
      };
      window.addEventListener("load", checkInView);
      setTimeout(checkInView, 250);
      window.addEventListener("scroll", checkInView, { passive: true });

      // Fallback 2: hard safety — never leave content permanently hidden.
      setTimeout(() => revealEls.forEach((el) => el.classList.add("in")), 2600);
    }
  }

  /* ---------- Counters ---------- */
  const counters = document.querySelectorAll("[data-count]");
  if (counters.length) {
    const cio = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (!e.isIntersecting) return;
          const el = e.target;
          cio.unobserve(el);
          const target = parseFloat(el.dataset.count);
          const dur = 1800;
          const dec = (el.dataset.dec ? parseInt(el.dataset.dec) : 0);
          const prefix = el.dataset.prefix || "";
          const suffix = el.dataset.suffix || "";
          if (reduce) { el.textContent = prefix + target.toFixed(dec) + suffix; return; }
          const start = performance.now();
          const tick = (now) => {
            const p = Math.min((now - start) / dur, 1);
            const eased = 1 - Math.pow(1 - p, 3);
            const val = target * eased;
            el.textContent = prefix + val.toFixed(dec) + suffix;
            if (p < 1) requestAnimationFrame(tick);
          };
          requestAnimationFrame(tick);
        });
      },
      { threshold: 0.5 }
    );
    counters.forEach((c) => cio.observe(c));
  }

  /* ---------- Magnetic buttons ---------- */
  if (!reduce && window.matchMedia("(pointer: fine)").matches) {
    document.querySelectorAll("[data-magnetic]").forEach((el) => {
      const strength = parseFloat(el.dataset.magnetic) || 0.32;
      el.addEventListener("mousemove", (e) => {
        const r = el.getBoundingClientRect();
        const x = e.clientX - r.left - r.width / 2;
        const y = e.clientY - r.top - r.height / 2;
        el.style.transform = `translate(${x * strength}px, ${y * strength}px)`;
      });
      el.addEventListener("mouseleave", () => { el.style.transform = ""; });
    });
  }

  /* ---------- Parallax (data-parallax = speed) ---------- */
  const parallaxEls = document.querySelectorAll("[data-parallax]");
  let mx = 0, my = 0, tmx = 0, tmy = 0;
  if (!reduce && parallaxEls.length) {
    window.addEventListener("mousemove", (e) => {
      tmx = (e.clientX / window.innerWidth - 0.5) * 2;
      tmy = (e.clientY / window.innerHeight - 0.5) * 2;
    });
    const loop = () => {
      mx += (tmx - mx) * 0.06;
      my += (tmy - my) * 0.06;
      const sy = window.scrollY;
      parallaxEls.forEach((el) => {
        const s = parseFloat(el.dataset.parallax) || 0.04;
        const mouse = el.dataset.parallaxMouse !== "off";
        const tx = mouse ? mx * s * 60 : 0;
        const ty = (mouse ? my * s * 60 : 0) - sy * s * 0.35;
        el.style.transform = `translate3d(${tx}px, ${ty}px, 0)`;
      });
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  /* ============================================================
     Motion components: assemble / ripples / tilt / drift
     Reduced motion (or no IntersectionObserver): do nothing at all, so
     every component stays in its static, final state. The hidden "pre"
     state exists only because this block sets data-assemble="pre".
     ============================================================ */
  if (!reduce && "IntersectionObserver" in window) {
    const ASM = ["asm-scatter", "asm-card", "asm-rise", "asm-fade", "asm-grow"];
    const pending = new Set();

    /* ---- assemble: [data-assemble] -> "pre" -> "in" (once) ---- */
    const startAssemble = (root) => {
      if (root.getAttribute("data-assemble") !== "pre") return; // runs once
      pending.delete(root);
      aio.unobserve(root);
      root.setAttribute("data-assemble", "in");
      setTimeout(() => root.setAttribute("data-assemble-done", ""), 3400);
    };
    const aio = new IntersectionObserver(
      (entries) => entries.forEach((e) => { if (e.isIntersecting) startAssemble(e.target); }),
      { threshold: 0, rootMargin: "0px 0px -10% 0px" }
    );
    document.querySelectorAll("[data-assemble]").forEach((root) => {
      ASM.forEach((cls) =>
        root.querySelectorAll("." + cls).forEach((el, i) => {
          el.style.setProperty("--i", i);
          el.style.setProperty("--dir", i % 2 ? 1 : -1);
        })
      );
      root.setAttribute("data-assemble", "pre");
      pending.add(root);
      aio.observe(root);
    });
    // Fallback: never leave a section hidden if the observer is slow to fire.
    const sweep = () => {
      const vh = window.innerHeight;
      pending.forEach((root) => {
        const r = root.getBoundingClientRect();
        if (r.top < vh * 0.9 && r.bottom > 0) startAssemble(root);
      });
    };
    window.addEventListener("load", sweep);
    setTimeout(sweep, 400);
    window.addEventListener("scroll", () => { if (pending.size) sweep(); }, { passive: true });

    /* ---- ripples: emit once for under 5 s after entering view, then rest ---- */
    const rio = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (!e.isIntersecting) return;
          rio.unobserve(e.target);
          e.target.classList.add("is-emitting");
          setTimeout(() => e.target.classList.remove("is-emitting"), 5000);
        }),
      { threshold: 0.05 }
    );
    document.querySelectorAll(".ripples").forEach((el) => rio.observe(el));

    /* ---- drift: [data-drift=factor] ripples drift against their host's distance from the
       viewport centre, so the offset stays bounded (+-120px, +-6deg) wherever the host sits ---- */
    const DRIFT_MAX = 120, ROT_MAX = 6;
    const clamp = (v, m) => Math.max(-m, Math.min(m, v));
    const drifters = [];
    const dio = new IntersectionObserver((entries) =>
      entries.forEach((e) => { e.target._drifting = e.isIntersecting; })
    );
    document.querySelectorAll("[data-drift]").forEach((el) => {
      el._host = el.offsetParent || el.parentElement; // untransformed, so no feedback loop
      drifters.push(el);
      dio.observe(el);
    });
    if (drifters.length) {
      let ticking = false;
      const drift = () => {
        ticking = false;
        const vc = window.innerHeight / 2;
        drifters.forEach((el) => {
          if (!el._drifting) return;
          const s = parseFloat(el.dataset.drift) || 0.12;
          const h = el._host.getBoundingClientRect();
          const d = h.top + h.height / 2 - vc;
          const ty = clamp(d * s, DRIFT_MAX);
          const rot = clamp(d * 0.01, ROT_MAX);
          el.style.transform = `translate3d(0, ${ty.toFixed(1)}px, 0) rotate(${rot.toFixed(2)}deg)`;
        });
      };
      window.addEventListener("scroll", () => {
        if (!ticking) { ticking = true; requestAnimationFrame(drift); }
      }, { passive: true });
    }

    /* ---- tilt: [data-tilt] cards follow the pointer; data-tilt="group" tilts its .asm-scatter glyphs ---- */
    const settled = (el) => {
      const root = el.closest("[data-assemble]");
      return !root || root.hasAttribute("data-assemble-done");
    };
    const mouseLike = (e) => e.pointerType !== "touch";
    document.querySelectorAll("[data-tilt]").forEach((el) => {
      if (el.dataset.tilt === "group") {
        const items = el.querySelectorAll(".asm-scatter");
        el.addEventListener("pointermove", (e) => {
          if (!mouseLike(e) || !settled(el)) return;
          const b = el.getBoundingClientRect();
          const x = (e.clientX - b.left) / b.width - 0.5;
          const y = (e.clientY - b.top) / b.height - 0.5;
          items.forEach((g, i) => {
            g.classList.add("is-tilting");
            g.style.transform = `rotateY(${x * 26}deg) rotateX(${-y * 18}deg) translate3d(${x * (8 + i * 3)}px, ${y * (6 + i * 2)}px, 0)`;
          });
        });
        el.addEventListener("pointerleave", () =>
          items.forEach((g) => { g.classList.remove("is-tilting"); g.style.transform = ""; })
        );
        return;
      }
      el.addEventListener("pointermove", (e) => {
        if (!mouseLike(e) || !settled(el)) return;
        const b = el.getBoundingClientRect();
        const x = (e.clientX - b.left) / b.width - 0.5;
        const y = (e.clientY - b.top) / b.height - 0.5;
        el.classList.add("is-tilting");
        el.style.transform = `rotateY(${x * 12}deg) rotateX(${-y * 10}deg) translateZ(14px)`;
      });
      el.addEventListener("pointerleave", () => {
        el.classList.remove("is-tilting");
        el.style.transform = "";
      });
    });
  }

  /* ---------- Year ---------- */
  document.querySelectorAll("[data-year]").forEach((el) => (el.textContent = new Date().getFullYear()));

  /* ============================================================
     Iris / radar hero canvas  (the "eye" of AYiN)
     ============================================================ */
  const canvas = document.getElementById("iris");
  if (canvas && !reduce) {
    const ctx = canvas.getContext("2d");
    let W, H, cx, cy, R, dpr;
    let nodes = [];

    /* Colours come from the CSS roles of the surface the canvas sits on (--accent-fill for the strokes,
       --surface for the pupil), read again whenever the theme changes. A canvas needs literal colour
       strings, so the role is resolved to #rrggbb through a throwaway 2D context and alpha is appended. */
    const probe = document.createElement("canvas").getContext("2d");
    const role = (name) => {
      const v = getComputedStyle(canvas).getPropertyValue(name).trim();
      if (v) probe.fillStyle = v;
      return probe.fillStyle;
    };
    let GOLD = "", PUPIL = "";
    const readColours = () => { GOLD = role("--accent-fill"); PUPIL = role("--surface"); };
    const tint = (a) => GOLD + Math.round(Math.max(0, Math.min(1, a)) * 255).toString(16).padStart(2, "0");
    readColours();
    window.addEventListener("themechange", readColours);

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      const rect = canvas.getBoundingClientRect();
      W = rect.width; H = rect.height;
      canvas.width = W * dpr; canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cx = W / 2; cy = H / 2;
      R = Math.min(W, H) * 0.46;
      buildNodes();
    }

    function buildNodes() {
      nodes = [];
      const count = 14;
      for (let i = 0; i < count; i++) {
        const ring = 0.5 + Math.random() * 0.52;
        nodes.push({
          a: Math.random() * Math.PI * 2,
          r: R * ring,
          sp: (0.0006 + Math.random() * 0.0016) * (Math.random() > 0.5 ? 1 : -1),
          sz: 1.1 + Math.random() * 2.2,
          pulse: Math.random() * Math.PI * 2,
        });
      }
    }

    let t = 0;
    let pmx = 0, pmy = 0;
    window.addEventListener("mousemove", (e) => {
      pmx = (e.clientX / window.innerWidth - 0.5);
      pmy = (e.clientY / window.innerHeight - 0.5);
    });

    function draw() {
      t += 1;
      ctx.clearRect(0, 0, W, H);
      const ox = pmx * 26, oy = pmy * 26;
      const ax = cx + ox, ay = cy + oy;

      // concentric rings
      const rings = 7;
      for (let i = 1; i <= rings; i++) {
        const rr = (R * i) / rings;
        const alpha = 0.09 + (i / rings) * 0.16;
        ctx.beginPath();
        ctx.arc(ax, ay, rr, 0, Math.PI * 2);
        ctx.strokeStyle = tint(alpha);
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      // dashed mid ring (slow rotate)
      ctx.save();
      ctx.translate(ax, ay);
      ctx.rotate(t * 0.0009);
      ctx.beginPath();
      ctx.arc(0, 0, R * 0.74, 0, Math.PI * 2);
      ctx.setLineDash([2, 14]);
      ctx.strokeStyle = tint(0.55);
      ctx.lineWidth = 1.4;
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.restore();

      // radar sweep
      const sweep = t * 0.012;
      const grad = ctx.createConicGradient ? ctx.createConicGradient(sweep, ax, ay) : null;
      if (grad) {
        grad.addColorStop(0, tint(0.0));
        grad.addColorStop(0.07, tint(0.26));
        grad.addColorStop(0.12, tint(0.0));
        grad.addColorStop(1, tint(0.0));
        ctx.beginPath();
        ctx.arc(ax, ay, R, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();
      }
      // sweep line
      ctx.save();
      ctx.translate(ax, ay);
      ctx.rotate(sweep);
      const lg = ctx.createLinearGradient(0, 0, R, 0);
      lg.addColorStop(0, tint(0.0));
      lg.addColorStop(1, tint(0.5));
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.lineTo(R, 0);
      ctx.strokeStyle = lg;
      ctx.lineWidth = 1.2;
      ctx.stroke();
      ctx.restore();

      // iris core
      const coreR = R * 0.26;
      const rg = ctx.createRadialGradient(ax, ay, 2, ax, ay, coreR);
      rg.addColorStop(0, tint(0.95));
      rg.addColorStop(0.4, tint(0.42));
      rg.addColorStop(1, tint(0.0));
      ctx.beginPath();
      ctx.arc(ax, ay, coreR, 0, Math.PI * 2);
      ctx.fillStyle = rg;
      ctx.fill();
      // pupil
      ctx.beginPath();
      ctx.arc(ax, ay, coreR * 0.34 + Math.sin(t * 0.03) * 2, 0, Math.PI * 2);
      ctx.fillStyle = PUPIL;
      ctx.fill();
      ctx.lineWidth = 1.3;
      ctx.strokeStyle = tint(0.8);
      ctx.stroke();

      // orbiting nodes + spokes
      nodes.forEach((n) => {
        n.a += n.sp * 16;
        n.pulse += 0.04;
        const x = ax + Math.cos(n.a) * n.r;
        const y = ay + Math.sin(n.a) * n.r;
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(x, y);
        ctx.strokeStyle = tint(0.08);
        ctx.lineWidth = 1;
        ctx.stroke();
        const p = 0.4 + (Math.sin(n.pulse) + 1) / 2 * 0.6;
        ctx.beginPath();
        ctx.arc(x, y, n.sz, 0, Math.PI * 2);
        ctx.fillStyle = tint(p);
        ctx.fill();
      });

      requestAnimationFrame(draw);
    }

    const ro = new ResizeObserver(resize);
    ro.observe(canvas);
    resize();
    requestAnimationFrame(draw);
  }
})();
