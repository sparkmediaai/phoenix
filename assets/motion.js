// Motion. Reads the data attributes the build writes and animates them with
// GSAP + ScrollTrigger. Loaded only when html.motion is set (see the gate in
// _build/build.py). Every initial hidden state lives in motion.css and uses
// opacity and transform only, so assistive technology reads the page in
// document order whether or not this file runs.
//
//   data-reveal            fade and rise into place once, on entering the viewport (CSS transitions; this file only adds .in)
//   data-reveal="stagger"  the same, for the element's children, 120ms apart
//   data-reveal="left|right|tiles|rows"  directional, popping and row-by-row variants
//   .scroll-progress       a bar that fills with the page's scroll position
//   data-parallax="0.2"    background layer drifts at that fraction of scroll speed
//   data-pin               section pins for data-pin-length viewport heights (default 2)
//                          while its [data-step] children play in turn; [data-hold]
//                          fades out as the first step arrives; [data-dim] fades up
//                          to opacity .85; a step's data-step-draw="#id" draws the
//                          paths in that SVG group as the step arrives
//   data-draw              an SVG whose paths draw themselves as it scrolls through
//   data-count="2500"      counts up from data-count-from (default 0) with optional
//                          data-count-prefix and data-count-suffix
(function () {
  // The loader takes html.motion off again if a script fails or four seconds
  // pass without motion.js reporting in. The scripts can still arrive after
  // that, so check the class before touching anything: without it the page is
  // the static site and must stay that way.
  if (!document.documentElement.classList.contains("motion")) return;
  if (window.__motionTimer) clearTimeout(window.__motionTimer);
  if (!window.gsap || !window.ScrollTrigger) { document.documentElement.classList.remove("motion"); return; }
  gsap.registerPlugin(ScrollTrigger);
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

  // ---- reveal
  //
  // Reveals are CSS transitions (see motion.css): this only says when. Tweening
  // them from here meant script work on every frame for every table row, and
  // on a slow machine that made scrolling stutter. An observer adds .in as the
  // element comes into view, or at once if the page opened below it; children
  // are numbered with --i so the stylesheet can stagger them.
  //   (none)   the element rises into place
  //   left     the element slides in from the left        right   from the right, growing slightly
  //   stagger  the element's children rise in turn        tiles   children pop in turn, with a little overshoot
  //   rows     a table's body rows arrive one after another
  (function () {
    var STEP = { stagger: 120, tiles: 90, rows: 60 }, LAST = { stagger: 900, tiles: 700, rows: 500, left: 1100, right: 1100 };
    function show(el) {
      var kind = el.getAttribute("data-reveal");
      var n = el.style.getPropertyValue("--n") | 0;
      el.classList.add("in");
      setTimeout(function () { el.classList.add("done"); }, (LAST[kind] || 900) + (STEP[kind] || 0) * n + 100);
    }
    var seen = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting && e.boundingClientRect.bottom > 0) return;   // still below the fold
        seen.unobserve(e.target);
        show(e.target);
      });
    }, { rootMargin: "0px 0px -14% 0px" });
    $$("[data-reveal]").forEach(function (el) {
      var kind = el.getAttribute("data-reveal");
      var kids = kind === "rows" ? $$("tbody tr", el) : STEP[kind] ? Array.prototype.slice.call(el.children) : [];
      kids.forEach(function (k, i) { k.style.setProperty("--i", Math.min(i, 14)); });
      el.style.setProperty("--n", Math.min(kids.length, 15));
      seen.observe(el);
    });
  })();

  // ---- scroll progress: the thin ember line under the header
  $$(".scroll-progress").forEach(function (bar) {
    gsap.to(bar, { scaleX: 1, ease: "none", scrollTrigger: { start: 0, end: "max", scrub: 0.3 } });
  });

  // ---- parallax
  $$("[data-parallax]").forEach(function (el) {
    var f = parseFloat(el.getAttribute("data-parallax")) || 0.2;
    gsap.fromTo(el, { yPercent: -f * 50 }, {
      yPercent: f * 50, ease: "none",
      scrollTrigger: { trigger: el.parentElement, start: "top bottom", end: "bottom top", scrub: true }
    });
  });

  // ---- draw helpers
  //
  // Only lines with no dash pattern of their own can be drawn by animating a
  // dash offset: doing it to the cost figure's target line (6 8) or the
  // panel's engraved nameplate rule (3 5) would overwrite the pattern and
  // leave them solid. Those, and every text label, fade in instead. The
  // initial states go through gsap.set rather than element.style so that a
  // gsap.matchMedia context can revert them along with its timeline.
  function drawable(root) {
    return $$("path, line, polyline, circle, rect, ellipse", root).filter(function (p) {
      return typeof p.getTotalLength === "function" && !p.hasAttribute("stroke-dasharray");
    });
  }
  function dashed(root) {
    return $$("[stroke-dasharray]", root);
  }
  function prepDraw(root) {
    var paths = drawable(root);
    paths.forEach(function (p) {
      var len = p.getTotalLength();
      gsap.set(p, { strokeDasharray: len, strokeDashoffset: len });
    });
    var fade = dashed(root).concat($$("text", root));
    if (fade.length) gsap.set(fade, { opacity: 0 });
    return { paths: paths, fade: fade };
  }

  // ---- pinned sequences
  //
  // Pins are desktop-only, and so is the hidden state that goes with them.
  // gsap.matchMedia builds the timeline and its gsap.set when the query
  // matches and reverts both -- inline styles included -- when it stops, so a
  // phone rotated into landscape and a desktop window narrowed past the
  // breakpoint both end up with the static stacked layout rather than a
  // hidden step no timeline will ever reveal. data-pin-armed is the mark
  // motion.css keys the hidden state off; it goes on before the gsap.set and
  // comes off in the cleanup below.
  gsap.matchMedia().add("(min-width: 768px)", function () {
    var armed = [];
    $$("[data-pin]").forEach(function (section) {
      var steps = $$("[data-step]", section);
      if (!steps.length) return;
      var length = parseFloat(section.getAttribute("data-pin-length")) || 2;
      var hold = $$("[data-hold]", section);
      var dim = $$("[data-dim]", section);
      section.setAttribute("data-pin-armed", "");
      armed.push(section);
      gsap.set(steps, { opacity: 0, y: 30 });
      var tl = gsap.timeline({
        scrollTrigger: { trigger: section, start: "top top", end: "+=" + (length * 100) + "%", pin: true, scrub: 0.6, anticipatePin: 1 }
      });
      if (hold.length) tl.to(hold, {
        opacity: 0, y: -40, duration: 1,
        // Opacity alone leaves the hero's buttons in the tab order behind the
        // steps that replaced them.
        onComplete: function () { hold.forEach(function (el) { el.setAttribute("inert", ""); }); },
        onReverseComplete: function () { hold.forEach(function (el) { el.removeAttribute("inert"); }); }
      }, 0);
      if (dim.length) tl.to(dim, { opacity: 0.85, duration: 1 }, 0);
      // With a headline to clear first (the hero), the first step waits for it.
      // Without one (the OEM path) there is nothing to wait for, and waiting
      // meant the section pinned on an empty screen: the first step and its
      // drawing are there from the moment the section arrives.
      var waits = hold.length > 0;
      if (!waits) gsap.set(steps[0], { opacity: 1, y: 0 });
      steps.forEach(function (step, i) {
        if (i > 0 || waits) tl.to(step, { opacity: 1, y: 0, duration: 1 }, i === 0 ? 0.6 : ">");
        else tl.to({}, { duration: 0.01 }, 0);               // an anchor for this step's drawing
        var sel = step.getAttribute("data-step-draw");
        if (sel) {
          var target = section.querySelector(sel) || document.querySelector(sel);
          var d = target && prepDraw(target);
          if (d && d.paths.length) tl.to(d.paths, { strokeDashoffset: 0, duration: 1.2, stagger: 0.15 }, "<");
          if (d && d.fade.length) tl.to(d.fade, { opacity: 1, duration: 0.6 }, "<0.6");
        }
        tl.to({}, { duration: 1 });                          // hold
        if (i < steps.length - 1) tl.to(step, { opacity: 0, y: -30, duration: 0.8 });
      });
    });
    return function () {
      armed.forEach(function (section) {
        section.removeAttribute("data-pin-armed");
        $$("[data-hold]", section).forEach(function (el) { el.removeAttribute("inert"); });
      });
    };
  });

  // ---- standalone drawings
  $$("svg[data-draw]").forEach(function (svg) {
    if (svg.closest("[data-pin]")) return;                 // handled by the pin above
    var d = prepDraw(svg);
    if (!d.paths.length && !d.fade.length) return;
    var tl = gsap.timeline({
      scrollTrigger: { trigger: svg, start: "top 85%", end: "bottom 45%", scrub: true }
    });
    if (d.paths.length) tl.to(d.paths, { strokeDashoffset: 0, ease: "none", stagger: 0.25, duration: 1 }, 0);
    if (d.fade.length) tl.to(d.fade, { opacity: 1, ease: "none", duration: 0.5 }, ">");
  });

  // ---- counters
  $$("[data-count]").forEach(function (el) {
    var to = parseFloat(el.getAttribute("data-count")) || 0;
    var from = parseFloat(el.getAttribute("data-count-from")) || 0;
    var prefix = el.getAttribute("data-count-prefix") || "";
    var suffix = el.getAttribute("data-count-suffix") || "";
    var state = { v: from };
    function render() { el.textContent = prefix + String(Math.round(state.v)).replace(/\B(?=(\d{3})+$)/g, ",") + suffix; }
    // Not rendered until the tween starts: rendering now would rewrite the
    // built-in $1,000 as $0 the moment the script runs, long before the
    // number is anywhere near the viewport.
    gsap.to(state, {
      v: to, duration: 1.8, ease: "power2.out", onStart: render, onUpdate: render,
      scrollTrigger: { trigger: el, start: "top 88%", once: true }
    });
  });

  // ---- hero video: play only on wide screens, so phones never fetch it
  $$("video.hero-video").forEach(function (v) {
    if (!matchMedia("(min-width: 768px)").matches) return;
    v.preload = "auto";
    // Play only while the hero is on screen: left looping, the video goes on
    // being decoded behind the whole rest of the page.
    new IntersectionObserver(function (entries) {
      if (!entries[0].isIntersecting) { v.pause(); return; }
      var p = v.play();
      if (p && p.catch) p.catch(function () {});
    }).observe(v);
  });

  window.__motionReady = true;
  window.addEventListener("load", function () { ScrollTrigger.refresh(); });
})();
