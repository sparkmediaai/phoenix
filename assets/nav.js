// The menu. Five headers, each opening a panel of pages. On a desktop the
// panel opens on hover or keyboard focus (CSS) and a click pins it open; on
// a phone the Menu button shows the list and each header is an accordion.
// Escape closes everything; so does a click anywhere else.
(function () {
  var btn = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (!btn || !nav) return;
  var heads = Array.prototype.slice.call(nav.querySelectorAll(".menu-head"));

  function closeAll(except) {
    heads.forEach(function (h) {
      if (h !== except) { h.setAttribute("aria-expanded", "false"); h.parentNode.classList.remove("open"); }
    });
  }
  function setMenu(open) {
    nav.classList.toggle("open", open);
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.querySelector(".nav-word").textContent = open ? "Close" : "Menu";
    if (!open) closeAll();
  }
  heads.forEach(function (h) {
    h.addEventListener("click", function () {
      var open = h.getAttribute("aria-expanded") === "true";
      closeAll(h);
      h.setAttribute("aria-expanded", open ? "false" : "true");
      h.parentNode.classList.toggle("open", !open);
    });
  });
  btn.addEventListener("click", function () { setMenu(!nav.classList.contains("open")); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") setMenu(false); });
  document.addEventListener("click", function (e) {
    if (!nav.contains(e.target) && !btn.contains(e.target)) closeAll();
  });
})();

// The family pills on catalog pages. Once the picture tiles have scrolled
// away, a slim bar of the same links slides out from under the header, and the
// family on screen is marked current. No script, no bar: the tiles still work.
(function () {
  var pills = document.querySelector(".family-pills");
  var tiles = document.querySelector(".family-index");
  var head = document.querySelector(".site-head");
  if (!pills || !tiles || !head || !("IntersectionObserver" in window)) return;
  function place() { pills.style.top = head.offsetHeight + "px"; }
  place();
  window.addEventListener("resize", place);
  new IntersectionObserver(function (entries) {
    var e = entries[0];
    pills.classList.toggle("show", !e.isIntersecting && e.boundingClientRect.top < 0);
  }).observe(tiles);
  var links = {};
  Array.prototype.forEach.call(pills.querySelectorAll("a"), function (a) { links[a.getAttribute("href").slice(1)] = a; });
  var spy = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting || !links[e.target.id]) return;
      Object.keys(links).forEach(function (k) { links[k].removeAttribute("aria-current"); });
      var a = links[e.target.id];
      a.setAttribute("aria-current", "true");
      pills.scrollTo({ left: a.offsetLeft - (pills.clientWidth - a.offsetWidth) / 2, behavior: "smooth" });
    });
  }, { rootMargin: "-40% 0px -55% 0px" });
  Array.prototype.forEach.call(document.querySelectorAll(".family-band"), function (s) { spy.observe(s); });
})();
