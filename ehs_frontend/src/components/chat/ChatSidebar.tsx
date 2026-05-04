const SUGGESTIONS = [
  'Provide a risk assessment for a construction project.',
  'List major activities and identify hazards for an office setup.',
  'Create a risk assessment matrix for a manufacturing project.',
  'Identify control measures for a chemical handling activity.',
]

interface Props {
  onSend: (msg: string) => void
  hasMessages: boolean
  onClear: () => void
  isStreaming: boolean
  collapsed: boolean
  onToggle: () => void
}

export function ChatSidebar({ onSend, hasMessages, onClear, isStreaming, collapsed, onToggle }: Props) {
  if (collapsed) {
    return (
      <aside style={{
        background: '#FFFFFF', borderRight: '1px solid #E4DFD3',
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        paddingTop: 16, width: 48, flexShrink: 0,
      }}>
        <button onClick={onToggle} title="Expand sidebar" style={{
          width: 32, height: 32, borderRadius: 6, background: '#F5F2EC',
          border: '1px solid #E4DFD3', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#5A6272',
        }}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M5 3l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </aside>
    )
  }

  return (
    <aside style={{
      background: '#FFFFFF', borderRight: '1px solid #E4DFD3',
      padding: '24px 20px', display: 'flex', flexDirection: 'column',
      width: 300, flexShrink: 0, overflow: 'hidden',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 6, background: '#E8ECF7', color: '#1F3A8A',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: '"Source Serif 4", serif', fontWeight: 700, fontSize: 16, fontStyle: 'italic',
          }}>A</div>
          <div style={{ fontFamily: '"Source Serif 4", serif', fontSize: 15, fontWeight: 600, color: '#0B1220', letterSpacing: '-0.01em' }}>
            WSH Risk Advisor
          </div>
        </div>
        <button onClick={onToggle} title="Collapse sidebar" style={{
          width: 28, height: 28, borderRadius: 6, background: 'transparent',
          border: '1px solid #E4DFD3', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#5A6272',
          flexShrink: 0,
        }}>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M9 3l-4 4 4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>

      <p style={{ fontFamily: 'Inter, system-ui', fontSize: 13, color: '#5A6272', lineHeight: 1.55, margin: '0 0 20px' }}>
        Workplace safety guidance grounded in Singapore WSH Act and Council Codes of Practice.
      </p>

      <div style={{ fontFamily: 'Inter, system-ui', fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: '#5A6272', fontWeight: 500, marginBottom: 8 }}>
        Try Asking
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {SUGGESTIONS.map(s => (
          <button
            key={s}
            onClick={() => onSend(s)}
            disabled={isStreaming}
            style={{
              textAlign: 'left', padding: '9px 12px',
              fontFamily: 'Inter, system-ui', fontSize: 12, color: '#0B1220',
              background: '#F5F2EC', border: '1px solid #E4DFD3', borderRadius: 4,
              cursor: isStreaming ? 'not-allowed' : 'pointer', lineHeight: 1.4,
              transition: 'background .15s, border-color .15s',
            }}
            onMouseEnter={e => { if (!isStreaming) { e.currentTarget.style.background = '#E8ECF7'; e.currentTarget.style.borderColor = 'rgba(31,58,138,0.3)' } }}
            onMouseLeave={e => { e.currentTarget.style.background = '#F5F2EC'; e.currentTarget.style.borderColor = '#E4DFD3' }}
          >{s}</button>
        ))}
      </div>

      <div style={{ flex: 1 }} />

      {hasMessages && (
        <button
          onClick={onClear}
          style={{
            marginTop: 20, padding: '9px 12px',
            fontFamily: 'Inter, system-ui', fontSize: 12, color: '#5A6272',
            background: 'transparent', border: '1px solid #E4DFD3', borderRadius: 4, cursor: 'pointer',
          }}
        >
          Clear Conversation
        </button>
      )}
    </aside>
  )
}
