"""
Build the prototype site.

Every page shares one header, one footer and one set of stylesheets. Writing
them by hand would mean changing the navigation in every file the first time
it moves, and it will move -- the structure is a proposal, not a decision. So
the pages are data and the shell is code.

Run:  python _build/build.py

Nothing else writes HTML. If you edit index.html directly the next build
discards it.

Same arrangement as thevalleyvenues, cut back to a starting point: the shell,
the page table, the image expander and the asset versioning are kept.
"""
import hashlib, os, re, struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")


# ------------------------------------------------------------- the site facts
SITE = "Phoenix Automation Solutions"
TAGLINE = "Engineered to the target. Not quoted from the shelf."

# Where the site lives. URL_ROOT is the path every internal link is written
# against and BASE is the absolute origin the og: tags need; nothing else in
# this file or in any stylesheet knows the site's address.
#
# Change BASE with _build/set_domain.py, not by hand -- it keeps CNAME in step.
URL_ROOT = "/"
BASE = "https://www.phoenixautomationsolutions.com/"

# The address the site is actually for. While BASE is anything else this is a
# staging copy of a real business's website on a public host, and it asks
# search engines to stay away. Point BASE at the line below (with
# set_domain.py) and the noindex disappears on its own, which is the point:
# "remember to take the noindex off" is a thing somebody forgets on launch day.
PRODUCTION = "https://www.phoenixautomationsolutions.com/"

# Where the intake form posts: a GoHighLevel inbound webhook, straight from
# the browser, exactly as The Valley does it. Empty until Phoenix's GHL
# sub-account exists. While it is empty the form does not submit; it shows the
# visitor the phone number instead, so nothing anybody types is lost.
#
# When it is set, remember what that means: the URL is the endpoint's only
# authentication, GHL bills Inbound Webhook per execution, and this repo is
# public. The honeypot in assets/forms.js is the only thing between a scraper
# and the invoice. Do not remove it.
FORM_ENDPOINT = ""
# No email on the site: Russ would rather every enquiry come through the form
# (22 Sep). Set this and the mailto links come back, on the contact page,
# in the footer and as the form's fallback.
CONTACT_EMAIL = ""
PHONE = "630 879 8412"

# Primary navigation: five headers, each a menu of pages, plus the one button.
# A header is a grouping, not a page; its intro line sits at the top of the
# open menu. Each page entry is (label, href, one-line summary). The page
# table's `nav` value names the page label; the header lights up when one of
# its pages is current.
NAV = [
    ("Machine Builders", "For OEMs who want controls designed for their machine.", [
        ("Custom Controls", "/machine-builders/custom-controls/",
         "Built to your print: logo on the bezel, panel cutout, mounting pattern, I/O count."),
        ("How a Design Win Works", "/machine-builders/design-win/",
         "One approved part across your whole machine lineup, from first call to production."),
        ("Industries", "/machine-builders/industries/",
         "Packaging, residential elevators and food equipment: the machines and the controls on them."),
    ]),
    ("Products", "For integrators, panel shops and maintenance buyers who already know what they need.", [
        ("HMIs", "/products/hmis/", "Touchscreens by screen size, with specs and stock status."),
        ("PLCs and HMI/PLC Combos", "/products/plcs/", "Controllers and all-in-one units, with specs and stock status."),
        ("I/O and Communication Modules", "/products/io-and-communication/",
         "Add-on inputs and outputs, plus Ethernet, serial and Modbus options."),
        ("Cross-Reference", "/products/cross-reference/",
         "Phoenix replacements matched to the brands already in your panel."),
        ("Datasheets", "/products/datasheets/", "Spec sheets and dimension drawings for every product."),
    ]),
    ("Proof", "Evidence that the work holds up.", [
        ("Case Studies", "/proof/case-studies/", "Real jobs: the problem, what was built, the result."),
        ("Custom Builds", "/proof/custom-builds/", "Custom parts installed in real machines."),
    ]),
    ("Support", "For current customers.", [
        ("Software, Manuals and Firmware", "/support/software/",
         "Programming software, user manuals and firmware updates."),
        ("Warranty and RMA", "/support/warranty-and-rma/", "Warranty terms and how to return a part."),
        ("Videos", "/support/videos/", "Product walkthroughs and software tutorials from the factory."),
    ]),
    ("Company", "Who Phoenix is.", [
        ("About Russ", "/company/about-russ/", "Russ's background, his introduction and how he works with customers."),
        ("Supply Chain", "/company/supply-chain/", "The factory relationship and the stock held in Mokena."),
        ("Certifications", "/company/certifications/", "Product certifications and company credentials."),
        ("Contact", "/company/contact/", "One phone number, one form, the Mokena address."),
    ]),
]
CTA = ("Talk to Russ", "/talk-to-russ/")

# Where the old URLs went. Each becomes a stub that sends the visitor on;
# the PACK EXPO QR code and anything already shared keep working.
MOVED = {
    "for-oems/index.html": "/machine-builders/design-win/",
    "capabilities/index.html": "/machine-builders/custom-controls/",
    "industries/index.html": "/machine-builders/industries/",
    "about/index.html": "/company/about-russ/",
    "start/index.html": "/talk-to-russ/",
}

ADDRESS = "Mokena, Illinois<br>Southwest of Chicago"     # TODO: street address
OG_ALT = "A control panel built for an OEM machine by Phoenix Automation Solutions"

# PACK EXPO International 2026, McCormick Place, Chicago.
SHOW = dict(name="PACK EXPO International", dates="September 28 &ndash; October 1, 2026",
            place="McCormick Place, Chicago")


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
    """Turn an img placeholder (img:name|alt|extra, in double braces, where
    name is the output name without its width suffix or extension) into a real
    img tag, and an inline placeholder into the file's contents.

    The srcset descriptors are the files' own widths, not 800 and 1600: a crop
    narrower than 1600px is never upscaled, so several of the large files are
    1050, 1160 or 1400 wide and a hard-coded 1600w would tell the browser to
    pick them for a display width they cannot fill.
    """
    def one(m):
        name, alt, extra = m.group(1), m.group(2), m.group(3)
        big, small = "%s-1600.webp" % name, "%s-800.webp" % name
        w, h = webp_size(os.path.join(IMG, big))
        sw = webp_size(os.path.join(IMG, small))[0]
        return ('<img src="%(r)sassets/img/%(big)s" '
                'srcset="%(r)sassets/img/%(small)s %(sw)dw, %(r)sassets/img/%(big)s %(w)dw" '
                'sizes="(max-width: 800px) 100vw, 800px" alt="%(alt)s" width="%(w)d" height="%(h)d" '
                'loading="lazy" decoding="async"%(extra)s>'
                % dict(r=URL_ROOT, big=big, small=small, alt=alt, w=w, h=h, sw=sw,
                       extra=(" " + extra) if extra else ""))
    body = _IMG.sub(one, body)

    def inline(m):
        path = os.path.join(ROOT, "assets", m.group(1).strip())
        return open(path, encoding="utf-8").read().strip()
    return _INLINE.sub(inline, body)


def note(text):
    """A working note. Invisible unless the page is opened with ?notes."""
    return '<aside class="note"><b>Working note</b> %s</aside>\n' % text


def cards(items, cls="three"):
    out = []
    for item in items:
        title, text = item[0], item[1]
        media = ""
        if len(item) == 4:
            media = ('<div class="card-media"><div class="card-shift" data-parallax="0.12">'
                     '{{img:%s|%s|class="card-img"}}</div></div>' % (item[2], html_attr(item[3])))
        out.append('      <div class="card">%s<div class="card-body"><h3>%s</h3><p>%s</p></div></div>'
                   % (media, title, text))
    return '<div class="cards %s" data-reveal="stagger">\n%s\n    </div>' % (cls, "\n".join(out))


def linked_cards(items, cls="three"):
    """Cards that are links: (title, href, text, image_name or None, alt or None)."""
    out = []
    for title, href, text, image, alt in items:
        media = ""
        if image:
            media = ('<div class="card-media"><div class="card-shift" data-parallax="0.12">'
                     '{{img:%s|%s|class="card-img"}}</div></div>' % (image, html_attr(alt)))
        out.append('      <a class="card" href="%s">%s<div class="card-body"><h3>%s</h3><p>%s</p></div></a>'
                   % (href, media, title, text))
    return '<div class="cards %s" data-reveal="stagger">\n%s\n    </div>' % (cls, "\n".join(out))


def spec_table(caption, headers, rows):
    """A specification table. First cell of each row is the row header (the part number)."""
    head = "".join('<th scope="col">%s</th>' % h for h in headers)
    body = "".join(
        "<tr>%s</tr>" % "".join(('<th scope="row">%s</th>' if i == 0 else "<td>%s</td>") % c
                                for i, c in enumerate(r)) for r in rows)
    return ('<div class="spec-wrap" data-reveal="rows"><table class="spec"><caption>%s</caption>'
            '<thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (caption, head, body))


def steps(items):
    return '<ol class="steps" data-reveal="stagger">\n%s\n    </ol>' % "\n".join(
        '      <li><h3>%s</h3><p>%s</p></li>' % (t, p) for t, p in items)


# The factory's videos, by YouTube id. Our own title and description go on
# the page; the player shows the channel's once it is playing.
VIDEOS = {
    "eco-plc": ("uxfkgtCQcvI", "The eco PLC, up close",
                "A walkthrough of the FL004: the controller itself, its I/O and ports, and the machines it is sized for."),
    "software": ("pe0WDcuWw18", "The programming software, start to finish",
                 "A complete tour of the programming environment, from installation to a first project set up and running."),
}


def video(key, eyebrow="Watch"):
    """A YouTube video as a poster with a play button. The player only loads on
    a click (nav.js swaps it in), so the page stays light and YouTube sets no
    cookies until someone chooses to watch. Without script the poster is a
    link to the video on YouTube."""
    vid, title, text = VIDEOS[key]
    return """<figure class="video" data-reveal>
      <a class="yt" href="https://www.youtube.com/watch?v=%(id)s" data-yt="%(id)s" data-title="%(t)s">
        <img src="https://i.ytimg.com/vi/%(id)s/hqdefault.jpg" alt="" width="480" height="360" loading="lazy" decoding="async">
        <span class="yt-play" aria-hidden="true"></span>
        <span class="vh">Play: %(title)s</span>
      </a>
      <figcaption><div class="eyebrow">%(eyebrow)s</div><h3>%(title)s</h3><p>%(text)s</p></figcaption>
    </figure>""" % dict(id=vid, t=html_attr(title), title=title, text=text, eyebrow=eyebrow)


def figure(svg_name, caption, cls=""):
    """An inlined drawing that draws itself as it scrolls in, with a caption."""
    return ('<figure class="art%s" data-reveal>{{inline:art/%s}}<figcaption>%s</figcaption></figure>'
            % ((" " + cls) if cls else "", svg_name, caption))


def pinned(steps, svg_name, length=None):
    """A section that pins while its steps play beside a drawing that draws
    itself one group per step. With motion off the steps stack under each
    other beside the finished drawing."""
    length = length or len(steps) + 1
    items = "".join(
        '      <div class="pin-step" data-step data-step-draw="%s"><div class="eyebrow">%s</div><h2>%s</h2><p>%s</p></div>\n'
        % (sel, eyebrow, heading, text) for eyebrow, heading, text, sel in steps)
    return ('<section class="band pin" data-pin data-pin-length="%d">\n  <div class="inner pin-grid">\n'
            '    <div class="pin-steps">\n%s    </div>\n'
            '    <figure class="art pin-figure">{{inline:art/%s}}</figure>\n  </div>\n</section>'
            % (length, items, svg_name))


MOTION_SCRIPTS = ["/assets/vendor/gsap.min.js", "/assets/vendor/ScrollTrigger.min.js", "/assets/motion.js"]


def motion_loader(root):
    """Loads GSAP and motion.js in order, only when the gate added html.motion.

    Dynamically inserted scripts are async by default; async=false restores
    document order. If any script fails, or motion.js has not reported in
    within four seconds, the motion class comes off so nothing stays hidden.

    The timer is on window so motion.js can clear it the moment it starts
    executing: a slow connection that delivers the scripts at four and a half
    seconds would otherwise strip the class out from under a script that is
    about to run, and motion.js checks for that too before it animates
    anything.
    """
    srcs = ",".join('"%s%s?v=%s"' % (root, s.lstrip("/"), digest(s)) for s in MOTION_SCRIPTS)
    return ('<script>(function(h){if(!h.classList.contains("motion"))return;'
            'function off(){h.classList.remove("motion")}'
            '[%s].forEach(function(s){var e=document.createElement("script");e.src=s;e.async=false;e.onerror=off;document.body.appendChild(e)});'
            'window.__motionTimer=setTimeout(function(){if(!window.__motionReady)off()},4000)})(document.documentElement)</script>\n' % srcs)


# -------------------------------------------------------------------- shell
def moved(to):
    """A stub for an old URL: says where the page went and sends the visitor on."""
    return dict(nav=None, motion=False, title="Moved | %s" % SITE, desc="This page has moved.",
                head='<meta http-equiv="refresh" content="0; url=%s">' % to + chr(10),
                eyebrow="Moved", h1="This page has a new address.",
                standfirst='It is now at <a href="%s">%s</a>. You will be taken there in a moment.' % (to, to),
                actions=[("Go there now", to)], body="")


def shell(page, path="index.html"):
    """Wrap one page's body in the site chrome."""
    root = URL_ROOT
    url = BASE + (path[:-len("index.html")] if path.endswith("index.html") else path)
    current = page.get("nav")
    items = []
    for i, (head, intro, pages) in enumerate(NAV, 1):
        here = any(label == current for label, _, _ in pages)
        links = "".join(
            '\n          <li><a href="%s"%s><b>%s</b><span>%s</span></a></li>'
            % (href, ' aria-current="page"' if label == current else "", label, summary)
            for label, href, summary in pages)
        items.append(
            '        <li class="menu-item%s">\n'
            '          <button type="button" class="menu-head" aria-expanded="false" aria-controls="menu-%d">%s</button>\n'
            '          <div class="menu-panel" id="menu-%d"><p class="menu-intro">%s</p><ul>%s\n          </ul></div>\n'
            '        </li>' % (" is-section" if here else "", i, head, i, intro, links))
    nav = "\n".join(items)

    foot = "\n".join(
        '      <div>\n        <h3>%s</h3>\n        <ul>%s</ul>\n      </div>'
        % (head, "".join('\n          <li><a href="%s">%s</a></li>' % (href, label)
                         for label, href, _ in pages) + "\n        ")
        for head, _, pages in NAV)

    hero, hero_class, hero_steps = "", "hero-plain", ""
    if page.get("hero_img"):
        # The hero photograph is the page's LCP element and spans the viewport,
        # so it gets the same two widths and real descriptors the body images
        # get; a phone that took the 1600-wide file here was most of the
        # PACK EXPO landing's budget.
        big = page["hero_img"]
        small = big.replace("-1600.webp", "-800.webp")
        w, h = webp_size(os.path.join(IMG, big))
        sw = webp_size(os.path.join(IMG, small))[0]
        hero_class = "hero-photo"
        hero = ('  <img class="hero-bg" src="%(r)sassets/img/%(big)s" '
                'srcset="%(r)sassets/img/%(small)s %(sw)dw, %(r)sassets/img/%(big)s %(w)dw" sizes="100vw" '
                'alt="%(alt)s" width="%(w)d" height="%(h)d" fetchpriority="high" decoding="async">\n'
                % dict(r=root, big=big, small=small, sw=sw, w=w, h=h,
                       alt=html_attr(page["hero_alt"])))

    if page.get("hero_art"):
        # Catalog pages: a product cut out onto transparency, over a faint engineering grid.
        aw, ah = webp_size(os.path.join(IMG, page["hero_art"]))
        hero_class = "hero-plain hero-catalog"
        hero = ('  <div class="hero-lines" aria-hidden="true"></div>\n'
                '  <img class="hero-art" src="%sassets/img/%s" alt="" width="%d" height="%d" decoding="async">\n'
                % (root, page["hero_art"], aw, ah))

    preload = ""
    if page.get("hero_video"):
        v = page["hero_video"]
        poster = "%sassets/video/%s-poster.webp" % (root, v["name"])
        w, h = webp_size(os.path.join(ROOT, "assets", "video", "%s-poster.webp" % v["name"]))
        # The hero pins, and its headline gives way to the steps, only when a page
        # supplies hero_steps. The homepage no longer does: three screens of scroll
        # before the page began was too much, and the body makes the same points.
        hero_class = "hero-cinema\" data-pin data-pin-length=\"2" if page.get("hero_steps") else "hero-cinema"
        preload = '<link rel="preload" as="image" href="%s">\n' % poster
        # MP4 first: the browser takes the first source it can play, and the
        # H.264 cut is 1704 KB against the VP9 cut's 2422 KB. Everything that
        # plays the WebM plays the MP4 too.
        # No parallax on this layer: a playing video is the most expensive thing
        # on the site to move, so it scrolls with the page and no more.
        hero = ('  <div class="hero-media">\n'
                '    <img class="hero-bg" src="%(p)s" alt="%(alt)s" width="%(w)d" height="%(h)d" fetchpriority="high" decoding="async">\n'
                '    <video class="hero-video" muted loop playsinline preload="none" poster="%(p)s" aria-hidden="true" tabindex="-1">\n'
                '      <source src="%(r)sassets/video/%(n)s.mp4" type="video/mp4">\n'
                '      <source src="%(r)sassets/video/%(n)s.webm" type="video/webm">\n'
                '    </video>\n  </div>\n  <div class="hero-dim" data-dim aria-hidden="true"></div>\n'
                % dict(p=poster, alt=html_attr(v["alt"]), w=w, h=h, r=root, n=v["name"]))
        if page.get("hero_steps"):
            hero_steps = "".join(
                '    <div class="hero-step" data-step><div class="eyebrow">%s</div><h2>%s</h2><p>%s</p></div>\n' % s
                for s in page["hero_steps"])

    actions = ""
    if page.get("actions"):
        actions = '\n    <div class="hero-actions">%s</div>' % "".join(
            '\n      <a class="btn%s" href="%s">%s</a>' % (
                " btn-solid" if i == 0 else "", h, t)
            for i, (t, h) in enumerate(page["actions"])) + "\n    "

    contact = ""
    if PHONE:
        contact += '<br><a href="tel:%s">%s</a>' % (re.sub(r"[^\d+]", "", PHONE), PHONE)
    if CONTACT_EMAIL:
        contact += '<br><a href="mailto:%s">%s</a>' % (CONTACT_EMAIL, CONTACT_EMAIL)
    contact += '<br><a href="%s">Send Russ a message</a>' % CTA[1]

    hold_attr = " data-hold" if page.get("hero_video") and page.get("hero_steps") else ""

    return version_assets("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
%(robots)s<link rel="icon" href="%(root)sassets/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="%(root)sassets/icon-180.png">
<meta name="theme-color" content="#1F1A17">
%(preload)s<meta property="og:type" content="website">
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
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600;700&family=Inter:wght@400;500;600&display=swap">
<link rel="stylesheet" href="%(root)sassets/site.css">
<link rel="stylesheet" href="%(root)sassets/forms.css">
<link rel="stylesheet" href="%(root)sassets/motion.css?v=%(motion_css_v)s">
%(head)s<script>document.documentElement.classList.add("js");window.FORM_ENDPOINT=%(endpoint)s;window.CONTACT_EMAIL=%(email)s;window.CONTACT_PHONE=%(phone)s;if(/[?&]notes\\b/.test(location.search))document.documentElement.classList.add("notes");%(gate)s</script>
</head>
<body>

<a class="skip" href="#main">Skip to content</a>

<header class="site-head">
  <div class="inner">
    <a class="wordmark" href="%(root)s">%(logo)s<span class="vh">%(site)s</span></a>
    <button type="button" class="nav-toggle" aria-expanded="false" aria-controls="site-nav"><span class="nav-bars" aria-hidden="true"><i></i><i></i></span><span class="nav-word">Menu</span></button>
    <nav class="site-nav" id="site-nav" aria-label="Primary">
      <ul class="menu">
%(nav)s
      </ul>
    </nav>
    <a class="btn btn-solid" href="%(cta_href)s">%(cta_text)s</a>
  </div>%(progress)s
</header>

<header class="hero %(hero_class)s">
%(hero)s%(hero_body)s%(hero_steps)s</header>

<main id="main">
%(body)s
</main>

<footer class="site-foot">
  <div class="inner">
%(foot)s
    <div>
      <h3>Contact</h3>
      <address class="addr">%(address)s%(contact)s</address>
    </div>
  </div>
  <div class="colophon">
    <span>&copy; %(site)s, Inc. Prototype by SparkMedia.</span>
    <a class="notes-on" href="?notes">Show working notes</a>
    <a class="notes-off" href="?">Hide working notes</a>
  </div>
</footer>
%(cta_bar)s%(foot_js)s
<script src="%(root)sassets/nav.js" defer></script>
<script src="%(root)sassets/forms.js" defer></script>
<script src="%(root)sassets/wizard.js" defer></script>
%(loader)s</body>
</html>
""" % {
        "title": page["title"], "desc": html_attr(page["desc"]), "root": root,
        "url": url, "base": BASE, "og_alt": html_attr(OG_ALT),
        "endpoint": json_str(FORM_ENDPOINT), "email": json_str(CONTACT_EMAIL), "phone": json_str(PHONE),
        "robots": "" if BASE == PRODUCTION else
                  '<meta name="robots" content="noindex,nofollow">' + chr(10),
        "site": SITE, "logo": LOGO, "nav": nav,
        "cta_href": CTA[1], "cta_text": CTA[0],
        "cta_bar": "" if path.startswith("talk-to-russ/") else
                   '<div class="cta-bar"><a class="btn btn-solid" href="%s">%s</a></div>\n' % (CTA[1], CTA[0]),
        "hero": hero, "hero_class": hero_class,
        "hero_body": "" if page.get("hero_text") is False else
                     '  <div class="hero-body"%s>\n    <div class="eyebrow">%s</div>\n    <h1>%s</h1>\n'
                     '    <p>%s</p>%s\n  </div>\n' % (hold_attr, page["eyebrow"], page["h1"], page["standfirst"], actions),
        "hero_steps": ('  <div class="hero-steps">\n%s  </div>\n' % hero_steps) if hero_steps else "",
        "preload": preload,
        "body": expand(page["body"]), "foot": foot, "address": ADDRESS, "contact": contact,
        "head": page.get("head", ""), "foot_js": page.get("foot_js", ""),
        "gate": "" if page.get("motion") is False else
                'if(matchMedia("(prefers-reduced-motion: no-preference)").matches)document.documentElement.classList.add("motion")',
        "loader": "" if page.get("motion") is False else motion_loader(root),
        "motion_css_v": digest("/assets/motion.css"),
        "progress": "" if page.get("motion") is False else '\n  <div class="scroll-progress" aria-hidden="true"></div>',
    })


# The header logo: Dave's high-resolution rendering, as a WebP with the grey
# wordmark recoloured for the ink header by _tools/logo_raster.py. The SVG
# mark remains the favicon and touch icon.
LOGO = '<img class="logo" src="%sassets/logo-header.webp" width="%d" height="%d" alt="" decoding="async">' % (
    (URL_ROOT,) + webp_size(os.path.join(ROOT, "assets", "logo-header.webp")))


# ---------------------------------------------------------------- the pages
PAGES = {}

# The ideal customer, as the 8 Sep session distilled it from Russell's own
# PACK EXPO hit list: every one of the 18 was US-built, made repeatable
# machine models, priced them in the tens of thousands, shipped real volume,
# and had electrical engineers on staff.
FIT = [
    ("You build machines in the United States.",
     "Repeatable models, not one-offs. The kind of machine that ships in the hundreds a year."),
    ("Your machines sell for $10,000 to $100,000.",
     "Big enough to need real controls. Small enough that a $1,000 operator panel is a problem."),
    ("You have engineers on staff.",
     "We work alongside your controls or electrical engineer. We are not a substitute for one."),
    ("You need more than a part number.",
     "A cost target to hit, a panel that carries your name, an application that has to work first time."),
]
NOT_FIT = [
    "You need one unit, today, off a shelf. A catalog distributor will serve you better.",
    "You have no engineering in house and expect a supplier to carry the whole application.",
    "You are building million-dollar machines on European control platforms. That is not our lane.",
]

PAGES["index.html"] = dict(
    nav=None, title="%s | %s" % (SITE, TAGLINE),
    desc=TAGLINE + " HMI, PLC, I/O and custom operator panels for OEM machine builders, with an engineer on the application from day one.",
    eyebrow="Controls and operator panels for OEM machine builders",
    h1=TAGLINE,
    standfirst="HMIs, PLCs, I/O and custom operator panels for machines built in the United States. "
               "Specified, cost-engineered and supported by an engineer who has done it for twenty years, "
               "not pulled from a catalog and shipped with a wish.",
    actions=[("Talk to Russ", "/talk-to-russ/"), ("Meet us at PACK EXPO", "/pack-expo/")],
    hero_video=dict(name="hero", alt="A multi-station automation machine on the shop floor, pneumatic slides and valve manifolds on a blue frame"),
    body=note("Positioning per the 8 Sep session and the SOW: Phoenix is the solution, Russell is the "
              "value, the supplier stays in the background. Every claim here is drawn from the two "
              "transcripts; Russell signs off technical claims before launch.") + """
<section class="band doors">
  <div class="inner">
    <div class="split" data-reveal="stagger">
      <a class="door" href="/machine-builders/design-win/">
        <div class="eyebrow">Machine builders</div>
        <h2>You build a machine and want controls designed for it.</h2>
        <p>Custom panels built to your print, one approved part across your lineup, an engineer on the first application. Start here.</p>
      </a>
      <a class="door" href="/products/hmis/">
        <div class="eyebrow">Products</div>
        <h2>You know the part you need.</h2>
        <p>HMIs, PLCs, I/O and communication modules, cross-references and datasheets, with stock held in Mokena.</p>
      </a>
    </div>
  </div>
</section>

<section class="band">
  <div class="inner narrow" data-reveal>
    <div class="eyebrow">What Phoenix is</div>
    <h2>A controls engineer on your side of the table.</h2>
    <p>Most suppliers sell you a part and hope it works. Phoenix starts with the machine: what it does,
    how many you build, what the controls cost you today and what they need to cost. Then we engineer to
    that target, through a direct factory relationship that treats your volume as an opportunity rather
    than a line item.</p>
    <p>Russell Homans has supplied and supported OEM controls for over twenty years. Your first
    application gets his hours until it ships. That is the whole difference.</p>
  </div>
</section>

<section class="band band-tint">
  <div class="inner">
    <div class="eyebrow">Three things a catalog cannot do</div>
    <div class="split wide-left">
      %(cards)s
      %(panel)s
    </div>
  </div>
</section>

<section class="band">
  <div class="inner">
    <div class="split">
      <div data-reveal>
        <div class="eyebrow">Proof</div>
        <h2>One customer, twenty years. Same engineer.</h2>
        <p>A residential elevator manufacturer has run on Phoenix-supplied controls for close to two decades,
        through every revision of their cab. The current project is an all-glass cab operating panel with an
        integrated phone.</p>
        <p class="stat"><span class="num" data-count="1000" data-count-prefix="$">$1,000</span> <span class="lbl">revision one, per unit</span></p>
        <p class="stat"><span class="num" data-count="350" data-count-prefix="$">$350</span> <span class="lbl">revision two, per unit, at <span data-count="2500" data-count-suffix=" units">2,500 units</span></span></p>
        <p>Because Phoenix took the number back to the factory instead of apologising for the catalog price.</p>
        <p class="muted">Commercial kitchen equipment, screen-printing presses, industrial slicers, municipal
        water plants and gutter machines run the same way. <a href="/machine-builders/industries/">See the industries.</a></p>
      </div>
      %(cost)s
    </div>
  </div>
</section>

<section class="band band-dark">
  <div class="inner">
    <div class="split">
      <div>
        <div class="eyebrow">Who this is for</div>
        <h2>A good fit looks like this.</h2>
        <ul class="ticks" data-reveal="stagger">%(fit)s</ul>
      </div>
      <div>
        <div class="eyebrow">And who it is not for</div>
        <h2>We would rather say so now.</h2>
        <ul class="crosses" data-reveal="stagger">%(notfit)s</ul>
      </div>
    </div>
  </div>
</section>

<section class="band">
  <div class="inner narrow" data-reveal>
    <div class="eyebrow">How it starts</div>
    %(steps)s
    <p class="center"><a class="btn btn-solid" href="/talk-to-russ/">Talk to Russ</a></p>
  </div>
</section>
""" % dict(
        cards=cards([
            ("Engineering before the order",
             "Application review, control architecture, network layout, sample code you can paste into your "
             "program. Pre-sale, at no charge, because the first application has to work."),
            ("Built to your target",
             "Your logo on the bezel. Your mounting. Your price point at your quantity. Customisation the big "
             "brands will not discuss below a seven-figure order."),
            ("A factory that answers the phone",
             "A million-dollar opportunity does not register with the largest control vendors. At our factory "
             "partner it gets engineers on a plane."),
        ], "one"),
        panel=figure("panel-front.svg", "A panel engineered to your target, with your name on the bezel.", "art-tall"),
        cost=figure("cost-figure.svg", "Revision one against revision two, at production quantity."),
        fit="".join("<li><b>%s</b> %s</li>" % f for f in FIT),
        notfit="".join("<li>%s</li>" % n for n in NOT_FIT),
        steps=steps([
            ("Tell us about the machine", "Four questions: what it does, how many a year, what controls it runs now, what you need. Two minutes."),
            ("Review it with Russell", "If it fits, you talk to the engineer, not a sales desk. If it does not, we say so and point you somewhere useful."),
            ("Ship the first application", "Phoenix stays on it, a few hours a week, until your first unit is running on the floor."),
        ]),
    ),
)

PAGES["machine-builders/design-win/index.html"] = dict(
    nav="How a Design Win Works", title="How a design win works | %s" % SITE,
    desc="How Phoenix works with OEM machine builders: application review, cost engineering, custom operator panels and first-application support.",
    eyebrow="For OEM machine builders",
    h1="One approved part, across your whole lineup.",
    standfirst="A builder with six machine models specs the part once and uses it in all six. That is why a "
               "single win is worth years of orders, and why the sale takes months rather than weeks. Here is "
               "what the months look like.",
    actions=[("Talk to Russ", "/talk-to-russ/")],
    body=note("The 'part-time employee for my customer' line is Russell's own (8 Sep, 16:37). "
              "The three-to-eight-hours-a-week figure and the taper after three to six months are his too.") + """
%(path)s

<section class="band band-tint">
  <div class="inner">
    <div class="eyebrow">What we supply</div>
    %(cards)s
    <p class="center"><a class="btn" href="/machine-builders/custom-controls/">Custom controls, built to your print</a></p>
  </div>
</section>

<section class="band">
  <div class="inner narrow">
    <div class="eyebrow">Straight answers</div>
    <h2>Questions OEM engineers ask first</h2>
    <dl class="faq" data-reveal="stagger">
      <dt>Is this a distributor?</dt>
      <dd>Phoenix supplies hardware, yes. The reason customers stay for twenty years is the engineering
      around it. If you only need a box moved, there are cheaper ways to move a box.</dd>
      <dt>What is the learning curve on the platform?</dt>
      <dd>Real, and we say so. That is why the first application gets an engineer. It is also why we
      prefer customers with engineers on staff: once the platform is learned, it is yours.</dd>
      <dt>What quantities make customisation worthwhile?</dt>
      <dd>It depends on the part, but as a guide, a custom operator panel becomes economical in the low
      thousands a year. Under that, we will tell you to use the standard part and put the money elsewhere.</dd>
      <dt>Where is it made?</dt>
      <dd>Phoenix works with a long-standing factory partner overseas and holds stock in Illinois.
      Russell has stood on that factory floor; ask him about it.</dd>
    </dl>
  </div>
</section>
""" % dict(
        path=pinned([
            ("Step one", "Send the machine, not a part number.",
             "Phoenix looks at the function, the environment, the quantity and the cost target, and comes back with a control architecture and a price at your volume.", "#g-hmi"),
            ("Step two", "A controller sized to the machine.",
             "If the software needs a routine written, Russell writes it and you paste it in. If the hardware needs a custom mount or a branded bezel, the factory quotes it. None of this is billed.", "#g-plc"),
            ("Step three", "I/O, drives and the first application.",
             "The first machine on a new platform is where a supplier is either a partner or a problem. Phoenix commits three to eight engineering hours a week until the first unit is running. After the first three to six months that tapers, because it has to, and by then your team owns the platform.", "#g-io"),
            ("Step four", "Then, production.",
             "Repeatable models mean repeatable orders. Phoenix holds stock, reboxes and ships from Illinois, and keeps the factory relationship warm so the next revision costs less than the last one. When a distributor makes sense for inventory, we will say so. When it does not, we will say that too.", "#g-net"),
        ], "topology.svg"),
        cards=cards([
            ("HMI and touchscreens", "Operator interfaces from small panel displays to full-glass fronts, branded to your machine."),
            ("PLC and controllers", "Controllers sized to the machine, with application code support from Phoenix."),
            ("I/O and networking", "Remote I/O, fieldbus and the network layout to make it all talk."),
            ("Custom operator panels", "Cab operating panels, hall stations, glass fronts with integrated phone, at production cost."),
        ], "two"),
    ),
)

PAGES["machine-builders/custom-controls/index.html"] = dict(
    nav="Custom Controls", title="Custom controls, built to your print | %s" % SITE,
    desc="HMI, PLC, I/O, custom operator panels, application programming, cost engineering and sourcing for OEM machine builders.",
    eyebrow="Custom controls",
    h1="Built to your print, not pulled from a shelf.",
    standfirst="Every capability below has shipped on a production machine. Nothing here is aspirational.",
    body=note("Product families are kept generic on purpose: no supplier names, per the positioning "
              "decision. Add photographs from the Drive folder (glass operator panels, hall stations, "
              "control panel, remote I/O, robot cell, soil sampling rig) as hero_img and inline images.") + """
<section class="band">
  <div class="inner narrow" data-reveal>
    <div class="eyebrow">What can be built to your print</div>
    <ul class="ticks" data-reveal="stagger">
      <li><b>Your logo on the bezel.</b> Printed or moulded, at production quantity, not as a one-off favour.</li>
      <li><b>Panel cutout to your dimensions.</b> The opening you already have, so a replacement drops in.</li>
      <li><b>Your mounting pattern.</b> Hole spacing and fixings to match the machine, not the catalog.</li>
      <li><b>The I/O count you need.</b> Discrete and analog points sized to the machine, with Ethernet, serial or Modbus as the application asks.</li>
      <li><b>One part number for the lineup.</b> Approved once, carried across every model that shares the panel.</li>
    </ul>
  </div>
</section>
<section class="band band-tint">
  <div class="inner">
    <div class="eyebrow">Hardware</div>
    %(hw)s
  </div>
</section>
<section class="band">
  <div class="inner">
    <div class="eyebrow">Engineering</div>
    %(eng)s
  </div>
</section>
""" % dict(
        hw=cards([
            ("HMI and touchscreen interfaces", "Panel-mount displays for temperature, recipe and machine control. Branded bezels, custom mounting.", "hall-station-screen", "Hall station screen showing car position"),
            ("PLCs and machine controllers", "Sized to the machine. Application support included, so the software learning curve is ours before it is yours.", "control-panel", "Control panel with PLC, I/O and wiring, built for an OEM machine"),
            ("I/O, drives and networking", "Remote I/O, fieldbus, sensor integration, barcode verification and the network layout that ties it together.", "factory-automation-remote-i-o", "Remote I/O modules wired into a factory automation enclosure"),
            ("Custom operator panels", "All-glass cab operating panels, hall stations and fixtures engineered to a cost target at production quantity.", "elevator-hall-station", "Elevator hall station with call display"),
        ], "two"),
        eng=cards([
            ("Application review", "The machine, the environment, the volume, the target. A control architecture and a price at your quantity, before any order."),
            ("Application programming", "Routines, recipes, comms and conversions written by Phoenix and handed over as code your engineer can paste and own."),
            ("Cost engineering", "Taking a $1,000 panel to $350 at 2,500 units is not discounting. It is redesign, at the factory, with your target on the drawing."),
            ("Sourcing and standardisation", "One platform across your model range, stocked and reboxed in Illinois, so the next revision costs less than the last."),
        ], "two"),
    ),
)

PAGES["machine-builders/industries/index.html"] = dict(
    nav="Industries", title="Industries | %s" % SITE,
    desc="Packaging, residential elevators, commercial kitchen equipment, printing, food processing, water treatment, building products, agriculture and medical equipment: where Phoenix controls run today.",
    eyebrow="Industries",
    h1="Different machines. The same problem underneath.",
    standfirst="A screen, a controller, some I/O, and an engineer who has to make them work at a price. "
               "These are the industries where Phoenix does that today.",
    body=note("Every industry listed is one Russell named on the calls or one the Drive photographs "
              "show (water and wastewater plants, knee rehabilitation machine, pad printing, t-shirt "
              "print curing). Packaging leads because PACK EXPO is the reason this site exists on "
              "28 September. Elevators are the twenty-year account.") + """
<section class="band">
  <div class="inner">
    <div class="eyebrow">Where Phoenix leads</div>
    %(lead)s
  </div>
</section>
<section class="band band-tint">
  <div class="inner">
    <div class="eyebrow">Every industry Phoenix controls run in today</div>
    %(cards)s
    <div class="eyebrow more-eyebrow">And on these machines too</div>
    %(more)s
  </div>
</section>
<section class="band">
  <div class="inner narrow center" data-reveal>
    <h2>Building something else?</h2>
    <p>If it is a repeatable machine with a screen and a controller on it, the conversation is the same.</p>
    <p><a class="btn btn-solid" href="/talk-to-russ/">Talk to Russ</a></p>
  </div>
</section>
""" % dict(lead=linked_cards([
        ("Packaging", "/machine-builders/industries/packaging/", "Die cutters, labellers, case erectors and fillers, with the operator interface and verification built in.", "barcode-verification", "Barcode verification station on a packaging line"),
        ("Residential elevators", "/machine-builders/industries/residential-elevators/", "Twenty years on one account: cab operating panels, hall stations, and the cost engineering behind revision two.", "elevator-hall-station", "Elevator hall station with call display"),
        ("Food equipment", "/machine-builders/industries/food-equipment/", "Ovens, mixers and slicers, with the temperature and recipe interfaces that set them.", "product-hmi-plc", "An HMI/PLC unit running a clean-in-place screen for a food process"),
    ]), cards=cards([
        ("Packaging machinery", "Die cutters with barcode verification, labellers, case erectors, fillers. The $10,000 to $100,000 machines still built in the States.", "barcode-verification", "Barcode verification station on a packaging line"),
        ("Residential elevators", "Twenty years on the same account. Glass cab operating panels, hall stations, and the cost engineering that made revision two possible.", "elevator-hall-station", "Elevator hall station with call display"),
        ("Printing and finishing", "Screen-printing presses, pad printers and print-curing lines with operator control at the press.", "pad-printing-machine", "Pad printing machine with touchscreen operator control"),
        ("Water and wastewater", "Municipal treatment plants: load balancing, remote I/O and operator screens that run for decades.", "waste-water-plant", "Exterior of a municipal waste water treatment plant, with aeration basins and the operations building"),
        ("Agriculture and field equipment", "Hydraulic soil-sampling rigs with carousel control and logging.", "soil-sampling-rig", "Hydraulic soil-sampling rig with carousel control"),
    ], "mosaic"), more=cards([
        ("Commercial kitchen equipment", "Ovens and mixers, and the temperature and recipe interfaces that set them."),
        ("Food processing", "Industrial slicers and portioning equipment with washdown-rated interfaces."),
        ("Building products machinery", "Seamless gutter machines and roll-forming lines that run from a truck."),
        ("Medical and rehabilitation equipment", "Controls and operator interfaces for therapy and rehabilitation machines."),
    ], "two")),
)

PAGES["company/about-russ/index.html"] = dict(
    nav="About Russ", title="About Russ Homans | %s" % SITE,
    desc="Phoenix Automation Solutions is owned and run by Russell Homans, a controls engineer with over twenty years supplying OEM machine builders.",
    eyebrow="About",
    h1="An engineer who owns the company.",
    standfirst="Phoenix Automation Solutions, Inc. is run by Russell Homans from Mokena, Illinois, "
               "southwest of Chicago.",
    body=note("Needs: Russell's bio and credentials list (he offered one, 28 Aug 54:14), a photograph, "
              "the years-in-business figure, and whether the bench of contract engineers is public. "
              "Everything below is drawn from the calls and wants his sign-off.") + """
<section class="band">
  <div class="inner">
    <div class="split">
      <div data-reveal>
        <h2>Russell Homans, owner and engineer</h2>
        <p class="stat"><span class="num" data-count="20" data-count-suffix="+">20+</span> <span class="lbl">years specifying, programming and supporting OEM controls</span></p>
        <p>Russell has specified, programmed and supported controls for OEM machine builders for more than
        two decades, and has owned Phoenix outright since the start of 2026. He writes application code,
        lays out networks, walks a customer's engineer through a platform's known problems before they hit
        them, and takes cost targets back to the factory personally. He has stood on that factory's floor.</p>
        <p>When a project needs more hands than one, Phoenix draws on a bench of contract controls engineers
        who have worked with Russell for years. Too much work is not a problem Phoenix turns away.</p>
      </div>
      <figure class="portrait" data-reveal>
        <div class="portrait-frame" aria-hidden="true"><img src="/assets/mark.webp" alt="" width="220" height="330" loading="lazy" decoding="async"></div>
        <figcaption>Photograph to come.</figcaption>
      </figure>
    </div>
  </div>
</section>
<section class="band band-tint">
  <div class="inner narrow">
    <div class="eyebrow">Proof points</div>
    <ol class="timeline" data-reveal="stagger">
      <li><b>Twenty years, one account.</b> A residential elevator manufacturer has run on Phoenix-supplied controls through every revision of their cab.</li>
      <li><b>$1,000 to $350.</b> A glass cab operating panel re-engineered at the factory to the customer's target, at 2,500 units.</li>
      <li><b>Nine industries.</b> Packaging, elevators, kitchens, printing, food, water, building products, agriculture, medical. <a href="/machine-builders/industries/">See them.</a></li>
      <li><b>Owner since 2026.</b> Phoenix Automation Solutions, Inc., Mokena, Illinois.</li>
    </ol>
  </div>
</section>
<section class="band">
  <div class="inner narrow" data-reveal>
    <h2>What Phoenix is becoming</h2>
    <p>For most of its history Phoenix supplied one control platform to a handful of loyal customers.
    That platform is not going anywhere. What is changing is breadth: additional product lines are
    shipping to Illinois now, so that one engineering relationship can cover more of your machine.</p>

    <h2>Credentials</h2>
    <p class="muted">Certifications and credentials to be listed here.</p>
  </div>
</section>
""",
)

PAGES["pack-expo/index.html"] = dict(
    nav=None, motion=False, title="Meet Phoenix at PACK EXPO 2026 | %s" % SITE,
    desc="Phoenix Automation Solutions at PACK EXPO International, McCormick Place, September 28 to October 1, 2026.",
    hero_img="barcode-verification-1600.webp", hero_alt="Barcode verification station on a packaging line",
    eyebrow="%(name)s &middot; %(place)s" % SHOW,
    h1="Bring us the machine you wish cost less to control.",
    standfirst="%(dates)s. Russell Homans is on the floor all four days." % SHOW,
    actions=[("Talk to Russ", "/talk-to-russ/"), ("What Phoenix does", "/machine-builders/design-win/")],
    body=note("This is the QR-code landing. Keep it to one screen of reading. The show is research "
              "for Phoenix as much as sales: the intake form is the instrument.") + """
<section class="band">
  <div class="inner narrow">
    <h2>What to bring to the conversation</h2>
    <ul class="ticks">
      <li>What the machine does and roughly how many you build a year</li>
      <li>What controls are on it now, and what they cost you</li>
      <li>The one thing about the current operator interface you would change</li>
    </ul>
    <p>That is enough for Russell to tell you, on the spot, whether Phoenix can engineer to your
    target. If it cannot, you will hear that on the spot too.</p>
    <p><a class="btn btn-solid" href="/talk-to-russ/">Or answer three questions now</a></p>
  </div>
</section>
<section class="band band-tint">
  <div class="inner narrow center">
    <div class="eyebrow">After the show</div>
    <p>Every conversation from the floor gets a written follow-up within two business days, from
    Russell, with the numbers you asked for.</p>
  </div>
</section>
""",
)

# Qualification, per the SOW: company and contact, machine type, annual
# production volume, current control platform, application requirement. The
# option strings are the ones forms.js allows; change both together.
CONTROLS = ["Allen-Bradley / Rockwell", "Siemens", "Omron", "Automation Direct", "Maple Systems",
            "Relay logic / no PLC", "Other", "Not sure"]
VOLUMES = ["Under 50", "50 to 250", "250 to 1,000", "1,000 to 5,000", "Over 5,000"]

PAGES["talk-to-russ/index.html"] = dict(
    nav=None, title="Talk to Russ | %s" % SITE,
    desc="Four questions about your machine. Russell reviews every submission personally.",
    eyebrow="Talk to Russ",
    h1="Three questions about the machine.",
    standfirst="What you build, how many a year, what controls are on it now. Then how to reach you. "
               "Russ reads every one and replies within two business days, with a straight answer either way.",
    body=note("Posts to FORM_ENDPOINT in _build/build.py; empty until Phoenix's GoHighLevel "
              "sub-account exists. Field names and option strings must match the CRM exactly; "
              "see assets/forms.js. Qualification thresholds are to be agreed with Russell.") + """
<section class="band">
  <div class="inner narrow">
    <form class="inquiry" method="post" action="#" novalidate>
      <fieldset data-wizard-step>
        <legend>1. The machine</legend>
        <label>What does the machine do? <input name="machine_type" placeholder="e.g. rotary die cutter with barcode verification" required></label>
      </fieldset>
      <fieldset data-wizard-step>
        <legend>2. Volume and controls</legend>
        <div class="row two">
          <label>How many do you build a year?
            <select name="annual_volume" required>
              <option value="">Choose one</option>%(volumes)s
            </select>
          </label>
          <label>What controls are on it now?
            <select name="current_controls" required>
              <option value="">Choose one</option>%(controls)s
            </select>
          </label>
        </div>
      </fieldset>
      <fieldset data-wizard-step>
        <legend>3. What you need (optional)</legend>
        <label>What do you need? <textarea name="application" rows="4" placeholder="A cost target, a custom panel, a platform change, an application that has to work first time..."></textarea></label>
        <label>Link to a spec, drawing or photo (optional) <input type="url" name="spec_link" placeholder="https://"></label>
      </fieldset>
      <fieldset data-wizard-step>
        <legend>4. You</legend>
        <div class="row two">
          <label>Company <input name="company" autocomplete="organization" required></label>
          <label>Your role <input name="role" autocomplete="organization-title" placeholder="Controls engineer, VP Engineering..."></label>
        </div>
        <div class="row two">
          <label>First name <input name="first_name" autocomplete="given-name" required></label>
          <label>Last name <input name="last_name" autocomplete="family-name" required></label>
        </div>
        <div class="row two">
          <label>Work email <input type="email" name="email" autocomplete="email" required></label>
          <label>Phone <input type="tel" name="phone" autocomplete="tel"></label>
        </div>
      </fieldset>
      <!-- Honeypot. Humans never see it; scrapers fill it. Do not remove. -->
      <label class="hp" aria-hidden="true">Website <input name="website" tabindex="-1" autocomplete="off"></label>
      <p class="form-actions"><button class="btn btn-solid" type="submit">Send for review</button></p>
      <p class="form-status" role="status" aria-live="polite"></p>
    </form>
  </div>
</section>
<section class="band band-tint">
  <div class="inner narrow">
    <div class="eyebrow">What happens next</div>
    %(next)s
  </div>
</section>
""" % dict(next=steps([
        ("Russ reads it himself", "Every submission goes to the engineer who would do the work, not to a sales desk."),
        ("A straight answer within two business days", "If the machine fits, you get a time to talk. If it does not, he says so and points you somewhere useful."),
        ("A call about the machine", "The machine, the volume, the controls on it now and the cost target. You leave the call knowing whether Phoenix can engineer to it."),
    ]), volumes="".join("<option>%s</option>" % v for v in VOLUMES),
           controls="".join("<option>%s</option>" % c for c in CONTROLS)),
)


# ---- Machine builders: the three industry pages
def industry(path, nav_title, title, h1, standfirst, machines, controls, note_text, hero=None, hero_alt=None, photos=()):
    body = note(note_text) + """
<section class="band">
  <div class="inner">
    <div class="split">
      <div data-reveal>
        <div class="eyebrow">Machines served</div>
        <ul class="ticks" data-reveal="stagger">%(machines)s</ul>
      </div>
      <div data-reveal>
        <div class="eyebrow">Controls on them</div>
        <ul class="ticks" data-reveal="stagger">%(controls)s</ul>
      </div>
    </div>
  </div>
</section>
%(photos)s<section class="band band-tint">
  <div class="inner narrow center" data-reveal>
    <h2>Building for this industry?</h2>
    <p>Three questions about the machine and Russ replies within two business days.</p>
    <p><a class="btn btn-solid" href="/talk-to-russ/">Talk to Russ</a></p>
  </div>
</section>
""" % dict(machines="".join("<li>%s</li>" % m for m in machines),
           controls="".join("<li>%s</li>" % c for c in controls),
           photos=('<section class="band">\n  <div class="inner">\n    <div class="eyebrow">Installed</div>\n    %s\n  </div>\n</section>\n'
                   % cards(photos, "two")) if photos else "")
    page = dict(nav="Industries", title="%s | %s" % (title, SITE), desc=standfirst, eyebrow=nav_title, h1=h1,
                standfirst=standfirst, actions=[("Talk to Russ", "/talk-to-russ/")], body=body)
    if hero:
        page.update(hero_img=hero, hero_alt=hero_alt)
    PAGES[path] = page


industry("machine-builders/industries/packaging/index.html", "Packaging",
         "Packaging machinery", "Controls for the packaging machines still built in the States.",
         "Die cutters, labellers, case erectors and fillers in the $10,000 to $100,000 range, built in repeatable models by OEMs with their own engineers.",
         ["Rotary and flatbed die cutters with barcode verification", "Labellers and print-and-apply stations", "Case erectors, sealers and fillers", "Conveying and accumulation between them"],
         ["Panel-mount touchscreen HMIs for recipe, count and fault display", "Compact PLCs sized to the machine, with application code support", "Remote I/O and barcode verification tied together over Ethernet or serial", "Operator panels branded to the machine builder"],
         "Packaging leads because PACK EXPO is the reason this site exists on 28 September. Machines listed are the kinds Russell named on the calls and the die cutter in the Drive footage; Russell to confirm the list.",
         hero="barcode-verification-1600.webp", hero_alt="Barcode verification station on a packaging line",
         photos=[("Barcode verification on the line", "A verification station reading every code before the product leaves the machine.", "barcode-verification", "Barcode verification station on a packaging line"),
                 ("Print curing", "Temperature control on a curing line, set from the operator interface.", "print-curing", "Print curing line with temperature control interface")])

industry("machine-builders/industries/residential-elevators/index.html", "Residential elevators",
         "Residential elevators", "Twenty years on one account, through every revision of the cab.",
         "Cab operating panels, hall stations and the controls behind them, for a manufacturer of residential elevators that has run on Phoenix-supplied parts for close to two decades.",
         ["Residential and home elevators, from single homes to thousand-unit developments", "Cab operating panels with integrated display and phone", "Hall stations with call display and car position", "Machine-room and controller interfaces"],
         ["All-glass cab operating panels engineered to a cost target at 2,500 units", "Hall station screens", "Discrete and analog I/O for car and hall signals", "Serial and Ethernet links to the elevator controller"],
         "The elevator customer is the twenty-year account (28 Aug call). Cab-panel photographs showing the customer's own splash screen are held back until Russell clears them; the hall station photographs are clean.",
         hero="elevator-hall-station-1600.webp", hero_alt="Elevator hall station with call display",
         photos=[("Hall station", "Call display and car position, at the landing.", "elevator-hall-station", "Elevator hall station with call display"),
                 ("Hall station screen", "The screen itself, showing car position and readiness.", "hall-station-screen", "Hall station screen showing car position")])

industry("machine-builders/industries/food-equipment/index.html", "Food equipment",
         "Food equipment", "Temperature, recipe and portion control for commercial food machines.",
         "Ovens, mixers and slicers for commercial kitchens and food processors, with the interfaces that set temperature, run recipes and control portions.",
         ["Commercial ovens and cooking lines", "Dough and ingredient mixers", "Industrial slicers and portioning equipment", "Washdown environments"],
         ["Touchscreen HMIs for temperature and recipe control", "PLCs and HMI/PLC combination units", "Analog I/O for temperature sensing and control", "Washdown-rated interfaces where the machine needs them"],
         "Commercial kitchen equipment, bakery mixers and industrial slicers are all from the 28 Aug call. No photographs exist yet; add them when Russell supplies installed examples.")


# ---- Products: the catalog side. Specifications are from the manufacturer's
# February 2025 documentation. The manufacturer and its family trademarks are
# never named (tests enforce it); part numbers are, because the catalog buyer
# arrives by searching for the one he already knows.
STOCK_BAND = """
<section class="band band-tint">
  <div class="inner narrow center" data-reveal>
    <div class="eyebrow">Stock and lead time</div>
    <h2>Ask for the position on any part number.</h2>
    <p>Stock is held in Mokena, Illinois. Send Russ the part number and the quantity and he will tell you
    what is on the shelf and the lead time on the rest, the same day.</p>
    <p><a class="btn btn-solid" href="/talk-to-russ/">Talk to Russ</a> &nbsp; <a class="btn" href="/products/datasheets/">Datasheets</a></p>
  </div>
</section>
"""
CATALOG_NOTE = ("Specifications are taken from the manufacturer's February 2025 brochure and current datasheets. "
                "Russell to confirm which part numbers he stocks in Mokena, and every approvals line, before launch. "
                "The manufacturer and its product-family trademarks are deliberately not named; part numbers are.")


# Each family's anchor, photograph and alt text, keyed by its eyebrow. The
# photographs are cut and retouched by _tools/product_images.py.
FAMILY_ART = {
    "Basic HMI": ("basic-hmi", "product-basic-hmi", "A 7 inch basic HMI, panel-mount, showing a gauge and a trend"),
    "Advanced HMI": ("advanced-hmi", "product-advanced-hmi", "Three advanced HMIs in 4.3, 7 and 10.1 inch sizes showing process screens"),
    "Rugged HMI": ("rugged-hmi", "product-rugged-hmi", "A rugged HMI with a metal housing and bonded glass, showing a production dashboard"),
    "Web panels": ("web-panels", "product-web-panel", "An HTML5 web panel in an industrial bezel"),
    "Eco PLC": ("eco-plc", "product-eco-plc", "A slim DIN-rail eco PLC with pluggable terminal blocks"),
    "Standard PLC": ("standard-plc", "product-standard-plc", "A DIN-rail standard PLC with an Ethernet port and pluggable terminal blocks"),
    "Expansion modules": ("expansion-modules", "product-plc-lineup", "Eco and standard PLCs side by side; the expansion modules snap onto the same rail beside them"),
    "HMI/PLC combination units": ("hmi-plc", "product-hmi-plc", "A 7 inch HMI/PLC combination unit with I/O modules plugged into the back"),
    "Field I/O, Modbus RTU": ("field-io", "product-field-io", "Two DIN-rail Modbus field I/O modules with an LED for every point"),
    "EtherCAT remote I/O": ("ethercat-io", "product-ethercat-io", "An EtherCAT remote I/O block with in and out ports and a 50 pin connector"),
}


def family(eyebrow, heading, intro, features, table, approvals, watch=None):
    anchor, image, alt = FAMILY_ART[eyebrow]
    shot = ""
    if image:
        shot = ('\n      <figure class="family-shot" data-reveal="right">{{img:%s|%s|class="family-img"}}</figure>'
                % (image, html_attr(alt)))
    return """
<section class="band family-band" id="%s" data-family="%s">
  <div class="inner">
    <div class="family-grid%s">
      <div class="family" data-reveal="left">
        <div class="eyebrow">%s</div>
        <h2>%s</h2>
        <p class="family-intro">%s</p>
        <ul class="ticks">%s</ul>
      </div>%s
    </div>
    %s
    <p class="approvals"><b>Approvals:</b> %s</p>%s
  </div>
</section>
""" % (anchor, eyebrow, "" if image else " no-shot", eyebrow, heading, intro,
       "".join("<li>%s</li>" % f for f in features), shot, table, approvals,
       ('\n    <div class="family-watch">%s</div>' % video(watch)) if watch else "")


def family_index(families):
    """The jump strip at the top of a catalog page: one tile per family, with its photograph."""
    tiles, pills = [], []
    for html in families:
        name = re.search(r'data-family="([^"]+)"', html).group(1)
        anchor, image, alt = FAMILY_ART[name]
        pic = ('<span class="tile-pic">{{img:%s|%s|class="tile-img"}}</span>' % (image, "")) if image else \
              '<span class="tile-pic tile-blank" aria-hidden="true"></span>'
        tiles.append('      <a class="tile" href="#%s">%s<span class="tile-name">%s</span></a>' % (anchor, pic, name))
        pills.append('<a href="#%s">%s</a>' % (anchor, name))
    return ('<nav class="family-pills" aria-label="Jump to a product family">%s</nav>\n' % "".join(pills) + '<section class="band family-index">\n  <div class="inner">\n    <nav class="tiles" aria-label="Product families" data-reveal="tiles">\n%s\n    </nav>\n  </div>\n</section>\n'
            % "\n".join(tiles))


def catalog_page(path, nav_label, title, h1, standfirst, families, art=None):
    PAGES[path] = dict(
        nav=nav_label, title="%s | %s" % (title, SITE), desc=standfirst, eyebrow="Products", h1=h1,
        standfirst=standfirst, hero_art=art,
        actions=[("Talk to Russ", "/talk-to-russ/"), ("Cross-reference a part", "/products/cross-reference/")],
        body=note(CATALOG_NOTE) + family_index(families) + "".join(families) + STOCK_BAND)


catalog_page(
    "products/hmis/index.html", "HMIs", "HMIs", "Touchscreens from 4.3 to 15 inch.",
    "Four families of panel-mount HMI: basic, advanced, rugged metal-housing, and HTML5 web panels. "
    "Every one is 24 VDC, IP66 at the front, and programmed in an IEC 61131-3 environment with free software.",
    [
        family("Basic HMI", "4.3 and 7 inch, for the machine that needs a screen and not a computer.",
               "Colour TFT with resistive touch. Trends, alarms, data logging, recipes and a built-in web server.",
               ["RS232 and RS485 serial; Ethernet on the TN models", "USB Type-C for programming, upload and download; one USB host",
                "IEC 61131-3 programming environment", "IP66 protection for front-panel mounting"],
               spec_table("Basic HMI part numbers", ["Part number", "Screen", "Serial", "Ethernet", "USB"], [
                   ["FP2043T-V2", "4.3 in TFT", "1 port (RS232 and RS485)", "No", "Type-C + host"],
                   ["FP2043TN-V2", "4.3 in TFT", "1 port (RS232 and RS485)", "Yes", "Type-C + host"],
                   ["FP2070T-V2", "7 in TFT", "2 ports (RS232/RS485)", "No", "Type-C + host"],
                   ["FP2070TN-V2", "7 in TFT", "2 ports (RS232/RS485)", "Yes", "Type-C + host"]]),
               "CE, UL Listed Class I Division 2, RoHS, IP66 front."),
        family("Advanced HMI", "4.3 to 15 inch, with the connectivity built in.",
               "For complex applications: VNC server, email, FTP host and client, MQTT and web server on the panel itself.",
               ["4 GB eMMC and 512 MB RAM; real-time clock; microSDHC slot", "10/100 Ethernet, RS232/RS485 serial, USB Type-C and USB host",
                "Trends, alarms, data logging and recipe management", "IEC 61131-3 programming environment; IP66 front"],
               spec_table("Advanced HMI part numbers", ["Part number", "Screen", "Serial", "Ethernet", "Storage"], [
                   ["FP4043TN", "4.3 in resistive", "1 x RS232/RS485", "1 x 10/100", "4 GB + microSDHC"],
                   ["FP4070TN", "7 in resistive", "2 x RS232/RS485", "1 x 10/100", "4 GB + microSDHC"],
                   ["FP4101TN", "10.1 in resistive", "2 x RS232/RS485", "1 x 10/100", "4 GB + microSDHC"],
                   ["FP4121TN", "12.1 in resistive", "2 x RS232/RS485", "1 x 10/100", "4 GB + microSDHC"],
                   ["FP4151TN-V2", "15 in resistive", "2 x RS232/RS485", "1 x 10/100", "4 GB + microSDHC"]]),
               "CE, UL Listed Class I Division 2, RoHS, IP66 front."),
        family("Rugged HMI", "Metal housing, bonded glass, readable in direct sun.",
               "Capacitive touch behind optically bonded glass at 1,000 nits, a quad-core Cortex-A53 at 1.4 GHz, "
               "and a PLC function built in. Made for outdoor and washdown-adjacent machines.",
               ["Operating temperature -20 to 70 &deg;C; IP66 front", "Two Ethernet ports, one of them gigabit; two RS232/RS485 serial ports",
                "FTP, HTTPS, MQTT and email; data logging to microSDHC", "Ladder, instruction list, structured text, SFC and function block diagram"],
               spec_table("Rugged HMI part numbers", ["Part number", "Screen", "Memory", "Ethernet", "USB"], [
                   ["FP6070CN-M", "7 in, 1024 x 600, PCAP", "8 GB eMMC, 1 GB RAM", "10/100 + 10/100/1000", "Type-C + 2 host"],
                   ["FP6101CN-M", "10.1 in, 1024 x 600, PCAP", "8 GB eMMC, 1 GB RAM", "10/100 + 10/100/1000", "Type-C + 2 host"],
                   ["FP6121CN-M", "12.1 in XGA, PCAP", "8 GB eMMC, 1 GB RAM", "10/100 + 10/100/1000", "Type-C + 2 host"],
                   ["FP6151CN-M", "15.1 in XGA, PCAP", "8 GB eMMC, 1 GB RAM", "10/100 + 10/100/1000", "Type-C + 2 host"],
                   ["FP7070CN-M", "7 in, 1024 x 600, capacitive", "4 GB flash, 1 GB RAM", "10/100 + 10/100/1000", "Type-C + 2 host"],
                   ["FP7101CN-M", "10.1 in, 1280 x 800, capacitive", "4 GB flash, 1 GB RAM", "10/100 + 10/100/1000", "Type-C + 2 host"]]),
               "FP7 metal-housing models: CE, UL Class I Division 2, IP66, RoHS, REACH. FP6 models: IP66 front; ask for the current listing."),
        family("Web panels", "An HTML5 browser in an industrial bezel.",
               "Thin clients for machines whose interface is already a web application. Point the panel at any web server and it runs.",
               ["4.3, 7 and 10.1 inch", "Chromium-based HTML5 browser on the Plus and capacitive models; a microbrowser on the Lite",
                "Capacitive, high-brightness and metal-housing options", "IP66 protection for front-panel mounting"],
               spec_table("Web panel part numbers", ["Part number", "Screen", "Browser", "Housing"], [
                   ["WP2043TN Lite / WP2070TN Lite / WP2101TN Lite", "4.3 / 7 / 10.1 in", "Microbrowser thin client", "Plastic"],
                   ["WP6043TN Plus / WP6070TN Plus / WP6101TN Plus", "4.3 / 7 / 10.1 in", "Chromium, HTML5", "Plastic"],
                   ["WP7043CN / WP7070CN / WP7101CN", "4.3 / 7 / 10.1 in capacitive", "Chromium, HTML5", "Plastic"],
                   ["WP7070CN-M / WP7101CN-M", "7 / 10.1 in PCAP", "Chromium, HTML5", "Metal"]]),
               "Lite: CE, UL Class I Division 2, IP66. Plus: CE, UL, RoHS, IP66. Capacitive models: IP66 front; ask for the current listing."),
    ], art="hero-hmi.webp")

catalog_page(
    "products/plcs/index.html", "PLCs and HMI/PLC Combos", "PLCs and HMI/PLC combos",
    "Controllers, and the units that put one behind the screen.",
    "DIN-rail PLCs with a 32-bit processor and high-speed I/O, expansion to 16 modules, and HMI/PLC combination "
    "units with pluggable or built-in I/O. All programmed in IEC 61131-3 with free software.",
    [
        family("Eco PLC", "The small controller, for the machine with a fixed job.",
               "DIN-rail mounted, 32-bit RISC processor, relay or transistor outputs, expandable to 8 modules.",
               ["8 bi-directional digital inputs: 2 single-phase high-speed counters to 25 kHz, or 8 to 10 kHz, or quadrature to 10 kHz",
                "6 outputs, relay or NPN transistor; 3 high-speed outputs to 10 kHz on the transistor model",
                "2 serial ports (RS232 and RS485) and USB Type-C", "IEC 61131-3 programming environment"],
               spec_table("Eco PLC part numbers", ["Part number", "Inputs", "Outputs", "Ports", "Expansion"], [
                   ["FL004-0806N-V2", "8 DI, high-speed capable", "6 NPN transistor", "2 serial, USB Type-C", "Up to 8 modules"],
                   ["FL004-0806R-V2", "8 DI, high-speed capable", "6 relay", "2 serial, USB Type-C", "Up to 8 modules"]]),
               "CE. Ask for the current UL listing.", watch="eco-plc"),
        family("Standard PLC", "200 kHz counting, Ethernet when you need it, 16 expansion modules.",
               "The same DIN-rail form with faster I/O: four single-phase counters or quadrature to 200 kHz, and four high-speed outputs to 200 kHz.",
               ["8 bi-directional digital inputs; 8 NPN or 6 relay outputs", "2 serial ports (RS232 and RS485) and USB Type-C; Ethernet on the FL055",
                "Expandable to 16 modules", "IEC 61131-3: ladder, function block, structured text, SFC, instruction list"],
               spec_table("Standard PLC part numbers", ["Part number", "Inputs", "Outputs", "Ethernet", "Expansion"], [
                   ["FL005-0808N-V2", "8 DI, 200 kHz capable", "8 NPN (4 to 200 kHz)", "No", "Up to 16 modules"],
                   ["FL005-0806R-V2", "8 DI, 200 kHz capable", "6 relay", "No", "Up to 16 modules"],
                   ["FL055-0808N-V2", "8 DI, 200 kHz capable", "8 NPN (4 to 200 kHz)", "Yes", "Up to 16 modules"],
                   ["FL055-0806R-V2", "8 DI, 200 kHz capable", "6 relay", "Yes", "Up to 16 modules"]]),
               "FL055: CE, UL Class I Division 2. FL005: ask for the current listing."),
        family("Expansion modules", "Digital, analog and load cell, on the PLC's own bus.",
               "Snap-on modules for the eco and standard PLCs.",
               ["Digital: 8 in, 8 out (NPN or relay), or 8 in and 8 out", "Analog: 4 inputs at 16 bit (0 to 10 V, 4 to 20 mA, 0 to 20 mA) and 2 outputs at 12 bit",
                "Load cell: 2 channels, 24-bit, up to 500 conversions a second, 4- or 6-wire strain gauge, one digital output per channel outside the scan"],
               spec_table("Expansion module part numbers", ["Part number", "Inputs", "Outputs"], [
                   ["FLD0800-V2", "8 digital", "None"], ["FLD0008N-V2", "None", "8 NPN"], ["FLD0008R-V2", "None", "8 relay"],
                   ["FLD0808N-V2", "8 digital", "8 NPN"], ["FLD0808R-V2", "8 digital", "8 relay"],
                   ["FLA0402L-V2", "4 analog, 16 bit", "2 analog, 12 bit"],
                   ["FLAD0202P-SO", "2 load cell channels, 24 bit", "2 digital"]]),
               "Load cell module: CE, cUL Class I Division 2, RoHS. Others: ask for the current listing."),
        family("HMI/PLC combination units", "One part number for the screen, the controller and the I/O.",
               "A basic or advanced HMI with the PLC function inside and the I/O plugged into the back, or built in. "
               "No separate controller, one program, one cutout.",
               ["Pluggable I/O modules: 1 on the 4.3 inch, 3 on the 7 inch, 5 on the 10.1 inch",
                "Built-in I/O models add 4 high-speed inputs to 200 kHz, RTD and thermocouple inputs, and analog outputs",
                "IP66 front; IEC 61131-3 programming environment"],
               spec_table("HMI/PLC combination part numbers", ["Part number", "Screen", "I/O", "Ethernet"], [
                   ["FP2043T-E / FP2043TN-E", "4.3 in", "1 pluggable module", "TN model"],
                   ["FP2070T-E / FP2070TN-E", "7 in", "3 pluggable modules", "TN model"],
                   ["FP4043TN-E", "4.3 in", "1 pluggable module", "Yes"],
                   ["FP4070TN-E", "7 in", "3 pluggable modules", "Yes"],
                   ["FP4101TN-E", "10.1 in", "5 pluggable modules", "Yes"],
                   ["FP2043TN-LE1208N-A0402U", "4.3 in", "12 DI, 8 NPN out, 4 AI (2 V/I, 2 RTD/TC), 2 AO, + 1 module", "Yes"],
                   ["FP2043TN-LE1208P-A0402U", "4.3 in", "12 DI, 8 PNP out, 4 AI (2 V/I, 2 RTD/TC), 2 AO, + 1 module", "Yes"],
                   ["FP2070TN-LE2016RP-A0402U", "7 in", "20 DI, 16 out (12 relay, 4 PNP), 4 AI, 2 AO, + 3 modules", "Yes"]]),
               "CE, UL Class I Division 2, IP66 front; RoHS on the basic series."),
    ], art="hero-plc.webp")

catalog_page(
    "products/io-and-communication/index.html", "I/O and Communication Modules", "I/O and communication modules",
    "Remote I/O, on the network the machine already runs.",
    "Modbus RTU field I/O that sets up with DIP switches, and an EtherCAT remote I/O block for machines on an EtherCAT master.",
    [
        family("Field I/O, Modbus RTU", "Remote points on two wires, configured with switches.",
               "Compact DIN-rail modules that expand any Modbus master. Address, baud rate and parity are set on DIP switches; "
               "the digital modules need no configuration software at all.",
               ["2-wire RS485 on a pluggable terminal block", "An LED for every input and output, plus power and communication",
                "Relay, NPN and PNP output versions", "A 3-phase energy module measures voltage, current, frequency and power, with 4 DI and 4 DO"],
               spec_table("Field I/O part numbers", ["Part number", "Points"], [
                   ["FIOA-0800-L-B", "8 analog inputs, 0 to 10 V or 4 to 20 mA, 12 bit"],
                   ["FIOA-0402-U-B / FIOA-0402-U-16-B", "4 universal analog inputs (V, mA, RTD, thermocouple), 2 analog outputs; 12 or 16 bit"],
                   ["FL001D-1600-V3", "16 digital inputs"],
                   ["FL001D-0008R-V3", "8 relay outputs"],
                   ["FL001D-0016N-V3 / -0016P-V3 / -0016R-V3", "16 outputs: NPN, PNP or relay"],
                   ["FL001D-0404N-V3 / -0404P-V3 / -0404R-V3", "4 inputs, 4 outputs: NPN, PNP or relay"],
                   ["FL001D-0808N-V3 / -0808P-V3 / -0808R-V3", "8 inputs, 8 outputs: NPN, PNP or relay"]]),
               "CE, with UL as an option. Say so when you order."),
        family("EtherCAT remote I/O", "Sixteen configurable digital points and twelve analog, in 50 mm.",
               "A DIN-rail EtherCAT block with in and out ports, for machines already on an EtherCAT master.",
               ["16 digital points at 24 VDC, each individually configurable as input or NPN output at 200 mA",
                "8 linear analog inputs, 12 bit, -10 to +10 VDC; 4 analog outputs", "Bicolour LED per digital point: green for input, red for output",
                "Isolated 24 VDC supply; 50 pin D-sub for I/O and power; 50 x 100 x 70 mm"],
               "", "Ask for the current listing."),
    ], art="hero-io.webp")

PAGES["products/cross-reference/index.html"] = dict(
    nav="Cross-Reference", title="Cross-reference | %s" % SITE,
    desc="What a Phoenix HMI talks to, and how to match a Phoenix part to the one in your panel now.",
    eyebrow="Products", h1="The Phoenix part that matches what is in your panel now.", hero_art="hero-hmi.webp",
    standfirst="Match by cutout, by I/O count and by protocol. Send Russ the part number you have and he will do it for you.",
    actions=[("Talk to Russ", "/talk-to-russ/"), ("HMIs", "/products/hmis/")],
    body=note("The driver list is from the manufacturer's current rugged-HMI datasheet. A model-by-model replacement "
              "table needs Russell's list of the brands and models he replaces most; none is invented here.") + """
<section class="band">
  <div class="inner">
    <div class="family" data-reveal>
      <div class="eyebrow">Drivers on the panel</div>
      <h2>What a Phoenix HMI already talks to.</h2>
      <p class="family-intro">The controller stays where it is. The HMI speaks its protocol, so the swap is a screen and a program, not a panel redesign.</p>
    </div>
    %(drivers)s
  </div>
</section>
<section class="band band-tint">
  <div class="inner narrow" data-reveal>
    <div class="eyebrow">How to cross-reference</div>
    <ul class="ticks" data-reveal="stagger">
      <li><b>By cutout.</b> 4.3, 7, 10.1, 12.1 and 15 inch. Give Russ the panel cutout you have and he will tell you which bezel drops in, or have one made that does.</li>
      <li><b>By I/O count.</b> Fixed and expandable PLCs to 16 modules; HMI/PLC units with the I/O on the back.</li>
      <li><b>By protocol.</b> Serial, Ethernet, Modbus RTU and TCP, MQTT where the data has to leave the machine.</li>
      <li><b>By what changes in the program.</b> Russ will say, before you order, what has to be rewritten and what does not.</li>
    </ul>
    <p><a class="btn btn-solid" href="/talk-to-russ/">Send Russ the part number</a></p>
  </div>
</section>
""" % dict(drivers=spec_table("Communication drivers", ["Make or protocol", "Driver"], [
        ["Allen-Bradley", "DF1 serial; EtherNet/IP (PCCC); Logix 5000 series"],
        ["Siemens", "Profinet PLCs"],
        ["Modbus", "RTU master and slave; ASCII master; TCP master (client)"],
        ["Delta", "PLCs"],
        ["Panasonic", "FP series PLCs"],
        ["Toshiba", "Inverters; Link-port series PLCs"],
        ["Anything with a serial port", "Universal serial driver (ASCII)"],
        ["IIoT", "MQTT publish and subscribe, with three quality-of-service levels"]])),
)

PAGES["products/datasheets/index.html"] = dict(
    nav="Datasheets", title="Datasheets | %s" % SITE,
    desc="Specification sheets and dimension drawings for Phoenix HMIs, PLCs and I/O, sent the same day.",
    eyebrow="Products", h1="Spec sheets and dimension drawings.", hero_art="hero-plc.webp",
    standfirst="One sheet per part: electrical, environmental and mechanical specifications, with the cutout and the mounting pattern.",
    actions=[("Ask for a datasheet", "/talk-to-russ/")],
    body=note("Phoenix-format datasheets, generated from the same specification tables as the product pages, are "
              "planned for after the show. Until then Russell sends the current sheet by email; the manufacturer's "
              "own PDFs are not published here.") + """
<section class="band">
  <div class="inner narrow" data-reveal>
    <div class="eyebrow">Sheets on hand today</div>
    <ul class="ticks" data-reveal="stagger">
      <li><b>Basic HMI</b>, 4.3 and 7 inch, including the 7 inch with pluggable I/O</li>
      <li><b>Advanced HMI</b>, 4.3 to 15 inch</li>
      <li><b>Rugged HMI</b>, 7 to 15.1 inch, with the full driver list</li>
      <li><b>HMI/PLC with built-in I/O</b>, 4.3 inch</li>
      <li><b>Eco PLC</b> and <b>standard PLC with Ethernet</b></li>
      <li><b>EtherCAT remote I/O</b> and the <b>load cell expansion module</b></li>
    </ul>
    <p>Tell Russ the part number or the function. He sends the sheet, and the dimension drawing if you need the
    cutout, the same day.</p>
    <p><a class="btn btn-solid" href="/talk-to-russ/">Ask for a datasheet</a></p>
  </div>
</section>
""",
)


# ---- Proof
PAGES["proof/case-studies/index.html"] = dict(
    nav="Case Studies", title="Case studies | %s" % SITE,
    desc="Real jobs, written up as the problem, what was built, and the result. The cab operating panel goes first.",
    eyebrow="Proof", h1="Real jobs: the problem, what was built, the result.",
    standfirst="Every case study here is a machine that shipped. Customers are named only where they have agreed to be.",
    actions=[("Talk to Russ", "/talk-to-russ/")],
    body=note("The cab operating panel story is from the 28 Aug call (31:37) and the 8 Sep session. The "
              "customer stays unnamed until Russell clears it, and the pricing needs his sign-off before "
              "launch, per the SOW.") + """
<section class="band">
  <div class="inner narrow" data-reveal>
    <div class="eyebrow">Case study one</div>
    <h2>The glass cab operating panel: $1,000 to $350 at 2,500 units.</h2>
    <h3>The problem</h3>
    <p>A residential elevator manufacturer, a Phoenix customer for close to twenty years, needed a new cab
    operating panel for its next cab: all glass, an integrated display, and a phone mounted on the back
    because the code requires one. Revision one came in near $1,000 a unit. The customer said it was too
    expensive, and it was.</p>
    <h3>What was built</h3>
    <p>Instead of losing the job, Phoenix took the target back to the factory: $350 to $400 a unit at a
    first quantity of 2,500. The part was redesigned for that machine and that price rather than pulled
    from a shelf. Same function, same glass front, same phone, on its second revision now.</p>
    <h3>The result</h3>
    <p class="stat"><span class="num" data-count="350" data-count-prefix="$">$350</span> <span class="lbl">per unit at <span data-count="2500" data-count-suffix=" units">2,500 units</span>, against $1,000 for revision one</span></p>
    <p>One approved part, carried across the customer's cab lineup. That is what a design win looks like
    from the builder's side of the table.</p>
  </div>
</section>
<section class="band band-tint">
  <div class="inner narrow center" data-reveal>
    <h2>More to come.</h2>
    <p>Packaging, water treatment and printing jobs are being written up in the same shape. If you want to
    know whether Phoenix has done a machine like yours, ask.</p>
    <p><a class="btn btn-solid" href="/talk-to-russ/">Talk to Russ</a></p>
  </div>
</section>
""",
)

PAGES["proof/custom-builds/index.html"] = dict(
    nav="Custom Builds", title="Custom builds | %s" % SITE,
    desc="Custom parts installed in real machines: operator panels, control panels, remote I/O and the machines around them.",
    eyebrow="Proof", h1="Custom parts, installed in real machines.",
    standfirst="Nothing here is a render. Every photograph is a Phoenix-supplied part on a machine that runs.",
    actions=[("Talk to Russ", "/talk-to-russ/")],
    body=note("The gallery is the ten photographs that passed the branding review. The cab operating panel "
              "photographs join it when Russell clears the customer's splash screen.") + """
<section class="band">
  <div class="inner">
    %(gallery)s
  </div>
</section>
""" % dict(gallery=cards([
        ("Hall station", "Residential elevator, call display and car position.", "elevator-hall-station", "Elevator hall station with call display"),
        ("Hall station screen", "The display itself, at the landing.", "hall-station-screen", "Hall station screen showing car position"),
        ("Control panel", "An OEM machine's panel, opened up with the wiring showing.", "control-panel", "Control panel with PLC, I/O and wiring, built for an OEM machine"),
        ("Remote I/O", "Modules wired into a factory automation enclosure.", "factory-automation-remote-i-o", "Remote I/O modules wired into a factory automation enclosure"),
        ("Barcode verification", "A verification station on a packaging line.", "barcode-verification", "Barcode verification station on a packaging line"),
        ("Pad printing", "Touchscreen operator control on a pad printer.", "pad-printing-machine", "Pad printing machine with touchscreen operator control"),
        ("Print curing", "Temperature control on a curing line.", "print-curing", "Print curing line with temperature control interface"),
        ("Waste water treatment", "A municipal plant that runs on Phoenix-supplied controls.", "waste-water-plant", "Exterior of a municipal waste water treatment plant, with aeration basins and the operations building"),
        ("Soil-sampling rig", "Hydraulic carousel control in the field.", "soil-sampling-rig", "Hydraulic soil-sampling rig with carousel control"),
        ("Soil sampler interface", "Control and logging on the rig.", "soil-sampler", "Soil sampler control and logging interface"),
    ], "mosaic")),
)


# ---- Support
def support_page(path, nav_label, title, h1, standfirst, items, now, note_text, extra=""):
    PAGES[path] = dict(
        nav=nav_label, title="%s | %s" % (title, SITE), desc=standfirst, eyebrow="Support", h1=h1,
        standfirst=standfirst, actions=[("Contact Phoenix", "/company/contact/")],
        body=note(note_text) + """
<section class="band">
  <div class="inner narrow" data-reveal>
    <div class="eyebrow">What this page will hold</div>
    <ul class="ticks" data-reveal="stagger">%(items)s</ul>
  </div>
</section>
%(extra)s<section class="band band-tint">
  <div class="inner narrow" data-reveal>
    <div class="eyebrow">For now</div>
    <p>%(now)s</p>
    <p><a class="btn btn-solid" href="/company/contact/">Contact Phoenix</a></p>
  </div>
</section>
""" % dict(items="".join("<li>%s</li>" % i for i in items), now=now, extra=extra))


support_page("support/software/index.html", "Software, Manuals and Firmware", "Software, manuals and firmware",
             "Programming software, user manuals and firmware.",
             "Downloads for current customers: the programming software for each controller and HMI, the user manuals, and firmware updates with their release notes.",
             ["Programming software by product family, with the version and the date", "User manuals as PDF", "Firmware updates with release notes and the products they apply to", "Sample code from application support, where Russ has written it for you"],
             "Current customers get software, manuals and firmware from Russ directly, the same day. Say which product and which version you are on.",
             "Scaffolding. The download library depends on what the product line's software and manuals are and on how they may be distributed; Russell decides.",
             extra='<section class="band">\n  <div class="inner narrow">\n    %s\n  </div>\n</section>\n' % video("software", "Before you install"))

PAGES["support/videos/index.html"] = dict(
    nav="Videos", title="Videos | %s" % SITE, eyebrow="Support", h1="Watch the products and the software.",
    desc="Product walkthroughs and software tutorials from the factory: the eco PLC up close, and the programming software from installation to a first project.",
    standfirst="Walkthroughs and tutorials from the factory. More are added as Russ picks them; "
               "if there is a product you want to see running before you buy it, ask.",
    actions=[("Talk to Russ", "/talk-to-russ/"), ("Software and manuals", "/support/software/")],
    body=note("Russ asked for the factory's videos on the site. The page copy is Phoenix's; the player carries the channel's branding once it plays.") + """
<section class="band">
  <div class="inner">
    <div class="videos">
      %(eco)s
      %(sw)s
    </div>
  </div>
</section>
<section class="band band-tint">
  <div class="inner narrow" data-reveal>
    <div class="eyebrow">Something not covered?</div>
    <h2>Ask for a demonstration.</h2>
    <p>Russ keeps the products on the bench in Mokena. If a video does not answer the question, he can put the part in front of a camera, or in front of you.</p>
    <p><a class="btn btn-solid" href="/talk-to-russ/">Talk to Russ</a></p>
  </div>
</section>
""" % dict(eco=video("eco-plc", "Product"), sw=video("software", "Software")))
support_page("support/warranty-and-rma/index.html", "Warranty and RMA", "Warranty and RMA",
             "Warranty terms, and how to return a part.",
             "The warranty on Phoenix-supplied hardware, what it covers, and the return process when a part needs to come back.",
             ["Warranty term and what it covers, by product family", "How to request a return authorisation", "Where to ship, and what to include", "Turnaround on repair or replacement"],
             "Until the terms are posted, send Russ the part, the serial number and what happened through the <a href=\"/talk-to-russ/\">form</a>, or call. He answers within two business days.",
             "Scaffolding. Warranty terms and the RMA process need Russell's wording; nothing is stated here until he supplies it.")


# ---- Company
PAGES["company/supply-chain/index.html"] = dict(
    nav="Supply Chain", title="Supply chain | %s" % SITE,
    desc="A direct factory relationship of seventeen years, and stock held in Mokena, Illinois.",
    eyebrow="Company", h1="A factory that answers the phone, and a shelf in Mokena.",
    standfirst="Purchasing wants to know a supplier can keep delivering. Here is how Phoenix does.",
    actions=[("Talk to Russ", "/talk-to-russ/")],
    body=note("Positioning decision: the factory partner is not named on the site. Footage from the production "
              "floor is in hand but shows the partner's signage, so it stays off the page until Russell "
              "decides whether it may be used at all. The seventeen-year figure is from the brand direction.") + """
<section class="band">
  <div class="inner narrow" data-reveal>
    <h2>The factory relationship</h2>
    <p>Phoenix has worked with the same factory for seventeen years. It is a direct relationship: Russ has
    stood on that floor, twice, and the engineers there answer him the same week. A million-dollar
    opportunity does not register with the largest control vendors. At this factory it gets engineers on
    a plane.</p>
    <p>That is what makes custom work possible at OEM quantities: a bezel with your logo, a cutout to your
    dimensions, an I/O count to your machine, at a price set against your volume rather than a list.</p>
    <h2>Stock in Mokena</h2>
    <p>Repeatable models mean repeatable orders. Phoenix holds stock, reboxes and ships from Mokena,
    Illinois, southwest of Chicago, so a production run is not waiting on a container. Lead time and stock
    position are stated on every product page as the catalog comes online.</p>
    <h2>Footage from the floor</h2>
    <p class="muted">Video from the production floor is in hand and will appear here once cleared.</p>
  </div>
</section>
""",
)

PAGES["company/certifications/index.html"] = dict(
    nav="Certifications", title="Certifications | %s" % SITE,
    desc="Product approvals by family for Phoenix HMIs, PLCs and I/O: CE, UL Class I Division 2, IP66, RoHS and REACH.",
    eyebrow="Company", h1="Approvals, family by family.",
    standfirst="What each product family carries today. Ask for the UL file number or the declaration of conformity "
               "for any part and Russ sends it the same day.",
    actions=[("Talk to Russ", "/talk-to-russ/")],
    body=note("Every line is from the manufacturer's February 2025 brochure or a current datasheet, and every line "
              "wants Russell's confirmation, with the UL file numbers, before launch. Company credentials are still "
              "to come from him (28 Aug call, 54:14). A certification claim that is wrong is worse than none.") + """
<section class="band">
  <div class="inner">
    %(table)s
    <p class="approvals">IP66 is the rating of the front face when the panel is mounted in a suitable enclosure.
    UL Class I Division 2 covers use in hazardous locations where ignitable gas is not normally present.</p>
  </div>
</section>
<section class="band band-tint">
  <div class="inner narrow" data-reveal>
    <div class="eyebrow">Company credentials</div>
    <p class="muted">Russ's credentials and the company's, in his approved wording, to follow.</p>
    <p>If an approval matters to your application today, ask. Russ will tell you what the part carries and what it
    does not.</p>
    <p><a class="btn btn-solid" href="/talk-to-russ/">Talk to Russ</a></p>
  </div>
</section>
""" % dict(table=spec_table("Approvals by product family", ["Family", "Approvals"], [
        ["Basic HMI, 4.3 and 7 inch", "CE, UL Listed Class I Division 2, RoHS, IP66 front"],
        ["Advanced HMI, 4.3 to 15 inch", "CE, UL Listed Class I Division 2, RoHS, IP66 front"],
        ["Rugged HMI, metal housing (FP7)", "CE, UL Class I Division 2, IP66, RoHS, REACH"],
        ["Rugged HMI, sunlight readable (FP6)", "IP66 front; other approvals on request"],
        ["HMI/PLC combination units", "CE, UL Class I Division 2, IP66 front; RoHS on the basic series"],
        ["Web panels", "Lite: CE, UL Class I Division 2, IP66. Plus: CE, UL, RoHS, IP66"],
        ["Eco PLC", "CE"],
        ["Standard PLC with Ethernet", "CE, UL Class I Division 2"],
        ["Load cell expansion module", "CE, cUL Class I Division 2, RoHS"],
        ["Field I/O, Modbus RTU", "CE, with UL as an option"]])),
)

PAGES["company/contact/index.html"] = dict(
    nav="Contact", title="Contact | %s" % SITE,
    desc="One phone number, one form and the Mokena, Illinois address for Phoenix Automation Solutions.",
    eyebrow="Company", h1="One number, one form, one address.",
    standfirst="Phoenix Automation Solutions, Inc., Mokena, Illinois, southwest of Chicago.",
    actions=[("Talk to Russ", "/talk-to-russ/")],
    body=note("PHONE, CONTACT_EMAIL and the street address are placeholders in _build/build.py until Russell "
              "picks the one number and the one inbox (8 Sep, 13:58). The request form is the Talk to Russ "
              "form; a second copy here would split the CRM feed.") + """
<section class="band">
  <div class="inner narrow" data-reveal>
    <div class="split">
      <div>
        <div class="eyebrow">Reach Phoenix</div>
        <address class="addr contact-addr">%(address)s%(contact)s</address>
      </div>
      <div>
        <div class="eyebrow">Building a machine?</div>
        <p>The fastest route to Russ is the three-question form: what you build, how many a year, what
        controls are on it now. He reads every one and replies within two business days.</p>
        <p><a class="btn btn-solid" href="/talk-to-russ/">Talk to Russ</a></p>
      </div>
    </div>
  </div>
</section>
""" % dict(address=ADDRESS,
           contact=('<br><a href="tel:%s">%s</a>' % (re.sub(r"[^\d+]", "", PHONE), PHONE) if PHONE else
                    '<br><span class="muted">Phone number to be confirmed.</span>')
                   + ('<br><a href="mailto:%s">%s</a>' % (CONTACT_EMAIL, CONTACT_EMAIL) if CONTACT_EMAIL else "")
                   + '<br><a href="/talk-to-russ/">Send Russ a message</a>'),
)


# ---- The old addresses
for old_path, new_url in MOVED.items():
    PAGES[old_path] = moved(new_url)

PAGES["404.html"] = dict(
    nav=None, motion=False, title="Not found | %s" % SITE, desc="That page is not here.",
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
ASSET_LINK = re.compile(r'((?:href|src)="/assets/[a-z0-9/-]+\.(?:css|js))"')
_digest = {}


def digest(rel):
    """Eight hex characters of the asset at root-relative path `rel`."""
    if rel not in _digest:
        with open(os.path.join(ROOT, rel.lstrip("/")), "rb") as f:
            _digest[rel] = hashlib.md5(f.read()).hexdigest()[:8]
    return _digest[rel]


def version_assets(html):
    def stamp(m):
        rel = m.group(1).split('"')[1]
        return '%s?v=%s"' % (m.group(1), digest(rel))
    return ASSET_LINK.sub(stamp, html)


if __name__ == "__main__":
    for path, page in PAGES.items():
        dest = os.path.join(ROOT, path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        html = version_assets(shell(page, path))
        open(dest, "w", encoding="utf-8", newline="\n").write(html)
        print("%-32s %6d bytes" % (path, len(html)))
    print("\n%d pages" % len(PAGES))
