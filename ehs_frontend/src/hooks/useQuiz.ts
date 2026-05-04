import { useReducer, useCallback } from 'react'
import { generateQuiz, QuizQuestion } from '../api/quiz'

type Phase = 'closed' | 'loading' | 'question' | 'results'

interface State {
  phase: Phase
  questions: QuizQuestion[]
  mcqAnswers: Record<number, number>   // questionIdx -> option index (0-3), MCQ only
  textAnswers: Record<number, string>  // questionIdx -> typed text, descriptive/scenario
  currentIdx: number
}

type Action =
  | { type: 'OPEN' }
  | { type: 'SET_QUESTIONS'; questions: QuizQuestion[] }
  | { type: 'SELECT_MCQ'; idx: number }
  | { type: 'SET_TEXT'; text: string }
  | { type: 'NEXT' }
  | { type: 'SUBMIT' }
  | { type: 'CLOSE' }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'OPEN': return { phase: 'loading', questions: [], mcqAnswers: {}, textAnswers: {}, currentIdx: 0 }
    case 'SET_QUESTIONS': return { ...state, phase: 'question', questions: action.questions }
    case 'SELECT_MCQ': return { ...state, mcqAnswers: { ...state.mcqAnswers, [state.currentIdx]: action.idx } }
    case 'SET_TEXT': return { ...state, textAnswers: { ...state.textAnswers, [state.currentIdx]: action.text } }
    case 'NEXT': return { ...state, currentIdx: state.currentIdx + 1 }
    case 'SUBMIT': return { ...state, phase: 'results' }
    case 'CLOSE': return { phase: 'closed', questions: [], mcqAnswers: {}, textAnswers: {}, currentIdx: 0 }
    default: return state
  }
}

export function useQuiz() {
  const [state, dispatch] = useReducer(reducer, {
    phase: 'closed', questions: [], mcqAnswers: {}, textAnswers: {}, currentIdx: 0,
  })

  const open = useCallback(async (params: {
    activity: string; hazard_type: string; severity_likelihood: string; moc_ppe: string; remarks: string
  }) => {
    dispatch({ type: 'OPEN' })
    try {
      const result = await generateQuiz(params)
      dispatch({ type: 'SET_QUESTIONS', questions: result.questions })
    } catch {
      dispatch({ type: 'CLOSE' })
    }
  }, [])

  const selectMcq = useCallback((idx: number) => dispatch({ type: 'SELECT_MCQ', idx }), [])
  const setText = useCallback((text: string) => dispatch({ type: 'SET_TEXT', text }), [])
  const next = useCallback(() => dispatch({ type: 'NEXT' }), [])
  const submit = useCallback(() => dispatch({ type: 'SUBMIT' }), [])
  const close = useCallback(() => dispatch({ type: 'CLOSE' }), [])

  // MCQ-only correct count (descriptive/scenario always counted as attempted)
  const correctCount = state.questions.reduce((acc, q, i) => {
    if (q.question_type !== 'mcq') return acc
    const ansIdx = state.mcqAnswers[i]
    if (ansIdx === undefined) return acc
    return acc + (ansIdx === q.correct_answer.charCodeAt(0) - 65 ? 1 : 0)
  }, 0)

  const mcqTotal = state.questions.filter(q => q.question_type === 'mcq').length

  return { ...state, open, selectMcq, setText, next, submit, close, correctCount, mcqTotal }
}
