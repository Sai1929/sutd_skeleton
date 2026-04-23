import { api } from './client'

export interface Prediction { label: string; score: number; rank: number }
export interface RecommendResponse {
  activity: string
  selections: Record<string, string>
  predictions: Partial<Record<'hazard_type' | 'severity_likelihood' | 'moc_ppe' | 'remarks', Prediction[]>>
}

export async function recommend(
  activity: string,
  selections: Record<string, string>
): Promise<RecommendResponse> {
  const { data } = await api.post('/api/v1/inspect/recommend', { activity, selections })
  return data
}
