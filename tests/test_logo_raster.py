import importlib.util, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, *rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_trim_removes_transparent_margins():
    t = load("logo_raster", ("_tools", "logo_raster.py"))
    im = Image.new("RGBA", (100, 60), (0, 0, 0, 0))
    im.paste((90, 90, 90, 255), (20, 10, 70, 40))
    assert t.trim(im).size == (50, 30)


def test_recolor_only_touches_dark_grey_pixels():
    t = load("logo_raster", ("_tools", "logo_raster.py"))
    im = Image.new("RGBA", (3, 1))
    im.putpixel((0, 0), (90, 90, 88, 255))      # wordmark grey: recoloured
    im.putpixel((1, 0), (240, 100, 30, 255))    # flame orange: untouched
    im.putpixel((2, 0), (90, 90, 88, 0))        # transparent: untouched
    out = t.recolor_wordmark(im, (230, 221, 209))
    assert out.getpixel((0, 0)) == (230, 221, 209, 255)
    assert out.getpixel((1, 0)) == (240, 100, 30, 255)
    assert out.getpixel((2, 0))[3] == 0


def test_header_uses_the_raster_logo():
    b = load("build", ("_build", "build.py"))
    html = b.shell(b.PAGES["index.html"], "index.html")
    assert '<img class="logo" src="/assets/logo-header.webp"' in html
    assert 'width="900"' in html and 'alt=""' in html
    assert '<span class="vh">Phoenix Automation Solutions</span>' in html
