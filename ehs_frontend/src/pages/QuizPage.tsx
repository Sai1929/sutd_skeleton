import { useState, useEffect } from 'react'
import { generateQuiz, QuizQuestion } from '../api/quiz'

type Phase = 'form' | 'loading' | 'question' | 'results'

function riskBandColor(pct: number) {
  if (pct >= 0.8) return '#1F7A3A'
  if (pct >= 0.5) return '#B26A00'
  return '#C4302B'
}

function ScoreRing({ correct, total }: { correct: number; total: number }) {
  const [animate, setAnimate] = useState(false)
  useEffect(() => { const t = setTimeout(() => setAnimate(true), 80); return () => clearTimeout(t) }, [])
  const pct = total > 0 ? correct / total : 0
  const r = 44
  const circ = 2 * Math.PI * r
  return (
    <div style={{ position: 'relative', width: 108, height: 108, margin: '0 auto 24px' }}>
      <svg width={108} height={108} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={54} cy={54} r={r} fill="none" stroke="#E4DFD3" strokeWidth={7} />
        <circle cx={54} cy={54} r={r} fill="none" stroke={riskBandColor(pct)} strokeWidth={7}
          strokeDasharray={`${animate ? pct * circ : 0} ${circ}`} strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.9s cubic-bezier(.2,.7,.3,1)' }} />
      </svg>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ fontFamily: '"Source Serif 4", serif', fontSize: 30, fontWeight: 600, color: riskBandColor(pct), lineHeight: 1 }}>{correct}</span>
        <span style={{ fontFamily: 'Inter, system-ui', fontSize: 12, color: '#5A6272', marginTop: 2 }}>/ {total}</span>
      </div>
    </div>
  )
}

function TypeBadge({ type }: { type: QuizQuestion['question_type'] }) {
  const map = {
    mcq: { label: 'MCQ', bg: 'rgba(31,58,138,0.09)', color: '#1F3A8A', border: 'rgba(31,58,138,0.2)' },
    descriptive: { label: 'Descriptive', bg: 'rgba(180,83,9,0.09)', color: '#B45309', border: 'rgba(180,83,9,0.2)' },
    scenario: { label: 'Scenario', bg: 'rgba(124,58,237,0.09)', color: '#7C3AED', border: 'rgba(124,58,237,0.2)' },
  }
  const s = map[type]
  return (
    <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 10, fontWeight: 700, fontFamily: 'Inter, system-ui', letterSpacing: '0.08em', textTransform: 'uppercase', background: s.bg, color: s.color, border: `1px solid ${s.border}` }}>
      {s.label}
    </span>
  )
}

const FIELD_LABEL: React.CSSProperties = {
  display: 'block', fontFamily: 'Inter, system-ui', fontSize: 11,
  letterSpacing: '0.12em', textTransform: 'uppercase', color: '#5A6272',
  fontWeight: 500, marginBottom: 8,
}
const INPUT_STYLE: React.CSSProperties = {
  width: '100%', padding: '12px 16px', fontFamily: 'Inter, system-ui', fontSize: 14,
  color: '#0B1220', background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: 4,
  outline: 'none', boxSizing: 'border-box',
}

export function QuizPage() {
  const [phase, setPhase] = useState<Phase>('form')
  const [activity, setActivity] = useState('')
  const [hazardType, setHazardType] = useState('')
  const [riskLevel, setRiskLevel] = useState('')
  const [controls, setControls] = useState('')
  const [remarks, setRemarks] = useState('')
  const [error, setError] = useState<string | null>(null)

  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [currentIdx, setCurrentIdx] = useState(0)
  const [mcqAnswers, setMcqAnswers] = useState<Record<number, number>>({})
  const [textAnswers, setTextAnswers] = useState<Record<number, string>>({})

  const canSubmit = activity.trim().length > 0
  const currentQ = questions[currentIdx]
  const isMcq = currentQ?.question_type === 'mcq'
  const selectedMcq = mcqAnswers[currentIdx]
  const typedText = textAnswers[currentIdx] ?? ''
  const canProceed = isMcq ? selectedMcq != null : typedText.trim().length > 0
  const isLast = currentIdx === questions.length - 1
  const mcqTotal = questions.filter(q => q.question_type === 'mcq').length
  const correctCount = questions.reduce((acc, q, i) => {
    if (q.question_type !== 'mcq') return acc
    const ans = mcqAnswers[i]
    return ans !== undefined && ans === q.correct_answer.charCodeAt(0) - 65 ? acc + 1 : acc
  }, 0)

  const handleGenerate = async () => {
    if (!canSubmit) return
    setPhase('loading')
    setError(null)
    try {
      const res = await generateQuiz({
        activity: activity.trim(),
        hazard_type: hazardType.trim() || 'Not specified',
        severity_likelihood: riskLevel.trim() || 'Not specified',
        moc_ppe: controls.trim() || 'Not specified',
        remarks: remarks.trim(),
      })
      setQuestions(res.questions)
      setCurrentIdx(0)
      setMcqAnswers({})
      setTextAnswers({})
      setPhase('question')
    } catch {
      setError('Failed to generate quiz. Check backend connection.')
      setPhase('form')
    }
  }

  const handleNext = () => { if (isLast) setPhase('results'); else setCurrentIdx(i => i + 1) }
  const handleRetake = () => { setCurrentIdx(0); setMcqAnswers({}); setTextAnswers({}); setPhase('question') }
  const handleReset = () => { setPhase('form'); setQuestions([]); setCurrentIdx(0); setMcqAnswers({}); setTextAnswers({}); setError(null) }

  return (
    <div style={{ padding: '56px 64px 80px', maxWidth: 900, margin: '0 auto' }}>
      <div style={{ marginBottom: 44, maxWidth: 720 }}>
        <div style={{ fontFamily: 'Inter, system-ui', fontSize: 11, letterSpacing: '0.16em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 500, marginBottom: 14 }}>
          § 04 · Compliance Quiz
        </div>
        <h1 style={{ fontFamily: '"Source Serif 4", serif', fontSize: 44, fontWeight: 500, color: '#0B1220', lineHeight: 1.1, letterSpacing: '-0.02em', margin: 0 }}>
          Test your <em style={{ fontStyle: 'italic' }}>understanding</em>.
        </h1>
        <p style={{ fontFamily: '"Source Serif 4", serif', fontSize: 18, color: '#5A6272', lineHeight: 1.55, marginTop: 18, letterSpacing: '-0.005em', fontWeight: 400 }}>
          Enter activity and RA details. Generates 2 MCQ + 2 descriptive + 1 scenario question.
        </p>
      </div>

      {/* ── FORM ── */}
      {phase === 'form' && (
        <div style={{ maxWidth: 760, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <label style={FIELD_LABEL}>Activity <span style={{ color: '#B91C1C' }}>*</span></label>
            <input value={activity} onChange={e => setActivity(e.target.value)} placeholder="e.g. Confined space entry for tank cleaning" style={INPUT_STYLE} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <label style={FIELD_LABEL}>Hazard Type</label>
              <input value={hazardType} onChange={e => setHazardType(e.target.value)} placeholder="e.g. Oxygen deficiency, toxic gas" style={INPUT_STYLE} />
            </div>
            <div>
              <label style={FIELD_LABEL}>Risk Level</label>
              <input value={riskLevel} onChange={e => setRiskLevel(e.target.value)} placeholder="e.g. High (L4 × S4)" style={INPUT_STYLE} />
            </div>
          </div>
          <div>
            <label style={FIELD_LABEL}>Controls / PPE</label>
            <textarea value={controls} onChange={e => setControls(e.target.value)} placeholder="e.g. Gas testing before entry, SCBA, safety watchman, PTW…" rows={3} style={{ ...INPUT_STYLE, resize: 'vertical', lineHeight: 1.6 }} />
          </div>
          <div>
            <label style={FIELD_LABEL}>Remarks</label>
            <input value={remarks} onChange={e => setRemarks(e.target.value)} placeholder="Optional additional context" style={INPUT_STYLE} />
          </div>
          {error && <div style={{ padding: '12px 16px', background: '#FFF3F3', border: '1px solid #FBBFBF', borderRadius: 4, fontFamily: 'Inter, system-ui', fontSize: 13, color: '#B91C1C' }}>{error}</div>}
          <div style={{ marginTop: 4 }}>
            <button onClick={handleGenerate} disabled={!canSubmit} style={{ padding: '14px 32px', fontFamily: 'Inter, system-ui', fontSize: 14, fontWeight: 600, color: '#FFFFFF', background: canSubmit ? '#0B1220' : '#9CA3AF', border: 'none', borderRadius: 4, cursor: canSubmit ? 'pointer' : 'not-allowed', transition: 'transform .15s' }}
              onMouseEnter={e => { if (canSubmit) e.currentTarget.style.transform = 'translateY(-1px)' }}
              onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)' }}>
              Generate Quiz →
            </button>
          </div>
        </div>
      )}

      {/* ── LOADING ── */}
      {phase === 'loading' && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: 80, gap: 24 }}>
          <div style={{ width: 40, height: 40, borderRadius: '50%', border: '3px solid #E4DFD3', borderTopColor: '#1F3A8A', animation: 'spin 0.9s linear infinite' }} />
          <div style={{ fontFamily: '"Source Serif 4", serif', fontSize: 20, color: '#0B1220', fontStyle: 'italic' }}>Generating questions…</div>
          <div style={{ fontFamily: 'Inter, system-ui', fontSize: 13, color: '#5A6272' }}>{activity}</div>
        </div>
      )}

      {/* ── QUESTION ── */}
      {phase === 'question' && currentQ && (
        <div style={{ maxWidth: 760 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 32, fontFamily: '"JetBrains Mono", monospace', fontSize: 11, color: '#5A6272' }}>
            <span>Question {currentIdx + 1} / {questions.length}</span>
            <div style={{ flex: 1, height: 3, borderRadius: 2, background: '#E4DFD3', overflow: 'hidden' }}>
              <div style={{ width: `${((currentIdx + 1) / questions.length) * 100}%`, height: '100%', background: '#1F3A8A', transition: 'width .3s' }} />
            </div>
            <button onClick={handleReset} style={{ background: 'none', border: 'none', color: '#5A6272', cursor: 'pointer', fontFamily: 'Inter, system-ui', fontSize: 12, textDecoration: 'underline', padding: 0 }}>Cancel</button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
            <TypeBadge type={currentQ.question_type} />
            <span style={{ fontFamily: 'Inter, system-ui', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 500 }}>
              {activity}
            </span>
          </div>
          <h2 style={{ fontFamily: '"Source Serif 4", serif', fontSize: 26, fontWeight: 500, color: '#0B1220', lineHeight: 1.3, letterSpacing: '-0.015em', margin: 0, marginBottom: 28 }}>
            {currentQ.question_text}
          </h2>

          {/* MCQ */}
          {currentQ.question_type === 'mcq' && currentQ.options && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {currentQ.options.map((opt, i) => {
                const picked = selectedMcq === i
                return (
                  <button key={i} onClick={() => setMcqAnswers(prev => ({ ...prev, [currentIdx]: i }))} style={{ textAlign: 'left', padding: '16px 20px', background: picked ? '#E8ECF7' : '#FFFFFF', border: `1.5px solid ${picked ? '#1F3A8A' : '#E4DFD3'}`, borderRadius: 6, cursor: 'pointer', fontFamily: 'Inter, system-ui', fontSize: 15, color: '#0B1220', lineHeight: 1.4, display: 'flex', alignItems: 'flex-start', gap: 14, transition: 'all .15s' }}>
                    <span style={{ width: 22, height: 22, borderRadius: '50%', border: `1.5px solid ${picked ? '#1F3A8A' : '#E4DFD3'}`, background: picked ? '#1F3A8A' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Inter, system-ui', fontSize: 11, fontWeight: 600, flexShrink: 0, marginTop: 1, color: picked ? '#fff' : '#0B1220' }}>
                      {picked ? <svg width={11} height={11} viewBox="0 0 16 16" fill="none"><path d="M3 8.5l3 3 7-7" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg> : String.fromCharCode(65 + i)}
                    </span>
                    <span>{opt}</span>
                  </button>
                )
              })}
            </div>
          )}

          {/* Descriptive / Scenario */}
          {(currentQ.question_type === 'descriptive' || currentQ.question_type === 'scenario') && (
            <textarea
              value={typedText}
              onChange={e => setTextAnswers(prev => ({ ...prev, [currentIdx]: e.target.value }))}
              placeholder="Type your answer here…"
              rows={6}
              style={{ width: '100%', padding: '14px 16px', fontFamily: 'Inter, system-ui', fontSize: 14, color: '#0B1220', background: '#FFFFFF', border: '1.5px solid #E4DFD3', borderRadius: 6, outline: 'none', resize: 'vertical', lineHeight: 1.6, boxSizing: 'border-box' }}
            />
          )}

          <div style={{ marginTop: 32, display: 'flex', justifyContent: 'flex-end' }}>
            <button disabled={!canProceed} onClick={handleNext} style={{ padding: '13px 28px', fontFamily: 'Inter, system-ui', fontSize: 14, fontWeight: 600, color: canProceed ? '#FFFFFF' : '#5A6272', background: canProceed ? '#0B1220' : '#E4DFD3', border: 'none', borderRadius: 4, cursor: canProceed ? 'pointer' : 'not-allowed' }}>
              {isLast ? 'Submit Quiz →' : 'Next Question →'}
            </button>
          </div>
        </div>
      )}

      {/* ── RESULTS ── */}
      {phase === 'results' && (
        <div style={{ maxWidth: 760 }}>
          <div style={{ textAlign: 'center', marginBottom: 40, paddingBottom: 32, borderBottom: '1px solid #E4DFD3' }}>
            <ScoreRing correct={correctCount} total={mcqTotal} />
            <h2 style={{ fontFamily: '"Source Serif 4", serif', fontSize: 28, fontWeight: 500, color: '#0B1220', margin: '0 0 10px', letterSpacing: '-0.015em' }}>Quiz Complete</h2>
            <div style={{ fontFamily: 'Inter, system-ui', fontSize: 14, color: '#5A6272', lineHeight: 1.5 }}>
              <span style={{ fontWeight: 600, color: riskBandColor(mcqTotal > 0 ? correctCount / mcqTotal : 0) }}>{correctCount} of {mcqTotal} MCQ correct</span>
              {' '}· {questions.length - mcqTotal} written question{questions.length - mcqTotal !== 1 ? 's' : ''} for self-review below.
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {questions.map((q, i) => {
              if (q.question_type === 'mcq') {
                const ansIdx = mcqAnswers[i]
                const correctIdx = q.correct_answer.charCodeAt(0) - 65
                const isCorrect = ansIdx === correctIdx
                const userAns = ansIdx != null ? q.options?.[ansIdx] : '—'
                const correctAns = q.options?.[correctIdx]
                return (
                  <div key={i} style={{ background: '#FFFFFF', border: `1px solid ${isCorrect ? '#C8DFC8' : 'rgba(196,48,43,0.22)'}`, borderRadius: 6, overflow: 'hidden' }}>
                    <div style={{ padding: '8px 16px', background: isCorrect ? 'rgba(31,122,58,0.07)' : 'rgba(196,48,43,0.06)', display: 'flex', alignItems: 'center', gap: 10, borderBottom: `1px solid ${isCorrect ? '#C8DFC8' : 'rgba(196,48,43,0.2)'}` }}>
                      <div style={{ width: 20, height: 20, borderRadius: '50%', background: isCorrect ? 'rgba(31,122,58,0.15)' : 'rgba(196,48,43,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                        {isCorrect ? <svg width={10} height={10} viewBox="0 0 16 16" fill="none"><path d="M3 8.5l3 3 7-7" stroke="#1F7A3A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg> : <span style={{ color: '#C4302B', fontSize: 9, fontWeight: 700 }}>✕</span>}
                      </div>
                      <TypeBadge type="mcq" />
                      <span style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: isCorrect ? '#1F7A3A' : '#C4302B', fontWeight: 600 }}>Q{i + 1} · {isCorrect ? 'Correct' : 'Incorrect'}</span>
                    </div>
                    <div style={{ padding: '14px 18px' }}>
                      <div style={{ fontFamily: 'Inter, system-ui', fontSize: 13, color: '#0B1220', lineHeight: 1.45, fontWeight: 500, marginBottom: 12 }}>{q.question_text}</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '8px 12px', borderRadius: 4, background: isCorrect ? 'rgba(31,122,58,0.07)' : 'rgba(196,48,43,0.07)', border: `1px solid ${isCorrect ? '#C8DFC8' : 'rgba(196,48,43,0.25)'}` }}>
                          <span style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 9, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: isCorrect ? '#1F7A3A' : '#C4302B', flexShrink: 0, paddingTop: 1, minWidth: 60 }}>Your ans.</span>
                          <span style={{ fontFamily: 'Inter, system-ui', fontSize: 12, color: '#0B1220', lineHeight: 1.4 }}>{ansIdx != null ? String.fromCharCode(65 + ansIdx) : '—'}. {userAns}</span>
                        </div>
                        {!isCorrect && (
                          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '8px 12px', borderRadius: 4, background: 'rgba(31,122,58,0.06)', border: '1px solid #C8DFC8' }}>
                            <span style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 9, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#1F7A3A', flexShrink: 0, paddingTop: 1, minWidth: 60 }}>Correct</span>
                            <span style={{ fontFamily: 'Inter, system-ui', fontSize: 12, color: '#0B1220', lineHeight: 1.4 }}>{q.correct_answer}. {correctAns}</span>
                          </div>
                        )}
                      </div>
                      {q.explanation && <div style={{ marginTop: 10, padding: '9px 12px', background: '#F5F2EC', borderRadius: 3, fontFamily: 'Inter, system-ui', fontSize: 12, color: '#5A6272', lineHeight: 1.5, fontStyle: 'italic' }}>{q.explanation}</div>}
                    </div>
                  </div>
                )
              }

              // Descriptive / Scenario
              const userText = textAnswers[i] || '—'
              return (
                <div key={i} style={{ background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: 6, overflow: 'hidden' }}>
                  <div style={{ padding: '8px 16px', background: '#F5F2EC', display: 'flex', alignItems: 'center', gap: 10, borderBottom: '1px solid #E4DFD3' }}>
                    <TypeBadge type={q.question_type} />
                    <span style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 600 }}>Q{i + 1} · Self-Review</span>
                  </div>
                  <div style={{ padding: '14px 18px' }}>
                    <div style={{ fontFamily: 'Inter, system-ui', fontSize: 13, color: '#0B1220', lineHeight: 1.45, fontWeight: 500, marginBottom: 12 }}>{q.question_text}</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      <div style={{ padding: '10px 12px', borderRadius: 4, background: 'rgba(31,58,138,0.05)', border: '1px solid rgba(31,58,138,0.15)' }}>
                        <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 9, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#1F3A8A', marginBottom: 6 }}>Your answer</div>
                        <div style={{ fontFamily: 'Inter, system-ui', fontSize: 12, color: '#0B1220', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{userText}</div>
                      </div>
                      <div style={{ padding: '10px 12px', borderRadius: 4, background: 'rgba(31,122,58,0.06)', border: '1px solid #C8DFC8' }}>
                        <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 9, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#1F7A3A', marginBottom: 6 }}>Model answer</div>
                        <div style={{ fontFamily: 'Inter, system-ui', fontSize: 12, color: '#0B1220', lineHeight: 1.5 }}>{q.correct_answer}</div>
                      </div>
                    </div>
                    {q.explanation && <div style={{ marginTop: 10, padding: '9px 12px', background: '#F5F2EC', borderRadius: 3, fontFamily: 'Inter, system-ui', fontSize: 12, color: '#5A6272', lineHeight: 1.5, fontStyle: 'italic' }}>{q.explanation}</div>}
                  </div>
                </div>
              )
            })}
          </div>

          <div style={{ marginTop: 36, display: 'flex', gap: 12 }}>
            <button onClick={handleRetake} style={{ padding: '13px 24px', fontFamily: 'Inter, system-ui', fontSize: 13, fontWeight: 600, color: '#FFFFFF', background: '#0B1220', border: 'none', borderRadius: 4, cursor: 'pointer' }}>Retake Quiz →</button>
            <button onClick={handleReset} style={{ padding: '13px 24px', fontFamily: 'Inter, system-ui', fontSize: 13, fontWeight: 500, color: '#5A6272', background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: 4, cursor: 'pointer' }}>New Quiz</button>
          </div>
        </div>
      )}
    </div>
  )
}
