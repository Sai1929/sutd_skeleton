import { useRef, useState } from 'react'
import { analyseHazard, HazardAnalysisResponse } from '../api/hazard'

type State = 'idle' | 'loading' | 'done' | 'error'

function riskColor(risk: string) {
  const r = risk.toLowerCase()
  if (r.includes('very high')) return '#B91C1C'
  if (r.includes('high')) return '#D97706'
  if (r.includes('medium')) return '#2563EB'
  return '#16A34A'
}

function priorityColor(p: string) {
  if (p === 'Immediate') return { bg: 'rgba(185,28,28,0.08)', color: '#B91C1C', border: 'rgba(185,28,28,0.2)' }
  if (p === 'Short-term') return { bg: 'rgba(217,119,6,0.08)', color: '#D97706', border: 'rgba(217,119,6,0.2)' }
  return { bg: 'rgba(22,163,74,0.08)', color: '#16A34A', border: 'rgba(22,163,74,0.2)' }
}

function hierarchyColor(h: string) {
  const map: Record<string, string> = {
    'Elimination': '#7C3AED',
    'Substitution': '#1D4ED8',
    'Engineering': '#0369A1',
    'Administrative': '#B45309',
    'PPE': '#047857',
  }
  return map[h] || '#5A6272'
}

export function HazardPage() {
  const [text, setText] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [state, setState] = useState<State>('idle')
  const [result, setResult] = useState<HazardAnalysisResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const canSubmit = text.trim().length > 0 || image !== null

  const handleImage = (f: File) => {
    setImage(f)
    const reader = new FileReader()
    reader.onload = e => setImagePreview(e.target?.result as string)
    reader.readAsDataURL(f)
  }

  const handleSubmit = async () => {
    if (!canSubmit) return
    setState('loading')
    setError(null)
    try {
      const res = await analyseHazard(text, image ?? undefined)
      setResult(res)
      setState('done')
    } catch {
      setError('Analysis failed. Check backend connection.')
      setState('error')
    }
  }

  const handleReset = () => {
    setState('idle')
    setResult(null)
    setError(null)
    setText('')
    setImage(null)
    setImagePreview(null)
  }

  return (
    <div style={{ padding: '56px 64px 80px', maxWidth: 1000, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 44, maxWidth: 720 }}>
        <div style={{ fontFamily: 'Inter, system-ui', fontSize: 11, letterSpacing: '0.16em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 500, marginBottom: 14 }}>
          § 05 · Hazard Analysis
        </div>
        <h1 style={{ fontFamily: '"Source Serif 4", serif', fontSize: 44, fontWeight: 500, color: '#0B1220', lineHeight: 1.1, letterSpacing: '-0.02em', margin: 0 }}>
          Identify & <em style={{ fontStyle: 'italic' }}>control</em> hazards.
        </h1>
        <p style={{ fontFamily: '"Source Serif 4", serif', fontSize: 18, color: '#5A6272', lineHeight: 1.55, marginTop: 18, letterSpacing: '-0.005em', fontWeight: 400 }}>
          Describe a workplace situation or upload an image. System identifies the hazard, assesses risk, and returns WSH-compliant control measures and mitigation activities.
        </p>
      </div>

      {/* Input form */}
      {state !== 'done' && (
        <div style={{ maxWidth: 760, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Text input */}
          <div>
            <label style={{ display: 'block', fontFamily: 'Inter, system-ui', fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 500, marginBottom: 8 }}>
              Describe the situation
            </label>
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="e.g. Worker observed climbing an unsecured ladder while carrying tools. No harness or fall arrest system in use. Working at approximately 4m height on a construction site…"
              rows={5}
              style={{ width: '100%', padding: '14px 16px', fontFamily: 'Inter, system-ui', fontSize: 14, color: '#0B1220', background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: 4, outline: 'none', resize: 'vertical', lineHeight: 1.6, boxSizing: 'border-box' }}
            />
          </div>

          {/* Image upload */}
          <div>
            <label style={{ display: 'block', fontFamily: 'Inter, system-ui', fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 500, marginBottom: 8 }}>
              Upload Image <span style={{ color: '#9CA3AF', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>(optional — JPEG, PNG, WebP · max 5 MB)</span>
            </label>
            <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" style={{ display: 'none' }}
              onChange={e => { const f = e.target.files?.[0]; if (f) handleImage(f) }} />

            {imagePreview ? (
              <div style={{ position: 'relative', display: 'inline-block' }}>
                <img src={imagePreview} alt="preview" style={{ maxWidth: 320, maxHeight: 220, borderRadius: 4, border: '1px solid #E4DFD3', display: 'block' }} />
                <button onClick={() => { setImage(null); setImagePreview(null); if (fileRef.current) fileRef.current.value = '' }}
                  style={{ position: 'absolute', top: 6, right: 6, width: 22, height: 22, borderRadius: '50%', background: 'rgba(11,18,32,0.7)', border: 'none', color: '#fff', cursor: 'pointer', fontSize: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  ✕
                </button>
              </div>
            ) : (
              <button onClick={() => fileRef.current?.click()} style={{ padding: '10px 20px', fontFamily: 'Inter, system-ui', fontSize: 13, fontWeight: 500, color: '#5A6272', background: '#FFFFFF', border: '1px dashed #C8C2B6', borderRadius: 4, cursor: 'pointer' }}>
                + Add image
              </button>
            )}
          </div>

          {error && (
            <div style={{ padding: '12px 16px', background: '#FFF3F3', border: '1px solid #FBBFBF', borderRadius: 4, fontFamily: 'Inter, system-ui', fontSize: 13, color: '#B91C1C' }}>{error}</div>
          )}

          {state === 'loading' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontFamily: 'Inter, system-ui', fontSize: 13, color: '#5A6272' }}>
              <div style={{ width: 16, height: 16, borderRadius: '50%', border: '2px solid #E4DFD3', borderTopColor: '#1F3A8A', animation: 'spin 0.9s linear infinite', flexShrink: 0 }} />
              Analysing hazard…
            </div>
          )}

          <div style={{ display: 'flex', gap: 10 }}>
            <button onClick={handleSubmit} disabled={!canSubmit || state === 'loading'}
              style={{ padding: '13px 32px', fontFamily: 'Inter, system-ui', fontSize: 14, fontWeight: 600, color: '#FFFFFF', background: canSubmit && state !== 'loading' ? '#0B1220' : '#9CA3AF', border: 'none', borderRadius: 4, cursor: canSubmit && state !== 'loading' ? 'pointer' : 'not-allowed', transition: 'transform .15s' }}
              onMouseEnter={e => { if (canSubmit && state !== 'loading') e.currentTarget.style.transform = 'translateY(-1px)' }}
              onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)' }}>
              Analyse Hazard →
            </button>
          </div>
        </div>
      )}

      {/* Result */}
      {state === 'done' && result && (
        <div style={{ maxWidth: 860 }}>
          {/* Top bar */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28, flexWrap: 'wrap' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 12px', borderRadius: 999, fontSize: 12, fontFamily: 'Inter, system-ui', fontWeight: 600, background: riskColor(result.risk_level) + '18', color: riskColor(result.risk_level), border: `1px solid ${riskColor(result.risk_level)}40` }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor', display: 'inline-block' }} />
              {result.risk_level}
            </span>
            <span style={{ fontFamily: '"Source Serif 4", serif', fontSize: 18, color: '#0B1220', fontWeight: 600 }}>{result.hazard_identified}</span>
            <button onClick={handleReset} style={{ marginLeft: 'auto', fontFamily: 'Inter, system-ui', fontSize: 12, color: '#5A6272', background: 'none', border: '1px solid #E4DFD3', borderRadius: 4, padding: '6px 14px', cursor: 'pointer' }}>New Analysis</button>
          </div>

          {/* Description */}
          <p style={{ fontFamily: 'Inter, system-ui', fontSize: 14, color: '#5A6272', lineHeight: 1.6, marginBottom: 28, padding: '14px 18px', background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: 4 }}>
            {result.hazard_description}
          </p>

          {/* Two-col: consequences + residual risk */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 28 }}>
            <div style={{ background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: 4, padding: '16px 20px' }}>
              <div style={{ fontFamily: 'Inter, system-ui', fontSize: 11, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#5A6272', marginBottom: 12 }}>Potential Consequences</div>
              <ul style={{ margin: 0, paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {result.potential_consequences.map((c, i) => (
                  <li key={i} style={{ fontFamily: 'Inter, system-ui', fontSize: 13, color: '#0B1220', lineHeight: 1.5 }}>{c}</li>
                ))}
              </ul>
            </div>
            <div style={{ background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: 4, padding: '16px 20px' }}>
              <div style={{ fontFamily: 'Inter, system-ui', fontSize: 11, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#5A6272', marginBottom: 12 }}>Residual Risk After Controls</div>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '6px 14px', borderRadius: 999, fontSize: 14, fontFamily: 'Inter, system-ui', fontWeight: 700, background: riskColor(result.residual_risk) + '18', color: riskColor(result.residual_risk), border: `1px solid ${riskColor(result.residual_risk)}40` }}>
                {result.residual_risk}
              </span>
              <div style={{ marginTop: 16 }}>
                <div style={{ fontFamily: 'Inter, system-ui', fontSize: 11, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#5A6272', marginBottom: 8 }}>Applicable Regulations</div>
                <ul style={{ margin: 0, paddingLeft: 18, display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {result.applicable_regulations.map((r, i) => (
                    <li key={i} style={{ fontFamily: 'Inter, system-ui', fontSize: 12, color: '#5A6272', lineHeight: 1.5 }}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Control measures */}
          <div style={{ marginBottom: 28 }}>
            <div style={{ fontFamily: 'Inter, system-ui', fontSize: 11, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#5A6272', marginBottom: 14 }}>Control Measures — Hierarchy of Controls</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {result.control_measures.map((cm, i) => (
                <div key={i} style={{ background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{ padding: '8px 16px', background: hierarchyColor(cm.hierarchy) + '10', borderBottom: '1px solid #E4DFD3', display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: hierarchyColor(cm.hierarchy), flexShrink: 0, display: 'inline-block' }} />
                    <span style={{ fontFamily: 'Inter, system-ui', fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: hierarchyColor(cm.hierarchy) }}>{cm.hierarchy}</span>
                  </div>
                  <ul style={{ margin: 0, padding: '12px 20px 12px 36px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {cm.measures.map((m, j) => (
                      <li key={j} style={{ fontFamily: 'Inter, system-ui', fontSize: 13, color: '#0B1220', lineHeight: 1.55 }}>{m}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>

          {/* Mitigation activities */}
          <div>
            <div style={{ fontFamily: 'Inter, system-ui', fontSize: 11, fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#5A6272', marginBottom: 14 }}>Mitigation Activities</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {result.mitigation_activities.map((ma, i) => {
                const pc = priorityColor(ma.priority)
                return (
                  <div key={i} style={{ background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: 4, padding: '12px 16px', display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                    <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 10, fontWeight: 700, fontFamily: 'Inter, system-ui', letterSpacing: '0.06em', textTransform: 'uppercase', background: pc.bg, color: pc.color, border: `1px solid ${pc.border}`, flexShrink: 0, marginTop: 1 }}>
                      {ma.priority}
                    </span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontFamily: 'Inter, system-ui', fontSize: 13, color: '#0B1220', lineHeight: 1.5, marginBottom: 4 }}>{ma.activity}</div>
                      <div style={{ fontFamily: 'Inter, system-ui', fontSize: 11, color: '#5A6272' }}>Responsible: {ma.responsible_party}</div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
