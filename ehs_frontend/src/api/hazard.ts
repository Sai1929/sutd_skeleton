import { api } from './client'

export interface ControlMeasure {
  hierarchy: string
  measures: string[]
}

export interface MitigationActivity {
  activity: string
  responsible_party: string
  priority: 'Immediate' | 'Short-term' | 'Ongoing'
}

export interface HazardAnalysisResponse {
  hazard_identified: string
  hazard_description: string
  risk_level: string
  potential_consequences: string[]
  control_measures: ControlMeasure[]
  mitigation_activities: MitigationActivity[]
  applicable_regulations: string[]
  residual_risk: string
}

export async function analyseHazard(text: string, image?: File): Promise<HazardAnalysisResponse> {
  const form = new FormData()
  if (text) form.append('text', text)
  if (image) form.append('image', image)
  const { data } = await api.post('/api/v1/hazard/analyse', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
