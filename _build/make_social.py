"""
Draw the placeholder social card and touch icon.

    python _build/make_social.py

Writes assets/og.jpg (1200x630, what a link preview shows) and
assets/icon-180.png (the iOS home-screen icon). Both are the house colour
with the wordmark on it until there is a photograph worth using; when there
is, replace og.jpg with a real frame and leave this script for the icon.

Needs Pillow:  pip install Pillow
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

INK = (31, 26, 23)        # #1F1A17
EMBER = (196, 84, 44)     # #C4542C
SAND = (243, 236, 226)    # #F3ECE2


def font(size):
    for name in ("georgia.ttf", "Georgia.ttf", "times.ttf", "DejaVuSerif.ttf"):
        for d in (os.path.join(os.environ.get("WINDIR", ""), "Fonts"), "/usr/share/fonts/truetype/dejavu"):
            p = os.path.join(d, name)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def flame(draw, cx, cy, r, fill):
    """A simple flame: a teardrop with a notch. Matches favicon.svg in spirit."""
    pts = [(cx, cy - r), (cx + r * 0.75, cy - r * 0.1), (cx + r * 0.55, cy + r * 0.8),
           (cx, cy + r), (cx - r * 0.55, cy + r * 0.8), (cx - r * 0.75, cy - r * 0.1)]
    draw.polygon(pts, fill=fill)


def og():
    im = Image.new("RGB", (1200, 630), INK)
    d = ImageDraw.Draw(im)
    flame(d, 600, 250, 110, EMBER)
    f = font(84)
    text = "Phoenix"
    w = d.textlength(text, font=f)
    d.text(((1200 - w) / 2, 380), text, font=f, fill=SAND)
    f2 = font(30)
    sub = "A Venue Worth the Journey."
    w2 = d.textlength(sub, font=f2)
    d.text(((1200 - w2) / 2, 490), sub, font=f2, fill=(200, 190, 178))
    im.save(os.path.join(ASSETS, "og.jpg"), quality=88, optimize=True)
    print("assets/og.jpg")


def icon():
    im = Image.new("RGB", (180, 180), INK)
    d = ImageDraw.Draw(im)
    flame(d, 90, 92, 62, EMBER)
    im.save(os.path.join(ASSETS, "icon-180.png"), optimize=True)
    print("assets/icon-180.png")


if __name__ == "__main__":
    og()
    icon()
