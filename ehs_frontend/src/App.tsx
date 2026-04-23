import { useState } from 'react'
import { NavBar } from './components/layout/NavBar'
import { InspectionPage } from './pages/InspectionPage'
import { ChatPage } from './pages/ChatPage'

export default function App() {
  const [tab, setTab] = useState<'Inspection' | 'Chat'>('Inspection')
  return (
    <div style={{ minHeight: '100vh', background: '#F5F2EC' }}>
      <NavBar activeTab={tab} onTab={setTab} />
      {tab === 'Inspection' ? <InspectionPage /> : <ChatPage />}
    </div>
  )
}
