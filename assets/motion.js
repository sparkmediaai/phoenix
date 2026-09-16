// Motion. Reads the data attributes the build writes and animates them with
// GSAP + ScrollTrigger. Loaded only when html.motion is set (see the gate in
// _build/build.py). Every initial hidden state lives in motion.css and uses
// opacity and transform only, so assistive technology reads the page in
// document order whether or not this file runs.
//
//   data-reveal            fade and rise into place once, on entering the viewport
//   data-reveal="stagger"  the same, for the element's children, 120ms apart
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
  if (!window.gsap || !window.ScrollTrigger) return;
  gsap.registerPlugin(ScrollTrigger);
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

  // ---- reveal
  $$("[data-reveal]").forEach(function (el) {
    var stagger = el.getAttribute("data-reveal") === "stagger";
    var targets = stagger ? Array.prototype.slice.call(el.children) : [el];
    if (!targets.length) return;
    gsap.to(targets, {
      opacity: 1, y: 0, duration: 0.9, ease: "power3.out", stagger: stagger ? 0.12 : 0,
      scrollTrigger: { trigger: el, start: "top 88%", once: true }
    });
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
  function prepDraw(paths) {
    paths.forEach(function (p) {
      var len = p.getTotalLength();
      p.style.strokeDasharray = len;
      p.style.strokeDashoffset = len;
    });
  }
  function drawable(root) {
    return $$("path, line, polyline, circle, rect, ellipse", root).filter(function (p) { return typeof p.getTotalLength === "function"; });
  }

  // ---- pinned sequences
  $$("[data-pin]").forEach(function (section) {
    var steps = $$("[data-step]", section);
    if (!steps.length) return;
    var length = parseFloat(section.getAttribute("data-pin-length")) || 2;
    var hold = $$("[data-hold]", section);
    var dim = $$("[data-dim]", section);
    gsap.set(steps, { opacity: 0, y: 30 });
    var tl = gsap.timeline({
      scrollTrigger: { trigger: section, start: "top top", end: "+=" + (length * 100) + "%", pin: true, scrub: 0.6, anticipatePin: 1 }
    });
    if (hold.length) tl.to(hold, { opacity: 0, y: -40, duration: 1 }, 0);
    if (dim.length) tl.to(dim, { opacity: 0.85, duration: 1 }, 0);
    steps.forEach(function (step, i) {
      var at = i === 0 ? 0.6 : ">";
      tl.to(step, { opacity: 1, y: 0, duration: 1 }, at);
      var sel = step.getAttribute("data-step-draw");
      if (sel) {
        var paths = drawable(section.querySelector(sel) || document.querySelector(sel));
        if (paths.length) { prepDraw(paths); tl.to(paths, { strokeDashoffset: 0, duration: 1.2, stagger: 0.15 }, "<"); }
      }
      tl.to({}, { duration: 1 });                          // hold
      if (i < steps.length - 1) tl.to(step, { opacity: 0, y: -30, duration: 0.8 });
    });
  });

  // ---- standalone drawings
  $$("svg[data-draw]").forEach(function (svg) {
    if (svg.closest("[data-pin]")) return;                 // handled by the pin above
    var paths = drawable(svg);
    if (!paths.length) return;
    prepDraw(paths);
    gsap.to(paths, {
      strokeDashoffset: 0, ease: "none", stagger: 0.25,
      scrollTrigger: { trigger: svg, start: "top 85%", end: "bottom 45%", scrub: true }
    });
  });

  // ---- counters
  $$("[data-count]").forEach(function (el) {
    var to = parseFloat(el.getAttribute("data-count")) || 0;
    var from = parseFloat(el.getAttribute("data-count-from")) || 0;
    var prefix = el.getAttribute("data-count-prefix") || "";
    var suffix = el.getAttribute("data-count-suffix") || "";
    var state = { v: from };
    function render() { el.textContent = prefix + Math.round(state.v).toLocaleString("en-US") + suffix; }
    render();
    gsap.to(state, {
      v: to, duration: 1.8, ease: "power2.out", onUpdate: render,
      scrollTrigger: { trigger: el, start: "top 88%", once: true }
    });
  });

  // ---- hero video: play only on wide screens, so phones never fetch it
  $$("video.hero-video").forEach(function (v) {
    if (!matchMedia("(min-width: 768px)").matches) return;
    v.preload = "auto";
    var p = v.play();
    if (p && p.catch) p.catch(function () {});
  });

  window.__motionReady = true;
  window.addEventListener("load", function () { ScrollTrigger.refresh(); });
})();
