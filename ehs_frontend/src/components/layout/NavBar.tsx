type Tab = 'Activity RA' | 'Generate RA' | 'Document RA' | 'Quiz' | 'Hazard'
interface Props { activeTab: Tab; onTab: (t: Tab) => void }

const TAB_LABELS: { tab: Tab; label: string; sub: string }[] = [
  { tab: 'Activity RA', label: 'Activity RA', sub: '§ 01' },
  { tab: 'Generate RA', label: 'Generate RA', sub: '§ 02' },
  { tab: 'Document RA', label: 'Document RA', sub: '§ 03' },
  { tab: 'Quiz', label: 'Quiz', sub: '§ 04' },
  { tab: 'Hazard', label: 'Hazard', sub: '§ 05' },
]

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
        {TAB_LABELS.map(({ tab, label, sub }) => (
          <button key={tab} onClick={() => onTab(tab)} style={{
            padding: '7px 16px', border: 'none', borderRadius: 6,
            background: activeTab === tab ? '#FFFFFF' : 'transparent',
            boxShadow: activeTab === tab ? '0 1px 2px rgba(11,18,32,0.08)' : 'none',
            fontFamily: 'Inter, system-ui', fontSize: 12,
            fontWeight: activeTab === tab ? 600 : 500,
            color: activeTab === tab ? '#0B1220' : '#5A6272',
            cursor: 'pointer', letterSpacing: '-0.005em',
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1,
          }}>
            <span style={{ fontSize: 9, fontWeight: 500, letterSpacing: '0.1em', color: activeTab === tab ? '#1F3A8A' : '#9CA3AF', textTransform: 'uppercase' }}>{sub}</span>
            {label}
          </button>
        ))}
      </div>
    </nav>
  )
}
