// Quiz overlay — slides up over the inspection page.
// Loading → Question (1 of 5) → Results.
// Styled to match the active variant's palette.

function QuizOverlay({ open, onClose, activity, palette, variant }) {
  const [phase, setPhase] = useState('loading'); // loading | question | results
  const [qIdx, setQIdx] = useState(0);
  const [answers, setAnswers] = useState({}); // { qIdx: optionIdx }

  // Reset when opening
  useEffect(() => {
    if (open) {
      setPhase('loading');
      setQIdx(0);
      setAnswers({});
      const t = setTimeout(() => setPhase('question'), 1800);
      return () => clearTimeout(t);
    }
  }, [open]);

  if (!open) return null;

  const currentQ = MOCK_QUIZ[qIdx];
  const selectedOpt = answers[qIdx];
  const total = MOCK_QUIZ.length;
  const isLast = qIdx === total - 1;

  const handleSelect = (i) => setAnswers(prev => ({ ...prev, [qIdx]: i }));
  const handleNext = () => {
    if (isLast) setPhase('results');
    else setQIdx(qIdx + 1);
  };

  const correctCount = Object.entries(answers).filter(
    ([i, a]) => MOCK_QUIZ[+i].correct === a
  ).length;

  const isSerif = variant === 'editorial' || variant === 'stacked';

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 100,
      background: palette.ink + 'AA',
      backdropFilter: 'blur(3px)',
      display: 'flex', alignItems: 'stretch',
      justifyContent: 'center',
      animation: 'fadeIn .25s ease-out',
    }}>
      <div style={{
        background: palette.bg,
        width: '100%',
        maxWidth: 880,
        margin: '48px auto',
        borderRadius: 6,
        overflow: 'hidden',
        animation: 'slideUp .4s cubic-bezier(.2,.8,.25,1)',
        display: 'flex', flexDirection: 'column',
        boxShadow: `0 20px 60px ${palette.ink}40`,
      }}>
        {/* Top bar */}
        <div style={{
          padding: '18px 32px',
          background: palette.card,
          borderBottom: `1px solid ${palette.rule}`,
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <button onClick={onClose} style={{
            background: 'transparent', border: 'none',
            color: palette.mute, cursor: 'pointer',
            fontFamily: "'Inter', system-ui", fontSize: 13,
            display: 'flex', alignItems: 'center', gap: 6,
            padding: 0,
          }}>
            ← Back to Inspection
          </button>
          {phase === 'question' && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 16,
              fontFamily: "'JetBrains Mono', monospace", fontSize: 11,
              color: palette.mute,
            }}>
              <span>Question {qIdx + 1} / {total}</span>
              <div style={{
                width: 140, height: 3, borderRadius: 2,
                background: palette.rule, overflow: 'hidden',
              }}>
                <div style={{
                  width: `${((qIdx + 1) / total) * 100}%`,
                  height: '100%', background: palette.accent,
                  transition: 'width .3s',
                }} />
              </div>
            </div>
          )}
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflow: 'auto', padding: '40px 56px 48px' }}>
          {phase === 'loading' && (
            <div style={{
              display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center',
              padding: '80px 0', gap: 24,
            }}>
              <div style={{
                width: 36, height: 36, borderRadius: '50%',
                border: `3px solid ${palette.rule}`,
                borderTopColor: palette.accent,
                animation: 'spin 0.9s linear infinite',
              }} />
              <div style={{
                fontFamily: isSerif ? "'Source Serif 4', serif" : "'Inter', system-ui",
                fontSize: 18, color: palette.ink, fontStyle: isSerif ? 'italic' : 'normal',
              }}>
                Generating questions from your inspection…
              </div>
              <div style={{
                fontFamily: "'Inter', system-ui", fontSize: 13,
                color: palette.mute,
              }}>
                Context: {activity || 'current inspection'}
              </div>
            </div>
          )}

          {phase === 'question' && (
            <div>
              <div style={{
                fontFamily: "'Inter', system-ui", fontSize: 11,
                letterSpacing: '0.14em', textTransform: 'uppercase',
                color: palette.mute, fontWeight: 500, marginBottom: 14,
              }}>
                Comprehension Check · Based on: {activity}
              </div>
              <h2 style={{
                fontFamily: isSerif ? "'Source Serif 4', serif" : "'Inter', system-ui",
                fontSize: 26, fontWeight: isSerif ? 500 : 600,
                color: palette.ink, lineHeight: 1.3,
                letterSpacing: '-0.015em', margin: 0,
                marginBottom: 28,
              }}>
                {currentQ.q}
              </h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {currentQ.options.map((opt, i) => {
                  const picked = selectedOpt === i;
                  return (
                    <button key={i} onClick={() => handleSelect(i)}
                      style={{
                        textAlign: 'left',
                        padding: '16px 20px',
                        background: picked ? palette.accentSoft : palette.card,
                        border: `1.5px solid ${picked ? palette.accent : palette.rule}`,
                        borderRadius: 6, cursor: 'pointer',
                        fontFamily: "'Inter', system-ui", fontSize: 15,
                        color: palette.ink, lineHeight: 1.4,
                        display: 'flex', alignItems: 'flex-start', gap: 14,
                        transition: 'all .15s',
                      }}>
                      <span style={{
                        width: 22, height: 22, borderRadius: '50%',
                        border: `1.5px solid ${picked ? palette.accent : palette.rule}`,
                        background: picked ? palette.accent : 'transparent',
                        color: palette.card,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontFamily: "'Inter', system-ui", fontSize: 11,
                        fontWeight: 600, flexShrink: 0, marginTop: 1,
                      }}>
                        {picked ? <CheckIcon size={11} color={palette.card} />
                                : String.fromCharCode(65 + i)}
                      </span>
                      <span>{opt}</span>
                    </button>
                  );
                })}
              </div>

              <div style={{
                marginTop: 32, display: 'flex', justifyContent: 'flex-end',
              }}>
                <button
                  disabled={selectedOpt == null}
                  onClick={handleNext}
                  style={{
                    padding: '13px 28px',
                    fontFamily: "'Inter', system-ui", fontSize: 14,
                    fontWeight: 600,
                    color: selectedOpt != null ? palette.card : palette.mute,
                    background: selectedOpt != null ? palette.ink : palette.rule,
                    border: 'none', borderRadius: 4,
                    cursor: selectedOpt != null ? 'pointer' : 'not-allowed',
                  }}>
                  {isLast ? 'Submit Quiz →' : 'Next Question →'}
                </button>
              </div>
            </div>
          )}

          {phase === 'results' && (
            <div>
              <div style={{
                textAlign: 'center', marginBottom: 36,
                paddingBottom: 28, borderBottom: `1px solid ${palette.rule}`,
              }}>
                <div style={{
                  width: 56, height: 56, margin: '0 auto 18px',
                  borderRadius: '50%',
                  background: TOKENS.state.confirmed + '18',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <CheckIcon size={26} color={TOKENS.state.confirmed} />
                </div>
                <h2 style={{
                  fontFamily: isSerif ? "'Source Serif 4', serif" : "'Inter', system-ui",
                  fontSize: 28, fontWeight: isSerif ? 500 : 600,
                  color: palette.ink, margin: 0,
                  letterSpacing: '-0.015em',
                }}>
                  Quiz Submitted
                </h2>
                <div style={{
                  marginTop: 10,
                  fontFamily: "'Inter', system-ui", fontSize: 14,
                  color: palette.mute, lineHeight: 1.5,
                }}>
                  {correctCount} of {total} correct · Your responses have been
                  recorded. An EHS administrator will review your answers.
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {MOCK_QUIZ.map((q, i) => {
                  const ans = answers[i];
                  const correct = q.correct === ans;
                  return (
                    <div key={i} style={{
                      padding: '14px 18px',
                      background: palette.card,
                      border: `1px solid ${correct ? palette.rule : TOKENS.risk.high.base + '40'}`,
                      borderRadius: 4,
                    }}>
                      <div style={{
                        display: 'flex', alignItems: 'flex-start', gap: 12,
                      }}>
                        <div style={{
                          width: 22, height: 22, borderRadius: '50%',
                          background: correct ? TOKENS.state.confirmed + '18'
                                              : TOKENS.risk.high.base + '18',
                          color: correct ? TOKENS.state.confirmed : TOKENS.risk.high.base,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          flexShrink: 0, marginTop: 1,
                          fontFamily: "'JetBrains Mono', monospace",
                          fontSize: 10, fontWeight: 600,
                        }}>
                          {correct ? <CheckIcon size={11} color={TOKENS.state.confirmed} /> : '✕'}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{
                            fontFamily: "'JetBrains Mono', monospace", fontSize: 10,
                            letterSpacing: '0.1em', textTransform: 'uppercase',
                            color: palette.mute, marginBottom: 4,
                          }}>
                            Q{i + 1} · {correct ? 'Correct' : 'Incorrect'}
                          </div>
                          <div style={{
                            fontFamily: "'Inter', system-ui", fontSize: 13,
                            color: palette.ink, lineHeight: 1.4, fontWeight: 500,
                          }}>
                            {q.q}
                          </div>
                          {!correct && (
                            <div style={{
                              marginTop: 10, padding: '10px 12px',
                              background: palette.bg, borderRadius: 3,
                              fontFamily: "'Inter', system-ui", fontSize: 12,
                              color: palette.mute, lineHeight: 1.5,
                            }}>
                              <strong style={{ color: palette.ink, fontWeight: 600 }}>
                                Correct answer:
                              </strong>{' '}
                              {q.options[q.correct]}
                              <br /><span style={{ fontStyle: 'italic', opacity: 0.9 }}>
                                {q.explain}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div style={{
                marginTop: 32, display: 'flex', justifyContent: 'center',
              }}>
                <button onClick={onClose}
                  style={{
                    padding: '13px 28px',
                    fontFamily: "'Inter', system-ui", fontSize: 13,
                    fontWeight: 600,
                    color: palette.ink,
                    background: palette.card,
                    border: `1px solid ${palette.rule}`,
                    borderRadius: 4, cursor: 'pointer',
                  }}>
                  ← Start New Inspection
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

window.QuizOverlay = QuizOverlay;
