import { useEffect, useState } from 'react'
import type { useQuiz } from '../../hooks/useQuiz'

type QuizState = ReturnType<typeof useQuiz>

interface Props {
  quiz: QuizState
  activity: string
  onClose: () => void
}

function CheckIcon({ size = 14, color = '#1F7A3A' }) {
  return <svg width={size} height={size} viewBox="0 0 16 16" fill="none"><path d="M3 8.5l3 3 7-7" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
}

function ScoreRing({ correct, total }: { correct: number; total: number }) {
  const pct = total > 0 ? correct / total : 0
  const r = 38
  const circ = 2 * Math.PI * r
  const dash = pct * circ
  const color = pct >= 0.8 ? '#1F7A3A' : pct >= 0.5 ? '#B26A00' : '#C4302B'
  return (
    <div style={{ position: 'relative', width: 96, height: 96, margin: '0 auto 20px' }}>
      <svg width={96} height={96} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={48} cy={48} r={r} fill="none" stroke="#E4DFD3" strokeWidth={6} />
        <circle
          cx={48} cy={48} r={r} fill="none"
          stroke={color} strokeWidth={6}
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.9s cubic-bezier(.2,.7,.3,1)' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0, display: 'flex',
        flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontFamily: '"Source Serif 4", serif', fontSize: 26, fontWeight: 600, color, lineHeight: 1 }}>{correct}</span>
        <span style={{ fontFamily: 'Inter, system-ui', fontSize: 11, color: '#5A6272', marginTop: 2 }}>/ {total}</span>
      </div>
    </div>
  )
}

export function QuizOverlay({ quiz, activity, onClose }: Props) {
  const [showRing, setShowRing] = useState(false)

  useEffect(() => {
    if (quiz.phase === 'results') {
      // Brief delay so CSS transition animates from 0
      const t = setTimeout(() => setShowRing(true), 80)
      return () => clearTimeout(t)
    } else {
      setShowRing(false)
    }
  }, [quiz.phase])

  if (quiz.phase === 'closed') return null

  const { phase, questions, currentIdx, answers, correctCount, select, next, submit, close } = quiz
  const currentQ = questions[currentIdx]
  const selectedOpt = answers[currentIdx]
  const isLast = currentIdx === questions.length - 1

  const handleNext = () => { if (isLast) submit(); else next() }
  const handleClose = () => { close(); onClose() }

  const scoreColor = questions.length > 0
    ? (correctCount / questions.length >= 0.8 ? '#1F7A3A' : correctCount / questions.length >= 0.5 ? '#B26A00' : '#C4302B')
    : '#5A6272'

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 100,
      background: 'rgba(11,18,32,0.67)', backdropFilter: 'blur(3px)',
      display: 'flex', alignItems: 'stretch', justifyContent: 'center',
      animation: 'fadeIn .25s ease-out',
    }}>
      <div style={{
        background: '#F5F2EC', width: '100%', maxWidth: 880,
        margin: '48px auto', borderRadius: 6, overflow: 'hidden',
        animation: 'slideUp .4s cubic-bezier(.2,.8,.25,1)',
        display: 'flex', flexDirection: 'column',
        boxShadow: '0 20px 60px rgba(11,18,32,0.25)',
      }}>
        {/* Header */}
        <div style={{ padding: '18px 32px', background: '#FFFFFF', borderBottom: '1px solid #E4DFD3', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <button onClick={handleClose} style={{ background: 'transparent', border: 'none', color: '#5A6272', cursor: 'pointer', fontFamily: 'Inter, system-ui', fontSize: 13, display: 'flex', alignItems: 'center', gap: 6, padding: 0 }}>
            ← Back to Inspection
          </button>
          {phase === 'question' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontFamily: '"JetBrains Mono", monospace', fontSize: 11, color: '#5A6272' }}>
              <span>Question {currentIdx + 1} / {questions.length}</span>
              <div style={{ width: 140, height: 3, borderRadius: 2, background: '#E4DFD3', overflow: 'hidden' }}>
                <div style={{ width: `${((currentIdx + 1) / questions.length) * 100}%`, height: '100%', background: '#1F3A8A', transition: 'width .3s' }} />
              </div>
            </div>
          )}
          {phase === 'results' && (
            <div style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 11, color: scoreColor, fontWeight: 600, letterSpacing: '0.08em' }}>
              {correctCount} / {questions.length} CORRECT
            </div>
          )}
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflow: 'auto', padding: '40px 56px 48px' }}>

          {/* Loading */}
          {phase === 'loading' && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '80px 0', gap: 24 }}>
              <div style={{ width: 36, height: 36, borderRadius: '50%', border: '3px solid #E4DFD3', borderTopColor: '#1F3A8A', animation: 'spin 0.9s linear infinite' }} />
              <div style={{ fontFamily: '"Source Serif 4", serif', fontSize: 18, color: '#0B1220', fontStyle: 'italic' }}>Generating questions from your inspection…</div>
              <div style={{ fontFamily: 'Inter, system-ui', fontSize: 13, color: '#5A6272' }}>Context: {activity || 'current inspection'}</div>
            </div>
          )}

          {/* Question */}
          {phase === 'question' && currentQ && (
            <div>
              <div style={{ fontFamily: 'Inter, system-ui', fontSize: 11, letterSpacing: '0.14em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 500, marginBottom: 14 }}>
                Comprehension Check · Based on: {activity}
              </div>
              <h2 style={{ fontFamily: '"Source Serif 4", serif', fontSize: 26, fontWeight: 500, color: '#0B1220', lineHeight: 1.3, letterSpacing: '-0.015em', margin: 0, marginBottom: 28 }}>
                {currentQ.question_text}
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {currentQ.options.map((opt, i) => {
                  const picked = selectedOpt === i
                  return (
                    <button key={i} onClick={() => select(i)} style={{
                      textAlign: 'left', padding: '16px 20px',
                      background: picked ? '#E8ECF7' : '#FFFFFF',
                      border: `1.5px solid ${picked ? '#1F3A8A' : '#E4DFD3'}`,
                      borderRadius: 6, cursor: 'pointer',
                      fontFamily: 'Inter, system-ui', fontSize: 15, color: '#0B1220', lineHeight: 1.4,
                      display: 'flex', alignItems: 'flex-start', gap: 14,
                      transition: 'all .15s',
                    }}>
                      <span style={{
                        width: 22, height: 22, borderRadius: '50%',
                        border: `1.5px solid ${picked ? '#1F3A8A' : '#E4DFD3'}`,
                        background: picked ? '#1F3A8A' : 'transparent',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontFamily: 'Inter, system-ui', fontSize: 11, fontWeight: 600, flexShrink: 0, marginTop: 1,
                        color: picked ? '#fff' : '#0B1220',
                      }}>
                        {picked ? <CheckIcon size={11} color="#fff" /> : String.fromCharCode(65 + i)}
                      </span>
                      <span>{opt}</span>
                    </button>
                  )
                })}
              </div>
              <div style={{ marginTop: 32, display: 'flex', justifyContent: 'flex-end' }}>
                <button disabled={selectedOpt == null} onClick={handleNext} style={{
                  padding: '13px 28px', fontFamily: 'Inter, system-ui', fontSize: 14, fontWeight: 600,
                  color: selectedOpt != null ? '#FFFFFF' : '#5A6272',
                  background: selectedOpt != null ? '#0B1220' : '#E4DFD3',
                  border: 'none', borderRadius: 4, cursor: selectedOpt != null ? 'pointer' : 'not-allowed',
                }}>
                  {isLast ? 'Submit Quiz →' : 'Next Question →'}
                </button>
              </div>
            </div>
          )}

          {/* Results */}
          {phase === 'results' && (
            <div>
              {/* Score header */}
              <div style={{ textAlign: 'center', marginBottom: 40, paddingBottom: 32, borderBottom: '1px solid #E4DFD3', animation: 'scoreReveal .5s ease-out' }}>
                {showRing && <ScoreRing correct={correctCount} total={questions.length} />}
                <h2 style={{ fontFamily: '"Source Serif 4", serif', fontSize: 28, fontWeight: 500, color: '#0B1220', margin: '0 0 10px', letterSpacing: '-0.015em' }}>
                  Quiz Submitted
                </h2>
                <div style={{ fontFamily: 'Inter, system-ui', fontSize: 14, color: '#5A6272', lineHeight: 1.5 }}>
                  <span style={{ fontWeight: 600, color: scoreColor }}>{correctCount} of {questions.length} correct</span>
                  {' '}· Your responses have been recorded.
                </div>
              </div>

              {/* Per-question review */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {questions.map((q, i) => {
                  const ansIdx = answers[i]
                  const correctIdx = q.correct_answer.charCodeAt(0) - 65
                  const isCorrect = ansIdx === correctIdx
                  const userAns = ansIdx != null ? q.options[ansIdx] : '—'
                  const correctAns = q.options[correctIdx]

                  return (
                    <div key={i} style={{
                      background: '#FFFFFF',
                      border: `1px solid ${isCorrect ? '#C8DFC8' : 'rgba(196,48,43,0.22)'}`,
                      borderRadius: 6,
                      overflow: 'hidden',
                      animation: `scoreReveal .4s ease-out ${i * 60}ms both`,
                    }}>
                      {/* Q header strip */}
                      <div style={{
                        padding: '8px 16px',
                        background: isCorrect ? 'rgba(31,122,58,0.07)' : 'rgba(196,48,43,0.06)',
                        display: 'flex', alignItems: 'center', gap: 10,
                        borderBottom: `1px solid ${isCorrect ? '#C8DFC8' : 'rgba(196,48,43,0.2)'}`,
                      }}>
                        <div style={{
                          width: 20, height: 20, borderRadius: '50%',
                          background: isCorrect ? 'rgba(31,122,58,0.15)' : 'rgba(196,48,43,0.15)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                        }}>
                          {isCorrect
                            ? <CheckIcon size={10} color="#1F7A3A" />
                            : <span style={{ color: '#C4302B', fontSize: 9, fontWeight: 700 }}>✕</span>}
                        </div>
                        <span style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 10, letterSpacing: '0.1em', textTransform: 'uppercase', color: isCorrect ? '#1F7A3A' : '#C4302B', fontWeight: 600 }}>
                          Q{i + 1} · {isCorrect ? 'Correct' : 'Incorrect'}
                        </span>
                      </div>

                      <div style={{ padding: '14px 18px' }}>
                        {/* Question text */}
                        <div style={{ fontFamily: 'Inter, system-ui', fontSize: 13, color: '#0B1220', lineHeight: 1.45, fontWeight: 500, marginBottom: 12 }}>
                          {q.question_text}
                        </div>

                        {/* Answer rows */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                          {/* User's answer */}
                          <div style={{
                            display: 'flex', alignItems: 'flex-start', gap: 10,
                            padding: '8px 12px', borderRadius: 4,
                            background: isCorrect ? 'rgba(31,122,58,0.07)' : 'rgba(196,48,43,0.07)',
                            border: `1px solid ${isCorrect ? '#C8DFC8' : 'rgba(196,48,43,0.25)'}`,
                          }}>
                            <span style={{
                              fontFamily: '"JetBrains Mono", monospace', fontSize: 9, fontWeight: 700,
                              letterSpacing: '0.08em', textTransform: 'uppercase',
                              color: isCorrect ? '#1F7A3A' : '#C4302B',
                              flexShrink: 0, paddingTop: 1, minWidth: 60,
                            }}>
                              Your ans.
                            </span>
                            <span style={{ fontFamily: 'Inter, system-ui', fontSize: 12, color: '#0B1220', lineHeight: 1.4 }}>
                              {String.fromCharCode(65 + (ansIdx ?? 0))}. {userAns}
                            </span>
                          </div>

                          {/* Correct answer — always show */}
                          {!isCorrect && (
                            <div style={{
                              display: 'flex', alignItems: 'flex-start', gap: 10,
                              padding: '8px 12px', borderRadius: 4,
                              background: 'rgba(31,122,58,0.06)',
                              border: '1px solid #C8DFC8',
                            }}>
                              <span style={{
                                fontFamily: '"JetBrains Mono", monospace', fontSize: 9, fontWeight: 700,
                                letterSpacing: '0.08em', textTransform: 'uppercase',
                                color: '#1F7A3A', flexShrink: 0, paddingTop: 1, minWidth: 60,
                              }}>
                                Correct
                              </span>
                              <span style={{ fontFamily: 'Inter, system-ui', fontSize: 12, color: '#0B1220', lineHeight: 1.4 }}>
                                {q.correct_answer}. {correctAns}
                              </span>
                            </div>
                          )}
                        </div>

                        {/* Explanation */}
                        {q.explanation && (
                          <div style={{ marginTop: 10, padding: '9px 12px', background: '#F5F2EC', borderRadius: 3, fontFamily: 'Inter, system-ui', fontSize: 12, color: '#5A6272', lineHeight: 1.5, fontStyle: 'italic' }}>
                            {q.explanation}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>

              <div style={{ marginTop: 36, display: 'flex', justifyContent: 'center' }}>
                <button onClick={handleClose} style={{ padding: '13px 28px', fontFamily: 'Inter, system-ui', fontSize: 13, fontWeight: 600, color: '#0B1220', background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: 4, cursor: 'pointer' }}>
                  ← Start New Inspection
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
