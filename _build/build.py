"""
Build the prototype site.

Every page shares one header, one footer and one set of stylesheets. Writing
them by hand would mean changing the navigation in every file the first time
it moves, and it will move -- the structure is a proposal, not a decision. So
the pages are data and the shell is code.

Run:  python _build/build.py

Nothing else writes HTML. If you edit index.html directly the next build
discards it.

This is the same arrangement as thevalleyvenues, cut back to a starting point:
the shell, the page table, the image expander and the asset versioning are
kept; the estate map, the film strips, the gallery scraper and the opening
band are not, because Phoenix does not have those yet and may never.
"""
import hashlib, os, re, struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")


# ------------------------------------------------------------- the site facts
SITE = "Phoenix"
TAGLINE = "A Venue Worth the Journey."

# Where the site lives. URL_ROOT is the path every internal link is written
# against and BASE is the absolute origin the og: tags need; nothing else in
# this file or in any stylesheet knows the site's address.
#
# Change BASE with _build/set_domain.py, not by hand -- it keeps CNAME in step.
URL_ROOT = "/"
BASE = "https://phoenix.sparkmedia.ai/"

# The address the site is actually for. While BASE is anything else this is a
# staging copy of a real business's website on a public host, and it asks
# search engines to stay away. Point BASE at the line below (with
# set_domain.py) and the noindex disappears on its own, which is the point:
# "remember to take the noindex off" is a thing somebody forgets on launch day.
PRODUCTION = "https://phoenix.example/"          # TODO: the client's own domain

# Where the inquiry form posts: a GoHighLevel inbound webhook, straight from
# the browser, exactly as The Valley does it. Empty until the client's GHL
# sub-account exists. While it is empty the form does not submit; it shows the
# visitor the contact email instead, so nothing anybody types is lost.
#
# When it is set, remember what that means: the URL is the endpoint's only
# authentication, GHL bills Inbound Webhook per execution, and this repo is
# public. The honeypot in assets/forms.js is the only thing between a scraper
# and the invoice. Do not remove it.
FORM_ENDPOINT = ""
CONTACT_EMAIL = "hello@phoenix.example"           # TODO: the client's inbox

# Primary navigation and the one invitation that sits beside it.
NAV = [
    ("Weddings", "/weddings/"),
    ("The Venue", "/the-venue/"),
    ("Gallery", "/gallery/"),
    ("About", "/about/"),
]
CTA = ("Inquire", "/inquire/")

FOOTER = [
    ("Celebrate", [
        ("Weddings", "/weddings/"),
        ("The Gallery", "/gallery/"),
        ("Inquire", "/inquire/"),
    ]),
    ("The Venue", [
        ("The property", "/the-venue/"),
        ("About", "/about/"),
    ]),
]

ADDRESS = "Address to come<br>City, State"       # TODO
OG_ALT = "Phoenix, the venue, at golden hour"    # TODO: describe assets/og.jpg


# ------------------------------------------------------------------ helpers
def json_str(value):
    """A JavaScript string literal that cannot end the script element early."""
    return ('"' + str(value).replace("\\", "\\\\").replace('"', '\\"')
            .replace("<", "\\x3c") + '"')


def html_attr(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def webp_size(path):
    """Width and height of a WebP, without a dependency.

    Every img on this site carries width and height attributes so the page
    reserves the right space before the bytes arrive. Typing those by hand is
    how they end up wrong, so the numbers are read from the file instead.
    """
    with open(path, "rb") as f:
        head = f.read(30)
    fmt = head[12:16]
    if fmt == b"VP8X":
        w = struct.unpack("<I", head[24:27] + b"\0")[0] + 1
        h = struct.unpack("<I", head[27:30] + b"\0")[0] + 1
        return w, h
    if fmt == b"VP8L":
        b = struct.unpack("<I", head[21:25])[0]
        return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    if fmt == b"VP8 ":
        w, h = struct.unpack("<HH", head[26:30])
        return w & 0x3FFF, h & 0x3FFF
    raise ValueError("not a webp: %s" % path)


_IMG = re.compile(r"\{\{img:([^|}]+)\|([^|}]*)\|?([^}]*)\}\}")
_INLINE = re.compile(r"\{\{inline:([^}]+)\}\}")


def expand(body):
    """Turn {{img:file.webp|alt text|extra attributes}} into a real img tag,
    and {{inline:file.svg}} into the file's contents."""
    def one(m):
        name, alt, extra = m.group(1), m.group(2), m.group(3)
        w, h = webp_size(os.path.join(IMG, name))
        return ('<img src="%sassets/img/%s" alt="%s" width="%d" '
                'height="%d" loading="lazy" decoding="async"%s>'
                % (URL_ROOT, name, alt, w, h, (" " + extra) if extra else ""))
    body = _IMG.sub(one, body)

    def inline(m):
        path = os.path.join(ROOT, "assets", m.group(1).strip())
        return open(path, encoding="utf-8").read().strip()
    return _INLINE.sub(inline, body)


def note(text):
    """A working note. Invisible unless the page is opened with ?notes."""
    return '<aside class="note"><b>Working note</b> %s</aside>\n' % text


# -------------------------------------------------------------------- shell
def shell(page, path="index.html"):
    """Wrap one page's body in the site chrome."""
    root = URL_ROOT
    url = BASE + (path[:-len("index.html")] if path.endswith("index.html") else path)
    nav = "\n".join(
        '        <li><a href="%s"%s>%s</a></li>'
        % (href, ' aria-current="page"' if page.get("nav") == label else "", label)
        for label, href in NAV)

    foot = "\n".join(
        '      <div>\n        <h3>%s</h3>\n        <ul>%s</ul>\n      </div>'
        % (head, "".join('\n          <li><a href="%s">%s</a></li>' % (h, t)
                         for t, h in links) + "\n        ")
        for head, links in FOOTER)

    # One kind of hero for now: words on a photograph when the page has one,
    # words on the house colour when it does not. The photograph arrives as
    # hero_img, a file in assets/img/.
    hero, hero_class = "", "hero-plain"
    if page.get("hero_img"):
        w, h = webp_size(os.path.join(IMG, page["hero_img"]))
        hero_class = "hero-photo"
        hero = ('  <img class="hero-bg" src="%sassets/img/%s" alt="%s" '
                'width="%d" height="%d" fetchpriority="high" decoding="async">\n'
                % (root, page["hero_img"], html_attr(page["hero_alt"]), w, h))
    actions = ""
    if page.get("actions"):
        actions = '\n    <div class="hero-actions">%s</div>' % "".join(
            '\n      <a class="btn%s" href="%s">%s</a>' % (
                " btn-solid" if i == 0 else "", h, t)
            for i, (t, h) in enumerate(page["actions"])) + "\n    "

    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
%(robots)s<link rel="icon" href="%(root)sassets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="%(root)sassets/icon-180.png">
<meta name="theme-color" content="#1F1A17">
<meta property="og:type" content="website">
<meta property="og:site_name" content="%(site)s">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<link rel="canonical" href="%(url)s">
<meta property="og:url" content="%(url)s">
<meta property="og:image" content="%(base)sassets/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="%(og_alt)s">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;1,400&family=Inter:wght@400;500;600&display=swap">
<link rel="stylesheet" href="%(root)sassets/site.css">
<link rel="stylesheet" href="%(root)sassets/forms.css">
%(head)s<script>document.documentElement.classList.add("js");window.FORM_ENDPOINT=%(endpoint)s;window.CONTACT_EMAIL=%(email)s;if(/[?&]notes\\b/.test(location.search))document.documentElement.classList.add("notes")</script>
</head>
<body>

<a class="skip" href="#main">Skip to content</a>

<header class="site-head">
  <div class="inner">
    <a class="wordmark" href="%(root)s"><span class="mark" aria-hidden="true">%(mark)s</span><span>%(site)s</span></a>
    <button type="button" class="nav-toggle" aria-expanded="false" aria-controls="site-nav"><span class="nav-bars" aria-hidden="true"><i></i><i></i></span><span class="nav-word">Menu</span></button>
    <nav class="site-nav" id="site-nav" aria-label="Primary">
      <ul>
%(nav)s
      </ul>
    </nav>
    <a class="btn btn-solid" href="%(cta_href)s">%(cta_text)s</a>
  </div>
</header>

<header class="hero %(hero_class)s">
%(hero)s%(hero_body)s</header>

<main id="main">
%(body)s
</main>

<footer class="site-foot">
  <div class="inner">
%(foot)s
    <div>
      <h3>Visit</h3>
      <address class="addr">%(address)s</address>
    </div>
  </div>
  <div class="colophon">
    <span>Prototype for %(site)s, built by SparkMedia.</span>
    <a class="notes-on" href="?notes">Show working notes</a>
    <a class="notes-off" href="?">Hide working notes</a>
  </div>
</footer>
%(cta_bar)s%(foot_js)s
<script src="%(root)sassets/nav.js" defer></script>
<script src="%(root)sassets/forms.js" defer></script>
</body>
</html>
""" % {
        "title": page["title"], "desc": html_attr(page["desc"]), "root": root,
        "url": url, "base": BASE, "og_alt": html_attr(OG_ALT),
        "endpoint": json_str(FORM_ENDPOINT), "email": json_str(CONTACT_EMAIL),
        "robots": "" if BASE == PRODUCTION else
                  '<meta name="robots" content="noindex,nofollow">' + chr(10),
        "site": SITE, "mark": MARK, "nav": nav,
        "cta_href": CTA[1], "cta_text": CTA[0],
        # On a phone the inquiry button lives in a bar at the foot of the
        # screen instead of the header. Not on the page the button leads to.
        "cta_bar": "" if path.startswith("inquire/") else
                   '<div class="cta-bar"><a class="btn btn-solid" href="%s">%s</a></div>\n' % (CTA[1], CTA[0]),
        "hero": hero, "hero_class": hero_class,
        # A page can leave the words out of its hero when its body opens with
        # its own heading (that heading is then the page's h1).
        "hero_body": "" if page.get("hero_text") is False else
                     '  <div class="hero-body">\n    <div class="eyebrow">%s</div>\n    <h1>%s</h1>\n'
                     '    <p>%s</p>%s\n  </div>\n' % (page["eyebrow"], page["h1"], page["standfirst"], actions),
        "body": expand(page["body"]), "foot": foot, "address": ADDRESS,
        "head": page.get("head", ""), "foot_js": page.get("foot_js", ""),
    }


# The wordmark's mark, inline so it can take the text colour.
MARK = open(os.path.join(ROOT, "assets", "favicon.svg"), encoding="utf-8").read().strip()


# ---------------------------------------------------------------- the pages
PAGES = {}

PAGES["index.html"] = dict(
    nav=None, title="%s | %s" % (SITE, TAGLINE), desc=TAGLINE,
    eyebrow="Weddings &middot; Celebrations &middot; Private events",
    h1=TAGLINE,
    standfirst="A private venue for one celebration at a time. "
               "The details of where, what and how many are coming; "
               "this page is the shape of the site, not the words.",
    actions=[("Inquire about a date", "/inquire/"), ("See the venue", "/the-venue/")],
    body=note("Every sentence on this site is a placeholder until the client brief lands. "
              "The structure (four destinations and one invitation) mirrors what worked "
              "for The Valley; change it in NAV at the top of _build/build.py.") + """
<section class="band">
  <div class="inner narrow">
    <div class="eyebrow">The idea</div>
    <h2>One venue. One celebration. Your day, undivided.</h2>
    <p>Placeholder for the positioning paragraph: what Phoenix is, where it is, and the one
    thing it does that nowhere else nearby does.</p>
  </div>
</section>

<section class="band band-tint">
  <div class="inner">
    <div class="cards three">
      <a class="card" href="/weddings/">
        <div class="card-body"><h3>Weddings</h3><p>Ceremony, reception and everything between, on one property.</p></div>
      </a>
      <a class="card" href="/the-venue/">
        <div class="card-body"><h3>The Venue</h3><p>The spaces, the grounds and how they fit together.</p></div>
      </a>
      <a class="card" href="/gallery/">
        <div class="card-body"><h3>Gallery</h3><p>Photographs, credited to the people who took them.</p></div>
      </a>
    </div>
  </div>
</section>

<section class="band">
  <div class="inner narrow center">
    <h2>Ready to look at dates?</h2>
    <p>The inquiry form takes two minutes and goes straight to the team.</p>
    <p><a class="btn btn-solid" href="/inquire/">Inquire</a></p>
  </div>
</section>
""",
)

PAGES["weddings/index.html"] = dict(
    nav="Weddings", title="Weddings | %s" % SITE,
    desc="Weddings at %s: what a day here looks like and what is included." % SITE,
    eyebrow="Weddings",
    h1="A day that is entirely yours.",
    standfirst="Placeholder standfirst. Ceremony, cocktails, dinner and dancing, "
               "each with its own room or view.",
    body=note("What's-included, capacity, pricing and the season calendar all live here "
              "once we have them. The Valley splits these into sub-pages; start with one.") + """
<section class="band">
  <div class="inner narrow">
    <h2>What is included</h2>
    <ul class="ticks">
      <li>Placeholder: exclusive use of the venue for the day</li>
      <li>Placeholder: ceremony and reception spaces</li>
      <li>Placeholder: tables, chairs and setup</li>
      <li>Placeholder: on-site coordinator</li>
    </ul>
  </div>
</section>
<section class="band band-tint">
  <div class="inner narrow center">
    <h2>Capacity and pricing</h2>
    <p>Placeholder. Publish a starting figure or do not; The Valley chose to.</p>
    <p><a class="btn btn-solid" href="/inquire/">Ask about a date</a></p>
  </div>
</section>
""",
)

PAGES["the-venue/index.html"] = dict(
    nav="The Venue", title="The Venue | %s" % SITE,
    desc="The spaces and grounds at %s." % SITE,
    eyebrow="The Venue",
    h1="The property, space by space.",
    standfirst="Placeholder standfirst. Each space gets a name, a capacity and a photograph.",
    body=note("One section per space. When the photographs arrive, each section gets an "
              "img placeholder (see expand() in build.py) and the build reads the "
              "dimensions from the file.") + """
<section class="band">
  <div class="inner">
    <div class="cards two">
      <div class="card"><div class="card-body"><h3>Space one</h3><p>Placeholder. Seats N, opens onto M.</p></div></div>
      <div class="card"><div class="card-body"><h3>Space two</h3><p>Placeholder. Seats N, opens onto M.</p></div></div>
      <div class="card"><div class="card-body"><h3>The grounds</h3><p>Placeholder. Acreage, views, the walk from ceremony to reception.</p></div></div>
      <div class="card"><div class="card-body"><h3>Getting here</h3><p>Placeholder. Minutes from the nearest city and airport.</p></div></div>
    </div>
  </div>
</section>
""",
)

PAGES["gallery/index.html"] = dict(
    nav="Gallery", title="Gallery | %s" % SITE,
    desc="Photographs of %s." % SITE,
    eyebrow="The Gallery",
    h1="Photographs sell this place better than we can.",
    standfirst="Placeholder. Real weddings, credited, once the client has permission from the couples.",
    body=note("The Valley's gallery is generated from assets/gallery.json by gallery.js "
              "with a per-photographer filter. Bring that over when there are photographs "
              "to fill it; a grid of six is a page, a grid of two is an apology.") + """
<section class="band">
  <div class="inner narrow center">
    <p class="muted">Photographs to come.</p>
  </div>
</section>
""",
)

PAGES["about/index.html"] = dict(
    nav="About", title="About | %s" % SITE,
    desc="The people behind %s." % SITE,
    eyebrow="About",
    h1="The people behind the place.",
    standfirst="Placeholder. Who owns it, who runs it, and why they do.",
    body=note("A named owner or coordinator with a photograph is the single most "
              "persuasive thing this page can carry.") + """
<section class="band">
  <div class="inner narrow">
    <h2>Our story</h2>
    <p>Placeholder paragraph one.</p>
    <p>Placeholder paragraph two.</p>
  </div>
</section>
""",
)

PAGES["inquire/index.html"] = dict(
    nav=None, title="Inquire | %s" % SITE,
    desc="Ask about a date at %s." % SITE,
    eyebrow="Inquire",
    h1="Tell us about your day.",
    standfirst="Two minutes. Someone from the team replies within a business day.",
    body=note("Posts to FORM_ENDPOINT in _build/build.py. While that is empty the form "
              "shows the contact email instead of submitting. Field names and option "
              "strings must match the CRM exactly; see assets/forms.js.") + """
<section class="band">
  <div class="inner narrow">
    <form class="inquiry" method="post" action="#" novalidate>
      <div class="row two">
        <label>First name <input name="first_name" autocomplete="given-name" required></label>
        <label>Last name <input name="last_name" autocomplete="family-name" required></label>
      </div>
      <div class="row two">
        <label>Email <input type="email" name="email" autocomplete="email" required></label>
        <label>Phone <input type="tel" name="phone" autocomplete="tel"></label>
      </div>
      <div class="row two">
        <label>Event type
          <select name="event_type" required>
            <option value="">Choose one</option>
            <option>Wedding</option>
            <option>Celebration</option>
            <option>Corporate</option>
            <option>Other</option>
          </select>
        </label>
        <label>Guest count <input type="number" name="guest_count" min="1" max="1000" inputmode="numeric"></label>
      </div>
      <div class="row two">
        <label>Preferred date <input type="date" name="event_date"></label>
        <label>Or a season
          <select name="season">
            <option value="">Not sure yet</option>
            <option>Spring</option><option>Summer</option><option>Autumn</option><option>Winter</option>
          </select>
        </label>
      </div>
      <label>Anything else <textarea name="message" rows="4"></textarea></label>
      <!-- Honeypot. Humans never see it; scrapers fill it. Do not remove. -->
      <label class="hp" aria-hidden="true">Website <input name="website" tabindex="-1" autocomplete="off"></label>
      <p class="form-actions"><button class="btn btn-solid" type="submit">Send inquiry</button></p>
      <p class="form-status" role="status" aria-live="polite"></p>
    </form>
  </div>
</section>
""",
)

PAGES["404.html"] = dict(
    nav=None, title="Not found | %s" % SITE, desc="That page is not here.",
    eyebrow="404", h1="That page is not here.",
    standfirst="It may have moved while the site is being built.",
    actions=[("Go to the home page", "/")],
    body="",
)


# --------------------------------------------------------------------- write
# Every stylesheet and script link carries a short hash of the file it points
# at. GitHub Pages serves assets with a ten-minute cache; without this a fix
# to site.css is invisible to anyone who looked at the site in the last ten
# minutes. The hash only changes when the file does.
ASSET_LINK = re.compile(r'((?:href|src)="/assets/[a-z0-9-]+\.(?:css|js))"')
_digest = {}


def version_assets(html):
    def stamp(m):
        rel = m.group(1).split('"')[1]
        if rel not in _digest:
            with open(os.path.join(ROOT, rel.lstrip("/")), "rb") as f:
                _digest[rel] = hashlib.md5(f.read()).hexdigest()[:8]
        return '%s?v=%s"' % (m.group(1), _digest[rel])
    return ASSET_LINK.sub(stamp, html)


if __name__ == "__main__":
    for path, page in PAGES.items():
        dest = os.path.join(ROOT, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        html = version_assets(shell(page, path))
        open(dest, "w", encoding="utf-8", newline="\n").write(html)
        print("%-32s %6d bytes" % (path, len(html)))
    print("\n%d pages" % len(PAGES))
