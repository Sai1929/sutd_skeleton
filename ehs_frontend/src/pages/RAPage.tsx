import { useState } from 'react'
import { generateRAJson, downloadRADocx } from '../api/ra'
import type { RecommendResponse, RARow } from '../api/inspect'

type State = 'idle' | 'loading' | 'done' | 'error'

const TH_STYLE: React.CSSProperties = {
  padding: '10px 12px', fontFamily: 'Inter, system-ui', fontSize: 11, fontWeight: 600,
  letterSpacing: '0.08em', textTransform: 'uppercase', background: '#1F3A8A', color: '#FFFFFF',
  whiteSpace: 'nowrap', textAlign: 'left', borderRight: '1px solid rgba(255,255,255,0.15)',
}

const TD_STYLE = (even: boolean): React.CSSProperties => ({
  padding: '10px 12px', fontFamily: 'Inter, system-ui', fontSize: 12, color: '#0B1220',
  verticalAlign: 'top', borderRight: '1px solid #E4DFD3', borderBottom: '1px solid #E4DFD3',
  background: even ? '#EEF2FF' : '#FFFFFF', lineHeight: 1.5,
})

function riskColor(risk: string): string {
  const r = risk.toLowerCase()
  if (r.includes('very high')) return '#B91C1C'
  if (r.includes('high')) return '#D97706'
  if (r.includes('medium')) return '#2563EB'
  return '#16A34A'
}

function RiskBadge({ value }: { value: string }) {
  return (
    <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 700, fontFamily: 'Inter, system-ui', background: riskColor(value) + '18', color: riskColor(value), border: `1px solid ${riskColor(value)}40`, whiteSpace: 'nowrap' }}>
      {value}
    </span>
  )
}

const COLS = ['Main Activity', 'Sub-Activity', 'Hazard', 'Consequences', 'L', 'S', 'Initial Risk', 'Control Measures', 'R-L', 'R-S', 'Residual Risk']

export function RAPage() {
  const [description, setDescription] = useState('')
  const [projectName, setProjectName] = useState('')
  const [state, setState] = useState<State>('idle')
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<RecommendResponse | null>(null)
  const [downloading, setDownloading] = useState(false)

  const canSubmit = description.trim().length > 0 || projectName.trim().length > 0

  const handleSubmit = async () => {
    if (!canSubmit) return
    setState('loading')
    setError(null)
    try {
      const desc = description.trim() || projectName.trim()
      const res = await generateRAJson(projectName.trim() || 'Risk Assessment', desc)
      setResult(res)
      setState('done')
    } catch {
      setError('Failed to generate risk assessment. Check backend connection.')
      setState('error')
    }
  }

  const handleDownload = async () => {
    if (!result) return
    setDownloading(true)
    try {
      const desc = description.trim() || projectName.trim()
      await downloadRADocx(projectName.trim() || 'Risk Assessment', desc)
    } catch {
      setError('Failed to download document.')
    } finally {
      setDownloading(false)
    }
  }

  const handleReset = () => {
    setState('idle'); setError(null); setDescription(''); setProjectName(''); setResult(null)
  }

  return (
    <div style={{ padding: '56px 64px 80px', maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 44, maxWidth: 720 }}>
        <div style={{ fontFamily: 'Inter, system-ui', fontSize: 11, letterSpacing: '0.16em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 500, marginBottom: 14 }}>
          § 02 · Proactive Risk Assessment
        </div>
        <h1 style={{ fontFamily: '"Source Serif 4", serif', fontSize: 44, fontWeight: 500, color: '#0B1220', lineHeight: 1.1, letterSpacing: '-0.02em', margin: 0 }}>
          Generate a <em style={{ fontStyle: 'italic' }}>risk assessment</em>.
        </h1>
        <p style={{ fontFamily: '"Source Serif 4", serif', fontSize: 18, color: '#5A6272', lineHeight: 1.55, marginTop: 18, letterSpacing: '-0.005em', fontWeight: 400 }}>
          Enter a project description or activity name. System generates a WSH-compliant RA as structured JSON and optionally downloads it as a Word document.
        </p>
      </div>

      {/* Form */}
      {state !== 'done' && (
        <div style={{ maxWidth: 760, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ display: 'block', fontFamily: 'Inter, system-ui', fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 500, marginBottom: 8 }}>Project Name</label>
            <input value={projectName} onChange={e => setProjectName(e.target.value)} placeholder="e.g. Marina Bay Office Tower Construction"
              style={{ width: '100%', padding: '12px 16px', fontFamily: 'Inter, system-ui', fontSize: 14, color: '#0B1220', background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: 4, outline: 'none', boxSizing: 'border-box' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontFamily: 'Inter, system-ui', fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 500, marginBottom: 8 }}>Project Description</label>
            <textarea value={description} onChange={e => setDescription(e.target.value)}
              placeholder="e.g. Construction of a 30-storey office tower including excavation, piling, structural steel erection, concrete works, and electrical installation…"
              rows={6} onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleSubmit() }}
              style={{ width: '100%', padding: '16px 18px', fontFamily: 'Inter, system-ui', fontSize: 14, color: '#0B1220', background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: 4, outline: 'none', resize: 'vertical', boxSizing: 'border-box', lineHeight: 1.6 }} />
          </div>
          <div style={{ display: 'flex', gap: 12, marginTop: 4 }}>
            <button onClick={handleSubmit} disabled={!canSubmit || state === 'loading'}
              style={{ padding: '14px 32px', fontFamily: 'Inter, system-ui', fontSize: 14, fontWeight: 600, color: '#FFFFFF', background: canSubmit && state !== 'loading' ? '#0B1220' : '#9CA3AF', border: 'none', borderRadius: 4, cursor: canSubmit && state !== 'loading' ? 'pointer' : 'not-allowed', transition: 'transform .15s' }}
              onMouseEnter={e => { if (canSubmit && state !== 'loading') e.currentTarget.style.transform = 'translateY(-1px)' }}
              onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)' }}>
              {state === 'loading' ? 'Generating…' : 'Generate RA →'}
            </button>
          </div>
          {state === 'loading' && (
            <div style={{ marginTop: 24 }}>
              {[0, 1, 2].map(i => <div key={i} className="shimmer-bar" style={{ height: 14, width: `${72 - i * 12}%`, marginBottom: 12, borderRadius: 3 }} />)}
            </div>
          )}
          {(state === 'error') && error && (
            <div style={{ padding: '14px 18px', background: '#FFF3F3', border: '1px solid #FBBFBF', borderRadius: 4, fontFamily: 'Inter, system-ui', fontSize: 13, color: '#B91C1C' }}>{error}</div>
          )}
        </div>
      )}

      {/* Result */}
      {state === 'done' && result && (
        <>
          {/* Top bar */}
          <div style={{ marginBottom: 20, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '4px 12px', borderRadius: 999, fontSize: 12, fontFamily: 'Inter, system-ui', fontWeight: 600, background: 'rgba(31,58,138,0.09)', color: '#1F3A8A', border: '1px solid rgba(31,58,138,0.2)' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor', display: 'inline-block' }} />
              AI-generated
            </span>
            <span style={{ fontFamily: '"Source Serif 4", serif', fontSize: 16, color: '#0B1220', fontWeight: 600 }}>{result.project}</span>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
              <button onClick={handleDownload} disabled={downloading}
                style={{ padding: '7px 16px', fontFamily: 'Inter, system-ui', fontSize: 12, fontWeight: 600, color: '#1F3A8A', background: 'rgba(31,58,138,0.07)', border: '1px solid rgba(31,58,138,0.2)', borderRadius: 4, cursor: downloading ? 'not-allowed' : 'pointer' }}>
                {downloading ? 'Downloading…' : '↓ Download .docx'}
              </button>
              <button onClick={handleReset} style={{ padding: '7px 14px', fontFamily: 'Inter, system-ui', fontSize: 12, color: '#5A6272', background: 'none', border: '1px solid #E4DFD3', borderRadius: 4, cursor: 'pointer' }}>
                Reset
              </button>
            </div>
          </div>

          {/* Assumptions */}
          {result.assumptions.length > 0 && (
            <details style={{ marginBottom: 20 }}>
              <summary style={{ fontFamily: 'Inter, system-ui', fontSize: 12, fontWeight: 600, color: '#5A6272', cursor: 'pointer', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
                Assumptions ({result.assumptions.length})
              </summary>
              <ol style={{ marginTop: 10, paddingLeft: 20 }}>
                {result.assumptions.map((a, i) => <li key={i} style={{ fontFamily: 'Inter, system-ui', fontSize: 12, color: '#5A6272', lineHeight: 1.6, marginBottom: 4 }}>{a}</li>)}
              </ol>
            </details>
          )}

          {/* RA Table */}
          <div style={{ overflowX: 'auto', borderRadius: 4, border: '1px solid #E4DFD3', boxShadow: '0 1px 3px rgba(11,18,32,0.07)' }}>
            <table style={{ borderCollapse: 'collapse', width: '100%', minWidth: 1100 }}>
              <thead>
                <tr>{COLS.map(col => <th key={col} style={TH_STYLE}>{col}</th>)}</tr>
              </thead>
              <tbody>
                {result.rows.map((row: RARow, i: number) => (
                  <tr key={i}>
                    <td style={TD_STYLE(i % 2 === 0)}>{row.main_activity}</td>
                    <td style={TD_STYLE(i % 2 === 0)}>{row.sub_activity}</td>
                    <td style={TD_STYLE(i % 2 === 0)}>{row.hazard}</td>
                    <td style={TD_STYLE(i % 2 === 0)}>{row.consequences}</td>
                    <td style={{ ...TD_STYLE(i % 2 === 0), textAlign: 'center' }}>{row.initial_l}</td>
                    <td style={{ ...TD_STYLE(i % 2 === 0), textAlign: 'center' }}>{row.initial_s}</td>
                    <td style={TD_STYLE(i % 2 === 0)}><RiskBadge value={row.initial_risk} /></td>
                    <td style={{ ...TD_STYLE(i % 2 === 0), maxWidth: 280, whiteSpace: 'pre-wrap' }}>{row.control_measures}</td>
                    <td style={{ ...TD_STYLE(i % 2 === 0), textAlign: 'center' }}>{row.residual_l}</td>
                    <td style={{ ...TD_STYLE(i % 2 === 0), textAlign: 'center' }}>{row.residual_s}</td>
                    <td style={TD_STYLE(i % 2 === 0)}><RiskBadge value={row.residual_risk} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Full RA JSON */}
          {result.full_ra && (
            <details style={{ marginTop: 28 }}>
              <summary style={{ fontFamily: 'Inter, system-ui', fontSize: 12, fontWeight: 600, color: '#5A6272', cursor: 'pointer', letterSpacing: '0.06em', textTransform: 'uppercase', userSelect: 'none' }}>
                Full RA JSON (incl. risk matrix, chemical note, references)
              </summary>
              <div style={{ marginTop: 12, position: 'relative' }}>
                <button onClick={() => navigator.clipboard.writeText(JSON.stringify(result.full_ra, null, 2))}
                  style={{ position: 'absolute', top: 10, right: 10, zIndex: 1, padding: '4px 10px', fontFamily: 'Inter, system-ui', fontSize: 11, fontWeight: 600, color: '#5A6272', background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: 4, cursor: 'pointer' }}>
                  Copy
                </button>
                <pre style={{ margin: 0, padding: '16px 20px', background: '#0B1220', color: '#E2E8F0', borderRadius: 6, fontSize: 11, fontFamily: '"JetBrains Mono", monospace', lineHeight: 1.65, overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: 520, overflowY: 'auto' }}>
                  {JSON.stringify(result.full_ra, null, 2)}
                </pre>
              </div>
            </details>
          )}
        </>
      )}
    </div>
  )
}
