import { api } from './client'
import type { RecommendResponse } from './inspect'

export async function generateRAJson(projectName: string, description: string): Promise<RecommendResponse> {
  const form = new FormData()
  form.append('project_name', projectName)
  form.append('description', description)
  const { data } = await api.post('/api/v1/ra/generate', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function downloadRADocx(projectName: string, description: string): Promise<void> {
  const form = new FormData()
  form.append('project_name', projectName)
  form.append('description', description)

  const response = await api.post('/api/v1/ra/generate/docx', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob',
  })

  const url = URL.createObjectURL(new Blob([response.data], {
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  }))
  const a = document.createElement('a')
  a.href = url
  a.download = (projectName.trim() || 'risk_assessment') + '.docx'
  a.click()
  URL.revokeObjectURL(url)
}
