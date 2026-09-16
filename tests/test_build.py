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
