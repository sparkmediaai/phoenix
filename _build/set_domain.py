"""
Move the site to a different hostname.

    python _build/set_domain.py phoenix.sparkmedia.ai
    python _build/set_domain.py www.the-clients-domain.com

Two files know the site's address and they have to agree: BASE in build.py,
which is written into every og:url and og:image, and CNAME, which is what
GitHub Pages serves the site as. Getting one and not the other gives you a
site that loads fine and previews, in every message anybody pastes it into,
under its old name.

So this changes both, rebuilds, and checks the result. It does not touch DNS
and it does not touch URL_ROOT -- the site is written for a domain root and
every internal link is already relative to one.
"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

HOST = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)(\.(?!-)[a-z0-9-]{1,63}(?<!-))+$")


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__.strip())
    host = sys.argv[1].strip().lower().rstrip(".")
    host = re.sub(r"^https?://", "", host).split("/")[0]
    if not HOST.match(host):
        raise SystemExit("that does not look like a hostname: %r" % host)

    build = os.path.join(HERE, "build.py")
    s = open(build, encoding="utf-8").read()
    m = re.search(r'^BASE = "https://([^/"]+)/"$', s, re.M)
    if not m:
        raise SystemExit("could not find BASE in build.py")
    was = m.group(1)
    if was == host:
        print("already set to %s" % host)
    else:
        s = s[:m.start(1)] + host + s[m.end(1):]
        open(build, "w", encoding="utf-8").write(s)
        print("BASE   %s -> %s" % (was, host))

    cname = os.path.join(ROOT, "CNAME")
    old = open(cname, encoding="utf-8").read().strip() if os.path.exists(cname) else "(none)"
    # No trailing newline: GitHub reads the whole file as the hostname and a
    # stray blank line has been known to confuse the domain check.
    open(cname, "w", encoding="utf-8", newline="").write(host)
    print("CNAME  %s -> %s" % (old, host))

    for step in (["python", os.path.join(HERE, "build.py")],
                 ["python", os.path.join(ROOT, "_tools", "linkcheck.py")]):
        print("\n$ " + " ".join(os.path.basename(p) for p in step))
        if subprocess.call(step, cwd=ROOT) != 0:
            raise SystemExit("that step failed; do not push this")

    print("""
Now, in this order:
  1. Commit and push.
  2. Add the DNS record and wait for it to resolve.
  3. GitHub Settings > Pages will pick the new name up from CNAME. Give it a
     few minutes to issue a certificate, then tick Enforce HTTPS.
  4. Leave a redirect at the old address if anything already points there.

If this is a domain the client already uses for email, change only the A,
AAAA and CNAME records. Touching MX takes their mail down with the website.""")


if __name__ == "__main__":
    main()
