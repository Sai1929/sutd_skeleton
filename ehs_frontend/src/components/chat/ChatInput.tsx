import { useRef, useEffect, useState } from 'react'

interface Props {
  value: string
  onChange: (v: string) => void
  onSend: (image?: File) => void
  disabled: boolean
}

export function ChatInput({ value, onChange, onSend, disabled }: Props) {
  const textRef = useRef<HTMLTextAreaElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const [image, setImage] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)

  useEffect(() => {
    if (textRef.current) {
      textRef.current.style.height = 'auto'
      textRef.current.style.height = Math.min(textRef.current.scrollHeight, 120) + 'px'
    }
  }, [value])

  const handleFile = (f: File) => {
    setImage(f)
    const reader = new FileReader()
    reader.onload = e => setPreview(e.target?.result as string)
    reader.readAsDataURL(f)
  }

  const removeImage = () => {
    setImage(null)
    setPreview(null)
    if (fileRef.current) fileRef.current.value = ''
  }

  const handleSend = () => {
    if (!value.trim() && !image) return
    onSend(image ?? undefined)
    setImage(null)
    setPreview(null)
    if (fileRef.current) fileRef.current.value = ''
  }

  const canSend = (value.trim().length > 0 || image !== null) && !disabled

  return (
    <div style={{ borderTop: '1px solid #E4DFD3', background: '#FFFFFF', padding: '12px 48px 24px' }}>
      <div style={{ maxWidth: 720, margin: '0 auto' }}>
        {preview && (
          <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ position: 'relative', display: 'inline-block' }}>
              <img src={preview} alt="attachment" style={{ height: 56, width: 'auto', maxWidth: 120, borderRadius: 4, border: '1px solid #E4DFD3', objectFit: 'cover', display: 'block' }} />
              <button onClick={removeImage}
                style={{ position: 'absolute', top: -6, right: -6, width: 18, height: 18, borderRadius: '50%', background: '#0B1220', border: 'none', color: '#fff', cursor: 'pointer', fontSize: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', lineHeight: 1 }}>
                ✕
              </button>
            </div>
            <span style={{ fontFamily: 'Inter, system-ui', fontSize: 11, color: '#5A6272' }}>{image?.name}</span>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8 }}>
          <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" style={{ display: 'none' }}
            onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }} />

          <button
            onClick={() => fileRef.current?.click()}
            disabled={disabled}
            title="Attach image"
            style={{ width: 38, height: 38, borderRadius: 6, flexShrink: 0, background: preview ? 'rgba(31,58,138,0.08)' : '#F5F2EC', border: `1px solid ${preview ? 'rgba(31,58,138,0.25)' : '#E4DFD3'}`, cursor: disabled ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={preview ? '#1F3A8A' : '#9CA3AF'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <polyline points="21 15 16 10 5 21"/>
            </svg>
          </button>

          <textarea ref={textRef} value={value} onChange={e => onChange(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
            placeholder="Ask about workplace safety, hazards, or WSH regulations…"
            rows={1} disabled={disabled}
            style={{ flex: 1, resize: 'none', padding: '10px 14px', fontFamily: 'Inter, system-ui', fontSize: 14, color: '#0B1220', background: '#F5F2EC', border: '1px solid #E4DFD3', borderRadius: 6, outline: 'none', lineHeight: 1.45, minHeight: 22, maxHeight: 120, overflow: 'hidden' }}
          />

          <button onClick={handleSend} disabled={!canSend} style={{
            width: 38, height: 38, borderRadius: 6, flexShrink: 0,
            background: canSend ? '#1F3A8A' : '#E4DFD3',
            border: 'none', cursor: canSend ? 'pointer' : 'not-allowed',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M2 8l12-5-5 12-2-5-5-2z" stroke="#FFFFFF" strokeWidth="1.6" strokeLinejoin="round" fill="#FFFFFF" />
            </svg>
          </button>
        </div>

        <div style={{ marginTop: 6, fontFamily: 'Inter, system-ui', fontSize: 11, color: '#9CA3AF' }}>
          Enter to send · Shift+Enter for new line · Attach image for visual hazard analysis
        </div>
      </div>
    </div>
  )
}
