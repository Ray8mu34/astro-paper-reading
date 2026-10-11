---
version: alpha
colors:
  paper: "#ffffff"
  ink: "#1c2833"
  muted: "#516270"
  line: "#c9d4dd"
  blue: "#245ea0"
  red: "#a33d47"
  panel: "#f3f6f9"
typography:
  body:
    fontFamily: 'Georgia, "Noto Serif SC", "Source Han Serif SC", SimSun, serif'
    fontSize: "17px"
    lineHeight: "1.85"
  utility:
    fontFamily: '"Segoe UI", "Microsoft YaHei", sans-serif'
    fontSize: "14px"
    lineHeight: "1.5"
rounded:
  control: "2px"
spacing:
  gutter: "24px"
  figureGap: "20px"
components:
  figure:
    rounded: "0px"
    backgroundColor: "{colors.paper}"
  control:
    rounded: "{rounded.control}"
---

# Astro Paper X-Ray design

## Overview

Register: scientific reading tool for astronomy graduate readers, zh-CN.
North Star: a reader who has not opened the PDF understands the research
problem, contribution, results and argument before entering local mechanisms.
Its signature is an original-section argument map followed by a few sustained
scientific questions. The paper determines those questions and their order.
Original figures carry evidence; interaction earns its place through added insight.
The user brief and references/scientific-integrity.md own scientific boundaries.
Paper X-Ray Figure Kit informs captions, semantic color and stroke discipline.
No recovered frontend exists to replace. Sibling figures use shared SVG axes.

## Colors

Runtime owner: assets/report.css `:root`; the frontmatter mirrors those values.
Token drift is checked in tests/test_frontend.py. blue is numerical single-lens
flux/critical curves; red is current source/caustics. Gray dashed lines distinguish
analytic comparison or schematic trajectory in addition to labels. No color-only
meaning. No decorative gradients or dashboard cards.

## Typography

Use system serif text and native MathML, plus utility sans-serif labels and
Consolas numbers. Offline fonts have locale-capable fallbacks; no font download.

## Layout

1100px outer frame, 780px prose measure, 24px gutters; paired figures become one column below
700px. A restrained 24–34px title gives the research overview room on the first screen.
The original-section map is visible after the overview; local navigation is a
native disclosure below it. Scientific mechanisms remain open in the article.
Only supplementary derivations use a labeled disclosure. Display equations and wide tables scroll inside their own
regions. Long prose uses natural page scrolling. SVG geometry has equal axes.
Controls form a compact grid below each figure; values stay in reserved fields.

## Elevation & Depth

Flat white plotting ground, rules between arguments, no shadows or overlays.

## Shapes

Square figures, 2px native-control corners. Circles mean physical source disks,
Einstein radius or points; they never serve as arbitrary card containers.

## Components

`assets/report.js` owns shared axes/line/point helpers and independent module
updates. `assets/report.css` owns every figure and control. Native selects use
OS-owned popup geometry intentionally. Labels activate each input, keyboard
arrows change ranges, and reset has visible status feedback. No network/loading
state exists: data is embedded synchronously. Invalid state shows inline errors
and clears stale figures. Scrollbar styling is global; forced colors use system
styles. There is no automatic animation; reduced motion is respected.

## Do's and Don'ts

Keep units, source/model captions and conclusion-changing assumptions visible.
Keep coverage logs, solver residuals, checks and evidence ledgers in separate
analysis-notes.md; link quietly from the footer. Do not front-load execution status.
Do not turn teaching geometry into a claimed OGLE fit. Do not infer binary
photometry from a caustic or couple it to the single-lens module. No hidden
extrapolation. No giant KPI headline or icon ornaments.
