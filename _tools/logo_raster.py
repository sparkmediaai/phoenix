"""The header logo from Dave's high-resolution rendering.

    python _tools/logo_raster.py

Reads _tools/brand/phoenix-logo.png (transparent, grey PHOENIX, orange
SOLUTIONS), trims the transparent margins, and writes one 450px-wide WebP:
assets/logo-header.webp, with the grey wordmark recoloured to the header's
pale text (#E6DDD1) so it reads on the ink header. The flame and the orange
word are untouched.

The header draws the mark 44px tall, about 149px wide, so 450px covers a 3x
display and the old 900px covered a 6x one that does not exist. Nothing on
the site asks for the logo on a light background, so the as-supplied
rendering is not written at all: an unreferenced file in a public repo is a
file somebody later assumes is used.
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
