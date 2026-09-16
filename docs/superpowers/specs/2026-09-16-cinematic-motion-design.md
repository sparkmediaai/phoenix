# Phoenix: cinematic motion and imagery

Design spec, 16 September 2026. Approved by Dave McCormick in conversation the same day.

## Goal

Keep the current ink-and-ember editorial design and typography, and add bold,
cinematic motion and real imagery throughout, in time for PACK EXPO
International (28 September to 1 October 2026). The site must still read as
an engineer speaking to engineers, vet the OEM before Russell gets on a call,
and keep the supplier invisible.

Sources: the 28 Aug intro call, the 8 Sep PACK EXPO strategy session, the
signed SOW, and the client's Google Drive folder "Phoenix Solutions" (38
items: photographs of installations and three videos of the supplier's
factory in India).

## Constraints that shape everything

- **Russell is the value; the supplier stays in the background.** No frame,
  caption or alt text names the supplier. Factory footage is usable only where
  no signage, badge or document shows the supplier's name.
- **Pages are data, the shell is code.** All motion is declared through data
  attributes the build script writes; nothing is hand-edited into HTML.
- **Progressive enhancement.** Every page renders complete with JavaScript
  off. With `prefers-reduced-motion: reduce` the motion script is not loaded
  at all and the page is the static site.
- **The PACK EXPO landing is scanned on phones on a crowded show floor.** It
  gets the lightest treatment and the strictest budget.
- **Accessibility.** Initial hidden states use only `opacity` and
  `transform`, never `visibility` or `display`, so assistive technology reads
  every page in document order. Pinned sections stay in DOM order.

## 1. The motion engine

- GSAP 3 core and the ScrollTrigger plugin, vendored as minified files in
  `assets/vendor/` (about 40 KB gzipped together). No CDN.
- One script, `assets/motion.js`, loaded `defer` after the vendor files, only
  when `matchMedia("(prefers-reduced-motion: no-preference)")` matches.
  The shell inserts the three script tags through a small inline gate so
  reduced-motion visitors download nothing extra.
- `motion.js` reads these attributes and nothing else:

  | Attribute | Effect |
  |---|---|
  | `data-reveal` | Fade and rise into place when the element enters the viewport. `data-reveal="stagger"` on a parent staggers its children. |
  | `data-parallax="0.2"` | Background layer moves at the given fraction of scroll speed. |
  | `data-pin` | Section pins for `data-pin-length` viewport heights while its `[data-step]` children play in sequence. |
  | `data-draw` | An SVG whose `path` elements draw themselves with the scroll position. |
  | `data-count="2500"` | A number counts up from 0 (or `data-count-from`) when it enters the viewport, with `data-count-prefix` and `data-count-suffix` for `$` and `units`. |

- The build script gains helpers (`reveal()`, `pinned()`, `figure()`) so the
  page table declares motion without repeating attribute strings.
- The `html.js` class already set by the shell scopes the initial hidden
  states in CSS: `html.js.motion [data-reveal] { opacity: 0 }` where
  `motion` is added by the inline gate. No JavaScript, or reduced motion,
  means no class and no hidden state.

## 2. Homepage hero

- Full-viewport hero (`min-height: 100svh`) with a muted, looping,
  `playsinline` video background: an 8-second cut from the robot assembly
  cell and factory footage, 1280 px wide, WebM (VP9) and H.264 MP4, under
  3 MB each, `preload="none"`, with a WebP poster preloaded for LCP.
- Phones (`max-width: 767px`) and reduced-motion visitors get the poster
  only; the video element is not given a source.
- Pinned for two viewport heights. Sequence: the headline holds, the footage
  darkens under a gradient, and three proofs arrive in turn, each a
  `[data-step]`: engineered to the target; a panel with your name on it; an
  engineer on your first application.
- The cost story from the 8 Sep call becomes an animated figure directly
  below the hero: a `$1,000` panel re-engineered to `$350` at `2,500`
  units, using `data-count`. Russell signs off the numbers before launch, as
  the SOW requires for every technical claim.

## 3. Inner pages

- **For OEMs.** The four-step OEM path becomes a pinned sequence. Beside the
  steps, a hand-drawn SVG of the controls topology (HMI, PLC, I/O, network)
  draws itself with `data-draw`, one subsystem per step.
- **Capabilities.** Hardware family cards carry Drive photographs with a
  slow parallax on scroll and a hover lift. The engineering services list
  staggers in.
- **Industries.** A staggered photo mosaic. Every tile is a real
  installation from the Drive with alt text from Russell's own file names:
  elevators (glass cab operator panels, hall stations), water and waste water
  treatment, agriculture (soil sampling rigs), manufacturing (robot cell,
  barcode verification, die cutter, pad printing, print curing), medical
  (knee rehabilitation machine), private label product.
- **About.** A portrait placeholder until Russell's photograph arrives, a
  twenty-year `data-count`, and a timeline of proof points that reveals
  line by line.
- **Start (intake).** The four-question form becomes a four-step wizard.
  Each step is a fieldset; steps slide between each other with GSAP; the
  form still submits as one form, and with JavaScript off all four
  fieldsets show at once. The honeypot and the no-endpoint fallback in
  `forms.js` are untouched.
- **PACK EXPO landing.** One still (a glass operator panel), one
  `data-reveal` pass, no video, no pinning, no parallax. Under 400 KB
  total transfer.
- **404.** Nothing.

## 4. Imagery pipeline

- `_tools/cut_images.py` reads `_originals/` (git-ignored) and writes WebP
  to `assets/img/` at two widths, 1600 and 800, named from the original's
  file name in kebab case. It reads a `picks.json` (git-ignored) that maps
  each chosen original to its crop box, alt text and target pages, so the
  selection is reproducible.
- The same script cuts the hero loop with the ffmpeg binary bundled by the
  `imageio-ffmpeg` package, since ffmpeg is not installed on this machine.
- A real `assets/og.jpg` (1200 by 630) is cut from a glass operator panel
  photograph.
- Every photograph gets a review for supplier branding before it is
  committed. Frames that fail are dropped, not cropped around.
- The existing `{{img:file|alt|extra}}` placeholder in the build script is
  extended with a `srcset` for the two widths.

## 5. Drawn graphics

Hand-drawn SVGs in `assets/art/`, inlined by the build so they can animate:

- An operator panel front, for the homepage proof step.
- The controls topology (HMI, PLC, I/O, network), for the OEM path.
- The cost-to-target figure, for the homepage.

Each SVG uses `currentColor` for lines so it sits on both light and dark
bands, and each draws in a fixed order the `data-draw` handler follows.

## 6. Budgets and verification

| Page | Budget |
|---|---|
| Homepage, first load, before video | under 1.5 MB |
| Hero video, each format | under 3 MB, `preload="none"` |
| PACK EXPO landing | under 400 KB |
| Every other page | under 1 MB |

Verification, in order:

1. `python _build/build.py` then `python _tools/linkcheck.py`, both clean.
2. A desktop pass and a phone pass in the browser pane, with screenshots
   sent to Dave.
3. A reduced-motion pass: emulate `prefers-reduced-motion: reduce` and
   confirm the motion script is not requested and every element is
   visible.
4. A JavaScript-off pass: every element visible, the intake form shows all
   four fieldsets.
5. Transfer sizes checked against the table above from the browser's
   network log.

## Out of scope

Page transitions, smooth scrolling, Russell on camera, testimonials and case
studies, and anything that names the supplier. Also the client's domain,
phone number and address, which remain open items in the README.

## Open questions for Russell

- Sign-off on the cost figures used in the animated proof.
- His photograph and bio for the About page.
- Whether any factory footage may be shown at all, given the positioning.
