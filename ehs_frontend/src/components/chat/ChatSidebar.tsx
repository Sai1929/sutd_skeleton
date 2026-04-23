const SUGGESTIONS = [
  'What PPE is required for welding near flammables?',
  'When is a Permit-to-Work required for electrical work?',
  'Confined space entry — gas monitoring thresholds?',
  'Arc flash protection categories explained',
  'WSH Act 2006 — employer penalties overview',
  'Working at height — harness inspection checklist',
]

interface Props { onSend: (msg: string) => void; hasMessages: boolean; onClear: () => void; isStreaming: boolean }

export function ChatSidebar({ onSend, hasMessages, onClear, isStreaming }: Props) {
  return (
    <aside style={{ background: '#FFFFFF', borderRight: '1px solid #E4DFD3', padding: '32px 24px', display: 'flex', flexDirection: 'column', overflow: 'auto', width: 300, flexShrink: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
        <div style={{ width: 32, height: 32, borderRadius: 6, background: '#E8ECF7', color: '#1F3A8A', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: '"Source Serif 4", serif', fontWeight: 700, fontSize: 16, fontStyle: 'italic' }}>A</div>
        <div style={{ fontFamily: '"Source Serif 4", serif', fontSize: 15, fontWeight: 600, color: '#0B1220', letterSpacing: '-0.01em' }}>WSH Risk Advisor</div>
      </div>
      <p style={{ fontFamily: 'Inter, system-ui', fontSize: 13, color: '#5A6272', lineHeight: 1.55, margin: 0, marginBottom: 24 }}>
        Workplace safety guidance grounded in Singapore WSH Act and Council Codes of Practice. Ask about hazards, PPE, permits, or regulatory references.
      </p>
      <div style={{ fontFamily: 'Inter, system-ui', fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 500, marginBottom: 10 }}>Try Asking</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {SUGGESTIONS.map(s => (
          <button key={s} onClick={() => onSend(s)} disabled={isStreaming} style={{
            textAlign: 'left', padding: '9px 12px', fontFamily: 'Inter, system-ui', fontSize: 12, color: '#0B1220',
            background: '#F5F2EC', border: '1px solid #E4DFD3', borderRadius: 4,
            cursor: isStreaming ? 'not-allowed' : 'pointer', lineHeight: 1.4, transition: 'background .15s, border-color .15s',
          }}
            onMouseEnter={e => { if (!isStreaming) { (e.currentTarget as HTMLButtonElement).style.background = '#E8ECF7'; (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(31,58,138,0.3)' } }}
            onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = '#F5F2EC'; (e.currentTarget as HTMLButtonElement).style.borderColor = '#E4DFD3' }}
          >{s}</button>
        ))}
      </div>
      <div style={{ flex: 1 }} />
      {hasMessages && (
        <button onClick={onClear} style={{ marginTop: 24, padding: '9px 12px', fontFamily: 'Inter, system-ui', fontSize: 12, color: '#5A6272', background: 'transparent', border: '1px solid #E4DFD3', borderRadius: 4, cursor: 'pointer' }}>
          Clear Conversation
        </button>
      )}
      <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid #E4DFD3', fontFamily: '"JetBrains Mono", monospace', fontSize: 10, color: '#5A6272', letterSpacing: '0.06em', lineHeight: 1.6 }}>
        Model · llama-4-scout<br />Context · WSH Act, SS 508, SS 668
      </div>
    </aside>
  )
}
