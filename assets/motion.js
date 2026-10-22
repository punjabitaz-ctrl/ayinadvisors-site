/* ============================================================
   AYiN Advisors - Phase 2d motion: smooth scroll (Lenis) + layered depth (GSAP ScrollTrigger)
   Loaded with `defer` after assets/vendor/{lenis,gsap,ScrollTrigger}.min.js on every page.

   Reduced motion: nothing here runs, so scrolling is the browser's own and nothing is offset.
   Touch: left native (syncTouch is off). Keyboard, find-in-page, Tab focus and back/forward are the
   browser's own; Lenis only smooths wheel input and the in-page anchor jumps handled below.
   Idle: Lenis is driven from a requestAnimationFrame loop that runs only while it is scrolling.
   ============================================================ */
(function () {
  "use strict";
  const root = document.documentElement;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  /* ScrollTrigger ships a built-in loop (`_rafBugFix`, a workaround for a Safari rAF bug) that calls
     requestAnimationFrame every frame for the life of the page. That is an idle loop for nothing, so the one
     self-rescheduling callback it names is dropped; every other requestAnimationFrame call is passed through. */
  const nativeRaf = window.requestAnimationFrame;
  window.requestAnimationFrame = function (cb) {
    return cb && cb.name === "_rafBugFix" ? 0 : nativeRaf.call(window, cb);
  };

  /* ---------- Lenis ---------- */
  let lenis = null;
  if (window.Lenis) {
    try {
      lenis = new window.Lenis({ lerp: 0.1, smoothWheel: true, syncTouch: false, autoRaf: false, anchors: false });
    } catch (e) { lenis = null; }
  }

  if (lenis) {
    let loop = 0;
    const tick = (t) => {
      loop = 0;
      lenis.raf(t);
      if (lenis.isScrolling) loop = requestAnimationFrame(tick);
    };
    const kick = () => { if (!loop) loop = requestAnimationFrame(tick); };
    ["wheel", "keydown", "touchmove"].forEach((ev) => window.addEventListener(ev, kick, { passive: true, capture: true }));

    /* The mobile drawer locks the page; keep Lenis out of the way while it is open. */
    const drawer = document.querySelector(".mobile-drawer");
    if (drawer) {
      const sync = () => { if (drawer.classList.contains("open")) lenis.stop(); else lenis.start(); };
      new MutationObserver(sync).observe(drawer, { attributes: true, attributeFilter: ["class"] });
    }
    /* Text areas scroll themselves. */
    document.querySelectorAll("textarea").forEach((el) => el.setAttribute("data-lenis-prevent", ""));

    /* In-page anchors (nav, skip link, footer): smooth, clear of the sticky nav, hash and focus kept. */
    const focusTarget = (el) => {
      const had = el.hasAttribute("tabindex");
      if (!had) {
        el.setAttribute("tabindex", "-1");
        el.style.outline = "none";
        el.addEventListener("blur", () => { el.removeAttribute("tabindex"); el.style.outline = ""; }, { once: true });
      }
      try { el.focus({ preventScroll: true }); } catch (e) { /* ignore */ }
    };
    document.addEventListener("click", (e) => {
      if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const a = e.target.closest && e.target.closest("a[href]");
      if (!a || (a.target && a.target !== "_self") || a.hasAttribute("download")) return;
      let u;
      try { u = new URL(a.href, location.href); } catch (err) { return; }
      if (u.origin !== location.origin || u.pathname !== location.pathname || u.search !== location.search || u.hash.length < 2) return;
      let id;
      try { id = decodeURIComponent(u.hash.slice(1)); } catch (err) { return; }
      const target = document.getElementById(id);
      if (!target) return;
      e.preventDefault();
      lenis.start();
      lenis.scrollTo(target, { force: true });    // Lenis itself honours scroll-padding-top and scroll-margin-top
      kick();
      if (location.hash !== u.hash) history.pushState(null, "", u.hash);
      focusTarget(target);
    });

    if (window.ScrollTrigger) lenis.on("scroll", window.ScrollTrigger.update);
  }

  /* ---------- GSAP: layered depth ----------
     Transform only. Every tween starts at offset 0 where the page rests, so the first paint is exactly the static
     layout. Elements that carry their own CSS transform transition (.reveal, .asm-*) are never animated
     directly; their wrappers or children are. */
  if (!window.gsap || !window.ScrollTrigger) return;
  const gsap = window.gsap, ScrollTrigger = window.ScrollTrigger;
  gsap.registerPlugin(ScrollTrigger);
  /* ScrollTrigger also polls every 250 ms (a safety net for scroll events that never fire, which a Lenis page does not
     need). Re-setting syncInterval replaces that timer; a very long one means no wake-ups while the page is idle. */
  ScrollTrigger.config({ ignoreMobileResize: true, syncInterval: 600000 });

  gsap.context(() => {
    const hero = document.querySelector(".hero");
    if (hero) {
      const layer = (sel, y) => {
        const el = hero.querySelector(sel);
        if (!el) return;
        el.classList.add("depth");
        gsap.to(el, { y, ease: "none", scrollTrigger: { trigger: hero, start: "top top", end: "bottom top", scrub: true } });
      };
      layer(".hero-inner", 80);     // headline layer lags the page the most
      layer(".hero-stats", 26);     // stat strip a little less
    }

    /* Photographs drift a few percent inside their frames. */
    document.querySelectorAll(".photo-card picture").forEach((pic) => {
      const img = pic.querySelector("img");
      if (!img) return;
      pic.classList.add("depth-frame");
      img.classList.add("depth");
      gsap.set(img, { scale: 1.12 });
      gsap.fromTo(img, { yPercent: -5 }, {
        yPercent: 5, ease: "none",
        scrollTrigger: { trigger: pic, start: "top bottom", end: "bottom top", scrub: true },
      });
    });

    /* Section headings lift into place. */
    document.querySelectorAll("h2:not(.reveal):not([class*='asm-'])").forEach((h) => {
      h.classList.add("depth");
      gsap.fromTo(h, { y: 22 }, {
        y: 0, ease: "none",
        scrollTrigger: { trigger: h, start: "top 96%", end: "top 62%", scrub: true },
      });
    });
  });
})();
