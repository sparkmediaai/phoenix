"""The header logo, from the company's own artwork.

    python _tools/logo_raster.py

Reads _tools/brand/phoenix-logo.png: the "Phoenix Automation Solutions, Inc."
lockup, rendered at high resolution from the vector artwork on the company's
December 2024 product mailer and lifted off its white box onto transparency.
Trims the transparent margins and writes assets/logo-header.webp, 450px
wide, with the grey wordmark recoloured to the header's pale text (#E6DDD1)
so it reads on the ink header. The flame and the orange line are untouched.
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "brand", "phoenix-logo.png")
OUT = os.path.join(ROOT, "assets")
WIDTH = 450
PALE = (230, 221, 209)


def trim(im):
    box = im.getchannel("A").getbbox()
    return im.crop(box) if box else im


def recolor_wordmark(im, rgb):
    """Dark, low-saturation, opaque-ish pixels are the grey wordmark."""
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if max(r, g, b) - min(r, g, b) < 40 and max(r, g, b) < 150:
                px[x, y] = (rgb[0], rgb[1], rgb[2], a)
    return im


def scaled(im, width):
    return im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)


def bird(im):
    """The mark alone: everything left of the first fully transparent gap in the lockup."""
    import numpy as np
    cols = np.asarray(im.getchannel("A")).max(0) > 8
    start = int(np.argmax(cols))
    gap = start + int(np.argmin(cols[start:]))          # first empty column after the bird begins
    return trim(im.crop((start, 0, gap, im.height)))


def icon(mark, size, radius):
    """The mark centred on a paper-coloured tile, for the browser tab and the home screen.
    The bird's lower wing is near-black, so it needs a light ground to read."""
    from PIL import ImageDraw
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(tile).rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=(251, 248, 243, 255))
    m = mark.copy()
    m.thumbnail((int(size * 0.72), int(size * 0.72)), Image.LANCZOS)
    tile.alpha_composite(m, ((size - m.width) // 2, (size - m.height) // 2))
    return tile


def run():
    im = trim(Image.open(SRC).convert("RGBA"))
    mark = bird(im)
    m512 = mark.copy()
    m512.thumbnail((512, 512), Image.LANCZOS)
    m512.save(os.path.join(OUT, "mark.webp"), "WEBP", quality=92, method=6)
    icon(mark, 64, 12).save(os.path.join(OUT, "favicon.png"), optimize=True)
    icon(mark, 180, 34).convert("RGB").save(os.path.join(OUT, "icon-180.png"), optimize=True)
    print("wrote assets/mark.webp, favicon.png, icon-180.png  (mark %dx%d)" % mark.size)
    dark = scaled(recolor_wordmark(im, PALE), WIDTH)
    name = "logo-header.webp"
    dark.save(os.path.join(OUT, name), "WEBP", quality=90, method=6)
    p = os.path.join(OUT, name)
    print("wrote assets/%s %dx%d %d KB" % (name, *Image.open(p).size, os.path.getsize(p) // 1024))


if __name__ == "__main__":
    run()
