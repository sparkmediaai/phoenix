// The application-review form. Posts JSON straight to the GoHighLevel inbound
// webhook in window.FORM_ENDPOINT, the way The Valley's forms do.
//
// Because there is no server, every rule the CRM depends on is enforced here:
// the exact option strings, phone to E.164, submitted_at at submit. A value
// that is not on the allowlist is dropped rather than sent -- an empty CRM
// field is at least visible, a wrong one is not. The option lists must match
// CONTROLS and VOLUMES in _build/build.py; change both together.
//
// The honeypot: the "website" field is hidden from people and filled by
// scrapers. A filled honeypot is silently accepted and never posted. It is the
// only thing between a scraper and the per-execution webhook invoice. Do not
// remove it.
(function () {
  var form = document.querySelector("form.inquiry");
  if (!form) return;
  var status = form.querySelector(".form-status");
  var endpoint = window.FORM_ENDPOINT || "";
  var email = window.CONTACT_EMAIL || "";

  var CONTROLS = ["Allen-Bradley / Rockwell", "Siemens", "Omron", "Automation Direct", "Maple Systems",
                  "Relay logic / no PLC", "Other", "Not sure"];
  var VOLUMES = ["Under 50", "50 to 250", "250 to 1,000", "1,000 to 5,000", "Over 5,000"];

  function say(msg, cls) {
    status.textContent = msg;
    status.className = "form-status" + (cls ? " " + cls : "");
  }

  function val(name) {
    var el = form.elements[name];
    return el ? (el.value || "").trim() : "";
  }

  function e164(raw) {
    var digits = (raw || "").replace(/\D/g, "");
    if (!digits) return "";
    if (digits.length === 10) return "+1" + digits;          // US, no country code
    if (digits.length === 11 && digits[0] === "1") return "+" + digits;
    if (raw.trim()[0] === "+" && digits.length >= 8) return "+" + digits;
    return "";                                               // not confidently a number
  }

  function collect() {
    return {
      machine_type: val("machine_type"),
      annual_volume: VOLUMES.indexOf(val("annual_volume")) >= 0 ? val("annual_volume") : "",
      current_controls: CONTROLS.indexOf(val("current_controls")) >= 0 ? val("current_controls") : "",
      application: val("application"),
      spec_link: /^https?:\/\//i.test(val("spec_link")) ? val("spec_link") : "",
      company: val("company"),
      role: val("role"),
      first_name: val("first_name"),
      last_name: val("last_name"),
      email: val("email"),
      phone: e164(val("phone")),
      source: location.hostname + location.pathname,
      submitted_at: new Date().toISOString()
    };
  }

  function invalid(name, yes) {
    var el = form.elements[name];
    if (el) el.setAttribute("aria-invalid", yes ? "true" : "false");
  }

  function validate(d) {
    var ok = true;
    ["machine_type", "annual_volume", "current_controls", "application",
     "company", "first_name", "last_name", "email"].forEach(function (k) {
      var bad = !d[k];
      invalid(k, bad); if (bad) ok = false;
    });
    if (d.email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(d.email)) { invalid("email", true); ok = false; }
    return ok;
  }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    if (form.elements.website && form.elements.website.value) {
      say("Thank you. Russell will be in touch.", "ok");
      form.reset();
      return;
    }
    var data = collect();
    if (!validate(data)) { say("Please check the highlighted fields.", "err"); return; }

    if (!endpoint) {
      say("Online submissions are not open yet. Please email the same details to " + email + " and Russell will reply within two business days.", "err");
      return;
    }

    var btn = form.querySelector("button[type=submit]");
    btn.disabled = true; say("Sending…");
    fetch(endpoint, {
      method: "POST", mode: "cors",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      say("Thank you. Russell reads every submission and will reply within two business days.", "ok");
      form.reset();
    }).catch(function () {
      say("That did not go through. Please email " + email + " instead; nothing you typed has been lost.", "err");
    }).finally(function () { btn.disabled = false; });
  });
})();
