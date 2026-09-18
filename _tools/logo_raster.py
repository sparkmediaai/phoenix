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


def run():
    im = trim(Image.open(SRC).convert("RGBA"))
    dark = scaled(recolor_wordmark(im, PALE), WIDTH)
    name = "logo-header.webp"
    dark.save(os.path.join(OUT, name), "WEBP", quality=90, method=6)
    p = os.path.join(OUT, name)
    print("wrote assets/%s %dx%d %d KB" % (name, *Image.open(p).size, os.path.getsize(p) // 1024))


if __name__ == "__main__":
    run()
