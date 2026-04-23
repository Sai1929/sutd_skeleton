interface Props { label: string }

function getRisk(label: string) {
  const l = label.toLowerCase()
  if (l.startsWith('high')) return { base: '#C4302B', bg: '#FBEDEC' }
  if (l.startsWith('medium')) return { base: '#B26A00', bg: '#FAF2E2' }
  return { base: '#1F7A3A', bg: '#E9F4EC' }
}

export function RiskBanner({ label }: Props) {
  const r = getRisk(label)
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      padding: '10px 16px', borderRadius: 8,
      background: r.bg, border: `1px solid ${r.base}22`,
      fontFamily: 'Inter, system-ui', fontSize: 13, color: r.base, fontWeight: 500,
    }}>
      <span style={{ width: 8, height: 8, borderRadius: '50%', background: r.base }} />
      <span style={{ letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 600, fontSize: 11 }}>Risk Level</span>
      <span style={{ opacity: 0.5 }}>—</span>
      <span style={{ fontVariant: 'small-caps', letterSpacing: '0.04em' }}>{label}</span>
    </div>
  )
}
