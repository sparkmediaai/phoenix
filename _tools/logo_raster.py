"""The header logo from Dave's high-resolution rendering.

    python _tools/logo_raster.py

Reads _tools/brand/phoenix-logo.png (transparent, grey PHOENIX, orange
SOLUTIONS), trims the transparent margins, and writes two 900px-wide WebPs:
assets/logo.webp as supplied, for light backgrounds, and
assets/logo-header.webp with the grey wordmark recoloured to the header's
pale text (#E6DDD1) so it reads on the ink header. The flame and the orange
word are untouched in both.
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(HERE, "brand", "phoenix-logo.png")
OUT = os.path.join(ROOT, "assets")
WIDTH = 900
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


def run():
    im = trim(Image.open(SRC).convert("RGBA"))
    light = scaled(im, WIDTH)
    light.save(os.path.join(OUT, "logo.webp"), "WEBP", quality=90, method=6)
    dark = scaled(recolor_wordmark(im, PALE), WIDTH)
    dark.save(os.path.join(OUT, "logo-header.webp"), "WEBP", quality=90, method=6)
    for n in ("logo.webp", "logo-header.webp"):
        p = os.path.join(OUT, n)
        print("wrote assets/%s %dx%d %d KB" % (n, *Image.open(p).size, os.path.getsize(p) // 1024))


if __name__ == "__main__":
    run()
