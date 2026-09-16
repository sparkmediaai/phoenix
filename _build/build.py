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
BASE = "https://phoenix.sparkmedia.ai/"

# The address the site is actually for. While BASE is anything else this is a
# staging copy of a real business's website on a public host, and it asks
# search engines to stay away. Point BASE at the line below (with
# set_domain.py) and the noindex disappears on its own, which is the point:
# "remember to take the noindex off" is a thing somebody forgets on launch day.
PRODUCTION = "https://phoenixautomationsolutions.example/"   # TODO: Russell's domain

# Where the intake form posts: a GoHighLevel inbound webhook, straight from
# the browser, exactly as The Valley does it. Empty until Phoenix's GHL
# sub-account exists. While it is empty the form does not submit; it shows the
# visitor the contact email instead, so nothing anybody types is lost.
#
# When it is set, remember what that means: the URL is the endpoint's only
# authentication, GHL bills Inbound Webhook per execution, and this repo is
# public. The honeypot in assets/forms.js is the only thing between a scraper
# and the invoice. Do not remove it.
FORM_ENDPOINT = ""
CONTACT_EMAIL = "russell@phoenixautomationsolutions.example"   # TODO: the one inbox
PHONE = ""                                                     # TODO: the one number

# Primary navigation and the one invitation that sits beside it.
NAV = [
    ("For OEMs", "/for-oems/"),
    ("Capabilities", "/capabilities/"),
    ("Industries", "/industries/"),
    ("About", "/about/"),
]
CTA = ("Start an application review", "/start/")

FOOTER = [
    ("Work with Phoenix", [
        ("For OEM machine builders", "/for-oems/"),
        ("Start an application review", "/start/"),
        ("PACK EXPO 2026", "/pack-expo/"),
    ]),
    ("What we do", [
        ("Capabilities", "/capabilities/"),
        ("Industries", "/industries/"),
        ("About Russell Homans", "/about/"),
    ]),
]

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
    """Turn an img placeholder (img:file.webp|alt|extra, in double braces)
    into a real img tag, and an inline placeholder into the file's contents."""
    def one(m):
        name, alt, extra = m.group(1), m.group(2), m.group(3)
        big, small = "%s-1600.webp" % name, "%s-800.webp" % name
        w, h = webp_size(os.path.join(IMG, big))
        return ('<img src="%(r)sassets/img/%(big)s" '
                'srcset="%(r)sassets/img/%(small)s 800w, %(r)sassets/img/%(big)s 1600w" '
                'sizes="(max-width: 800px) 100vw, 800px" alt="%(alt)s" width="%(w)d" height="%(h)d" '
                'loading="lazy" decoding="async"%(extra)s>'
                % dict(r=URL_ROOT, big=big, small=small, alt=alt, w=w, h=h,
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


def steps(items):
    return '<ol class="steps" data-reveal="stagger">\n%s\n    </ol>' % "\n".join(
        '      <li><h3>%s</h3><p>%s</p></li>' % (t, p) for t, p in items)


def figure(svg_name, caption, cls=""):
    """An inlined drawing that draws itself as it scrolls in, with a caption."""
    return ('<figure class="art%s" data-reveal>{{inline:art/%s}}<figcaption>%s</figcaption></figure>'
            % ((" " + cls) if cls else "", svg_name, caption))


def pinned(steps, svg_name, length=None):
    """A section that pins while its steps play beside a drawing that draws
    itself one group per step. With motion off the steps stack under each
    other beside the finished drawing."""
    length = length or len(steps) + 2
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
    """
    srcs = ",".join('"%s%s?v=%s"' % (root, s.lstrip("/"), digest(s)) for s in MOTION_SCRIPTS)
    return ('<script>(function(h){if(!h.classList.contains("motion"))return;'
            'function off(){h.classList.remove("motion")}'
            '[%s].forEach(function(s){var e=document.createElement("script");e.src=s;e.async=false;e.onerror=off;document.body.appendChild(e)});'
            'setTimeout(function(){if(!window.__motionReady)off()},4000)})(document.documentElement)</script>\n' % srcs)


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

    hero, hero_class, hero_steps = "", "hero-plain", ""
    if page.get("hero_img"):
        w, h = webp_size(os.path.join(IMG, page["hero_img"]))
        hero_class = "hero-photo"
        hero = ('  <img class="hero-bg" src="%sassets/img/%s" alt="%s" '
                'width="%d" height="%d" fetchpriority="high" decoding="async">\n'
                % (root, page["hero_img"], html_attr(page["hero_alt"]), w, h))

    preload = ""
    if page.get("hero_video"):
        v = page["hero_video"]
        poster = "%sassets/video/%s-poster.webp" % (root, v["name"])
        w, h = webp_size(os.path.join(ROOT, "assets", "video", "%s-poster.webp" % v["name"]))
        hero_class = "hero-cinema\" data-pin data-pin-length=\"3"
        preload = '<link rel="preload" as="image" href="%s">\n' % poster
        hero = ('  <div class="hero-media" data-parallax="0.15">\n'
                '    <img class="hero-bg" src="%(p)s" alt="%(alt)s" width="%(w)d" height="%(h)d" fetchpriority="high" decoding="async">\n'
                '    <video class="hero-video" muted loop playsinline preload="none" poster="%(p)s" aria-hidden="true" tabindex="-1">\n'
                '      <source src="%(r)sassets/video/%(n)s.webm" type="video/webm">\n'
                '      <source src="%(r)sassets/video/%(n)s.mp4" type="video/mp4">\n'
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
    contact += '<br><a href="mailto:%s">%s</a>' % (CONTACT_EMAIL, CONTACT_EMAIL)

    hold_attr = " data-hold" if page.get("hero_video") else ""

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
%(head)s<script>document.documentElement.classList.add("js");window.FORM_ENDPOINT=%(endpoint)s;window.CONTACT_EMAIL=%(email)s;if(/[?&]notes\\b/.test(location.search))document.documentElement.classList.add("notes");%(gate)s</script>
</head>
<body>

<a class="skip" href="#main">Skip to content</a>

<header class="site-head">
  <div class="inner">
    <a class="wordmark" href="%(root)s">%(logo)s<span class="vh">%(site)s</span></a>
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
%(loader)s</body>
</html>
""" % {
        "title": page["title"], "desc": html_attr(page["desc"]), "root": root,
        "url": url, "base": BASE, "og_alt": html_attr(OG_ALT),
        "endpoint": json_str(FORM_ENDPOINT), "email": json_str(CONTACT_EMAIL),
        "robots": "" if BASE == PRODUCTION else
                  '<meta name="robots" content="noindex,nofollow">' + chr(10),
        "site": SITE, "logo": LOGO, "nav": nav,
        "cta_href": CTA[1], "cta_text": CTA[0],
        "cta_bar": "" if path.startswith("start/") else
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
    }


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
    actions=[("Start an application review", "/start/"), ("Meet us at PACK EXPO", "/pack-expo/")],
    hero_video=dict(name="hero", alt="A packaging machine running with barcode verification, controlled by a Phoenix-engineered operator panel"),
    hero_steps=[
        ("Proof one", "Engineered to the target.", "A $1,000 operator panel taken back to the factory and re-engineered to $350 at 2,500 units. Not discounted. Redesigned."),
        ("Proof two", "A panel with your name on it.", "Your logo on the bezel, your mounting, your price at your quantity. The big brands will not discuss it below a seven-figure order."),
        ("Proof three", "An engineer on your first application.", "Russell Homans, three to eight hours a week, until the first unit is running on your floor."),
    ],
    body=note("Positioning per the 8 Sep session and the SOW: Phoenix is the solution, Russell is the "
              "value, the supplier stays in the background. Every claim here is drawn from the two "
              "transcripts; Russell signs off technical claims before launch.") + """
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
        water plants and gutter machines run the same way. <a href="/industries/">See the industries.</a></p>
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
    <p class="center"><a class="btn btn-solid" href="/start/">Start an application review</a></p>
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

PAGES["for-oems/index.html"] = dict(
    nav="For OEMs", title="For OEM machine builders | %s" % SITE,
    desc="How Phoenix works with OEM machine builders: application review, cost engineering, custom operator panels and first-application support.",
    eyebrow="For OEM machine builders",
    h1="Think of us as the controls engineer you did not have to hire.",
    standfirst="Russell describes it as being a part-time employee of your engineering department. "
               "Here is what that means in practice.",
    actions=[("Start an application review", "/start/")],
    body=note("The 'part-time employee for my customer' line is Russell's own (8 Sep, 16:37). "
              "The three-to-eight-hours-a-week figure and the taper after three to six months are his too.") + """
%(path)s

<section class="band band-tint">
  <div class="inner">
    <div class="eyebrow">What we supply</div>
    %(cards)s
    <p class="center"><a class="btn" href="/capabilities/">All capabilities</a></p>
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
             "The first machine on a new platform is where a supplier is either a partner or a problem. Phoenix commits three to eight engineering hours a week until the first unit is running.", "#g-io"),
            ("Step four", "Then, production.",
             "Repeatable models mean repeatable orders. Phoenix holds stock, reboxes and ships from Illinois, and keeps the factory relationship warm so the next revision costs less than the last one.", "#g-net"),
        ], "topology.svg"),
        cards=cards([
            ("HMI and touchscreens", "Operator interfaces from small panel displays to full-glass fronts, branded to your machine."),
            ("PLC and controllers", "Controllers sized to the machine, with application code support from Phoenix."),
            ("I/O and networking", "Remote I/O, fieldbus and the network layout to make it all talk."),
            ("Custom operator panels", "Cab operating panels, hall stations, glass fronts with integrated phone, at production cost."),
        ], "two"),
    ),
)

PAGES["capabilities/index.html"] = dict(
    nav="Capabilities", title="Capabilities | %s" % SITE,
    desc="HMI, PLC, I/O, custom operator panels, application programming, cost engineering and sourcing for OEM machine builders.",
    eyebrow="Capabilities",
    h1="Controls hardware, and the engineering that makes it fit.",
    standfirst="Every capability below has shipped on a production machine. Nothing here is aspirational.",
    body=note("Product families are kept generic on purpose: no supplier names, per the positioning "
              "decision. Add photographs from the Drive folder (glass operator panels, hall stations, "
              "control panel, remote I/O, robot cell, soil sampling rig) as hero_img and inline images.") + """
<section class="band">
  <div class="inner">
    <div class="eyebrow">Hardware</div>
    %(hw)s
  </div>
</section>
<section class="band band-tint">
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

PAGES["industries/index.html"] = dict(
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
    %(cards)s
  </div>
</section>
<section class="band band-tint">
  <div class="inner narrow center" data-reveal>
    <h2>Building something else?</h2>
    <p>If it is a repeatable machine with a screen and a controller on it, the conversation is the same.</p>
    <p><a class="btn btn-solid" href="/start/">Start an application review</a></p>
  </div>
</section>
""" % dict(cards=cards([
        ("Packaging machinery", "Die cutters with barcode verification, labellers, case erectors, fillers. The $10,000 to $100,000 machines still built in the States.", "barcode-verification", "Barcode verification station on a packaging line"),
        ("Residential elevators", "Twenty years on the same account. Glass cab operating panels, hall stations, and the cost engineering that made revision two possible.", "elevator-hall-station", "Elevator hall station with call display"),
        ("Commercial kitchen equipment", "Ovens and mixers, and the temperature and recipe interfaces that set them."),
        ("Printing and finishing", "Screen-printing presses, pad printers and print-curing lines with operator control at the press.", "pad-printing-machine", "Pad printing machine with touchscreen operator control"),
        ("Food processing", "Industrial slicers and portioning equipment with washdown-rated interfaces."),
        ("Water and wastewater", "Municipal treatment plants: load balancing, remote I/O and operator screens that run for decades.", "waste-water-plant", "Exterior of a municipal waste water treatment plant, with aeration basins and the operations building"),
        ("Building products machinery", "Seamless gutter machines and roll-forming lines that run from a truck."),
        ("Agriculture and field equipment", "Hydraulic soil-sampling rigs with carousel control and logging.", "soil-sampling-rig", "Hydraulic soil-sampling rig with carousel control"),
        ("Medical and rehabilitation equipment", "Controls and operator interfaces for therapy and rehabilitation machines."),
    ], "mosaic")),
)

PAGES["about/index.html"] = dict(
    nav="About", title="About Russell Homans | %s" % SITE,
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
        <div class="portrait-frame" aria-hidden="true">{{inline:mark.svg}}</div>
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
      <li><b>Nine industries.</b> Packaging, elevators, kitchens, printing, food, water, building products, agriculture, medical. <a href="/industries/">See them.</a></li>
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
    actions=[("Start an application review", "/start/"), ("What Phoenix does", "/for-oems/")],
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
    <p><a class="btn btn-solid" href="/start/">Or answer four questions now</a></p>
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

PAGES["start/index.html"] = dict(
    nav=None, title="Start an application review | %s" % SITE,
    desc="Four questions about your machine. Russell reviews every submission personally.",
    eyebrow="Application review",
    h1="Four questions about the machine.",
    standfirst="Two minutes. Russell reads every one and replies within two business days, "
               "with a straight answer either way.",
    body=note("Posts to FORM_ENDPOINT in _build/build.py; empty until Phoenix's GoHighLevel "
              "sub-account exists. Field names and option strings must match the CRM exactly; "
              "see assets/forms.js. Qualification thresholds are to be agreed with Russell.") + """
<section class="band">
  <div class="inner narrow">
    <form class="inquiry" method="post" action="#" novalidate>
      <fieldset>
        <legend>The machine</legend>
        <label>What does the machine do? <input name="machine_type" placeholder="e.g. rotary die cutter with barcode verification" required></label>
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
        <label>What do you need? <textarea name="application" rows="4" placeholder="A cost target, a custom panel, a platform change, an application that has to work first time..." required></textarea></label>
        <label>Link to a spec, drawing or photo (optional) <input type="url" name="spec_link" placeholder="https://"></label>
      </fieldset>
      <fieldset>
        <legend>You</legend>
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
""" % dict(volumes="".join("<option>%s</option>" % v for v in VOLUMES),
           controls="".join("<option>%s</option>" % c for c in CONTROLS)),
)

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
