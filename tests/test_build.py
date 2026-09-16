import importlib.util, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_build():
    spec = importlib.util.spec_from_file_location("build", os.path.join(ROOT, "_build", "build.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_digest_is_eight_hex_chars():
    b = load_build()
    d = b.digest("/assets/site.css")
    assert len(d) == 8 and int(d, 16) >= 0
    assert d == b.digest("/assets/site.css")


def test_shell_gates_motion_on_reduced_motion():
    b = load_build()
    html = b.shell(b.PAGES["index.html"], "index.html")
    assert 'matchMedia("(prefers-reduced-motion: no-preference)")' in html
    assert 'classList.add("motion")' in html
    assert "/assets/vendor/gsap.min.js?v=" in html
    assert "/assets/vendor/ScrollTrigger.min.js?v=" in html
    assert "/assets/motion.js?v=" in html
    assert "/assets/motion.css?v=" in html
    # The four-second fallback timer is reachable so motion.js can cancel it
    # the moment it starts executing.
    assert "window.__motionTimer" in html


def css_rules(css):
    """(selector, ancestors) for every rule in a small stylesheet."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out, sel, stack = [], "", []
    for ch in css:
        if ch == "{":
            s = " ".join(sel.split())
            if not s.startswith("@"):
                out.append((s, list(stack)))
            stack.append(s)
            sel = ""
        elif ch == "}":
            if stack:
                stack.pop()
            sel = ""
        else:
            sel += ch
    return out


def test_motion_css_hides_steps_only_behind_the_armed_mark():
    """The hidden state and the timeline must never disagree.

    motion.css used to hide [data-step] inside its own @media (min-width:
    768px), while motion.js decided once, at load, whether to build the pin.
    Rotate a phone into landscape and the CSS hid three steps no timeline
    would ever reveal. Both sides now key off data-pin-armed, which lives and
    dies with the gsap.matchMedia branch.
    """
    css = open(os.path.join(ROOT, "assets", "motion.css"), encoding="utf-8").read()
    step_rules = [(sel, anc) for sel, anc in css_rules(css) if "[data-step]" in sel]
    assert step_rules, "no [data-step] rule found in motion.css"
    for sel, ancestors in step_rules:
        assert not ancestors, "[data-step] rule inside %s: %s" % (ancestors, sel)
        assert "data-pin-armed" in sel, "[data-step] rule not keyed off the mark: %s" % sel


def test_pack_expo_loads_no_motion_script():
    b = load_build()
    html = b.shell(b.PAGES["pack-expo/index.html"], "pack-expo/index.html")
    assert "gsap.min.js" not in html
    assert "motion.js" not in html
    assert 'classList.add("motion")' not in html


def test_cards_and_steps_stagger():
    b = load_build()
    assert 'data-reveal="stagger"' in b.cards([("A", "a"), ("B", "b")])
    assert 'data-reveal="stagger"' in b.steps([("A", "a")])


def test_homepage_marks_reveals():
    b = load_build()
    html = b.shell(b.PAGES["index.html"], "index.html")
    assert html.count("data-reveal") >= 6


def test_expand_img_emits_srcset(tmp_path, monkeypatch):
    """Odd widths on purpose: a crop narrower than 1600px is never upscaled,
    so the descriptors have to be read from the files, not assumed."""
    b = load_build()
    from PIL import Image
    Image.new("RGB", (1234, 926)).save(tmp_path / "x-1600.webp", "WEBP")
    Image.new("RGB", (617, 463)).save(tmp_path / "x-800.webp", "WEBP")
    monkeypatch.setattr(b, "IMG", str(tmp_path))
    html = b.expand("{{img:x|A panel|class=\"card-img\"}}")
    assert 'src="/assets/img/x-1600.webp"' in html
    assert 'srcset="/assets/img/x-800.webp 617w, /assets/img/x-1600.webp 1234w"' in html
    assert 'sizes="(max-width: 800px) 100vw, 800px"' in html
    assert 'width="1234" height="926"' in html
    assert 'alt="A panel"' in html and 'class="card-img"' in html


def test_cinematic_hero_markup():
    b = load_build()
    html = b.shell(b.PAGES["index.html"], "index.html")
    assert 'class="hero hero-cinema" data-pin data-pin-length="2"' in html
    assert '<video class="hero-video" muted loop playsinline preload="none"' in html
    assert 'type="video/webm"' in html and 'type="video/mp4"' in html
    assert 'rel="preload" as="image" href="/assets/video/hero-poster.webp"' in html
    assert html.count('data-step') == 3
    assert 'data-hold' in html and 'data-dim' in html


def test_homepage_has_cost_figure_and_counts():
    b = load_build()
    html = b.shell(b.PAGES["index.html"], "index.html")
    assert 'data-count="2500"' in html and 'data-count="350"' in html and 'data-count="1000"' in html
    assert 'id="cost-figure"' in html and "data-draw" in html
    assert 'id="panel-front"' in html


def test_figure_helper():
    b = load_build()
    out = b.figure("cost-figure.svg", "From $1,000 to $350.")
    assert out.startswith('<figure class="art" data-reveal>') and "{{inline:art/cost-figure.svg}}" in out
    assert "<figcaption>From $1,000 to $350.</figcaption>" in out


def test_pinned_helper_and_oem_page():
    b = load_build()
    out = b.pinned([("A", "B", "C", "#g-hmi"), ("D", "E", "F", "#g-plc")], "topology.svg")
    assert 'data-pin data-pin-length="3"' in out
    assert out.count('class="pin-step" data-step') == 2
    assert 'data-step-draw="#g-hmi"' in out and "{{inline:art/topology.svg}}" in out
    html = b.shell(b.PAGES["machine-builders/design-win/index.html"], "machine-builders/design-win/index.html")
    assert html.count("data-step-draw") == 4 and 'id="topology"' in html


def test_cards_accept_images():
    b = load_build()
    out = b.cards([("T", "x", "control-panel", "A panel"), ("U", "y")])
    assert out.count('class="card-shift" data-parallax="0.12"') == 1
    assert '{{img:control-panel|A panel|class="card-img"}}' in out


def test_photo_pages():
    b = load_build()
    for path in ("machine-builders/custom-controls/index.html", "machine-builders/industries/index.html", "pack-expo/index.html"):
        html = b.shell(b.PAGES[path], path)
        assert "/assets/img/" in html, path
    about = b.shell(b.PAGES["company/about-russ/index.html"], "company/about-russ/index.html")
    assert 'data-count="20"' in about and 'class="timeline"' in about
    assert 'class="portrait-frame"' in about
    expo = b.shell(b.PAGES["pack-expo/index.html"], "pack-expo/index.html")
    assert "data-parallax" not in expo and "data-pin" not in expo and "motion.js" not in expo
    # The hero photograph is the page's LCP element and the landing is scanned
    # on phones: it must offer the 800-wide file too.
    hero_img = re.search(r'<img class="hero-bg"[^>]*>', expo).group(0)
    assert re.search(r'srcset="[^"]*barcode-verification-800\.webp \d+w', hero_img), hero_img


def test_intake_has_four_wizard_steps():
    b = load_build()
    html = b.shell(b.PAGES["talk-to-russ/index.html"], "talk-to-russ/index.html")
    assert html.count("<fieldset data-wizard-step>") == 4
    assert "/assets/wizard.js?v=" in html
    assert html.count('<legend>') == 4


def test_navigation_has_five_headers_and_every_page_exists():
    b = load_build()
    html = b.shell(b.PAGES["index.html"], "index.html")
    assert html.count('class="menu-head"') == 5
    assert 'href="/talk-to-russ/">Talk to Russ</a>' in html
    for head, intro, pages in b.NAV:
        assert intro in html
        for label, href, summary in pages:
            assert href in html and summary in html
            assert href.strip("/") + "/index.html" in b.PAGES, href


def test_current_page_lights_its_header():
    b = load_build()
    html = b.shell(b.PAGES["products/hmis/index.html"], "products/hmis/index.html")
    assert 'class="menu-item is-section"' in html and html.count("is-section") == 1
    assert '<a href="/products/hmis/" aria-current="page">' in html


def test_old_urls_redirect():
    b = load_build()
    for old, new in b.MOVED.items():
        html = b.shell(b.PAGES[old], old)
        assert 'http-equiv="refresh" content="0; url=%s"' % new in html
        assert "motion.js" not in html
