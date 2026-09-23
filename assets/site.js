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

  /* ---------- Mobile menu ---------- */
  const toggle = document.querySelector(".nav-toggle");
  const drawer = document.querySelector(".mobile-drawer");
  if (toggle && drawer) {
    toggle.addEventListener("click", () => {
      const open = drawer.classList.toggle("open");
      toggle.classList.toggle("is-open", open);
      document.body.style.overflow = open ? "hidden" : "";
    });
    drawer.querySelectorAll("a").forEach((a) =>
      a.addEventListener("click", () => {
        drawer.classList.remove("open");
        toggle.classList.remove("is-open");
        document.body.style.overflow = "";
      })
    );
  }

  /* ---------- Reveal on scroll ---------- */
  const revealEls = document.querySelectorAll(".reveal, .line-reveal");
  if (revealEls.length) {
    if (!("IntersectionObserver" in window)) {
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

  /* ---------- Year ---------- */
  document.querySelectorAll("[data-year]").forEach((el) => (el.textContent = new Date().getFullYear()));

  /* ============================================================
     Iris / radar hero canvas  (the "eye" of AYiN)
     ============================================================ */
  const canvas = document.getElementById("iris");
  if (canvas && !reduce) {
    const ctx = canvas.getContext("2d");
    let W, H, cx, cy, R, dpr;
    const GOLD = "198,161,92";
    let nodes = [];

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
        ctx.strokeStyle = `rgba(${GOLD},${alpha})`;
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
      ctx.strokeStyle = `rgba(${GOLD},0.55)`;
      ctx.lineWidth = 1.4;
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.restore();

      // radar sweep
      const sweep = t * 0.012;
      const grad = ctx.createConicGradient ? ctx.createConicGradient(sweep, ax, ay) : null;
      if (grad) {
        grad.addColorStop(0, `rgba(${GOLD},0.0)`);
        grad.addColorStop(0.07, `rgba(${GOLD},0.26)`);
        grad.addColorStop(0.12, `rgba(${GOLD},0.0)`);
        grad.addColorStop(1, `rgba(${GOLD},0.0)`);
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
      lg.addColorStop(0, `rgba(${GOLD},0.0)`);
      lg.addColorStop(1, `rgba(${GOLD},0.5)`);
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
      rg.addColorStop(0, `rgba(${GOLD},0.95)`);
      rg.addColorStop(0.4, `rgba(${GOLD},0.42)`);
      rg.addColorStop(1, `rgba(${GOLD},0.0)`);
      ctx.beginPath();
      ctx.arc(ax, ay, coreR, 0, Math.PI * 2);
      ctx.fillStyle = rg;
      ctx.fill();
      // pupil
      ctx.beginPath();
      ctx.arc(ax, ay, coreR * 0.34 + Math.sin(t * 0.03) * 2, 0, Math.PI * 2);
      ctx.fillStyle = "#061325";
      ctx.fill();
      ctx.lineWidth = 1.3;
      ctx.strokeStyle = `rgba(${GOLD},0.8)`;
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
        ctx.strokeStyle = `rgba(${GOLD},0.08)`;
        ctx.lineWidth = 1;
        ctx.stroke();
        const p = 0.4 + (Math.sin(n.pulse) + 1) / 2 * 0.6;
        ctx.beginPath();
        ctx.arc(x, y, n.sz, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${GOLD},${p})`;
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
