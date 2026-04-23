export function TypingIndicator() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{ width: 28, height: 28, borderRadius: 6, background: '#E8ECF7', color: '#1F3A8A', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: '"Source Serif 4", serif', fontWeight: 700, fontSize: 13, fontStyle: 'italic' }}>A</div>
      <div style={{ padding: '12px 16px', background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: '10px 10px 10px 2px', display: 'flex', gap: 4 }}>
        {[0, 1, 2].map(i => (
          <span key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: '#5A6272', animation: `dotBounce 1.2s infinite ${i * 0.16}s`, display: 'inline-block' }} />
        ))}
      </div>
    </div>
  )
}
