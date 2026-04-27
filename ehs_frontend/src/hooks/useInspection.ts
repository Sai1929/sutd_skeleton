import { useCallback, useReducer, useRef } from 'react'
import { recommend, recommendFromDocument, RecommendResponse } from '../api/inspect'

export type FetchState = 'idle' | 'loading' | 'done' | 'error'

interface State {
  activity: string
  fetchState: FetchState
  result: RecommendResponse | null
  error: string | null
}

type Action =
  | { type: 'SET_ACTIVITY'; value: string }
  | { type: 'LOADING' }
  | { type: 'SUCCESS'; result: RecommendResponse }
  | { type: 'ERROR'; error: string }
  | { type: 'RESET' }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_ACTIVITY':
      return { ...state, activity: action.value }
    case 'LOADING':
      return { ...state, fetchState: 'loading', error: null }
    case 'SUCCESS':
      return { ...state, fetchState: 'done', result: action.result, error: null }
    case 'ERROR':
      return { ...state, fetchState: 'error', error: action.error, result: null }
    case 'RESET':
      return { activity: '', fetchState: 'idle', result: null, error: null }
    default:
      return state
  }
}

export function useInspection() {
  const [state, dispatch] = useReducer(reducer, {
    activity: '',
    fetchState: 'idle',
    result: null,
    error: null,
  })
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const setActivity = useCallback((value: string) => {
    dispatch({ type: 'SET_ACTIVITY', value })
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!value.trim()) { dispatch({ type: 'RESET' }); return }
    dispatch({ type: 'LOADING' })
    debounceRef.current = setTimeout(async () => {
      try {
        const result = await recommend(value)
        dispatch({ type: 'SUCCESS', result })
      } catch {
        dispatch({ type: 'ERROR', error: 'Failed to fetch recommendation.' })
      }
    }, 600)
  }, [])

  const uploadDocument = useCallback(async (file: File) => {
    dispatch({ type: 'LOADING' })
    try {
      const result = await recommendFromDocument(file)
      dispatch({ type: 'SET_ACTIVITY', value: result.project })
      dispatch({ type: 'SUCCESS', result })
    } catch {
      dispatch({ type: 'ERROR', error: 'Failed to process document.' })
    }
  }, [])

  const reset = useCallback(() => dispatch({ type: 'RESET' }), [])

  return { ...state, setActivity, uploadDocument, reset }
}
