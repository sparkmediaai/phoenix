// The inquiry form. Posts JSON straight to the GoHighLevel inbound webhook in
// window.FORM_ENDPOINT, the way The Valley's forms do.
//
// Because there is no server, every rule the CRM depends on is enforced here:
// the exact option strings, guest_count as a number, phone to E.164,
// submitted_at at submit. A value that is not on the allowlist is dropped
// rather than sent -- an empty CRM field is at least visible, a wrong one is
// not.
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

  var EVENT_TYPES = ["Wedding", "Celebration", "Corporate", "Other"];
  var SEASONS = ["Spring", "Summer", "Autumn", "Winter"];

  function say(msg, cls) {
    status.textContent = msg;
    status.className = "form-status" + (cls ? " " + cls : "");
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
    var f = form.elements;
    var out = {
      first_name: f.first_name.value.trim(),
      last_name: f.last_name.value.trim(),
      email: f.email.value.trim(),
      phone: e164(f.phone.value),
      event_type: EVENT_TYPES.indexOf(f.event_type.value) >= 0 ? f.event_type.value : "",
      guest_count: f.guest_count.value ? parseInt(f.guest_count.value, 10) : null,
      event_date: f.event_date.value || "",
      season: SEASONS.indexOf(f.season.value) >= 0 ? f.season.value : "",
      message: f.message.value.trim(),
      source: location.hostname + location.pathname,
      submitted_at: new Date().toISOString()
    };
    return out;
  }

  function invalid(name, yes) {
    var el = form.elements[name];
    if (el) el.setAttribute("aria-invalid", yes ? "true" : "false");
  }

  function validate(d) {
    var ok = true;
    ["first_name", "last_name", "email", "event_type"].forEach(function (k) {
      var bad = !d[k];
      invalid(k, bad); if (bad) ok = false;
    });
    if (d.email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(d.email)) { invalid("email", true); ok = false; }
    return ok;
  }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    if (form.elements.website && form.elements.website.value) {
      // Honeypot filled: pretend it worked, post nothing.
      say("Thank you. We will be in touch.", "ok");
      form.reset();
      return;
    }
    var data = collect();
    if (!validate(data)) { say("Please check the highlighted fields.", "err"); return; }

    if (!endpoint) {
      say("Inquiries are not open online yet. Please email " + email + " and we will reply within a business day.", "err");
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
      say("Thank you. Someone from the team will reply within a business day.", "ok");
      form.reset();
    }).catch(function () {
      say("That did not go through. Please email " + email + " instead; nothing you typed has been lost.", "err");
    }).finally(function () { btn.disabled = false; });
  });
})();
