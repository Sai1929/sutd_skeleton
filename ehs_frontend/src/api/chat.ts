import { api } from './client'

export interface ChatMessage { role: 'user' | 'assistant'; content: string }
export interface ChatResponse { reply: string; model: string }

export async function sendChat(message: string, history: ChatMessage[]): Promise<ChatResponse> {
  const { data } = await api.post('/api/v1/chat/query', { message, history })
  return data
}
