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

// Video posters. A click swaps the poster for YouTube's player, on the
// no-cookie domain and set to play at once. Without this the poster is a
// plain link to the video on YouTube.
document.addEventListener("click", function (e) {
  var a = e.target.closest && e.target.closest("a.yt[data-yt]");
  if (!a) return;
  e.preventDefault();
  var f = document.createElement("iframe");
  f.src = "https://www.youtube-nocookie.com/embed/" + a.getAttribute("data-yt") + "?autoplay=1&rel=0";
  f.title = a.getAttribute("data-title") || "Video";
  f.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
  f.setAttribute("allowfullscreen", "");
  var box = document.createElement("div");
  box.className = "yt";
  box.appendChild(f);
  a.parentNode.replaceChild(box, a);
});
