"""Every internal link and asset on the site, resolved against the filesystem.

    python _tools/linkcheck.py

Run it after a build, and always after changing where the site lives.

A wrong path does not show up until somebody clicks it, which is a bad way to
find out. This walks the built HTML instead: for each href/src that starts
with "/", work out what file would answer it and check the file is there.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAT = re.compile(r'(?:href|src)="(/[^"#?]*)', re.I)
SRCSET = re.compile(r'srcset="([^"]+)"', re.I)
CSSURL = re.compile(r'url\((["\']?)(/[^)"\']+)\1\)')
SCRIPT = re.compile('<script[^>]*>.*?</script>', re.I | re.S)
# The motion loader's script tag builds src attributes at runtime from an
# array of string literals rather than writing src="...", so it is invisible
# to PAT once SCRIPT has blanked out script bodies. Those literals are the
# one case where a path built at runtime *is* a literal worth checking, so
# they are pulled from the untouched HTML before SCRIPT runs.
VENDOR = re.compile(r'"(/assets/(?:vendor/[^"?]+|motion\.js))')

# Paths the site used to live under. If any of these appear in built HTML the
# site was moved and something was not rebuilt.
STALE = ("/phoenix/",)

pages = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in (".git", "_build", "_tools", ".claude")]
    for f in filenames:
        if f.endswith((".html", ".css")):
            pages.append(os.path.join(dirpath, f))


def resolve(url):
    """The file GitHub Pages would serve for this path."""
    p = url.lstrip("/")
    cand = os.path.join(ROOT, p)
    if url.endswith("/") or os.path.isdir(cand):
        cand = os.path.join(cand, "index.html")
    return cand


missing, checked, stale = [], 0, []
for page in pages:
    raw = open(page, encoding="utf-8", errors="replace").read()
    vendor_urls = set(VENDOR.findall(raw))
    # Script bodies are not markup; a path built at runtime is not a literal.
    text = SCRIPT.sub(" ", raw)
    rel = os.path.relpath(page, ROOT).replace("\\", "/")
    urls = set(PAT.findall(text)) | {u for _, u in CSSURL.findall(text)} | vendor_urls
    for s in SRCSET.findall(text):
        for part in s.split(","):
            bit = part.strip().split(" ")[0]
            if bit.startswith("/"):
                urls.add(bit)
    for u in sorted(urls):
        checked += 1
        if not os.path.exists(resolve(u)):
            missing.append("%s -> %s" % (rel, u))
    for bad in STALE:
        if bad in text:
            stale.append("%s contains %s" % (rel, bad))

print("%d internal references across %d files" % (checked, len(pages)))
if stale:
    print("\nSTALE PATHS:"); [print("  " + s) for s in sorted(set(stale))]
if missing:
    print("\nMISSING TARGETS:"); [print("  " + m) for m in missing]
if not missing and not stale:
    print("all resolve, nothing points at the old address")
sys.exit(1 if (missing or stale) else 0)
