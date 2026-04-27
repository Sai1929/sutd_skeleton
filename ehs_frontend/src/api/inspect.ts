import { api } from './client'

export interface RARow {
  main_activity: string
  sub_activity: string
  hazard: string
  consequences: string
  initial_l: number
  initial_s: number
  initial_risk: string
  control_measures: string
  residual_l: number
  residual_s: number
  residual_risk: string
}

export interface RiskBand {
  range: string
  level: string
  action: string
}

export interface FullRA {
  project: string
  document_no?: string
  revision?: string
  date?: string
  prepared_by?: string
  reviewed_by?: string
  approved_by?: string
  scope?: string
  purpose?: string
  assumptions: string[]
  rows: RARow[]
  risk_matrix?: { note: string; bands: RiskBand[] }
  emergency_response?: string[]
  chemical_note?: string
  references?: string[]
  review_schedule?: string
  [key: string]: unknown
}

export interface RecommendResponse {
  activity: string
  from_db: boolean
  project: string
  assumptions: string[]
  rows: RARow[]
  full_ra?: FullRA | null
}

export async function recommend(activity: string): Promise<RecommendResponse> {
  const { data } = await api.post('/api/v1/inspect/recommend', { activity })
  return data
}

export async function recommendFromDocument(file: File): Promise<RecommendResponse> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/api/v1/inspect/from-document', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
