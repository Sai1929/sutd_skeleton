import { useReducer, useCallback } from 'react'
import { generateQuiz, QuizQuestion } from '../api/quiz'

type Phase = 'closed' | 'loading' | 'question' | 'results'
interface State {
  phase: Phase
  questions: QuizQuestion[]
  answers: Record<number, number>  // questionIdx -> option index (0-3)
  currentIdx: number
}

type Action =
  | { type: 'OPEN' }
  | { type: 'SET_QUESTIONS'; questions: QuizQuestion[] }
  | { type: 'SELECT'; idx: number }
  | { type: 'NEXT' }
  | { type: 'SUBMIT' }
  | { type: 'CLOSE' }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'OPEN': return { phase: 'loading', questions: [], answers: {}, currentIdx: 0 }
    case 'SET_QUESTIONS': return { ...state, phase: 'question', questions: action.questions }
    case 'SELECT': return { ...state, answers: { ...state.answers, [state.currentIdx]: action.idx } }
    case 'NEXT': return { ...state, currentIdx: state.currentIdx + 1 }
    case 'SUBMIT': return { ...state, phase: 'results' }
    case 'CLOSE': return { phase: 'closed', questions: [], answers: {}, currentIdx: 0 }
    default: return state
  }
}

export function useQuiz() {
  const [state, dispatch] = useReducer(reducer, { phase: 'closed', questions: [], answers: {}, currentIdx: 0 })

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

  const select = useCallback((idx: number) => dispatch({ type: 'SELECT', idx }), [])
  const next = useCallback(() => dispatch({ type: 'NEXT' }), [])
  const submit = useCallback(() => dispatch({ type: 'SUBMIT' }), [])
  const close = useCallback(() => dispatch({ type: 'CLOSE' }), [])

  const correctCount = state.questions.reduce((acc, q, i) => {
    const answerIdx = state.answers[i]
    if (answerIdx === undefined) return acc
    const correctIdx = q.correct_answer.charCodeAt(0) - 65  // 'A'->0, 'B'->1 etc
    return acc + (answerIdx === correctIdx ? 1 : 0)
  }, 0)

  return { ...state, open, select, next, submit, close, correctCount }
}
