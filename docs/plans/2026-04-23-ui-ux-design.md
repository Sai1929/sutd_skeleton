# EHS Portal — UI/UX Design Spec
**Date:** 2026-04-23
**Audience:** Mixed — SUTD professors + EHS professionals
**Device:** Laptop, kiosk-style (unattended, self-guided)
**Stack:** React + Tailwind CSS
**Backend:** `http://localhost:8000`

---

## 0. Design Principles

| Principle | Application |
|-----------|-------------|
| **Zero learning curve** | User knows what to do in 3 seconds |
| **AI is the hero** | Predictions animate in visibly — not hidden |
| **One flow, no dead ends** | Inspection → Quiz plays out without navigation |
| **Confidence visible** | Scores shown as bars — technical audience sees the ML |
| **Override is easy** | User can change any field, rest re-predicts instantly |

---

## 1. App Shell

### Layout
```
┌──────────────────────────────────────────────────────────┐
│  🛡 EHS Portal                    [Inspection] [Chat]     │
│  SUTD Environment, Health & Safety                        │
└──────────────────────────────────────────────────────────┘
│                                                          │
│                   <page content>                         │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### Nav Bar
- **Left:** Shield icon + "EHS Portal" wordmark + "SUTD" subtitle in smaller text
- **Right:** Two pill tabs — `Inspection` (default active) and `Chat`
- **Style:** Dark navy (`#0F172A`) background, white text, active tab has white pill with navy text
- **Height:** 64px

### Color Palette
```
Navy (primary):     #0F172A
Blue (accent):      #3B82F6
Green (safe/good):  #22C55E
Amber (medium):     #F59E0B
Red (high risk):    #EF4444
Background:         #F8FAFC
Card:               #FFFFFF
Border:             #E2E8F0
Text primary:       #0F172A
Text muted:         #64748B
```

### Typography
- **Font:** Inter (Google Fonts)
- **Headings:** Semi-bold
- **Body:** Regular 14–16px
- **Labels:** 12px uppercase tracking-wide text-muted

---

## 2. Inspection Page

### 2.1 Overall Layout (top to bottom)

```
┌─────────────────────────────────────────────────────────┐
│  PAGE HEADER                                            │
│  "AI-Assisted EHS Inspection"                           │
│  "Enter your activity below. The AI will predict all    │
│   hazard fields automatically."                         │
├─────────────────────────────────────────────────────────┤
│  ACTIVITY INPUT                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  🔍  What activity are you inspecting?          │   │
│  │      e.g. Electrical Works, Welding...          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  AI PREDICTION CARDS (2 × 2 grid on desktop)           │
│                                                         │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  Hazard Type     │  │  Severity        │            │
│  │  (Step 1)        │  │  (Step 2)        │            │
│  └──────────────────┘  └──────────────────┘            │
│                                                         │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │  Controls / PPE  │  │  Remarks         │            │
│  │  (Step 3)        │  │  (Step 4)        │            │
│  └──────────────────┘  └──────────────────┘            │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [  Submit Inspection  ]   (disabled until all filled)  │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Activity Input

- **Width:** 100%, max-width 640px, centered
- **Height:** 56px
- **Style:** Large rounded input, subtle shadow, blue focus ring
- **Placeholder:** *"What activity are you inspecting? e.g. Electrical Works, Welding..."*
- **Behavior:**
  - On blur (or after 600ms debounce): calls `POST /api/v1/inspect/recommend` with `{ activity, selections: {} }`
  - All 4 cards enter **loading state** simultaneously (shimmer animation)
  - Predictions populate with **fade + slide-up animation** (staggered 100ms per card)
- **Clear button (×):** appears when text present, resets all 4 cards

### 2.3 Prediction Card (each of the 4)

```
┌─────────────────────────────────────────────────────────┐
│  HAZARD TYPE                              ✏ Override    │
│  ─────────────────────────────────────────────────────  │
│  ● Electric Shock                                       │
│    ████████████████████░░░░░░░░  44%                   │
│                                                         │
│    Arc Flash              ░░░░░░░░░░░░░░░░░░ 39%       │
│    Fire / Explosion       ░░░░░░░░░░░░░░░░░░  4%       │
│    + 7 more...                                          │
└─────────────────────────────────────────────────────────┘
```

**Card states:**

| State | Visual |
|-------|--------|
| **Empty** (no activity yet) | Grey shimmer placeholder, "Enter activity to predict" |
| **Loading** | Animated shimmer skeleton |
| **Predicted** | Top prediction highlighted in blue, confidence bars shown |
| **Confirmed** (user accepted) | Green checkmark + green border, field locked |
| **Overridden** (user changed) | Amber badge "Overridden", downstream cards reload |

**Card anatomy:**
- **Header row:** Step label (HAZARD TYPE) left, small `✏ Override` link right
- **Top prediction:** Bold text, full-width blue progress bar with `%` label
- **2nd and 3rd predictions:** Muted text, thinner grey bar, smaller `%`
- **"+ N more..."** link expands to show all options as a dropdown
- **Override mode:** Clicking `✏ Override` or `+ N more...` opens a **select dropdown** with all options — selecting one sets that field as overridden, calls API for downstream re-prediction

**Override downstream behavior:**
- When user overrides Step 1 (Hazard Type): Steps 2, 3, 4 shimmer and re-predict
- When user overrides Step 2: Steps 3, 4 re-predict only
- Step 1 card never re-predicts (it's always first)

**Confirm behavior:**
- Clicking anywhere on the top prediction (highlighted area) = **confirm** that prediction
- Card gets green border + green check icon
- No downstream re-prediction for confirm (only override triggers re-predict)

### 2.4 Risk Level Indicator

Between the activity input and the cards, show a small **risk badge** that updates live:

```
Risk Level:  ● HIGH × LIKELY
```

- Derived from `severity_likelihood` top prediction
- Color: Red = High, Amber = Medium, Green = Low
- Updates as predictions change

### 2.5 Submit Button

- **Position:** Bottom center, full-width on mobile, 320px on desktop
- **Style:** Large (56px), navy background, white text, rounded-full
- **State disabled:** Grey, tooltip "Fill in all fields first" — shown when any card is unconfirmed
- **State enabled:** Navy, hover darkens slightly, subtle shadow
- **Label:** `Submit Inspection →`
- **On click:** Sends `POST /api/v1/quiz/generate` with all 5 fields, opens quiz overlay

---

## 3. Quiz Overlay

Triggered immediately after Submit. Covers the inspection page with a **slide-up overlay** (not a new page).

### 3.1 Overall Structure

```
┌─────────────────────────────────────────────────────────┐
│  ← Back to Inspection          Question 1 of 5  [━━━░░] │
│                                                         │
│  Test Your Understanding                                │
│  Based on your inspection: Electrical Works             │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │                                                   │  │
│  │  What is the primary injury risk from arc flash   │  │
│  │  during electrical panel maintenance?             │  │
│  │                                                   │  │
│  │  ○  A. Burns from high-temperature plasma arc     │  │
│  │  ○  B. Electric shock from live terminals         │  │
│  │  ○  C. Falls from ladder instability              │  │
│  │  ○  D. Noise-induced hearing loss                 │  │
│  │                                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│                    [ Next Question → ]                  │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Quiz Flow

1. **Loading state** (while Groq generates): spinner + "Generating questions..." for 2–4s
2. **Question view**: one question at a time, no skipping
3. **Progress bar**: thin blue bar at top, fills as questions complete
4. **Option cards**: each option is a clickable card (full width), hover highlights in blue
5. **On select**: selected card turns blue, `Next Question →` button activates
6. **On last question**: button becomes `Submit Quiz →`
7. **On submit**: slide transition to **results view**

### 3.3 Results View

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│              ✅  Quiz Submitted                          │
│                                                         │
│   Your responses have been recorded.                    │
│   An EHS administrator will review your answers.        │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │  Q1  ✓ Correct answer selected                  │   │
│   │  Q2  ✓ Correct answer selected                  │   │
│   │  Q3  ✗ Incorrect — see explanation below        │   │
│   │  Q4  ✓ Correct answer selected                  │   │
│   │  Q5  ✓ Correct answer selected                  │   │
│   └─────────────────────────────────────────────────┘   │
│                                                         │
│   [ ← Start New Inspection ]                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

- Each row expandable → shows question, user answer, correct answer, explanation
- Incorrect answers shown in red with explanation expanded by default
- "Start New Inspection" resets and returns to inspection page

---

## 4. Chat Page

Fully separate page (top nav tab). Nothing shared with inspection flow.

### 4.1 Layout

```
┌─────────────────────────────────────────────────────────┐
│  NAV BAR                         [Inspection] [Chat ●]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌────────────┐  ┌────────────────────────────────────┐ │
│  │            │  │                                    │ │
│  │  SIDEBAR   │  │      CHAT AREA                     │ │
│  │  280px     │  │      flex-1                        │ │
│  │            │  │                                    │ │
│  │  About     │  │                                    │ │
│  │  Quick Qs  │  │                                    │ │
│  │            │  │                                    │ │
│  │            │  │  ────────────────────────────────  │ │
│  │            │  │  [Type a question...        ] [→]  │ │
│  └────────────┘  └────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Sidebar (left, 280px)

**Top section — About:**
```
🤖 WSH Risk Advisor

Ask me anything about workplace
safety in Singapore — hazards,
PPE requirements, permits,
WSH regulations, and more.

Powered by Llama 4 Scout
```

**Middle section — Suggested questions (chips):**

```
Try asking:
┌─────────────────────────────┐
│  What PPE for welding?      │
└─────────────────────────────┘
┌─────────────────────────────┐
│  When is a PTW required?    │
└─────────────────────────────┘
┌─────────────────────────────┐
│  Confined space entry rules │
└─────────────────────────────┘
┌─────────────────────────────┐
│  Arc flash protection       │
└─────────────────────────────┘
┌─────────────────────────────┐
│  WSH Act penalties          │
└─────────────────────────────┘
```

Clicking a chip fires it as a message instantly.

**Bottom section:**
```
[ 🗑 Clear Conversation ]
```

### 4.3 Chat Area

**Empty state (no messages yet):**
```
        🛡️

   How can I help with your
   workplace safety today?

   Ask about hazards, PPE, permits,
   or Singapore WSH regulations.
```

Centered, faded, disappears when first message sent.

**Message bubbles:**
- **User:** Right-aligned, navy background, white text, rounded (top-left sharp)
- **Assistant:** Left-aligned, white card with subtle shadow, navy text, rounded (top-right sharp)
- **Timestamp:** Tiny, muted, below each bubble
- **Avatar:** Small 🤖 icon left of assistant messages

**Typing indicator** (while Groq responds):
```
🤖  ● ● ●  (animated dots)
```

**Input bar (bottom, sticky):**
- Full-width text area (auto-expand, max 4 rows)
- Send button (blue arrow icon) right side
- `Enter` sends, `Shift+Enter` = new line
- Placeholder: *"Ask about workplace safety, hazards, or WSH regulations..."*
- Disabled with spinner while response loading

**Message actions** (on hover):
- Copy button on assistant messages

---

## 5. Micro-interactions & Animation

| Trigger | Animation |
|---------|-----------|
| Activity typed → API call | Cards fade to shimmer simultaneously |
| Predictions arrive | Cards fade in + slide up, staggered 100ms |
| Card confirmed | Border pulses green once, checkmark drops in |
| Card overridden | Amber badge slides in from right, downstream cards shimmer |
| Submit clicked | Button shows spinner, then quiz slides up from bottom |
| Quiz question answered | Selected card bounces slightly, Next button slides in |
| Quiz submitted | Confetti burst (subtle, 1 second) → results fade in |
| Chat message sent | Message pops in from right, typing indicator appears |
| Chat response arrives | Text streams in word-by-word |

---

## 6. Responsive Behaviour (laptop-first)

| Breakpoint | Change |
|------------|--------|
| ≥ 1280px | 2×2 prediction card grid, sidebar visible in chat |
| 768–1280px | 2×2 grid, sidebar collapses to icon-only |
| < 768px | Single column cards, no sidebar (suggested Qs as horizontal scroll chips) |

---

## 7. Empty / Error States

| State | Message |
|-------|---------|
| No activity entered | Cards show "Enter an activity above to get predictions" |
| API timeout / error | Toast: "Prediction failed — please try again" + retry button on card |
| Groq unavailable (quiz) | "Unable to generate quiz right now" with retry |
| Groq unavailable (chat) | "AI advisor is offline" banner, input disabled |
| Unknown activity | Model still predicts — show as normal (model generalises) |

---

## 8. Tech Stack Recommendation

| Concern | Choice | Reason |
|---------|--------|--------|
| Framework | React 18 + Vite | Fast dev, HMR, small bundle |
| Styling | Tailwind CSS v3 | Utility-first, consistent with design tokens above |
| Animations | Framer Motion | Declarative, smooth, easy stagger |
| Icons | Lucide React | Clean, consistent set |
| HTTP | Axios or native fetch | Lightweight |
| State | React useState + useReducer | No external state lib needed at this scale |
| Chat streaming | fetch + ReadableStream | If Groq streaming is enabled, else polling |

**Folder structure:**
```
src/
  components/
    inspection/
      ActivityInput.tsx
      PredictionCard.tsx
      RiskBadge.tsx
      SubmitButton.tsx
    quiz/
      QuizOverlay.tsx
      QuestionCard.tsx
      QuizResults.tsx
    chat/
      ChatPage.tsx
      MessageBubble.tsx
      ChatInput.tsx
      Sidebar.tsx
    layout/
      NavBar.tsx
      AppShell.tsx
  hooks/
    useRecommend.ts    ← debounced API call
    useQuiz.ts
    useChat.ts
  api/
    client.ts          ← axios instance pointing to localhost:8000
    inspect.ts
    quiz.ts
    chat.ts
  pages/
    InspectionPage.tsx
    ChatPage.tsx
```

---

## 9. Key Demo Script (self-guided kiosk)

The page should make this flow obvious without any instructions:

1. User sees big input box → types "Electrical Works"
2. Watches all 4 cards animate in with predictions
3. Notices "Electric Shock — 44%" highlighted
4. Clicks one prediction to confirm it → green ✓
5. Notices downstream cards shimmer and re-predict
6. Confirms remaining fields
7. Clicks "Submit Inspection →"
8. Quiz slides up automatically
9. Answers 5 questions
10. Sees results
11. Clicks "Start New Inspection" or switches to Chat tab
