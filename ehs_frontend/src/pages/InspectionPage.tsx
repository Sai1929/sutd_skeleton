import { useInspection } from '../hooks/useInspection'
import { ActivityInput } from '../components/inspection/ActivityInput'
import { SuggestionChips } from '../components/inspection/SuggestionChips'
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

function riskColor(risk: string): string {
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
      border: `1px solid ${riskColor(value)}40`,
      whiteSpace: 'nowrap',
    }}>{value}</span>
  )
}

const COLS = [
  'Main Activity', 'Sub-Activity', 'Hazard', 'Consequences',
  'L', 'S', 'Initial Risk', 'Control Measures', 'R-L', 'R-S', 'Residual Risk',
]

export function InspectionPage() {
  const S = useInspection()

  return (
    <div style={{ padding: '56px 64px 80px', maxWidth: 1400, margin: '0 auto' }}>
      <div style={{ marginBottom: 44, maxWidth: 720 }}>
        <div style={{ fontFamily: 'Inter, system-ui', fontSize: 11, letterSpacing: '0.16em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 500, marginBottom: 14 }}>
          § 01 · Activity-Based RA
        </div>
        <h1 style={{ fontFamily: '"Source Serif 4", serif', fontSize: 44, fontWeight: 500, color: '#0B1220', lineHeight: 1.1, letterSpacing: '-0.02em', margin: 0 }}>
          Record an <em style={{ fontStyle: 'italic' }}>inspection</em>.
        </h1>
        <p style={{ fontFamily: '"Source Serif 4", serif', fontSize: 18, color: '#5A6272', lineHeight: 1.55, marginTop: 18, letterSpacing: '-0.005em', fontWeight: 400 }}>
          Enter activity name or description. System retrieves or generates a WSH-compliant risk assessment table.
        </p>
      </div>

      <div style={{ marginBottom: 12 }}>
        <ActivityInput value={S.activity} onChange={S.setActivity} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 10 }}>
          <SuggestionChips onPick={S.setActivity} />
        </div>
      </div>

      {S.fetchState === 'loading' && (
        <div style={{ marginTop: 36 }}>
          {[0, 1, 2, 3].map(i => (
            <div key={i} className="shimmer-bar" style={{ height: 14, width: `${80 - i * 10}%`, marginBottom: 12, borderRadius: 3 }} />
          ))}
        </div>
      )}

      {S.fetchState === 'error' && (
        <div style={{ marginTop: 28, padding: '14px 18px', background: '#FFF3F3', border: '1px solid #FBBFBF', borderRadius: 4, fontFamily: 'Inter, system-ui', fontSize: 13, color: '#B91C1C' }}>
          {S.error}
        </div>
      )}

      {S.fetchState === 'done' && S.result && (
        <>
          <div style={{ marginTop: 28, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '4px 12px', borderRadius: 999, fontSize: 12, fontFamily: 'Inter, system-ui', fontWeight: 600,
              background: S.result.from_db ? 'rgba(31,122,58,0.09)' : 'rgba(31,58,138,0.09)',
              color: S.result.from_db ? '#1F7A3A' : '#1F3A8A',
              border: `1px solid ${S.result.from_db ? 'rgba(31,122,58,0.2)' : 'rgba(31,58,138,0.2)'}`,
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'currentColor', display: 'inline-block' }} />
              {S.result.from_db ? 'Retrieved from database' : 'AI-generated'}
            </span>
            <span style={{ fontFamily: '"Source Serif 4", serif', fontSize: 16, color: '#0B1220', fontWeight: 600 }}>
              {S.result.project}
            </span>
          </div>


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

        </>
      )}
    </div>
  )
}
