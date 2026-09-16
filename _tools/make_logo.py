"""Generate the Phoenix logo files from vector sources.

    python _tools/make_logo.py            # writes assets/logo.svg, mark.svg, favicon.svg, icon-180.png
    python _tools/make_logo.py --preview  # also writes a side-by-side against the reference JPEG

The mark (flame and bird) is hand-drawn below as SVG paths in the pixel
space of the only artwork the client supplied, a 532x123 JPEG of a GIF.
The wordmark is set in Michroma (OFL, in _tools/fonts), the closest open
face to the Eurostile Extended the original uses, and converted to outlines
so the SVG needs no font.
"""
import os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
FONT = os.path.join(HERE, "fonts", "Michroma-Regular.ttf")
REFERENCE = os.path.expanduser(r"~\Downloads\Phoenix Sol w Logo gif.jpg")

# ------------------------------------------------------------------ colours
GREY = "#5A5753"        # PHOENIX, and the default for currentColor
ORANGE = "#E8632A"      # SOLUTIONS
FLAME = [("0", "#F6762F"), ("0.5", "#EA5F28"), ("0.78", "#C4502D"), ("1", "#8E3A28")]
WING = [("0", "#A9532F"), ("0.55", "#7E3A2B"), ("1", "#4A2A22")]

# ------------------------------------------------------------------ the mark
# Drawn in the reference image's pixel space: x 0..80, y 10..106.
BODY = (
    # neck, left side, up to the left tongue
    "M 9 74 C 6 68 5 62 6 55 "
    "C 7 47 10 39 14 30 C 15 38 18 45 21 51 "           # left tongue up and down
    "C 19 42 25 24 34 11 "                               # central tongue up
    "C 38 20 43 34 43 53 "                               # central tongue down
    "C 44 48 47 44 51 39 C 52 48 54 55 57 60 "           # right tongue up and down
    "C 58 61 59 63 60 65 C 59 70 58 76 56 80 "           # beak tip and hook
    "C 55 75 52 70 48 66 "                               # inside of the hook
    "C 44 64 40 65 35 67 "                               # crown of the head
    "C 30 68 25 69 20 70 C 16 71 12 72 9 74 Z"           # back to the neck
)
LICKS = (
    "M 21 12 C 25 15 27 20 25 26 C 21 23 20 17 21 12 Z "       # above left of the tip
    "M 44 30 C 48 32 50 36 48 40 C 45 37 44 34 44 30 Z "       # right of the tip
    "M 0 55 C 3 58 4 63 2 68 C -1 65 -2 60 0 55 Z"             # far left, cut off in the source
)
WING_PATH = (
    "M 5 75 C 12 76 20 79 30 83 C 36 86 40 90 41 94 "          # top edge to the upper tip
    "C 37 93 33 92 30 91 C 32 95 33 98 32 102 "                # upper feather back, middle tip
    "C 28 99 25 96 22 94 C 22 98 21 102 18 105 "               # middle feather back, lower tip
    "C 13 101 9 94 7 87 C 6 83 5 79 5 75 Z"                    # left edge up
)
CREST = "M 20 77 C 24 76 28 76 31 78"                          # the light feather line on the cheek
BROW = "M 29 64.5 C 31 62.5 34 62.5 36 64 C 34 65.5 31 65.5 29 64.5 Z"   # the closed-lid slit, cut out of the body
FEATHERS = "M 9 80 C 14 82 19 85 23 89 M 27 90 C 30 92 32 95 33 98"       # the light lines in the wing

MARK_VIEW = (-2, 10, 64, 96)   # x, y, w, h


def gradient(gid, stops, x1, y1, x2, y2):
    s = "".join('<stop offset="%s" stop-color="%s"/>' % st for st in stops)
    return ('<linearGradient id="%s" gradientUnits="userSpaceOnUse" x1="%s" y1="%s" x2="%s" y2="%s">%s'
            '</linearGradient>' % (gid, x1, y1, x2, y2, s))


def mark_defs(prefix=""):
    return "<defs>%s%s</defs>" % (
        gradient(prefix + "flame", FLAME, 30, 11, 30, 80),
        gradient(prefix + "wing", WING, 20, 75, 20, 105))


def mark_body(prefix=""):
    return ('<path fill="url(#%sflame)" fill-rule="evenodd" d="%s %s"/>'
            '<path fill="url(#%sflame)" d="%s"/>'
            '<path fill="url(#%swing)" d="%s"/>'
            '<path fill="none" stroke="#F1C4A3" stroke-width="1.2" stroke-linecap="round" d="%s"/>'
            '<path fill="none" stroke="#D9A07C" stroke-width="1" stroke-linecap="round" d="%s"/>'
            '<circle cx="36.5" cy="72.5" r="1.3" fill="#C46A3A"/>'
            % (prefix, BODY, BROW, prefix, LICKS, prefix, WING_PATH, CREST, FEATHERS))


# --------------------------------------------------------------- the wordmark
class Face:
    def __init__(self, path):
        self.font = TTFont(path)
        self.gs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.cap = self.font["OS/2"].sCapHeight
        self.hmtx = self.font["hmtx"]

    def word(self, text, x, baseline, cap_px, width_px):
        """Outline `text` with the cap height `cap_px`, tracked to fill `width_px`."""
        scale = cap_px / self.cap
        glyphs = [self.cmap[ord(c)] for c in text]
        # ink width without tracking: first glyph's left bearing to last glyph's right edge
        adv = sum(self.hmtx[g][0] for g in glyphs)
        first = BoundsPen(self.gs); self.gs[glyphs[0]].draw(first)
        last = BoundsPen(self.gs); self.gs[glyphs[-1]].draw(last)
        lsb = first.bounds[0]
        rsb = self.hmtx[glyphs[-1]][0] - last.bounds[2]
        ink = (adv - lsb - rsb) * scale
        track = (width_px - ink) / (len(glyphs) - 1)
        d = []
        pen_x = x - lsb * scale
        for g in glyphs:
            pen = SVGPathPen(self.gs, ntos=lambda v: ("%.2f" % v).rstrip("0").rstrip("."))
            t = TransformPen(pen, (scale, 0, 0, -scale, pen_x, baseline))
            self.gs[g].draw(t)
            d.append(pen.getCommands())
            pen_x += self.hmtx[g][0] * scale + track
        return " ".join(d)


def wordmark_paths(face):
    # Measured from the reference: PHOENIX x 79..362, cap 38..70; SOLUTIONS x 74..362, cap 81..102.
    phoenix = face.word("PHOENIX", 79, 70.5, 33, 283)
    solutions = face.word("SOLUTIONS", 74, 102.5, 22, 288)
    return ('<path fill="currentColor" d="%s"/>' % phoenix,
            '<path fill="%s" d="%s"/>' % (ORANGE, solutions))


# ------------------------------------------------------------------ the files
def logo_svg(face):
    p, s = wordmark_paths(face)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 10 384 96" width="384" height="96" '
            'role="img" aria-label="Phoenix Solutions" color="%s">%s%s%s%s</svg>'
            % (GREY, mark_defs(), mark_body(), p, s))


def mark_svg():
    x, y, w, h = MARK_VIEW
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s %s %s %s" role="img" aria-label="Phoenix">'
            '%s%s</svg>' % (x, y, w, h, mark_defs(), mark_body()))


def favicon_svg():
    # The mark on the site's ink tile, so it holds up at 16px on a light tab strip.
    x, y, w, h = MARK_VIEW
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Phoenix">'
            '<rect width="64" height="64" rx="12" fill="#1F1A17"/>'
            '<g transform="translate(6 4) scale(0.58)"><g transform="translate(%s %s)">%s%s</g></g></svg>'
            % (-x, -y, mark_defs(), mark_body()))


def write(name, text):
    with open(os.path.join(ASSETS, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    print("wrote assets/" + name)


def png(svg_text, path, width):
    import resvg_py
    data = resvg_py.svg_to_bytes(svg_string=svg_text, width=width)
    with open(path, "wb") as f:
        f.write(bytes(data))
    print("wrote", os.path.relpath(path, ROOT))


def preview(face):
    """Reference on top, vector below, and a 50% overlay, at 3x."""
    from PIL import Image
    import io, resvg_py
    ref = Image.open(REFERENCE).convert("RGBA")
    S = 3
    ref = ref.resize((ref.width * S, ref.height * S), Image.LANCZOS)
    # render the lockup in the reference's own pixel frame
    p, s = wordmark_paths(face)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 532 123" width="%d" height="%d" color="%s">'
           '<rect width="532" height="123" fill="white"/>%s%s%s%s</svg>'
           % (532 * S, 123 * S, GREY, mark_defs(), mark_body(), p, s))
    vec = Image.open(io.BytesIO(bytes(resvg_py.svg_to_bytes(svg_string=svg, width=532 * S)))).convert("RGBA")
    over = Image.blend(ref, vec, 0.5)
    sheet = Image.new("RGBA", (ref.width, ref.height * 3 + 20), "white")
    sheet.paste(ref, (0, 0)); sheet.paste(vec, (0, ref.height + 10)); sheet.paste(over, (0, ref.height * 2 + 20))
    out = os.path.join(os.environ.get("TMP", HERE), "logo", "preview.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print("preview", out)


def main():
    face = Face(FONT)
    if "--preview" in sys.argv:
        preview(face)
        if "--only" in sys.argv:
            return
    write("logo.svg", logo_svg(face))
    write("mark.svg", mark_svg())
    write("favicon.svg", favicon_svg())
    png(favicon_svg(), os.path.join(ASSETS, "icon-180.png"), 180)


if __name__ == "__main__":
    main()
