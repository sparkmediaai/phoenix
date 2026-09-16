import importlib.util, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_tool():
    spec = importlib.util.spec_from_file_location("cut_images", os.path.join(ROOT, "_tools", "cut_images.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_jpg(path, size=(3000, 2000)):
    Image.new("RGB", size, (200, 90, 40)).save(path, "JPEG")
    return path


def test_cut_image_writes_two_widths(tmp_path):
    t = load_tool()
    src = make_jpg(tmp_path / "src")
    out = t.cut_image(str(src), str(tmp_path), "panel")
    names = sorted(os.path.basename(p) for p in out)
    assert names == ["panel-1600.webp", "panel-800.webp"]
    assert Image.open(tmp_path / "panel-1600.webp").size == (1600, 1067)
    assert Image.open(tmp_path / "panel-800.webp").size == (800, 533)


def test_cut_image_crops_first(tmp_path):
    t = load_tool()
    src = make_jpg(tmp_path / "src")
    t.cut_image(str(src), str(tmp_path), "sq", crop=[500, 0, 2500, 2000])
    assert Image.open(tmp_path / "sq-1600.webp").size == (1600, 1600)


def test_cut_image_never_upscales(tmp_path):
    t = load_tool()
    src = make_jpg(tmp_path / "src", (960, 720))
    out = t.cut_image(str(src), str(tmp_path), "small")
    assert Image.open(tmp_path / "small-1600.webp").size == (960, 720)
    assert Image.open(tmp_path / "small-800.webp").size == (800, 600)


def test_cut_og_is_1200_by_630(tmp_path):
    t = load_tool()
    src = make_jpg(tmp_path / "src")
    t.cut_og(str(src), str(tmp_path / "og.jpg"))
    im = Image.open(tmp_path / "og.jpg")
    assert im.size == (1200, 630) and im.format == "JPEG"


def test_slug():
    t = load_tool()
    assert t.slug("Elevator Glass Cab Operator Panel") == "elevator-glass-cab-operator-panel"
    assert t.slug("[supplier] Factory Automation Remote I_O") == "factory-automation-remote-i-o"
