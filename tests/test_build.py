import importlib.util, os, sys

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
    b = load_build()
    from PIL import Image
    Image.new("RGB", (1600, 1200)).save(tmp_path / "x-1600.webp", "WEBP")
    Image.new("RGB", (800, 600)).save(tmp_path / "x-800.webp", "WEBP")
    monkeypatch.setattr(b, "IMG", str(tmp_path))
    html = b.expand("{{img:x|A panel|class=\"card-img\"}}")
    assert 'src="/assets/img/x-1600.webp"' in html
    assert 'srcset="/assets/img/x-800.webp 800w, /assets/img/x-1600.webp 1600w"' in html
    assert 'sizes="(max-width: 800px) 100vw, 800px"' in html
    assert 'width="1600" height="1200"' in html
    assert 'alt="A panel"' in html and 'class="card-img"' in html


def test_cinematic_hero_markup():
    b = load_build()
    html = b.shell(b.PAGES["index.html"], "index.html")
    assert 'class="hero hero-cinema" data-pin data-pin-length="3"' in html
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
