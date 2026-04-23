// InspectionPage — renders one of three layout variants.
// Owns all state: activity, per-card state (empty/loading/predicted/confirmed/
// overridden), selected indices, plus downstream re-prediction orchestration.

const STEPS = [
  { key: 'hazard',   title: 'Hazard Type' },
  { key: 'severity', title: 'Severity · Likelihood' },
  { key: 'controls', title: 'Controls & PPE' },
  { key: 'remarks',  title: 'Recommended Remark' },
];

function useInspectionState() {
  const [activity, setActivity] = useState('');
  const [predictions, setPredictions] = useState(null);
  const [cardStates, setCardStates] = useState(
    () => STEPS.reduce((a, s) => ({ ...a, [s.key]: 'empty' }), {})
  );
  const [selected, setSelected] = useState(
    () => STEPS.reduce((a, s) => ({ ...a, [s.key]: 0 }), {})
  );
  const debounceRef = useRef(null);

  // Trigger prediction flow on activity change (debounced)
  const runPrediction = useCallback((value) => {
    clearTimeout(debounceRef.current);
    if (!value.trim()) {
      setPredictions(null);
      setCardStates(STEPS.reduce((a, s) => ({ ...a, [s.key]: 'empty' }), {}));
      setSelected(STEPS.reduce((a, s) => ({ ...a, [s.key]: 0 }), {}));
      return;
    }
    // All cards shimmer
    setCardStates(STEPS.reduce((a, s) => ({ ...a, [s.key]: 'loading' }), {}));
    debounceRef.current = setTimeout(() => {
      const result = lookupPredictions(value);
      setPredictions(result);
      // Stagger results: 0, 120, 240, 360 ms
      STEPS.forEach((s, i) => {
        setTimeout(() => {
          setCardStates(prev => ({ ...prev, [s.key]: 'predicted' }));
        }, i * 120);
      });
      setSelected(STEPS.reduce((a, s) => ({ ...a, [s.key]: 0 }), {}));
    }, 500);
  }, []);

  const setActivityAndRun = useCallback((v) => {
    setActivity(v);
    runPrediction(v);
  }, [runPrediction]);

  const confirmCard = (key) => {
    setCardStates(prev => ({ ...prev, [key]: 'confirmed' }));
  };

  const overrideCard = (key, idx) => {
    setSelected(prev => ({ ...prev, [key]: idx }));
    setCardStates(prev => ({ ...prev, [key]: 'overridden' }));
    // Shimmer downstream cards, then re-predict. In the mock we just reuse
    // existing predictions but shift top pick by 1 to simulate a different path.
    const thisStepIndex = STEPS.findIndex(s => s.key === key);
    const downstream = STEPS.slice(thisStepIndex + 1);
    downstream.forEach((s, i) => {
      setCardStates(prev => ({ ...prev, [s.key]: 'loading' }));
    });
    downstream.forEach((s, i) => {
      setTimeout(() => {
        setCardStates(prev => ({ ...prev, [s.key]: 'predicted' }));
        // Mock: override step slightly changes downstream top picks deterministically
        setSelected(prev => ({ ...prev, [s.key]: 0 }));
      }, 500 + i * 140);
    });
  };

  const reset = () => {
    setActivity('');
    setPredictions(null);
    setCardStates(STEPS.reduce((a, s) => ({ ...a, [s.key]: 'empty' }), {}));
    setSelected(STEPS.reduce((a, s) => ({ ...a, [s.key]: 0 }), {}));
  };

  const allConfirmed = STEPS.every(s => cardStates[s.key] === 'confirmed');

  return {
    activity, setActivity: setActivityAndRun,
    predictions, cardStates, selected,
    confirmCard, overrideCard, reset, allConfirmed,
  };
}

// ─── Activity input (variant-styled) ────────────────────────
function ActivityInput({ value, onChange, palette, variant, suggestions = [] }) {
  const [focused, setFocused] = useState(false);
  const inputStyle = {
    editorial: {
      width: '100%', height: 60,
      padding: '0 20px 0 52px',
      fontFamily: "'Source Serif 4', serif",
      fontSize: 19, fontWeight: 400, fontStyle: 'italic',
      color: palette.ink,
      background: palette.card,
      border: `1px solid ${focused ? palette.accent : palette.rule}`,
      borderRadius: 4,
      outline: 'none',
      transition: 'border-color .2s, box-shadow .2s',
      boxShadow: focused ? `0 0 0 3px ${palette.accent}15` : 'none',
    },
    technical: {
      width: '100%', height: 52,
      padding: '0 20px 0 48px',
      fontFamily: "'Inter', system-ui",
      fontSize: 15, fontWeight: 500,
      color: palette.ink,
      background: palette.card,
      border: `1px solid ${focused ? palette.accent : palette.rule}`,
      borderRadius: 6,
      outline: 'none',
      transition: 'border-color .2s, box-shadow .2s',
      boxShadow: focused ? `0 0 0 3px ${palette.accent}15` : 'none',
    },
    stacked: {
      width: '100%', height: 72,
      padding: '0 24px 0 56px',
      fontFamily: "'Source Serif 4', serif",
      fontSize: 22, fontWeight: 400,
      color: palette.ink,
      background: palette.card,
      border: `1px solid ${focused ? palette.accent : palette.rule}`,
      borderRadius: 2,
      outline: 'none',
      transition: 'border-color .2s',
    },
  }[variant];

  return (
    <div style={{ position: 'relative' }}>
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none"
        style={{
          position: 'absolute',
          left: variant === 'stacked' ? 22 : 18,
          top: '50%', transform: 'translateY(-50%)',
          pointerEvents: 'none',
        }}>
        <circle cx="9" cy="9" r="6" stroke={palette.mute} strokeWidth="1.5" />
        <path d="M13.5 13.5L17 17" stroke={palette.mute}
          strokeWidth="1.5" strokeLinecap="round" />
      </svg>
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder="What activity are you inspecting? e.g. Electrical Works, Welding…"
        style={inputStyle}
      />
      {value && (
        <button onClick={() => onChange('')}
          style={{
            position: 'absolute',
            right: 16, top: '50%',
            transform: 'translateY(-50%)',
            width: 24, height: 24, borderRadius: '50%',
            background: palette.bg,
            border: `1px solid ${palette.rule}`,
            color: palette.mute, cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 14, lineHeight: 1,
          }}>×</button>
      )}
    </div>
  );
}

// ─── Suggestion chips ───────────────────────────────────────
function SuggestionChips({ onPick, palette, variant }) {
  const suggestions = ['Electrical Works', 'Welding', 'Confined Space', 'Working at Height'];
  return (
    <div style={{
      display: 'flex', flexWrap: 'wrap', gap: 8,
      marginTop: 14, alignItems: 'center',
    }}>
      <span style={{
        fontFamily: "'Inter', system-ui", fontSize: 11,
        color: palette.mute, letterSpacing: '0.1em',
        textTransform: 'uppercase', fontWeight: 500,
        marginRight: 4,
      }}>Common</span>
      {suggestions.map(s => (
        <button key={s} onClick={() => onPick(s)}
          style={{
            padding: '6px 12px',
            fontFamily: "'Inter', system-ui",
            fontSize: 12, color: palette.ink,
            background: palette.card,
            border: `1px solid ${palette.rule}`,
            borderRadius: 999, cursor: 'pointer',
            transition: 'background .15s, border-color .15s',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = palette.accentSoft;
            e.currentTarget.style.borderColor = palette.accent + '40';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = palette.card;
            e.currentTarget.style.borderColor = palette.rule;
          }}>
          {s}
        </button>
      ))}
    </div>
  );
}

window.STEPS = STEPS;
window.useInspectionState = useInspectionState;
window.ActivityInput = ActivityInput;
window.SuggestionChips = SuggestionChips;
