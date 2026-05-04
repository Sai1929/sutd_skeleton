import { api } from './client'

export interface ChatMessage { role: 'user' | 'assistant'; content: string }
export interface ChatResponse { reply: string; model: string }

export async function sendChat(message: string, history: ChatMessage[], image?: File): Promise<ChatResponse> {
  const form = new FormData()
  form.append('message', message)
  form.append('history', JSON.stringify(history))
  if (image) form.append('image', image)
  const { data } = await api.post('/api/v1/chat/query', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
