# Phoenix

Prototype site for Phoenix, a wedding and events venue. Built by SparkMedia,
on the same footing as [thevalleyvenues](https://github.com/sparkmediaai/thevalleyvenues).

**Live:** https://phoenix.sparkmedia.ai
**Working notes:** add `?notes` to any page, e.g. `/weddings/?notes`

Every page carries `noindex,nofollow`. That comes off when the client signs
off, not before: a prototype indexed on a real domain competes with their live
site in search results. It comes off by itself when `BASE` in
`_build/build.py` equals `PRODUCTION`, which `set_domain.py` handles.

## Pages are generated, not written

Every page shares one header, one footer and one set of stylesheets, so the
pages are data and the shell is code:

```
python _build/build.py
```

That reads the page table at the bottom of `_build/build.py` and writes the
HTML. Nothing else writes HTML; if you edit `index.html` directly the next
build discards it.

`_build/build.py` also holds the only facts about where the site lives:

```python
URL_ROOT = "/"                              # what internal links point at
BASE = "https://phoenix.sparkmedia.ai/"     # absolute origin, for og: tags
PRODUCTION = "https://phoenix.example/"     # the client's own domain, when known
```

Moving the site to the client's domain is one command:

```
python _build/set_domain.py www.their-domain.com
```

which changes `BASE` and `CNAME` together, rebuilds and link-checks.

| | |
|---|---|
| `_build/build.py` | The shell, the site facts and the page table. |
| `_build/set_domain.py` | Moves the site to a new hostname. |
| `_build/make_social.py` | Placeholder `assets/og.jpg` and `assets/icon-180.png`. Needs Pillow. |
| `_tools/linkcheck.py` | Resolves every internal href, src, srcset and CSS url() against the filesystem. Run it after a build and always after moving the site. |

## Local preview

```
python -m http.server 8792
```

Then http://localhost:8792. The site is written for a domain root, so it will
not work served from a subdirectory.

## Hosting

GitHub Pages, from the `main` branch root of `sparkmediaai/phoenix`. The
custom domain is the `CNAME` file; DNS is one record at Namecheap on
`sparkmedia.ai`:

| Type | Host | Value |
|---|---|---|
| CNAME | `phoenix` | `sparkmediaai.github.io` |

After the record resolves, GitHub Settings > Pages issues a certificate for
the name (a few minutes) and Enforce HTTPS can be ticked.

## The inquiry form

`/inquire/` posts **straight to a GoHighLevel inbound webhook from the
browser**, the same decision The Valley took. `FORM_ENDPOINT` in
`_build/build.py` holds that URL and is empty until the client's GHL
sub-account exists; while it is empty the form shows the contact email instead
of submitting.

Once it is set: the URL is the endpoint's only authentication, GHL bills
Inbound Webhook per execution, and this repo is public. **The honeypot in
`assets/forms.js` is the only thing between a scraper and the invoice; do not
remove it.**

Every rule the CRM depends on is enforced in `assets/forms.js`: the exact
option strings, `guest_count` as a number, phone to E.164, `submitted_at` at
submit. GHL learns key names from one sample payload, so re-fetch the sample in
the workflow trigger whenever a field is added.

## What is still open

- The client brief: full business name, address, spaces and capacities,
  what is included, pricing, the owner's name and a photograph.
- Photography. `assets/img/` is empty; every page has a `hero_img` slot.
- The GoHighLevel webhook URL and the contact inbox (`CONTACT_EMAIL`).
- The production domain (`PRODUCTION`).
- A real `assets/og.jpg` once there is a photograph worth previewing.
