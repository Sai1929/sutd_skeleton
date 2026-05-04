import { useState } from 'react'

interface Props { value: string; onChange: (v: string) => void }

export function ActivityInput({ value, onChange }: Props) {
  const [focused, setFocused] = useState(false)
  return (
    <div style={{ position: 'relative' }}>
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none"
        style={{ position: 'absolute', left: 18, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}>
        <circle cx="9" cy="9" r="6" stroke="#5A6272" strokeWidth="1.5" />
        <path d="M13.5 13.5L17 17" stroke="#5A6272" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder="What activity are you inspecting? e.g. Electrical Works, Welding…"
        style={{
          width: '100%', height: 60, padding: '0 20px 0 52px',
          fontFamily: '"Source Serif 4", serif', fontSize: 19, fontWeight: 400, fontStyle: 'italic',
          color: '#0B1220', background: '#FFFFFF',
          border: `1px solid ${focused ? '#1F3A8A' : '#E4DFD3'}`,
          borderRadius: 4, outline: 'none',
          boxShadow: focused ? '0 0 0 3px rgba(31,58,138,0.08)' : 'none',
          transition: 'border-color .2s, box-shadow .2s',
        }}
      />
      {value && (
        <button onClick={() => onChange('')} style={{
          position: 'absolute', right: 16, top: '50%', transform: 'translateY(-50%)',
          width: 24, height: 24, borderRadius: '50%',
          background: '#F5F2EC', border: '1px solid #E4DFD3',
          color: '#5A6272', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 14, lineHeight: 1,
        }}>×</button>
      )}
    </div>
  )
}
