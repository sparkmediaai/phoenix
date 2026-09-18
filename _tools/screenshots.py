"""Full-page screenshots of the local site, through the Chrome already installed on the machine.

    python _tools/screenshots.py OUT_DIR WIDTH [path ...]      e.g.  ... shots 1360 "" products/hmis/
    (start the local server first: python -m http.server 8792)

Needs `pip install playwright`; no browser download, it drives the installed
Chrome. The page is walked top to bottom so lazy images load, reduced motion
is requested so nothing is mid-animation, and any image that failed to load
is reported. In Git Bash set MSYS_NO_PATHCONV=1 so paths are not rewritten.
"""
import sys, os
from playwright.sync_api import sync_playwright
out, width, paths = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    ctx = b.new_context(viewport={"width": width, "height": 900 if width > 600 else 780}, device_scale_factor=1, reduced_motion="reduce")
    page = ctx.new_page()
    for path in paths:
        page.goto("http://localhost:8792/" + path.lstrip("/"), wait_until="networkidle")
        # walk the page so lazy images load, then wait until every image has settled
        page.evaluate("""async () => {
            const h = document.documentElement.scrollHeight;
            for (let y = 0; y < h; y += 500) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); }
            window.scrollTo(0, 0);
            await Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; })));
        }""")
        page.wait_for_timeout(400)
        broken = page.evaluate("[...document.images].filter(i => !i.naturalWidth).map(i => i.currentSrc || i.src)")
        if broken: print("BROKEN IMAGES on", path, broken)
        name = (path.strip("/").replace("/", "_") or "home") + ("_%d" % width) + ".png"
        page.screenshot(path=os.path.join(out, name), full_page=True)
        print("shot", name)
    b.close()
