interface Props { onPick: (v: string) => void }
const CHIPS = ['Electrical Works', 'Welding', 'Confined Space', 'Working at Height']

export function SuggestionChips({ onPick }: Props) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 14, alignItems: 'center' }}>
      <span style={{ fontFamily: 'Inter, system-ui', fontSize: 11, color: '#5A6272', letterSpacing: '0.1em', textTransform: 'uppercase', fontWeight: 500, marginRight: 4 }}>Common</span>
      {CHIPS.map(s => (
        <button key={s} onClick={() => onPick(s)} style={{
          padding: '6px 12px', fontFamily: 'Inter, system-ui', fontSize: 12, color: '#0B1220',
          background: '#FFFFFF', border: '1px solid #E4DFD3', borderRadius: 999, cursor: 'pointer',
          transition: 'background .15s, border-color .15s',
        }}
          onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.background = '#E8ECF7'; (e.currentTarget as HTMLButtonElement).style.borderColor = 'rgba(31,58,138,0.25)' }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.background = '#FFFFFF'; (e.currentTarget as HTMLButtonElement).style.borderColor = '#E4DFD3' }}
        >{s}</button>
      ))}
    </div>
  )
}
