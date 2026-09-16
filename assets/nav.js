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
