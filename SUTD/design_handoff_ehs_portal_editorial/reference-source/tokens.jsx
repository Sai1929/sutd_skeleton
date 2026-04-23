// Design tokens for EHS Portal prototype.
// Three aesthetic systems layered on top of the same semantic tokens so we
// can compare Editorial vs Technical vs Stacked without forking the logic.

const TOKENS = {
  // Risk colors — desaturated a notch from spec for institutional feel
  risk: {
    high:   { base: '#C4302B', bg: '#FBEDEC', dot: '#C4302B', label: 'HIGH' },
    medium: { base: '#B26A00', bg: '#FAF2E2', dot: '#B26A00', label: 'MEDIUM' },
    low:    { base: '#1F7A3A', bg: '#E9F4EC', dot: '#1F7A3A', label: 'LOW' },
  },
  // State colors shared across variations
  state: {
    confirmed: '#1F7A3A',
    overridden: '#B26A00',
    predicted:  '#1F3A8A',
    loading:    '#94A3B8',
  },
  // Per-variation surface palettes
  editorial: {
    bg: '#F5F2EC',
    card: '#FFFFFF',
    ink: '#0B1220',
    mute: '#5A6272',
    rule: '#E4DFD3',
    accent: '#1F3A8A',
    accentSoft: '#E8ECF7',
  },
  technical: {
    bg: '#F4F6F8',
    card: '#FFFFFF',
    ink: '#0B1220',
    mute: '#64748B',
    rule: '#DCE2E9',
    accent: '#1F3A8A',
    accentSoft: '#E8ECF7',
  },
  stacked: {
    bg: '#FAFAF7',
    card: '#FFFFFF',
    ink: '#0B1220',
    mute: '#5A6272',
    rule: '#E5E2DA',
    accent: '#0F172A',
    accentSoft: '#EEF0F5',
  },
};

// Mock ML predictions — realistic EHS content keyed by activity keyword.
// All percentages sum to 100 for the top-3 + residual; "more" stays hidden.
const MOCK_PREDICTIONS = {
  'electrical works': {
    hazard: [
      { label: 'Electric Shock',          score: 0.44 },
      { label: 'Arc Flash',               score: 0.39 },
      { label: 'Fire / Explosion',        score: 0.04 },
      { label: 'Burns — Thermal',         score: 0.03 },
      { label: 'Falls from Height',       score: 0.03 },
      { label: 'Mechanical Injury',       score: 0.02 },
      { label: 'Noise Exposure',          score: 0.02 },
      { label: 'Chemical Exposure',       score: 0.01 },
      { label: 'Ergonomic Strain',        score: 0.01 },
      { label: 'Other',                   score: 0.01 },
    ],
    severity: [
      { label: 'High × Likely',           score: 0.52 },
      { label: 'High × Possible',         score: 0.28 },
      { label: 'Medium × Likely',         score: 0.12 },
      { label: 'Medium × Possible',       score: 0.05 },
      { label: 'Low × Unlikely',          score: 0.03 },
    ],
    controls: [
      { label: 'LOTO + Arc-rated PPE (Cat 2)', score: 0.48 },
      { label: 'Insulated gloves Class 0 + face shield', score: 0.31 },
      { label: 'De-energize + verify zero voltage', score: 0.14 },
      { label: 'Hot-work permit + fire watch', score: 0.04 },
      { label: 'Barrier + signage only', score: 0.03 },
    ],
    remarks: [
      { label: 'Confirm isolation points before commencing work.', score: 0.41 },
      { label: 'Two-person rule required for live work >50V.', score: 0.33 },
      { label: 'Maintain 1m approach boundary for unqualified staff.', score: 0.18 },
      { label: 'Review single-line diagram on-site.', score: 0.08 },
    ],
  },
  'welding': {
    hazard: [
      { label: 'Fire / Explosion',        score: 0.38 },
      { label: 'Burns — Thermal',         score: 0.27 },
      { label: 'Eye Injury (Arc Eye)',    score: 0.18 },
      { label: 'Fume Inhalation',         score: 0.09 },
      { label: 'Electric Shock',          score: 0.04 },
      { label: 'Noise Exposure',          score: 0.02 },
      { label: 'Crush / Impact',          score: 0.02 },
    ],
    severity: [
      { label: 'High × Possible',         score: 0.47 },
      { label: 'Medium × Likely',         score: 0.29 },
      { label: 'High × Likely',           score: 0.15 },
      { label: 'Medium × Possible',       score: 0.06 },
      { label: 'Low × Possible',          score: 0.03 },
    ],
    controls: [
      { label: 'Hot-work permit + fire watch + extinguisher', score: 0.51 },
      { label: 'Welding helmet (shade 10+) + leather apron',  score: 0.27 },
      { label: 'Local exhaust ventilation (LEV)',             score: 0.14 },
      { label: 'Flame-retardant curtains + clear 10m radius', score: 0.08 },
    ],
    remarks: [
      { label: 'Obtain PTW before ignition source is introduced.', score: 0.44 },
      { label: 'Fire watch to remain 30 min post-work.',           score: 0.31 },
      { label: 'Confirm no flammable vapours within 11m.',         score: 0.16 },
      { label: 'Gas cylinders upright + secured.',                 score: 0.09 },
    ],
  },
  'confined space': {
    hazard: [
      { label: 'Oxygen Deficiency',       score: 0.41 },
      { label: 'Toxic Gas Exposure',      score: 0.28 },
      { label: 'Engulfment',              score: 0.12 },
      { label: 'Fire / Explosion',        score: 0.09 },
      { label: 'Entrapment',              score: 0.06 },
      { label: 'Heat Stress',             score: 0.04 },
    ],
    severity: [
      { label: 'High × Likely',           score: 0.58 },
      { label: 'High × Possible',         score: 0.24 },
      { label: 'Medium × Likely',         score: 0.12 },
      { label: 'Medium × Possible',       score: 0.06 },
    ],
    controls: [
      { label: 'Entry permit + continuous gas monitoring', score: 0.49 },
      { label: 'Supplied-air respirator + rescue harness', score: 0.28 },
      { label: 'Standby attendant + communications',       score: 0.16 },
      { label: 'Pre-entry ventilation (≥5 volumes)',       score: 0.07 },
    ],
    remarks: [
      { label: 'Gas test: O₂ 19.5–23.5%, LEL <10%, CO <25ppm.', score: 0.46 },
      { label: 'Retest atmosphere every 2 hours minimum.',       score: 0.29 },
      { label: 'Rescue plan rehearsed before entry.',            score: 0.18 },
      { label: 'Communications check every 15 minutes.',         score: 0.07 },
    ],
  },
  'working at height': {
    hazard: [
      { label: 'Falls from Height',       score: 0.61 },
      { label: 'Falling Objects',         score: 0.19 },
      { label: 'Struck-by (Swing Fall)',  score: 0.08 },
      { label: 'Collapse of Platform',    score: 0.06 },
      { label: 'Weather Exposure',        score: 0.04 },
      { label: 'Electrical (Overhead)',   score: 0.02 },
    ],
    severity: [
      { label: 'High × Likely',           score: 0.54 },
      { label: 'High × Possible',         score: 0.31 },
      { label: 'Medium × Likely',         score: 0.10 },
      { label: 'Medium × Possible',       score: 0.05 },
    ],
    controls: [
      { label: 'Full-body harness + double lanyard', score: 0.44 },
      { label: 'Guardrails + toe-boards on platform', score: 0.28 },
      { label: 'Anchor point certified ≥22kN',        score: 0.18 },
      { label: 'Exclusion zone below + signage',      score: 0.10 },
    ],
    remarks: [
      { label: 'Work-at-height permit required above 3m.', score: 0.42 },
      { label: 'Daily harness inspection before use.',     score: 0.29 },
      { label: 'Stop work if wind exceeds 10 m/s.',        score: 0.19 },
      { label: 'Rescue-from-height plan on site.',         score: 0.10 },
    ],
  },
};

// Default to "electrical works" if user types something unrecognised.
function lookupPredictions(activity) {
  if (!activity) return null;
  const a = activity.toLowerCase().trim();
  const keys = Object.keys(MOCK_PREDICTIONS);
  const hit = keys.find(k => a.includes(k) || k.includes(a));
  return MOCK_PREDICTIONS[hit || 'electrical works'];
}

// Quiz questions keyed by activity + step-1 hazard. Static; enough variety
// to feel generated.
const MOCK_QUIZ = [
  {
    q: 'What is the primary injury mechanism when an arc flash occurs during electrical panel maintenance?',
    options: [
      'Burns from high-temperature plasma and pressure wave',
      'Electric shock from direct contact with live terminals',
      'Falls caused by instinctive recoil from the arc',
      'Long-term hearing loss from the arc acoustic signature',
    ],
    correct: 0,
    explain: 'Arc flash generates plasma temperatures up to 19,000°C and a pressure wave that can exceed 900 kg/m². Severe burns — not shock — are the dominant injury mode.',
  },
  {
    q: 'Before beginning work on de-energized electrical equipment, which step comes FIRST in the LOTO sequence?',
    options: [
      'Apply personal lock to the disconnect',
      'Notify affected personnel of the shutdown',
      'Verify absence of voltage with a tested meter',
      'Dissipate stored energy (capacitors, springs)',
    ],
    correct: 1,
    explain: 'The WSH LOTO sequence requires notification first, then isolation, lockout, voltage verification, and stored-energy release. Notification prevents unexpected energization attempts.',
  },
  {
    q: 'Arc-rated PPE Category 2 is rated for an incident energy of at least:',
    options: [
      '1.2 cal/cm²',
      '4 cal/cm²',
      '8 cal/cm²',
      '25 cal/cm²',
    ],
    correct: 2,
    explain: 'Category 2 arc-rated clothing is rated to 8 cal/cm². Cat 1 is 4, Cat 3 is 25, Cat 4 is 40.',
  },
  {
    q: 'The minimum approach boundary for unqualified personnel near exposed energized conductors rated 50–300V is:',
    options: [
      '300 mm',
      '1.07 m',
      '3.05 m',
      'No restriction if wearing gloves',
    ],
    correct: 1,
    explain: 'WSH electrical safety guidance mirrors NFPA 70E: 1.07 m (42 in) limited approach for unqualified personnel at 50–300V phase-to-phase.',
  },
  {
    q: 'Who bears ultimate legal responsibility for ensuring a Permit-to-Work is valid and conditions are met before electrical work begins?',
    options: [
      'The equipment manufacturer',
      'The issuing authority who signed the PTW',
      'The individual worker performing the task',
      'The facility insurance provider',
    ],
    correct: 1,
    explain: 'Under the WSH Act, the issuing authority carries legal accountability for PTW validity and precondition verification. Workers verify conditions on-site but the issuer holds the duty.',
  },
];

Object.assign(window, { TOKENS, MOCK_PREDICTIONS, MOCK_QUIZ, lookupPredictions });
