"""Product photographs for the catalog pages, cut from the manufacturer's brochures.

    python _tools/product_images.py            # writes assets/img/<name>-1600.webp and -800.webp
    python _tools/product_images.py --preview  # also writes a contact sheet to the temp folder

The brochures live in _originals/brochures/ (git-ignored). Each pick names a
PDF, a page and the index of the image on that page (the same ordering
find_images() prints), a crop inside that image, and a list of fixes.

The renders carry the manufacturer's name on the bezel or on a label. The
site does not name the manufacturer, so each fix paints that lettering out:

    ("bezel", box)  light lettering on a dark bezel: inpaint the bright,
                    unsaturated pixels inside the box
    ("label", box)  dark lettering on a white label: inpaint the dark pixels
    ("fill", box)   inpaint the whole box

Boxes are (left, top, right, bottom) in pixels of the uncropped image. The
long-term fix is unbranded or Phoenix-bezel renders from the factory; this
tool is the stop-gap, and its output is only ever shown at card size.
"""
import io, os, sys
import numpy as np
import cv2
import pypdfium2 as pdfium
import pypdfium2.raw as raw
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BROCHURES = os.path.join(ROOT, "_originals", "brochures")
OUT = os.path.join(ROOT, "assets", "img")
SCALE = 4

BROCHURE = "Brochure_feb_2025.pdf"
PICKS = [
    dict(name="product-basic-hmi", pdf=BROCHURE, page=12, k=0, crop=(40, 560, 951, 1400),
         fixes=[("bezel", (222, 1138, 312, 1202))]),
    dict(name="product-advanced-hmi", pdf=BROCHURE, page=17, k=0, crop=None,
         fixes=[("bezel", (228, 508, 330, 560)), ("bezel", (640, 692, 730, 740)), ("bezel", (232, 812, 306, 850))]),
    dict(name="product-rugged-hmi", pdf="fp6-datasheet.pdf", page=1, embedded=1, crop=None, fixes=[]),
    dict(name="product-web-panel", pdf=BROCHURE, page=30, k=1, crop=None,
         fixes=[("bezel", (150, 428, 232, 472))]),
    dict(name="product-eco-plc", pdf="FL004.pdf", page=1, k=0, crop=None, fixes=[], background="lime",
         post_white=[(0, 665, 37, 775)]),      # a streak of the backdrop beside the lower terminal block
    dict(name="product-standard-plc", pdf=BROCHURE, page=8, k=0, crop=(0, 470, 841, 1420),
         fixes=[("label", (405, 870, 452, 1000))]),
    dict(name="product-plc-lineup", pdf=BROCHURE, page=5, k=0, crop=None,
         fixes=[("label", (1126, 332, 1204, 612))]),
    dict(name="product-hmi-plc", pdf="ds-fp2070tn-e.pdf", page=1, k=0, crop=None,
         fixes=[("bezel", (318, 648, 412, 698))]),
    dict(name="product-field-io", pdf=BROCHURE, page=35, k=0, crop=(40, 570, 610, 1580), fixes=[]),
    dict(name="product-ethercat-io", pdf="Ethercat IO Module.pdf", page=1, k=0, crop=(0, 10, 787, 1155), fixes=[]),
    dict(name="product-gateway", pdf=BROCHURE, page=37, k=0, crop=None,
         fixes=[("fill", (128, 292, 270, 324))]),
]


def find_images(pdf_path, page_no):
    """The sizeable images on a page, as rendered crops, in the order this tool indexes them."""
    pdf = pdfium.PdfDocument(pdf_path)
    page = pdf[page_no - 1]
    W, H = page.get_size()
    boxes = []
    for obj in page.get_objects(filter=[raw.FPDF_PAGEOBJ_IMAGE], max_depth=6):
        l, b, r, t = obj.get_bounds()
        l, b, r, t = max(0, l), max(0, b), min(W, r), min(H, t)
        w, h = r - l, t - b
        if w < 90 or h < 70 or (w > W * 0.9 and h > H * 0.55):
            continue
        boxes.append((l, b, r, t))
    im = page.render(scale=SCALE).to_pil().convert("RGB")
    crops = []
    for l, b, r, t in boxes:
        c = im.crop((int(l * SCALE), int((H - t) * SCALE), int(r * SCALE), int((H - b) * SCALE)))
        if c.width >= 300 and c.height >= 240:
            crops.append(c)
    return crops


def embedded_image(pdf_path, page_no, index):
    """An image taken straight out of the PDF, flattened onto white."""
    from pypdf import PdfReader
    data = list(PdfReader(pdf_path).pages[page_no - 1].images)[index].data
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    flat = Image.new("RGBA", im.size, (255, 255, 255, 255))
    flat.alpha_composite(im)
    return flat.convert("RGB")


def retouch(im, fixes):
    a = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)
    for kind, (x0, y0, x1, y1) in fixes:
        roi = a[y0:y1, x0:x1]
        lum = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY).astype(int)
        sat = roi.max(-1).astype(int) - roi.min(-1).astype(int)
        if kind == "bezel":
            base = int(np.percentile(lum, 30))
            m = (lum > base + 28) & (sat < 70)
        elif kind == "label":
            m = lum < 165
        else:
            m = np.ones(lum.shape, bool)
        mask = np.zeros(a.shape[:2], np.uint8)
        mask[y0:y1, x0:x1] = m.astype(np.uint8) * 255
        mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=1)
        a = cv2.inpaint(a, mask, 5, cv2.INPAINT_TELEA)
    return Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB))


def lime_to_white(im):
    """The eco PLC is photographed on a lime gradient; lift it onto white.
    The backdrop is a bright yellow-green; the terminal blocks are a darker blue-green and stay."""
    a = np.asarray(im).astype(np.uint8)
    hsv = cv2.cvtColor(cv2.cvtColor(a, cv2.COLOR_RGB2BGR), cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    bg = ((h >= 22) & (h <= 48) & (s > 60) & (v > 120)) | ((s < 40) & (v > 225))
    # Keep only the product itself: open the foreground so thin leftovers of the
    # backdrop's darker swoosh detach, keep the largest piece, and grow it back.
    fg = (~bg).astype(np.uint8)
    opened = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(opened)
    if n > 1:
        keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        body = cv2.dilate((labels == keep).astype(np.uint8), np.ones((13, 13), np.uint8))
        bg = bg | (body == 0)
    m = bg.astype(np.uint8) * 255
    m = cv2.GaussianBlur(m, (0, 0), 1.2).astype(float)[..., None] / 255.0
    out = a.astype(float) * (1 - m) + 255.0 * m
    return Image.fromarray(out.round().astype(np.uint8))


def cutout_from_white(im, tol=14, shrink=1):
    """Transparent background for a render on white: only the white that touches
    the border goes, so white labels and screens inside the product stay."""
    a = np.asarray(im.convert("RGB")).copy()
    h, w = a.shape[:2]
    near_white = (a.min(-1) >= 255 - tol).astype(np.uint8)
    mask = np.zeros((h + 2, w + 2), np.uint8)
    canvas = near_white.copy()
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        if canvas[seed[1], seed[0]] == 1:
            cv2.floodFill(canvas, mask, seed, 2)
    alpha = np.where(canvas == 2, 0, 255).astype(np.uint8)
    # shrink eats the pale anti-aliased rim that would glow on the dark hero
    alpha = cv2.GaussianBlur(cv2.erode(alpha, np.ones((3, 3), np.uint8), iterations=shrink), (0, 0), 0.9)
    return Image.fromarray(np.dstack([a, alpha]), "RGBA")


def hero_cutouts():
    """Three products on transparency, for the catalog pages' hero bands."""
    from pypdf import PdfReader
    out = []
    data = list(PdfReader(os.path.join(BROCHURES, "fp6-datasheet.pdf")).pages[0].images)[1].data
    out.append(("hero-hmi", Image.open(io.BytesIO(data)).convert("RGBA")))
    eco = build(next(p for p in PICKS if p["name"] == "product-eco-plc"))
    out.append(("hero-plc", cutout_from_white(eco, shrink=2)))
    fio = find_images(os.path.join(BROCHURES, BROCHURE), 35)[0].crop((40, 570, 610, 1490))
    out.append(("hero-io", cutout_from_white(fio, tol=40, shrink=4)))
    for name, im in out:
        box = im.getchannel("A").getbbox()
        im = im.crop(box)
        if im.height > 900:
            im = im.resize((round(im.width * 900 / im.height), 900), Image.LANCZOS)
        p = os.path.join(OUT, name + ".webp")
        im.save(p, "WEBP", quality=88, method=6)
        print("wrote assets/img/%s.webp  %dx%d  %d KB" % (name, im.width, im.height, os.path.getsize(p) // 1024))
    return out


def trim_white(im, pad=24):
    a = np.asarray(im.convert("L"))
    ys, xs = np.where(a < 246)
    if not len(xs):
        return im
    box = (max(0, xs.min() - pad), max(0, ys.min() - pad), min(im.width, xs.max() + pad), min(im.height, ys.max() + pad))
    return im.crop(box)


def build(pick):
    path = os.path.join(BROCHURES, pick["pdf"])
    if "embedded" in pick:
        im = embedded_image(path, pick["page"], pick["embedded"])
    else:
        im = find_images(path, pick["page"])[pick["k"]]
    im = retouch(im, pick["fixes"])
    if pick.get("crop"):
        im = im.crop(pick["crop"])
    if pick.get("background") == "lime":
        im = lime_to_white(im)
    im = trim_white(im)
    for box in pick.get("post_white", []):
        im.paste((255, 255, 255), box)
    return im


def save(im, name):
    os.makedirs(OUT, exist_ok=True)
    for w in (1600, 800):
        frame = im if im.width <= w else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        p = os.path.join(OUT, "%s-%d.webp" % (name, w))
        frame.save(p, "WEBP", quality=84, method=6)
    print("wrote assets/img/%s-{1600,800}.webp  %dx%d  %d KB" % (name, im.width, im.height, os.path.getsize(p) // 1024))


def main():
    built = []
    for pick in PICKS:
        im = build(pick)
        save(im, pick["name"])
        built.append((pick["name"], im))
    heroes = hero_cutouts()
    if "--preview" in sys.argv:
        for name, im in heroes:
            dark = Image.new("RGBA", im.size, (31, 26, 23, 255)); dark.alpha_composite(im)
            built.append((name, dark.convert("RGB")))
        cell = 420
        sheet = Image.new("RGB", (cell * 4, cell * ((len(built) + 3) // 4)), "white")
        for i, (name, im) in enumerate(built):
            t = im.copy(); t.thumbnail((cell - 16, cell - 16))
            sheet.paste(t, ((i % 4) * cell + 8, (i // 4) * cell + 8))
        out = os.path.join(os.environ.get("TMP", HERE), "product_images_preview.jpg")
        sheet.save(out, quality=88)
        print("preview", out)


if __name__ == "__main__":
    main()
