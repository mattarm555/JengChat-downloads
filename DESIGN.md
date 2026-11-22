# Design: JengChat download page

<!-- Derived from the shipped site/ (index.html, style.css, app.js), 2026-11-22. -->

## World

A members' club invitation on dark baize. The first screen is a cream invitation card with a gold-foil wordmark, set beside the real Lounge screenshot. Every later section shows the app itself, in gold frames. The page should feel like an invitation from a friend, not a sales page (PRODUCT.md).

## Colour

| Token | Value | Use |
|---|---|---|
| `--baize` | `#14201a` | Page ground |
| `--baize-2` | `#1a2a22` | Download section, live panel, nav |
| `--baize-3` | `#223529` | Player chips |
| `--card` | `#efe6d2` | Invitation card, body text on baize |
| `--ink` | `#1d2a22` | Text on the card, button fill |
| `--gold` | `#e7be65` | Headings, links, foil, frames |
| `--gold-deep` | `#a97b2c` | Engraved rules on the card, button edge |
| `--red` | `#e76c60` | "JENG" in the wordmark, the main download button, the matchbook |
| `--cream-dim` | `#cbc3ad` | Secondary text on baize |

Red and gold are the app's own accents. Red marks the one action (download) and the brand; gold marks headings and frames. The tables section uses a lighter felt green radial ground; all other sections are flat baize.

## Type

- **Cormorant Garamond** (600 and 500, variable, self-hosted): the wordmark, headings, the invitation's lines, list items.
- **Inter** (self-hosted, the app's own UI font): body text, buttons, small print. The detector's overused-font rule is waived for Inter for that reason.
- Headings: `clamp(2.4rem, 4.6vw, 4rem)` in gold. Lede: 1.05 to 1.2rem in `--cream-dim`, at most 58ch.

## Components

- **Invitation card:** cream gradient card, an inset double rule in `--gold-deep`, foil wordmark (`background-clip: text`: the look's foil material, its gradient-text finding is waived for `site/`), the h1, one italic brand line, a star rule, the body and the download button.
- **Frame:** 8px gold gradient border around every screenshot (5px on phones); the image zooms to 1.025 on hover.
- **Button:** ink fill with an inset gold hairline; lifts 2px on hover and presses to 0.98. The main download button is red. The nav uses a small outlined gold variant.
- **Live panel:** bordered baize box with a server dot (green online, red offline, grey unknown), the count in Cormorant, and one chip per player with an initial on a colour chosen from the name.
- **Matchbook:** a red cover strip with the wordmark set vertically, then install notes as a definition list (already installed, the Windows warning, the checksum).

## Layout and motion

- Sections are at least one screen tall (`100svh`) on desktop and tablet and grow with their content on phones. The content column is 1200px with 20 to 48px gutters. Splits are 5:7 and stack below 1024px, text first.
- The hero's card and frame settle 16px upward once on load; both start visible.
- The one moment: the three table screenshots are dealt onto the felt (64 to 80px up, with a slight rotation) when the tables section first enters the viewport. It is skipped when the section is already on screen and under reduced motion.
- Reduced motion turns off every animation and transition.

## Constraints

- No third-party requests. Fonts, images and scripts are all local; the only other fetches are `release.json` and the optional status feed.
- `noindex,nofollow,noarchive`, plus `robots.txt` disallowing everything.
- Screenshots come only from demo and presentation runs with made-up names. No testimonials, counts or ratings.
