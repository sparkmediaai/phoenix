"""Page weight against the budgets in the design spec.

    python _tools/budget.py

Sums each page's HTML and every same-origin asset it references (stylesheets,
scripts, images including srcset candidates at the largest width, the video
poster; not the video itself, which is preload="none"). Exits 1 if any page
is over budget.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUDGET = {"index.html": 1_500_000, "pack-expo/index.html": 400_000}
DEFAULT = 1_000_000
PAGES = ["index.html", "for-oems/index.html", "capabilities/index.html", "industries/index.html",
         "about/index.html", "pack-expo/index.html", "start/index.html", "404.html"]
REF = re.compile(r'(?:href|src)="(/assets/[^"?]+)|srcset="([^"]+)|"(/assets/vendor/[^"?]+|/assets/motion\.js)')


def size(rel):
    path = os.path.join(ROOT, rel.lstrip("/"))
    return os.path.getsize(path) if os.path.exists(path) else 0


def weigh(page):
    html = open(os.path.join(ROOT, page), encoding="utf-8").read()
    total = len(html.encode("utf-8"))
    seen = set()
    for m in REF.finditer(html):
        if m.group(2):
            cands = [c.strip().split()[0] for c in m.group(2).split(",")]
            rel = cands[-1]
        else:
            rel = m.group(1) or m.group(3)
        if rel and rel not in seen and not rel.endswith((".webm", ".mp4")):
            seen.add(rel)
            total += size(rel)
    return total


def main():
    bad = 0
    for page in PAGES:
        total, budget = weigh(page), BUDGET.get(page, DEFAULT)
        flag = "" if total <= budget else "   OVER"
        print("%-28s %8.0f KB of %5.0f KB%s" % (page, total / 1024, budget / 1024, flag))
        bad |= total > budget
    for name in ("hero.webm", "hero.mp4"):
        rel = "/assets/video/" + name
        s = size(rel)
        print("%-28s %8.0f KB of  2929 KB%s" % (name, s / 1024, "" if s <= 3_000_000 else "   OVER"))
        bad |= s > 3_000_000
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
