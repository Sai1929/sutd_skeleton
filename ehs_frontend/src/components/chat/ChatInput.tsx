import { useRef, useEffect } from 'react'

interface Props { value: string; onChange: (v: string) => void; onSend: () => void; disabled: boolean }

export function ChatInput({ value, onChange, onSend, disabled }: Props) {
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (ref.current) {
      ref.current.style.height = 'auto'
      ref.current.style.height = Math.min(ref.current.scrollHeight, 120) + 'px'
    }
  }, [value])

  return (
    <div style={{ borderTop: '1px solid #E4DFD3', background: '#FFFFFF', padding: '16px 48px 24px' }}>
      <div style={{ maxWidth: 720, margin: '0 auto', display: 'flex', alignItems: 'flex-end', gap: 10 }}>
        <textarea ref={ref} value={value} onChange={e => onChange(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onSend() } }}
          placeholder="Ask about workplace safety, hazards, or WSH regulations…"
          rows={1} disabled={disabled}
          style={{ flex: 1, resize: 'none', padding: '12px 14px', fontFamily: 'Inter, system-ui', fontSize: 14, color: '#0B1220', background: '#F5F2EC', border: '1px solid #E4DFD3', borderRadius: 6, outline: 'none', lineHeight: 1.45, minHeight: 22, maxHeight: 120, overflow: 'hidden' }}
        />
        <button onClick={onSend} disabled={!value.trim() || disabled} style={{
          width: 44, height: 44, borderRadius: 6, flexShrink: 0,
          background: value.trim() && !disabled ? '#1F3A8A' : '#E4DFD3',
          border: 'none', cursor: value.trim() && !disabled ? 'pointer' : 'not-allowed',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M2 8l12-5-5 12-2-5-5-2z" stroke="#FFFFFF" strokeWidth="1.6" strokeLinejoin="round" fill="#FFFFFF" />
          </svg>
        </button>
      </div>
      <div style={{ maxWidth: 720, margin: '8px auto 0', fontFamily: 'Inter, system-ui', fontSize: 11, color: '#5A6272' }}>
        Enter to send · Shift+Enter for a new line · Responses may require verification against source regulations.
      </div>
    </div>
  )
}
