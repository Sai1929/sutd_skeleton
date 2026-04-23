import { useInspection, STEPS } from '../hooks/useInspection'
import { useQuiz } from '../hooks/useQuiz'
import { ActivityInput } from '../components/inspection/ActivityInput'
import { SuggestionChips } from '../components/inspection/SuggestionChips'
import { RiskBanner } from '../components/inspection/RiskBanner'
import { PredictionCard } from '../components/inspection/PredictionCard'
import { QuizOverlay } from '../components/quiz/QuizOverlay'

export function InspectionPage() {
  const S = useInspection()
  const quiz = useQuiz()

  const topSeverity = S.predictions.severity_likelihood[S.selected.severity_likelihood]
  const allConfirmedCount = STEPS.filter(s => S.cardStates[s.key] === 'confirmed' || S.cardStates[s.key] === 'overridden').length

  const handleSubmit = () => {
    if (!S.allConfirmed) return
    quiz.open({
      activity: S.activity,
      hazard_type: S.getSelectedLabel('hazard_type'),
      severity_likelihood: S.getSelectedLabel('severity_likelihood'),
      moc_ppe: S.getSelectedLabel('moc_ppe'),
      remarks: S.getSelectedLabel('remarks'),
    })
  }

  return (
    <div style={{ padding: '56px 64px 80px', maxWidth: 1200, margin: '0 auto' }}>
      {/* Page header */}
      <div style={{ marginBottom: 44, maxWidth: 720 }}>
        <div style={{ fontFamily: 'Inter, system-ui', fontSize: 11, letterSpacing: '0.16em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 500, marginBottom: 14 }}>
          § 02 · AI-Assisted Inspection
        </div>
        <h1 style={{ fontFamily: '"Source Serif 4", serif', fontSize: 44, fontWeight: 500, color: '#0B1220', lineHeight: 1.1, letterSpacing: '-0.02em', margin: 0 }}>
          Record an <em style={{ fontStyle: 'italic' }}>inspection</em>.
        </h1>
        <p style={{ fontFamily: '"Source Serif 4", serif', fontSize: 18, color: '#5A6272', lineHeight: 1.55, marginTop: 18, letterSpacing: '-0.005em', fontWeight: 400 }}>
          Enter the activity below. The model will predict hazard type, severity, required controls, and a recommended remark. You may confirm each prediction or override any field — downstream predictions refresh accordingly.
        </p>
      </div>

      {/* Activity input */}
      <div style={{ marginBottom: 12 }}>
        <ActivityInput value={S.activity} onChange={S.setActivity} />
        <SuggestionChips onPick={S.setActivity} />
      </div>

      {/* Risk banner */}
      {topSeverity && (
        <div style={{ marginTop: 28, marginBottom: 28 }}>
          <RiskBanner label={topSeverity.label} />
        </div>
      )}

      {/* 2×2 card grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginTop: topSeverity ? 0 : 36 }}>
        {STEPS.map((s, i) => (
          <PredictionCard
            key={s.key}
            step={i + 1}
            title={s.title}
            stepKey={s.key}
            options={S.predictions[s.key]}
            state={S.cardStates[s.key]}
            selectedIndex={S.selected[s.key]}
            onConfirm={() => S.confirmCard(s.key)}
            onOverride={(idx) => S.overrideCard(s.key, idx)}
          />
        ))}
      </div>

      {/* Submit footer */}
      <div style={{ marginTop: 48, display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 28, borderTop: '1px solid #E4DFD3' }}>
        <div style={{ fontFamily: 'Inter, system-ui', fontSize: 12, color: '#5A6272' }}>
          {S.allConfirmed ? 'All four fields confirmed. Ready to submit for review.' : `${allConfirmedCount} of 4 fields confirmed.`}
        </div>
        <button disabled={!S.allConfirmed} onClick={handleSubmit} style={{
          padding: '15px 36px', fontFamily: 'Inter, system-ui', fontSize: 14, fontWeight: 600, letterSpacing: '-0.005em',
          color: S.allConfirmed ? '#FFFFFF' : '#5A6272',
          background: S.allConfirmed ? '#0B1220' : '#E4DFD3',
          border: 'none', borderRadius: 4, cursor: S.allConfirmed ? 'pointer' : 'not-allowed',
          boxShadow: S.allConfirmed ? '0 4px 12px rgba(11,18,32,0.13)' : 'none',
          transition: 'background .2s, transform .15s',
        }}
          onMouseEnter={e => { if (S.allConfirmed) (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(-1px)' }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.transform = 'translateY(0)' }}
        >
          Submit Inspection →
        </button>
      </div>

      {/* Quiz overlay */}
      <QuizOverlay quiz={quiz} activity={S.activity} onClose={S.reset} />
    </div>
  )
}
