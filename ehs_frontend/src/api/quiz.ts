import { api } from './client'

export interface QuizQuestion {
  question_number: number
  question_type: 'mcq' | 'descriptive' | 'scenario'
  question_text: string
  options: string[] | null   // MCQ only
  correct_answer: string     // MCQ: "A"/"B"/"C"/"D" | descriptive/scenario: model answer text
  explanation: string | null
}
export interface QuizResponse { questions: QuizQuestion[] }

export async function generateQuiz(params: {
  activity: string
  hazard_type: string
  severity_likelihood: string
  moc_ppe: string
  remarks: string
}): Promise<QuizResponse> {
  const { data } = await api.post('/api/v1/quiz/generate', params)
  return data
}
