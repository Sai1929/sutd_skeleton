interface Props { activeTab: 'Inspection' | 'Chat'; onTab: (t: 'Inspection' | 'Chat') => void }

export function NavBar({ activeTab, onTab }: Props) {
  return (
    <nav style={{
      height: 68, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 32px', background: '#FFFFFF', borderBottom: '1px solid #E4DFD3',
      position: 'sticky', top: 0, zIndex: 40,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{
          width: 28, height: 28, borderRadius: 6, background: '#0B1220',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontFamily: '"Source Serif 4", serif', fontSize: 15, fontWeight: 700, fontStyle: 'italic',
        }}>E</div>
        <div>
          <div style={{ fontFamily: '"Source Serif 4", serif', fontSize: 17, fontWeight: 600, color: '#0B1220', letterSpacing: '-0.01em', lineHeight: 1 }}>
            EHS Portal
          </div>
          <div style={{ fontFamily: 'Inter, system-ui', fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', color: '#5A6272', marginTop: 3, fontWeight: 500 }}>
            Environment · Health · Safety
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', background: '#F5F2EC', borderRadius: 8, padding: 3, border: '1px solid #E4DFD3' }}>
        {(['Inspection', 'Chat'] as const).map(tab => (
          <button key={tab} onClick={() => onTab(tab)} style={{
            padding: '7px 18px', border: 'none', borderRadius: 6,
            background: activeTab === tab ? '#FFFFFF' : 'transparent',
            boxShadow: activeTab === tab ? '0 1px 2px rgba(11,18,32,0.08)' : 'none',
            fontFamily: 'Inter, system-ui', fontSize: 13,
            fontWeight: activeTab === tab ? 600 : 500,
            color: activeTab === tab ? '#0B1220' : '#5A6272',
            cursor: 'pointer', letterSpacing: '-0.005em',
          }}>{tab}</button>
        ))}
      </div>
    </nav>
  )
}
