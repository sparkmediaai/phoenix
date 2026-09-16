# Phoenix Automation Solutions

Prototype site for Phoenix Automation Solutions, Inc. of Mokena, Illinois:
HMI, PLC, I/O and custom operator panels for OEM machine builders, run by
Russell Homans. Built by SparkMedia under the September 2026 SOW, Phase 1
(foundation and PACK EXPO readiness), on the same footing as
[thevalleyvenues](https://github.com/sparkmediaai/thevalleyvenues).

**Live:** https://phoenix.sparkmedia.ai
**Working notes:** add `?notes` to any page, e.g. `/for-oems/?notes`
**Deadline:** PACK EXPO International, McCormick Place, 28 September to 1 October 2026.

The navigation is five headers (Machine Builders, Products, Proof, Support, Company), each a menu of pages, plus the Talk to Russ button; all of it is the `NAV` and `CTA` tables in `_build/build.py`. Every page carries `noindex,nofollow`. That comes off when the client signs
off, not before. It comes off by itself when `BASE` in `_build/build.py`
equals `PRODUCTION`, which `set_domain.py` handles.

## The positioning, in one paragraph

Phoenix is the solution and Russell is the value. The supplier stays in the
background. The audience is the OEM machine builder in the United States with
repeatable machine models in the $10,000 to $100,000 range, real annual
volume, and electrical engineers on staff, who needs more than a part number:
a cost target hit, a panel with their name on it, an application that works
first time. The site's job before the show is to make Phoenix credible and
findable, and to qualify the right prospects through a four-question intake.
Sources: the 28 Aug intro call, the 8 Sep PACK EXPO strategy session, and the
signed SOW.

## Pages are generated, not written

Every page shares one header, one footer and one set of stylesheets, so the
pages are data and the shell is code:

```
python _build/build.py
```

That reads the page table in `_build/build.py` and writes the HTML. Nothing
else writes HTML; if you edit `index.html` directly the next build discards it.

| Page | Purpose |
|---|---|
| `/` | Positioning, the two doors (machine builders, products), the three differentiators, the proof, fit and not-fit, how it starts. |
| `/machine-builders/custom-controls/` | What can be built to a customer's print, the hardware families and the engineering services. |
| `/machine-builders/design-win/` | How one approved part carries across a lineup; the pinned four-step path; straight answers. |
| `/machine-builders/industries/` | The three lead industries, then every industry Phoenix controls run in. |
| `/machine-builders/industries/{packaging,residential-elevators,food-equipment}/` | Machines served and the controls on them, one page each. |
| `/products/{hmis,plcs,io-and-communication,cross-reference,datasheets}/` | The catalog side, scaffolded: what each page will list and how to get the numbers until it does. No part numbers are invented. |
| `/proof/case-studies/` | The cab operating panel: problem, what was built, result. |
| `/proof/custom-builds/` | The photograph gallery. |
| `/support/{software,warranty-and-rma}/` | Scaffolded until Russell supplies the downloads and the terms. |
| `/company/{about-russ,supply-chain,certifications,contact}/` | Who Phoenix is. Certifications is empty until Russell approves the wording. |
| `/talk-to-russ/` | The Talk to Russ form: what you build, how many a year, what controls now, then contact. |
| `/pack-expo/` | The QR-code landing for the show floor. |
| `/for-oems/`, `/capabilities/`, `/industries/`, `/about/`, `/start/` | Stubs that send the visitor to the page's new address. |

`_build/build.py` also holds the only facts about where the site lives:

```python
URL_ROOT = "/"                                        # what internal links point at
BASE = "https://phoenix.sparkmedia.ai/"               # absolute origin, for og: tags
PRODUCTION = "https://phoenixautomationsolutions.example/"   # the client's domain, when known
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
| `_tools/logo_raster.py` | Cuts the header logo from `_tools/brand/phoenix-logo.png`, Dave's high-resolution rendering, into a pale-wordmark `assets/logo-header.webp` at 450px, three times the width the header draws it at. |
| `_tools/make_logo.py` | Draws the logo. The flame-and-bird mark is hand-drawn SVG paths; the wordmark is Michroma (OFL, in `_tools/fonts`) converted to outlines. Writes `assets/logo.svg`, `mark.svg`, `favicon.svg` and `icon-180.png`, which now serve the favicon and touch icon only; `--preview` renders a side-by-side against the client's 532px JPEG, the only artwork supplied. Needs `pip install fonttools resvg-py pillow`. |
| `_tools/linkcheck.py` | Resolves every internal href, src, srcset and CSS url() against the filesystem. Run it after a build and always after moving the site. |
| `_tools/cut_images.py` | Cuts the client's originals into `assets/img/`, `assets/video/` and `assets/og.jpg` per `_tools/image-picks.json`. `--images`, `--video` and `--og` run one part on its own; with no flag it runs all three. |
| `_tools/budget.py` | Sums each page's HTML plus its same-origin CSS, JS and images (largest srcset candidate; the video itself is excluded, since it is `preload="none"`) and checks the total against the weight budgets in the design spec. |

## Motion

Motion is declared, not written. The build puts data attributes on elements
(`data-reveal`, `data-parallax`, `data-pin` with `data-step`, `data-draw`,
`data-count`) and `assets/motion.js` animates them with GSAP 3.15 and
ScrollTrigger, vendored in `assets/vendor/`. An inline gate in the shell adds
`motion` to `<html>` only when the visitor does not prefer reduced motion,
and the loader takes it off again if a script fails or `motion.js` has not
reported in within four seconds. The hidden initial states in
`assets/motion.css` are scoped to `html.motion`, so with JavaScript off, with
reduced motion on, or after a failed load, every page is the static site.

The PACK EXPO landing and the 404 opt out with `motion=False` in the page
table: they load no motion script at all.

Photographs are cut from `_originals/` by `_tools/cut_images.py` according
to `_tools/image-picks.json`; the hero loop is cut by the same tool. No
committed file names the supplier; a grep for the supplier's name over the
repo must stay empty. `python _tools/budget.py` checks every page against
the weight budgets in the design spec.

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

## The intake form

`/start/` posts **straight to a GoHighLevel inbound webhook from the
browser**, the same decision The Valley took. `FORM_ENDPOINT` in
`_build/build.py` holds that URL and is empty until Phoenix's GHL sub-account
exists; while it is empty the form shows the contact email instead of
submitting.

Once it is set: the URL is the endpoint's only authentication, GHL bills
Inbound Webhook per execution, and this repo is public. **The honeypot in
`assets/forms.js` is the only thing between a scraper and the invoice; do not
remove it.**

The fields follow the SOW's qualification list: `machine_type`,
`annual_volume`, `current_controls`, `application`, `spec_link`, `company`,
`role`, `first_name`, `last_name`, `email`, `phone`, plus `source` and
`submitted_at`. The option strings for `annual_volume` and `current_controls`
live in both `_build/build.py` and `assets/forms.js` and must match. GHL learns
key names from one sample payload, so re-fetch the sample in the workflow
trigger whenever a field is added.

## Photography

The client's photographs are in a shared Google Drive folder ("Phoenix
Solutions"): glass cab operator panels, hall stations, a control panel, remote
I/O, a robot assembly cell, soil-sampling rigs, water treatment plants, pad
printing and print curing, the factory, and the logo. Originals go in
`_originals/` (ignored by git); the cut, resized WebP frames go in
`assets/img/` and are committed.

## What is still open

- Russell's sign-off on every technical claim (the SOW makes him responsible for accuracy).
- Russell's bio, credentials list and a photograph. He offered the list on 28 Aug.
- The one phone number and the one email address (`PHONE`, `CONTACT_EMAIL`).
- The street address in Mokena, for the footer and the Google Business Profile.
- The production domain (`PRODUCTION`).
- The GoHighLevel webhook URL once the sub-account exists.
- Photographs cut from the Drive folder into `assets/img/`, and a real `assets/og.jpg`.
- Qualification thresholds for the intake, agreed with Russell.
- A LinkedIn company page and Google Business Profile link in the footer once they exist.
- Russell's sign-off on the cost figures shown in the homepage proof and About timeline.
- Whether factory footage may be used at all.
- His photograph replaces the portrait placeholder on About.
- Whether the cab-panel photographs showing the elevator customer's own splash screen may be used; they were left out of the cut.
