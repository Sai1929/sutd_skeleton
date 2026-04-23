interface Props { value: number; top?: boolean }

export function ConfidenceBar({ value, top = false }: Props) {
  const pct = Math.round(value * 100)
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{ flex: 1, height: top ? 8 : 4, borderRadius: 2, background: '#E4DFD3', overflow: 'hidden' }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: top ? '#1F3A8A' : '#5A6272',
          opacity: top ? 1 : 0.45,
          transition: 'width 600ms cubic-bezier(.2,.7,.3,1)',
        }} />
      </div>
      <span style={{
        fontFamily: '"JetBrains Mono", ui-monospace, monospace',
        fontSize: 11, fontVariantNumeric: 'tabular-nums',
        color: top ? '#0B1220' : '#5A6272',
        fontWeight: top ? 600 : 500,
        minWidth: 32, textAlign: 'right',
      }}>{pct}%</span>
    </div>
  )
}
