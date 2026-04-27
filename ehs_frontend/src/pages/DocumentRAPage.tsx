import { useRef } from 'react'
import { useInspection } from '../hooks/useInspection'
import type { RARow } from '../api/inspect'

const TH_STYLE: React.CSSProperties = {
  padding: '10px 12px',
  fontFamily: 'Inter, system-ui',
  fontSize: 11,
  fontWeight: 600,
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
  background: '#1F3A8A',
  color: '#FFFFFF',
  whiteSpace: 'nowrap',
  textAlign: 'left',
  borderRight: '1px solid rgba(255,255,255,0.15)',
}

const TD_STYLE = (even: boolean): React.CSSProperties => ({
  padding: '10px 12px',
  fontFamily: 'Inter, system-ui',
  fontSize: 12,
  color: '#0B1220',
  verticalAlign: 'top',
  borderRight: '1px solid #E4DFD3',
  borderBottom: '1px solid #E4DFD3',
  background: even ? '#EEF2FF' : '#FFFFFF',
  lineHeight: 1.5,
})

function riskColor(risk: string) {
  const r = risk.toLowerCase()
  if (r.includes('very high')) return '#B91C1C'
  if (r.includes('high')) return '#D97706'
  if (r.includes('medium')) return '#2563EB'
  return '#16A34A'
}

function RiskBadge({ value }: { value: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 999,
      fontSize: 11, fontWeight: 700, fontFamily: 'Inter, system-ui',
      background: riskColor(value) + '18', color: riskColor(value),
      border: `1px solid ${riskColor(value)}40`, whiteSpace: 'nowrap',
    }}>{value}</span>
  )
}

const COLS = [
  'Main Activity', 'Sub-Activity', 'Hazard', 'Consequences',
  'L', 'S', 'Initial Risk', 'Control Measures', 'R-L', 'R-S', 'Residual Risk',
]

export function DocumentRAPage() {
  const S = useInspection()
  const fileRef = useRef<HTMLInputElement>(null)

  return (
    <div style={{ padding: '56px 64px 80px', maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 44, maxWidth: 720 }}>
        <div style={{ fontFamily: 'Inter, system-ui', fontSize: 11, letterSpacing: '0.16em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 500, marginBottom: 14 }}>
          § 03 · Document-Based RA
        </div>
        <h1 style={{ fontFamily: '"Source Serif 4", serif', fontSize: 44, fontWeight: 500, color: '#0B1220', lineHeight: 1.1, letterSpacing: '-0.02em', margin: 0 }}>
          Upload a <em style={{ fontStyle: 'italic' }}>document</em>.
        </h1>
        <p style={{ fontFamily: '"Source Serif 4", serif', fontSize: 18, color: '#5A6272', lineHeight: 1.55, marginTop: 18, letterSpacing: '-0.005em', fontWeight: 400 }}>
          Upload a Word document containing existing RA data. The system extracts all content, fills missing fields using AI, and returns a structured risk assessment.
        </p>
      </div>

      {/* Upload area */}
      {S.fetchState !== 'done' && (
        <div
          onClick={() => S.fetchState !== 'loading' && fileRef.current?.click()}
          style={{
            maxWidth: 600, padding: '48px 32px', border: '2px dashed #C8C2B6',
            borderRadius: 6, textAlign: 'center', cursor: S.fetchState === 'loading' ? 'default' : 'pointer',
            background: '#FAFAF8', transition: 'border-color .15s',
          }}
          onMouseEnter={e => { if (S.fetchState !== 'loading') (e.currentTarget as HTMLDivElement).style.borderColor = '#1F3A8A' }}
          onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = '#C8C2B6' }}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".docx"
            style={{ display: 'none' }}
            onChange={e => {
              const f = e.target.files?.[0]
              if (f) { S.uploadDocument(f); e.target.value = '' }
            }}
          />
          {S.fetchState === 'loading' ? (
            <div style={{ fontFamily: 'Inter, system-ui', fontSize: 14, color: '#5A6272' }}>
              Extracting and generating risk assessment…
            </div>
          ) : (
            <>
              <div style={{ fontFamily: 'Inter, system-ui', fontSize: 32, marginBottom: 12, color: '#C8C2B6' }}>↑</div>
              <div style={{ fontFamily: 'Inter, system-ui', fontSize: 15, fontWeight: 600, color: '#0B1220', marginBottom: 6 }}>
                Click to upload .docx
              </div>
              <div style={{ fontFamily: 'Inter, system-ui', fontSize: 12, color: '#5A6272' }}>
                Max 10 MB · Word documents only
              </div>
            </>
          )}
        </div>
      )}

      {/* Loading shimmer */}
      {S.fetchState === 'loading' && (
        <div style={{ marginTop: 36 }}>
          {[0, 1, 2, 3].map(i => (
            <div key={i} className="shimmer-bar" style={{ height: 14, width: `${80 - i * 10}%`, marginBottom: 12, borderRadius: 3 }} />
          ))}
        </div>
      )}

      {/* Error */}
      {S.fetchState === 'error' && (
        <div style={{ marginTop: 28, maxWidth: 600, padding: '14px 18px', background: '#FFF3F3', border: '1px solid #FBBFBF', borderRadius: 4, fontFamily: 'Inter, system-ui', fontSize: 13, color: '#B91C1C' }}>
          {S.error}
          <button onClick={S.reset} style={{ marginLeft: 16, fontFamily: 'Inter, system-ui', fontSize: 12, color: '#5A6272', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>Try again</button>
        </div>
      )}

      {/* Result */}
      {S.fetchState === 'done' && S.result && (
        <>
          <div style={{ marginTop: 28, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '4px 12px', borderRadius: 999, fontSize: 12, fontFamily: 'Inter, system-ui', fontWeight: 600,
              background: 'rgba(31,58,138,0.09)', color: '#1F3A8A', border: '1px solid rgba(31,58,138,0.2)',
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor', display: 'inline-block' }} />
              Extracted from document
            </span>
            <span style={{ fontFamily: '"Source Serif 4", serif', fontSize: 16, color: '#0B1220', fontWeight: 600 }}>
              {S.result.project}
            </span>
            <button onClick={S.reset} style={{ marginLeft: 'auto', fontFamily: 'Inter, system-ui', fontSize: 12, color: '#5A6272', background: 'none', border: '1px solid #E4DFD3', borderRadius: 4, padding: '6px 14px', cursor: 'pointer' }}>
              Upload another
            </button>
          </div>

          {/* Assumptions */}

          {/* RA Table */}
          <div style={{ overflowX: 'auto', borderRadius: 4, border: '1px solid #E4DFD3', boxShadow: '0 1px 3px rgba(11,18,32,0.07)' }}>
            <table style={{ borderCollapse: 'collapse', width: '100%', minWidth: 1100 }}>
              <thead>
                <tr>{COLS.map(col => <th key={col} style={TH_STYLE}>{col}</th>)}</tr>
              </thead>
              <tbody>
                {S.result.rows.map((row: RARow, i: number) => (
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
          {S.result.full_ra && (
            <details style={{ marginTop: 28 }}>
              <summary style={{
                fontFamily: 'Inter, system-ui', fontSize: 12, fontWeight: 600, color: '#5A6272',
                cursor: 'pointer', letterSpacing: '0.06em', textTransform: 'uppercase',
                userSelect: 'none',
              }}>
                Full RA JSON (complete output incl. risk matrix, chemical note, references)
              </summary>
              <div style={{ marginTop: 12, position: 'relative' }}>
                <button
                  onClick={() => navigator.clipboard.writeText(JSON.stringify(S.result!.full_ra, null, 2))}
                  style={{
                    position: 'absolute', top: 10, right: 10, zIndex: 1,
                    padding: '4px 10px', fontFamily: 'Inter, system-ui', fontSize: 11, fontWeight: 600,
                    color: '#5A6272', background: '#FFFFFF', border: '1px solid #E4DFD3',
                    borderRadius: 4, cursor: 'pointer',
                  }}
                >
                  Copy
                </button>
                <pre style={{
                  margin: 0, padding: '16px 20px', background: '#0B1220', color: '#E2E8F0',
                  borderRadius: 6, fontSize: 11, fontFamily: '"JetBrains Mono", monospace',
                  lineHeight: 1.65, overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                  maxHeight: 520, overflowY: 'auto',
                }}>
                  {JSON.stringify(S.result.full_ra, null, 2)}
                </pre>
              </div>
            </details>
          )}
        </>
      )}
    </div>
  )
}
