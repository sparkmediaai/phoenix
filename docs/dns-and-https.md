# DNS and HTTPS for phoenixautomationsolutions.com

State on 2026-09-24. The site is served by GitHub Pages from `main`; the
domain's DNS is at Bluehost (ns1/ns2.hostmonster.com), where the domain is
parked on the hosting account that also runs Russ's email. Do not unassign
the parked domain in Bluehost: cPanel removes the domain's email accounts
with it.

## The zone as it stands

| Host | Type | Value | Purpose |
|---|---|---|---|
| `@` | A | 185.199.108.153, 185.199.109.153, 185.199.110.153 | GitHub Pages (add 185.199.111.153) |
| `www` | CNAME | sparkmediaai.github.io | GitHub Pages |
| `@` | MX 0 | mail.phoenixautomationsolutions.com | Russ's email, on Bluehost |
| `@` | TXT | `v=spf1 a mx ptr include:hostmonster.com ?all` | SPF for that email |
| `mail`, `webmail`, `cpanel`, `webdisk`, `whm`, `autodiscover`, `autoconfig`, `cpcalendars`, `cpcontacts` | A | 67.20.76.83 | Bluehost / cPanel services |
| `_autodiscover._tcp` | SRV | 0 0 443 autodiscover.hostmonster.com | Mail client autodiscovery |
| `ftp` | CNAME | phoenixautomationsolutions.com | cPanel default |
| `localhost` | A | 127.0.0.1 | cPanel default |

No AAAA, CAA, DKIM or DMARC records exist. No wildcard.

## The certificate problem

GitHub Pages runs a DNS check when a custom domain is saved and, if it
passes, queues a Let's Encrypt request. The check passes for both names
(`GET /repos/sparkmediaai/phoenix/pages/health`), Let's Debug reports no
problems for either name, Bluehost's nameservers answer CAA queries over UDP
and TCP, and the `/.well-known/acme-challenge/` path reaches GitHub on both
names. The queued request has never started: `https_certificate.state` has
read `new` since 22 September, with the custom domain set to the bare
domain and to www alike. Removing and re-adding the domain, and deleting and
re-creating the Pages site, changed nothing. A second site on the account,
sparkmediaai/thevalleyvenues, is stuck in `bad_authz` with clean DNS.
Resolved on 24 September at 10:56: GitHub issued the certificate on its own,
about a day and a half after the request was queued, with no change on our
side. HTTPS enforcement went on at 11:28. If it ever happens again: check the
health API, then wait; the remove/re-add cycles did nothing.

## Plan B: Cloudflare in front

If GitHub Support is slow, move the DNS (only the DNS) to a free Cloudflare
account and proxy the two web records. Cloudflare then terminates HTTPS with
its own certificate within minutes, GitHub keeps serving the pages over
HTTP behind it, and Bluehost keeps hosting the email untouched. It also ends
Bluehost resetting records.

1. Add the domain to Cloudflare. It will import most of the zone; check the
   import against the table above and add anything missing. Every record
   above is needed; the email ones are the ones that matter most.
2. Set the two web records to **Proxied** (orange cloud): `@` A x4 and `www`
   CNAME. Leave every other record **DNS only** (grey cloud), especially
   `mail` and the MX.
3. SSL/TLS mode: **Flexible** while GitHub has no certificate (Cloudflare to
   visitor is https; Cloudflare to GitHub is http). Switch to **Full** the
   day GitHub's certificate finally issues.
4. Turn on **Always Use HTTPS**.
5. At Bluehost (Domains > the domain > Nameservers), replace
   ns1/ns2.hostmonster.com with the two nameservers Cloudflare assigns.
   Propagation takes up to a day; the site and email keep working throughout
   because both sets of nameservers serve the same records.

The site's build does not change for any of this.
