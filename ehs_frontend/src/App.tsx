import { useState } from 'react'
import { NavBar } from './components/layout/NavBar'
import { InspectionPage } from './pages/InspectionPage'
import { RAPage } from './pages/RAPage'
import { DocumentRAPage } from './pages/DocumentRAPage'
import { QuizPage } from './pages/QuizPage'
import { HazardPage } from './pages/HazardPage'

type Tab = 'Activity RA' | 'Generate RA' | 'Document RA' | 'Quiz' | 'Hazard'

export default function App() {
  const [tab, setTab] = useState<Tab>('Activity RA')
  return (
    <div style={{ minHeight: '100vh', background: '#F5F2EC' }}>
      <NavBar activeTab={tab} onTab={setTab} />
      {tab === 'Activity RA' && <InspectionPage />}
      {tab === 'Generate RA' && <RAPage />}
      {tab === 'Document RA' && <DocumentRAPage />}
      {tab === 'Quiz' && <QuizPage />}
      {tab === 'Hazard' && <HazardPage />}
    </div>
  )
}
