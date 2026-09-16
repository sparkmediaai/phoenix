// The intake form as four steps. Purely presentational: the form, its
// fields, forms.js's validation and the honeypot are untouched. With
// JavaScript off all four fieldsets show and the form works as one page.
(function () {
  var form = document.querySelector("form.inquiry");
  if (!form) return;
  var steps = Array.prototype.slice.call(form.querySelectorAll("[data-wizard-step]"));
  if (steps.length < 2) return;
  var submitRow = form.querySelector(".form-actions");
  var current = 0;

  var nav = document.createElement("p");
  nav.className = "wizard-nav";
  var back = document.createElement("button");
  back.type = "button"; back.className = "btn"; back.textContent = "Back";
  var next = document.createElement("button");
  next.type = "button"; next.className = "btn btn-solid"; next.textContent = "Next";
  var progress = document.createElement("span");
  progress.className = "wizard-progress"; progress.setAttribute("aria-live", "polite");
  nav.appendChild(back); nav.appendChild(next); nav.appendChild(progress);
  submitRow.parentNode.insertBefore(nav, submitRow);
  form.classList.add("wizard");

  function stepValid(i) {
    var ok = true;
    Array.prototype.slice.call(steps[i].querySelectorAll("input, select, textarea")).forEach(function (el) {
      var bad = el.required && !el.value.trim();
      if (!bad && el.type === "email" && el.value && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(el.value)) bad = true;
      el.setAttribute("aria-invalid", bad ? "true" : "false");
      if (bad) ok = false;
    });
    return ok;
  }

  function show(i, dir) {
    var from = steps[current];
    current = i;
    steps.forEach(function (s, k) { s.hidden = k !== i; });
    back.hidden = i === 0;
    next.hidden = i === steps.length - 1;
    submitRow.hidden = i !== steps.length - 1;
    progress.textContent = "Step " + (i + 1) + " of " + steps.length;
    var to = steps[i];
    if (window.gsap && document.documentElement.classList.contains("motion") && from !== to) {
      gsap.fromTo(to, { opacity: 0, x: 24 * (dir || 1) }, { opacity: 1, x: 0, duration: 0.45, ease: "power2.out" });
    }
    var first = to.querySelector("input, select, textarea");
    if (first && dir) first.focus({ preventScroll: true });
  }

  next.addEventListener("click", function () { if (stepValid(current)) show(current + 1, 1); });
  back.addEventListener("click", function () { show(current - 1, -1); });
  form.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && e.target.tagName !== "TEXTAREA" && e.target.tagName !== "BUTTON" && current < steps.length - 1) { e.preventDefault(); next.click(); }
  });
  // If forms.js flags a field on a hidden step, jump to it.
  form.addEventListener("submit", function () {
    setTimeout(function () {
      var bad = form.querySelector('[aria-invalid="true"]');
      if (!bad) return;
      var i = steps.indexOf(bad.closest("[data-wizard-step]"));
      if (i >= 0 && i !== current) show(i, -1);
    }, 0);
  });
  show(0, 0);
})();
