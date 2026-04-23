# Handoff — EHS Portal (Editorial variant)

## Overview

The **EHS Portal** is a kiosk-style web application for the Singapore University of Technology and Design (SUTD) Environment, Health & Safety office. It is used by **SUTD professors and EHS professionals** in a **laptop kiosk** context (unattended, self-guided). It has two features:

1. **AI-Assisted Inspection** — User types an activity (e.g. "Electrical Works"). A backend ML model returns predictions for four fields — Hazard Type, Severity, Controls/PPE, and a recommended Remark — each with confidence scores. The user confirms or overrides each field; downstream fields re-predict when upstream fields are overridden. After all four fields are confirmed, a Groq-generated quiz is opened as a modal overlay.
2. **WSH Risk Advisor (Chat)** — A chat surface answering Singapore WSH (Workplace Safety & Health) questions, powered by a Llama-family model. Sidebar offers suggested prompts.

**Stack assumed:** React 18 + Vite + TypeScript + Tailwind CSS + Framer Motion + Lucide icons + Axios.
**Backend:** `http://localhost:8000` (REST API — endpoints listed in §7).

## About the design files

The files in `reference-source/` are a **clickable HTML prototype** (React via Babel in-browser, single-file preview). They are **design references, not production code to copy directly**. Your task: **recreate this design in a real React + Vite + Tailwind codebase** using the codebase's existing patterns (TypeScript, proper component files, state management, API layer). Read the JSX for visual spec, state machines, and interaction details — then re-implement cleanly.

A standalone preview `prototype.html` is included — open it in a browser to see every state end-to-end.

## Fidelity

**High-fidelity.** Pixel-perfect colors, typography, spacing, and interactions. Recreate exactly; the only things to change are framework idioms (Tailwind classes instead of inline style objects, real API calls instead of mocked predictions, TypeScript types, etc.).

---

## 1. Design tokens

### Colors

```ts
// Semantic tokens
const tokens = {
  // Surfaces
  bg:       '#F5F2EC', // page background — warm off-white, editorial paper feel
  card:     '#FFFFFF',
  ink:      '#0B1220', // near-black, slight warm tilt
  mute:     '#5A6272', // secondary text
  rule:     '#E4DFD3', // dividers, borders, card outlines

  // Brand / accent — primary interactive
  accent:   '#7A1F36', // SUTD-adjacent maroon (the chosen tweak). Use this everywhere the prototype uses its accent color.
  accentSoft: '#7A1F3615', // 15% alpha of accent — used for highlighted-prediction fill

  // Risk scale (for severity/likelihood bucket)
  riskHigh:   { base: '#C4302B', bg: '#FBEDEC' },
  riskMedium: { base: '#B26A00', bg: '#FAF2E2' },
  riskLow:    { base: '#1F7A3A', bg: '#E9F4EC' },

  // Card state colors
  stateConfirmed:  '#1F7A3A', // green accent when user confirms a prediction
  stateOverridden: '#B26A00', // amber accent when user overrides
  statePredicted:  '#1F3A8A', // blue emphasis on top prediction (if not using accent)
};
```

Risk bucket is derived from the top severity prediction label:
- starts with `High` → `riskHigh`
- starts with `Medium` → `riskMedium`
- else → `riskLow`

### Typography

Three-family pairing — loaded from Google Fonts:

```html
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,300..700;1,8..60,300..700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

| Use | Family | Weight | Notes |
|-----|--------|--------|-------|
| Headlines, card titles, input text | **Source Serif 4** | 500–600 | Academic-journal feel. Letter-spacing `-0.015em` to `-0.02em` on large sizes. Italic for subtle voice shifts (input placeholder feel, "Record an *inspection*"). |
| Body, UI labels, buttons, chat messages | **Inter** | 400–600 | The workhorse. Letter-spacing `-0.005em` to `-0.01em`. |
| Meta labels, percentages, model IDs, timestamps | **JetBrains Mono** | 400–600 | `font-variant-numeric: tabular-nums` on percentages. |

### Type scale (exact)

| Token | Size | Weight | Family | Leading | Tracking | Where |
|-------|------|--------|--------|---------|----------|-------|
| `display`   | 44px | 500 | Serif | 1.1 | -0.02em | `<h1>` page hero "Record an inspection." |
| `title`     | 26–28px | 500–600 | Serif | 1.3 | -0.015em | Quiz question, modal headers |
| `card-title` | 17px | 600 | Serif | 1.2 | -0.015em | Prediction card title |
| `top-pick` | 15px | 600 | Serif | 1.3 | -0.005em | Highlighted prediction label |
| `body-lg`  | 18px | 400 | Serif | 1.55 | -0.005em | Page intro paragraph |
| `body`     | 14px | 400–500 | Sans | 1.55 | — | Chat body, card runner-up labels |
| `ui`       | 13px | 500–600 | Sans | 1.4 | -0.005em | Buttons, tabs |
| `micro`    | 12px | 400–500 | Sans | 1.4 | — | Footer text, hint text |
| `eyebrow`  | 11px | 500 | Sans | — | 0.14–0.16em, UPPERCASE | "§ 02 · AI-Assisted Inspection", "STEP 01" |
| `meta`     | 10–11px | 500–600 | Mono | — | 0.10–0.14em, UPPERCASE | Confidence %, timestamps, model IDs |

### Spacing

Follows an **8px grid** with 4px half-steps. Common values used: 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 28, 32, 36, 44, 48, 56, 64, 72, 80.

### Radii

- Cards and primary surfaces: **4px** (editorial, restrained — not the usual 12–16px)
- Small UI elements (buttons, inputs): **4–6px**
- Pills (risk badge, tabs): **999px**
- Avatar/icon tiles: **6–10px**

### Shadows

Minimal. The editorial aesthetic leans on borders and whitespace, not shadows.

- Card default: none, or `0 1px 2px rgba(11,18,32,0.08)`
- Card confirmed: `0 0 0 3px rgba(31,122,58,0.07)` (green halo)
- Submit button (enabled): `0 4px 12px rgba(11,18,32,0.13)`
- Quiz modal backdrop: `rgba(11,18,32,0.67)` with `backdrop-filter: blur(3px)`
- Quiz modal shell: `0 20px 60px rgba(11,18,32,0.25)`

### Borders

- Rule/divider: `1px solid #E4DFD3`
- Card default: `1px solid #E4DFD3`
- Card confirmed: `1.5px solid #1F7A3A`
- Card overridden: `1.5px solid #B26A00`
- Input focused: `1px solid var(--accent)` + `0 0 0 3px rgba(accent, 0.08)`

---

## 2. App shell

### Layout

```
┌──────────────────────────────────────────────────────────┐
│  [E]  EHS Portal                 ┌──────────────────┐    │  ← 68px nav
│       ENVIRONMENT · HEALTH · SAFETY  Inspection Chat │    │
└──────────────────────────────────────────────────────────┘
│                                                          │
│                   <page content>                         │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Nav bar

- **Height:** 68px, sticky top, `z-index: 40`
- **Background:** `#FFFFFF`, `border-bottom: 1px solid #E4DFD3`
- **Padding:** `0 32px`
- **Left cluster** (flex, gap 14):
  - 28×28 rounded-square tile — `background: #0B1220`, corner `6px`, contains white italic serif **"E"** (Source Serif 4, 15px, 700, italic)
  - Two-line wordmark:
    - `EHS Portal` — Source Serif 4, 17px, 600, `color: #0B1220`, `letter-spacing: -0.01em`, `line-height: 1`
    - `ENVIRONMENT · HEALTH · SAFETY` — Inter, 10px, 500, `color: #5A6272`, `letter-spacing: 0.14em`, uppercase, `margin-top: 3px`
- **Right cluster** — tab pill group:
  - Container: `background: #F5F2EC`, `border: 1px solid #E4DFD3`, `border-radius: 8px`, `padding: 3px`
  - Buttons (Inspection / Chat): `padding: 7px 18px`, Inter 13px 500, `color: #5A6272` inactive, rounded 6px
  - Active tab: `background: #FFFFFF`, `color: #0B1220`, 600 weight, `box-shadow: 0 1px 2px rgba(11,18,32,0.08)`

---

## 3. Inspection page (Editorial)

### Container

- `max-width: 1200px`, centered
- `padding: 56px 64px 80px`

### 3.1 Page header (prose block)

- `max-width: 720px`, `margin-bottom: 44px`
- **Eyebrow**: `§ 02 · AI-Assisted Inspection` — Inter 11px 500, `#5A6272`, `letter-spacing: 0.16em`, uppercase, `margin-bottom: 14px`
- **H1**: `Record an inspection.` (the word "inspection" italicized) — Source Serif 4, **44px**, 500, `color: #0B1220`, `line-height: 1.1`, `letter-spacing: -0.02em`, `margin: 0`
- **Description paragraph** (18px Source Serif 4, 400, `color: #5A6272`, `line-height: 1.55`, `margin-top: 18px`):
  > Enter the activity below. The model will predict hazard type, severity, required controls, and a recommended remark. You may confirm each prediction or override any field — downstream predictions refresh accordingly.

### 3.2 Activity input

- `width: 100%`, `height: 60px`, `padding: 0 20px 0 52px`
- Source Serif 4, **19px, 400, italic**, `color: #0B1220`
- `background: #FFFFFF`, `border-radius: 4px`
- Border: `1px solid #E4DFD3` default → `1px solid var(--accent)` + `box-shadow: 0 0 0 3px rgba(accent, 0.08)` on focus
- Placeholder: `What activity are you inspecting? e.g. Electrical Works, Welding…`
- **Search icon** (custom SVG — circle + tail) positioned absolutely `left: 18px`, 18×18, `stroke: #5A6272`
- **Clear button** (when value present): positioned `right: 16px`, 24×24 circle, `background: #F5F2EC`, `border: 1px solid #E4DFD3`, shows `×`

**Behaviour:**
- Debounce 500ms after last keystroke → call `POST /api/v1/inspect/recommend`
- All four cards enter simultaneous shimmer loading state on call
- On response: reveal cards one-by-one with 120ms stagger (fade + slide-up 12px)
- If user clears input: return all four cards to empty state

### 3.3 Suggestion chips

Row below input, `margin-top: 14px`, flex, gap 8:

- Leading label `COMMON` — Inter 11px 500, `#5A6272`, `letter-spacing: 0.1em`, uppercase, `margin-right: 4px`
- Chips for: **Electrical Works**, **Welding**, **Confined Space**, **Working at Height**
  - `padding: 6px 12px`, Inter 12px, `color: #0B1220`
  - `background: #FFFFFF`, `border: 1px solid #E4DFD3`, `border-radius: 999px`
  - Hover: `background: rgba(accent, 0.08)`, `border-color: rgba(accent, 0.25)`
- Clicking a chip sets the activity and fires the API call immediately (no debounce)

### 3.4 Risk banner

Appears only once predictions arrive (between input and card grid). `margin-top: 28px, margin-bottom: 28px`.

- **Full-width banner**, `padding: 10px 16px`, `border-radius: 8px`
- `background: <risk.bg>`, `border: 1px solid <risk.base>22`
- Flex row, gap 12, items center, Inter 13px 500, `color: <risk.base>`
- Contents: `●` dot (8×8, `background: <risk.base>`) · `RISK LEVEL` (11px 600 uppercase 0.08em) · `—` · severity label in small-caps (e.g. "High × Likely")

### 3.5 Prediction cards — 2×2 grid

`display: grid; grid-template-columns: 1fr 1fr; gap: 20px;`

Four cards: **Hazard Type**, **Severity · Likelihood**, **Controls & PPE**, **Recommended Remark**.

#### Card shell

- `background: #FFFFFF`
- `padding: 20px 22px 22px`
- `border-radius: 4px`
- `border: 1px solid #E4DFD3` (default) — colored per state (see below)
- Transition: `border-color 0.25s, box-shadow 0.25s`

#### Header row (flex, justify-between, align-start, margin-bottom 16px)

Left side:
- **Step indicator** — Source Serif 4, 11px, italic, `color: #5A6272` (or green if confirmed / amber if overridden): `Step 01` / `Step 02` / `Step 03` / `Step 04`
- **Card title** — Source Serif 4, 17px, 600, `color: #0B1220`, `letter-spacing: -0.015em`, `margin-top: 4px`

Right side:
- **Confirmed badge**: green pill (`background: rgba(31,122,58,0.09)`, `color: #1F7A3A`, Inter 11px 600, `padding: 3px 9px`, `border-radius: 999px`), check icon + "Confirmed"
- **Overridden badge**: amber pill (same geom, `background: rgba(178,106,0,0.09)`, `color: #B26A00`), "Overridden"
- **Override link** (when not confirmed): "✏ Override" — Inter 12px, `color: #5A6272`, transparent button, opens expanded dropdown

### 3.6 Card states

State machine: `empty → loading → predicted → confirmed | overridden`

#### Empty (no activity yet)
- Italic hint: "Awaiting activity…" — 12px, `color: #5A6272`, opacity 0.7
- Two shimmer placeholders above (60% and 40% width)

#### Loading (API in flight)
- 4 shimmer bars at varying widths (70%, 100%, 55%, 75%), using `#E4DFD3` as base with moving gradient highlight
- Shimmer animation: background-position `200% 0` → `-200% 0` over 1.4s infinite

#### Predicted (top pick highlighted, runner-ups below)

**Top prediction** — clickable block to confirm:
- `padding: 12px 14px`, `border-radius: 4px`
- `background: rgba(accent, 0.08)` (= `accentSoft`)
- `border: 1px solid rgba(accent, 0.13)`
- Top row (flex, gap 8, items center, margin-bottom 8):
  - 7×7 accent dot
  - Label in Source Serif 4, 15px, 600, `#0B1220`
- Confidence bar (see §3.7)
- Hint: "Click to confirm" — 11px Inter, italic, `#5A6272`, `margin-top: 8px`

**Runner-ups (2 shown below)**, flex column gap 8:
- Each row: `padding: 6px 14px`, clickable (hover → `background: #F5F2EC`)
- Label: Inter 13px, `color: #5A6272`, `margin-bottom: 5px`
- Muted confidence bar
- Clicking a runner-up = override that prediction (shifts selected index to it)

**"+ N more alternatives"** button below runner-ups (if predictions > 3):
- Inter 12px, `color: #5A6272`, transparent button
- Chevron-down icon left, rotates to up when expanded
- Expanded panel shows full list with % values, max-height 220px, scrollable, separated by a top border `1px solid #E4DFD3`

#### Confirmed
- Card border: `1.5px solid #1F7A3A`
- Outer glow: `box-shadow: 0 0 0 3px rgba(31,122,58,0.07)`
- Top prediction block: `background: rgba(31,122,58,0.06)`, `border: 1px solid rgba(31,122,58,0.19)`, dot green
- Runner-ups hidden
- Step number + "Confirmed" badge both green
- **Border pulse animation on confirm**: one-shot pulse (200ms) of stronger green halo, then settles

#### Overridden
- Card border: `1.5px solid #B26A00`
- Top prediction block: amber tinted (`background: rgba(178,106,0,0.06)`, `border: 1px solid rgba(178,106,0,0.19)`, dot amber)
- "Overridden" amber badge in header
- Downstream cards re-enter loading state → re-predict with stagger

### 3.7 Confidence bar

Flex row, gap 10, items center:

- Bar track: `flex: 1`, `height: 8px` (top) or `4px` (runner-up), `background: #E4DFD3`, `border-radius: 2px`, overflow hidden
- Fill: `background: var(--accent)` (top) or `#5A6272` at 45% opacity (runner-up)
- **Transition: `width 600ms cubic-bezier(.2,.7,.3,1)`** — bar animates from 0 to target when prediction arrives
- Value label: JetBrains Mono **11px**, `font-variant-numeric: tabular-nums`, `min-width: 32px`, right-aligned
  - 600 weight & `#0B1220` when top pick
  - 500 weight & `#5A6272` when runner-up

### 3.8 Submit footer

Below the 2×2 grid, `margin-top: 48px`, `padding-top: 28px`, `border-top: 1px solid #E4DFD3`.

Flex, justify-between, align-center:

- **Left status text** — Inter 12px, `#5A6272`:
  - If all confirmed: `All four fields confirmed. Ready to submit for review.`
  - Else: `N of 4 fields confirmed.`
- **Submit button**:
  - Enabled: `background: #0B1220`, `color: #FFFFFF`, `padding: 15px 36px`, `border-radius: 4px`, Inter 14px 600, `box-shadow: 0 4px 12px rgba(11,18,32,0.13)`. Hover: `translateY(-1px)`
  - Disabled: `background: #E4DFD3`, `color: #5A6272`, `cursor: not-allowed`
  - Label: `Submit Inspection →`
- Clicking enabled → POST quiz generate, open quiz modal

---

## 4. Quiz overlay

Triggered immediately after Submit. Slides up over inspection page.

### Shell

- Fullscreen overlay: `position: fixed; inset: 0; z-index: 100;`
- Backdrop: `background: rgba(11,18,32,0.67)`, `backdrop-filter: blur(3px)`, fade-in 250ms
- Modal panel: centered, `max-width: 880px`, `margin: 48px auto`, `background: #F5F2EC`, `border-radius: 6px`, `box-shadow: 0 20px 60px rgba(11,18,32,0.25)`
- Entrance: slide-up 24px + fade over 400ms cubic-bezier(.2,.8,.25,1)

### Header bar

- `padding: 18px 32px`, `background: #FFFFFF`, `border-bottom: 1px solid #E4DFD3`
- Left: `← Back to Inspection` button, Inter 13px, `#5A6272`, transparent
- Right (question phase only): `Question N / 5` (JetBrains Mono 11px `#5A6272`) + 140×3px progress bar (fill in accent, 300ms transition)

### Body padding: `40px 56px 48px`

### Phase 1 — Loading (1.8s mock delay, real backend call duration in prod)

Centered column, gap 24:
- 36×36 circular spinner (`border: 3px solid #E4DFD3; border-top-color: var(--accent);` 0.9s linear)
- Source Serif 4 18px italic `#0B1220`: `Generating questions from your inspection…`
- Inter 13px `#5A6272`: `Context: {activity}`

### Phase 2 — Question

- Eyebrow: `Comprehension Check · Based on: {activity}` — Inter 11px 500 `#5A6272`, uppercase 0.14em, margin-bottom 14
- **Question H2** — Source Serif 4, **26px**, 500, `#0B1220`, line-height 1.3, `letter-spacing: -0.015em`, margin-bottom 28
- **4 option buttons**, flex column gap 10:
  - `padding: 16px 20px`, `background: #FFFFFF`, `border: 1.5px solid #E4DFD3`, `border-radius: 6px`, Inter 15px, `#0B1220`, line-height 1.4
  - Selected state: `background: rgba(accent, 0.08)`, `border: 1.5px solid var(--accent)`
  - Leading 22×22 circle (A/B/C/D letter, Inter 11px 600) → replaced with checkmark on selection; background becomes accent when selected
- **Next button** (right-aligned, margin-top 32): `padding: 13px 28px`, `#0B1220` bg, white, 14px 600, disabled grey when nothing selected
- Label flips from `Next Question →` to `Submit Quiz →` on last question

### Phase 3 — Results

- Centered column at top:
  - 56×56 green tinted circle with large checkmark
  - H2 Source Serif 4 28px 500: `Quiz Submitted`
  - Inter 14px `#5A6272` line-height 1.5: `{N} of {total} correct · Your responses have been recorded. An EHS administrator will review your answers.`
- Divider: `border-bottom: 1px solid #E4DFD3`, padding-bottom 28, margin-bottom 36
- **Question result list** (flex column gap 10):
  - Each row: `padding: 14px 18px`, white bg, border `#E4DFD3` (correct) or `rgba(196,48,43,0.25)` (incorrect), radius 4
  - 22×22 leading indicator: green tinted circle + check (correct), red tinted circle + ✕ (incorrect)
  - Eyebrow: `Q{n} · Correct` or `Q{n} · Incorrect` — JetBrains Mono 10px uppercase 0.1em
  - Question text: Inter 13px 500, `#0B1220`, line-height 1.4
  - For incorrect only — expanded explanation panel below in `#F5F2EC` background, radius 3, padding 10/12, Inter 12px `#5A6272` line-height 1.5, with **Correct answer:** bold + explanation italicized
- Footer `← Start New Inspection` button centered — white bg, `#0B1220` text, `#E4DFD3` border, radius 4

---

## 5. Chat page (Risk Advisor)

Two-column grid, `grid-template-columns: 300px 1fr`, height = `calc(100% - 68px)` (below nav).

### 5.1 Sidebar (300px)

- `background: #FFFFFF`, `border-right: 1px solid #E4DFD3`, `padding: 32px 24px`, flex column
- **Header** (flex row gap 10, margin-bottom 14):
  - 32×32 rounded tile `background: rgba(accent, 0.08)`, `color: var(--accent)`, contains italic serif **"A"** (Source Serif 4 16px 700)
  - Title `WSH Risk Advisor` — Source Serif 4, 15px, 600, `#0B1220`, `letter-spacing: -0.01em`
- **About paragraph** — Inter 13px, `#5A6272`, line-height 1.55, margin-bottom 24:
  > Workplace safety guidance grounded in Singapore WSH Act and Council Codes of Practice. Ask about hazards, PPE, permits, or regulatory references.
- **"Try Asking" label** — Inter 10px 500 `#5A6272` uppercase 0.14em, margin-bottom 10
- **Suggestion chip list** (flex column gap 6). Each chip:
  - `padding: 9px 12px`, Inter 12px, `#0B1220`
  - `background: #F5F2EC`, `border: 1px solid #E4DFD3`, `border-radius: 4px`, line-height 1.4
  - Hover: bg `rgba(accent, 0.08)`, border `rgba(accent, 0.19)`
  - Clicking a chip sends the prompt immediately (same path as pressing Send)
- Suggestions text content (exact):
  1. `What PPE is required for welding near flammables?`
  2. `When is a Permit-to-Work required for electrical work?`
  3. `Confined space entry — gas monitoring thresholds?`
  4. `Arc flash protection categories explained`
  5. `WSH Act 2006 — employer penalties overview`
  6. `Working at height — harness inspection checklist`
- Spacer `flex: 1`
- **Clear Conversation button** (only if messages present): Inter 12px `#5A6272`, transparent bg, `#E4DFD3` border, radius 4
- **Meta footer** (margin-top 24, padding-top 16, border-top `#E4DFD3`):
  - JetBrains Mono 10px `#5A6272`, letter-spacing 0.06em, line-height 1.6:
    - `Model · llama-4-scout`
    - `Context · WSH Act, SS 508, SS 668`

### 5.2 Conversation area (flex column)

#### Scroll region — `flex: 1`, padding `32px 48px 16px`

**Empty state** (no messages):
- Centered column, max-width 460
- 52×52 tile `background: rgba(accent, 0.08)`, radius 10, with a shield SVG (24×24, stroke `var(--accent)`, strokeWidth 1.6)
- H2 Source Serif 4 26px 500 `#0B1220`: `How can I help with workplace safety today?`
- Inter 14px `#5A6272` line-height 1.55: `Ask about hazards, PPE selection, permits, or specific clauses in the Singapore WSH Act.`

**Message list** (max-width 720, centered, flex column gap 18):
- **User bubble** (right-aligned, gap 10):
  - `max-width: 82%`, `padding: 12px 16px`, Inter 14px, line-height 1.55
  - `background: #0B1220`, `color: #FFFFFF`
  - Radius: `10px 10px 2px 10px` (pointed corner toward the user)
- **Assistant bubble** (left-aligned, with 28×28 avatar tile reusing the "A" mark):
  - White bg, `border: 1px solid #E4DFD3`, `color: #0B1220`
  - Radius: `10px 10px 10px 2px`
  - Light markdown rendering: `**bold**`, line breaks, bullet lines starting with `•`, pipe tables preserved as pre-wrap
- **Typing indicator** (while waiting for first token): "A" avatar + bubble shell containing three 6×6 dots at `#5A6272` bouncing 4px on `dotBounce 1.2s` staggered 160ms

#### Input bar — sticky bottom

- `border-top: 1px solid #E4DFD3`, `background: #FFFFFF`, `padding: 16px 48px 24px`
- Inner row `max-width: 720; margin: 0 auto; display: flex; align-items: flex-end; gap: 10`:
  - **Textarea**: flex 1, `padding: 12px 14px`, Inter 14px, `color: #0B1220`, `background: #F5F2EC`, `border: 1px solid #E4DFD3`, `border-radius: 6px`, `line-height: 1.45`, auto-expand 22→120px (max 4 rows)
    - Placeholder: `Ask about workplace safety, hazards, or WSH regulations…`
    - `Enter` sends, `Shift+Enter` new line
    - Disabled during response stream
  - **Send button**: 44×44, radius 6, `background: var(--accent)` when ready, `#E4DFD3` disabled, contains a paper-plane SVG (16×16) in white
- **Helper line** (max-width 720, margin-top 8): Inter 11px `#5A6272`:
  > Enter to send · Shift+Enter for a new line · Responses may require verification against source regulations.

### 5.3 Response streaming

- Target backend: `POST /api/v1/chat` with `{ messages, stream: true }`
- Use `fetch` + `ReadableStream` (or SSE) — append tokens to last assistant message
- Mock prototype streams split-on-whitespace with 18–38ms delay to simulate

---

## 6. Interactions & animations

| Trigger | Animation | Implementation |
|---|---|---|
| Activity typed | All 4 cards → shimmer | Set state to `loading` simultaneously |
| Predictions arrive | Cards fade-in + slide-up | Stagger 120ms per card, `translateY(8px)` → 0, 400ms, `ease-out` |
| Confidence bar reveals | Width grows from 0 | `transition: width 600ms cubic-bezier(.2,.7,.3,1)` |
| Confirm top prediction | Green border pulse | Border color transition 250ms, optional one-shot `box-shadow` keyframe |
| Override prediction | Amber badge slide-in from right + downstream cards shimmer | Downstream: set to `loading`, then `predicted` with 140ms stagger after 500ms delay |
| Submit clicked | Quiz overlay slides up + fades backdrop | 400ms slide-up, 250ms fade-in |
| Quiz option selected | Border + bg swap | 150ms transition |
| Quiz submitted | Results fade in | Optional: 1s confetti burst (subtle — the user explicitly wants this to remain "professional" so keep confetti low-key or omit) |
| Chat message sent | User bubble pops in from bottom-right | 180ms, `translateY(4px) → 0`, fade |
| Chat response | Typing dots → tokens append word-by-word | 18–38ms per token |

All animations must respect `prefers-reduced-motion: reduce` → set duration to 0.01s.

---

## 7. State management

### Inspection page state

```ts
type CardState = 'empty' | 'loading' | 'predicted' | 'confirmed' | 'overridden';
type StepKey = 'hazard' | 'severity' | 'controls' | 'remarks';

interface InspectionState {
  activity: string;
  predictions: Record<StepKey, Prediction[]> | null;
  cardStates: Record<StepKey, CardState>;
  selected: Record<StepKey, number>; // index into predictions[step]
}

interface Prediction {
  label: string;
  score: number; // 0..1
}
```

### State transitions

1. **`setActivity(value)`** — debounce 500ms → set all cards to `loading` → fetch → set all to `predicted` with stagger → reset `selected` to zeros.
2. **`confirmCard(key)`** — set that card to `confirmed`. No downstream effects.
3. **`overrideCard(key, idx)`** — set `selected[key] = idx`, set state to `overridden`. Then for each card with step index > this one: set to `loading`, after 500+140·i ms fetch new predictions for downstream fields (server receives `{ activity, selections: { ...confirmedAndOverriddenSoFar } }`) and set back to `predicted`.
4. **`reset()`** — clear activity, all cards back to `empty`.
5. **`allConfirmed`** — all 4 cards in `confirmed` state → submit button enables.

### Quiz state

```ts
interface QuizState {
  open: boolean;
  phase: 'loading' | 'question' | 'results';
  questions: Question[];
  answers: Record<number, number>; // questionIdx → selectedOptionIdx
  currentIdx: number;
}
```

### Chat state

```ts
interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  ts: number;
}

interface ChatState {
  messages: ChatMessage[];
  input: string;
  isStreaming: boolean;
}
```

Consider colocating with `useReducer` per page (spec-recommended). React Query / TanStack Query acceptable if the codebase uses it.

---

## 8. API contract (backend `http://localhost:8000`)

### `POST /api/v1/inspect/recommend`
Request:
```json
{ "activity": "Electrical Works", "selections": { "hazard": "Electric Shock" } }
```
Response:
```json
{
  "hazard":   [ { "label": "Electric Shock", "score": 0.44 }, ... ],
  "severity": [ { "label": "High × Likely",  "score": 0.52 }, ... ],
  "controls": [ ... ],
  "remarks":  [ ... ]
}
```
- `selections` lists confirmed/overridden fields so far; backend re-predicts only downstream fields given those constraints.
- All arrays sorted by `score` descending, typically 5–10 items.

### `POST /api/v1/quiz/generate`
Request:
```json
{ "activity": "...", "hazard": "...", "severity": "...", "controls": "...", "remarks": "..." }
```
Response:
```json
{ "questions": [ { "q": "...", "options": ["...","...","...","..."], "correct": 2, "explain": "..." }, ... ] }
```

### `POST /api/v1/quiz/submit`
Request:
```json
{ "answers": [ { "qIdx": 0, "selected": 2 }, ... ] }
```
Response:
```json
{ "recordedAt": "2026-04-23T12:00:00Z", "adminReviewPending": true }
```

### `POST /api/v1/chat`
- Supports streaming (SSE or chunked). Body: `{ messages: [...], stream: true }`.
- Fallback to non-streaming if backend disabled.

---

## 9. Empty / error / loading states

| State | Copy / behavior |
|---|---|
| No activity entered | Cards show empty hint "Awaiting activity…" with shimmer placeholder |
| API timeout (inspect) | Toast in top-right: "Prediction failed — please try again" + retry button on affected card(s). Card returns to empty state. |
| Quiz generation fails | Replace modal body with error block + "Retry" button. |
| Chat backend offline | Banner above input: "AI advisor is offline. Try again later." Input disabled. |
| Unknown activity | Model still predicts — render as normal. |

---

## 10. Accessibility

- **Keyboard**: All interactive elements reachable via Tab. Enter/Space to activate buttons/cards. Arrow keys navigate quiz options.
- **Focus rings**: All interactive elements get `outline: 2px solid var(--accent); outline-offset: 2px` on `:focus-visible`.
- **Semantics**: Use `<button>` for cards that confirm predictions (not divs with onClick). `role="radiogroup"` for quiz options. `<main>` / `<nav>` / `<aside>` landmarks.
- **Live regions**: Chat new-message announcements via `aria-live="polite"` on the message list container.
- **Contrast**: All text pairs meet WCAG AA. The mute color `#5A6272` on `#F5F2EC` is 5.7:1.
- **Reduced motion**: Respect `prefers-reduced-motion: reduce` — disable all fade/slide/shimmer/stream animations (or drop to 0.01s).
- **Screen-reader text** on confidence bars: `<span class="sr-only">44 percent confidence</span>`.

---

## 11. Responsive behaviour

Laptop-first (≥1280px target). The EHS Portal is kiosk-style so desktop is primary, but handle graceful reflow:

| Breakpoint | Change |
|---|---|
| ≥ 1280px | 2×2 card grid, full layout. |
| 768–1280px | Keep 2×2 grid but contract container padding to 32px horizontal. Chat sidebar becomes icon-rail (64px) with chips as tooltip/drawer. |
| < 768px | Single column cards. Nav shrinks to icon + compact tabs. Chat sidebar hides; suggested prompts become a horizontal chip scroll above the input. |

---

## 12. Recommended folder structure

```
src/
├── components/
│   ├── inspection/
│   │   ├── ActivityInput.tsx
│   │   ├── SuggestionChips.tsx
│   │   ├── RiskBanner.tsx
│   │   ├── PredictionCard.tsx
│   │   ├── ConfidenceBar.tsx
│   │   └── SubmitButton.tsx
│   ├── quiz/
│   │   ├── QuizOverlay.tsx
│   │   ├── QuestionView.tsx
│   │   └── QuizResults.tsx
│   ├── chat/
│   │   ├── ChatPage.tsx
│   │   ├── ChatSidebar.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── TypingIndicator.tsx
│   │   └── ChatInput.tsx
│   ├── layout/
│   │   ├── NavBar.tsx
│   │   └── AppShell.tsx
│   └── ui/                        # primitives: Button, Badge, Pill, Icon, Spinner
├── hooks/
│   ├── useInspection.ts           # the reducer + API
│   ├── useQuiz.ts
│   └── useChat.ts                 # streaming handler
├── api/
│   ├── client.ts                  # axios instance baseURL localhost:8000
│   ├── inspect.ts
│   ├── quiz.ts
│   └── chat.ts
├── pages/
│   ├── InspectionPage.tsx
│   └── ChatPage.tsx
├── styles/
│   ├── tokens.css                 # CSS custom properties from §1
│   └── globals.css
└── App.tsx
```

Tailwind `tailwind.config.ts`:
- Extend `theme.colors` with the token names in §1 (e.g. `ink`, `mute`, `rule`, `accent`, `risk-{high,medium,low}`)
- Extend `theme.fontFamily` with `serif: ['Source Serif 4', 'serif']`, `sans: ['Inter', 'sans-serif']`, `mono: ['JetBrains Mono', 'monospace']`
- Extend `theme.borderRadius.sm` = 2, `DEFAULT` = 4, `md` = 6, `lg` = 8

---

## 13. Files in this bundle

```
design_handoff_ehs_portal_editorial/
├── README.md                               ← this document
├── prototype.html                          ← standalone clickable design reference (open in browser)
└── reference-source/                       ← original JSX source (React via Babel, NOT production-ready)
    ├── tokens.jsx                          ← design tokens + mock API data
    ├── primitives.jsx                      ← NavBar, RiskBadge, ConfidenceBar, icons
    ├── prediction-card.jsx                 ← the PredictionCard component (all states)
    ├── inspection-state.jsx                ← the state machine + ActivityInput + SuggestionChips
    ├── inspection-editorial.jsx            ← the Editorial variant page composition
    ├── quiz-overlay.jsx                    ← quiz modal (loading/question/results)
    ├── chat-page.jsx                       ← chat page + sidebar + streaming
    └── app.jsx                             ← app shell composition
```

## 14. Assets

- **Fonts**: Google Fonts (Source Serif 4, Inter, JetBrains Mono). Self-host for production; include WOFF2 files in `/public/fonts` and add `@font-face` declarations.
- **Icons**: Lucide React recommended. The prototype uses inline SVGs for Check, Edit (pencil), Chevron, Search, Shield, Send — all of these exist in Lucide: `Check`, `Pencil`, `ChevronDown`, `Search`, `Shield`, `Send`. Keep stroke widths at 1.5–1.6.
- **Wordmark "E" tile**: Generated inline — a 28×28 dark square with an italic serif "E". Reproduce with a `<div>` (not an image). Same for the chat "A" tile.
- **No external imagery** is required. The design is typographic.

---

## 15. Implementation checklist

- [ ] Scaffold Vite + React 18 + TypeScript + Tailwind CSS
- [ ] Load Google Fonts (or self-host)
- [ ] Define tokens in `tailwind.config.ts` and a `tokens.css` for CSS custom properties
- [ ] Build `NavBar` + `AppShell` with tab routing
- [ ] Build `InspectionPage`:
  - [ ] `ActivityInput` with debounced API call
  - [ ] `SuggestionChips`
  - [ ] `RiskBanner`
  - [ ] `PredictionCard` with all five states
  - [ ] `ConfidenceBar` with animated width
  - [ ] `SubmitButton` with disabled logic
- [ ] Wire `useInspection` hook (reducer + API)
- [ ] Build `QuizOverlay` (three phases, modal, keyboard accessible)
- [ ] Build `ChatPage` (sidebar + conversation + streaming input)
- [ ] Implement `useChat` with SSE/chunked streaming
- [ ] Accessibility sweep: focus order, ARIA, reduced motion, color contrast
- [ ] Responsive breakpoints
- [ ] Error states for each API failure mode
- [ ] Unit tests for the inspection reducer state transitions
- [ ] E2E test for the happy path: type activity → confirm all → quiz → submit
