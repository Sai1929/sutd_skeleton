// Variation A — Editorial Grid
// Serif headlines, warm off-white bg, 2×2 card grid, numbered "Step" indicators,
// prose-like page header. The academic-journal feel.

function InspectionEditorial({ onSubmit }) {
  const palette = TOKENS.editorial;
  const S = useInspectionState();

  const topHazard = S.predictions?.hazard[S.selected.hazard];
  const topSeverity = S.predictions?.severity[S.selected.severity];

  return (
    <div style={{ padding: '56px 64px 80px', maxWidth: 1200, margin: '0 auto' }}>
      {/* Page header */}
      <div style={{ marginBottom: 44, maxWidth: 720 }}>
        <div style={{
          fontFamily: "'Inter', system-ui", fontSize: 11,
          letterSpacing: '0.16em', textTransform: 'uppercase',
          color: palette.mute, fontWeight: 500, marginBottom: 14,
        }}>
          § 02 · AI-Assisted Inspection
        </div>
        <h1 style={{
          fontFamily: "'Source Serif 4', serif",
          fontSize: 44, fontWeight: 500,
          color: palette.ink, lineHeight: 1.1,
          letterSpacing: '-0.02em', margin: 0,
        }}>
          Record an <em style={{ fontStyle: 'italic' }}>inspection</em>.
        </h1>
        <p style={{
          fontFamily: "'Source Serif 4', serif",
          fontSize: 18, color: palette.mute,
          lineHeight: 1.55, marginTop: 18,
          letterSpacing: '-0.005em', fontWeight: 400,
        }}>
          Enter the activity below. The model will predict hazard type, severity,
          required controls, and a recommended remark. You may confirm each
          prediction or override any field — downstream predictions refresh
          accordingly.
        </p>
      </div>

      {/* Activity input */}
      <div style={{ marginBottom: 12 }}>
        <ActivityInput
          value={S.activity}
          onChange={S.setActivity}
          palette={palette}
          variant="editorial"
        />
        <SuggestionChips onPick={S.setActivity} palette={palette} variant="editorial" />
      </div>

      {/* Risk banner */}
      {topSeverity && (
        <div style={{ marginTop: 28, marginBottom: 28 }}>
          <RiskBadge severityLabel={topSeverity.label} variant="banner" />
        </div>
      )}

      {/* 2x2 card grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 20,
        marginTop: S.predictions ? 0 : 36,
      }}>
        {STEPS.map((s, i) => (
          <PredictionCard
            key={s.key}
            step={i + 1}
            title={s.title}
            options={S.predictions ? S.predictions[s.key] : []}
            state={S.cardStates[s.key]}
            selectedIndex={S.selected[s.key]}
            onConfirm={() => S.confirmCard(s.key)}
            onOverride={(idx) => S.overrideCard(s.key, idx)}
            palette={palette}
            variant="editorial"
          />
        ))}
      </div>

      {/* Submit */}
      <div style={{
        marginTop: 48,
        display: 'flex', alignItems: 'center',
        justifyContent: 'space-between',
        paddingTop: 28, borderTop: `1px solid ${palette.rule}`,
      }}>
        <div style={{
          fontFamily: "'Inter', system-ui", fontSize: 12,
          color: palette.mute,
        }}>
          {S.allConfirmed
            ? 'All four fields confirmed. Ready to submit for review.'
            : `${STEPS.filter(s => S.cardStates[s.key] === 'confirmed').length} of 4 fields confirmed.`}
        </div>
        <button
          disabled={!S.allConfirmed}
          onClick={() => S.allConfirmed && onSubmit(S.activity)}
          style={{
            padding: '15px 36px',
            fontFamily: "'Inter', system-ui", fontSize: 14,
            fontWeight: 600, letterSpacing: '-0.005em',
            color: S.allConfirmed ? palette.card : palette.mute,
            background: S.allConfirmed ? palette.ink : palette.rule,
            border: 'none', borderRadius: 4,
            cursor: S.allConfirmed ? 'pointer' : 'not-allowed',
            transition: 'background .2s, transform .15s',
            boxShadow: S.allConfirmed ? `0 4px 12px ${palette.ink}20` : 'none',
          }}
          onMouseEnter={e => { if (S.allConfirmed) e.currentTarget.style.transform = 'translateY(-1px)'; }}
          onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; }}
        >
          Submit Inspection →
        </button>
      </div>
    </div>
  );
}

window.InspectionEditorial = InspectionEditorial;
