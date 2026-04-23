import { useCallback, useReducer, useRef } from 'react'
import { recommend, Prediction } from '../api/inspect'

export type CardState = 'empty' | 'loading' | 'predicted' | 'confirmed' | 'overridden'
export type StepKey = 'hazard_type' | 'severity_likelihood' | 'moc_ppe' | 'remarks'

export const STEPS: { key: StepKey; title: string }[] = [
  { key: 'hazard_type',         title: 'Hazard Type' },
  { key: 'severity_likelihood', title: 'Severity · Likelihood' },
  { key: 'moc_ppe',             title: 'Controls & PPE' },
  { key: 'remarks',             title: 'Recommended Remark' },
]

interface State {
  activity: string
  predictions: Record<StepKey, Prediction[]>
  cardStates: Record<StepKey, CardState>
  selected: Record<StepKey, number>
}

type Action =
  | { type: 'SET_ACTIVITY'; value: string }
  | { type: 'ALL_LOADING' }
  | { type: 'SET_CARD_STATE'; key: StepKey; state: CardState }
  | { type: 'SET_PREDICTIONS'; predictions: Partial<Record<StepKey, Prediction[]>> }
  | { type: 'CONFIRM'; key: StepKey }
  | { type: 'OVERRIDE'; key: StepKey; idx: number }
  | { type: 'RESET' }

const emptyStates = () => STEPS.reduce((a, s) => ({ ...a, [s.key]: 'empty' as CardState }), {} as Record<StepKey, CardState>)
const zeroSelected = () => STEPS.reduce((a, s) => ({ ...a, [s.key]: 0 }), {} as Record<StepKey, number>)
const emptyPreds = () => STEPS.reduce((a, s) => ({ ...a, [s.key]: [] }), {} as Record<StepKey, Prediction[]>)

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_ACTIVITY':
      return { ...state, activity: action.value }
    case 'ALL_LOADING':
      return { ...state, cardStates: STEPS.reduce((a, s) => ({ ...a, [s.key]: 'loading' as CardState }), {} as Record<StepKey, CardState>) }
    case 'SET_CARD_STATE':
      return { ...state, cardStates: { ...state.cardStates, [action.key]: action.state } }
    case 'SET_PREDICTIONS':
      return {
        ...state,
        predictions: { ...state.predictions, ...action.predictions },
        selected: { ...state.selected, ...STEPS.reduce((a, s) => action.predictions[s.key] ? { ...a, [s.key]: 0 } : a, {}) },
      }
    case 'CONFIRM':
      return { ...state, cardStates: { ...state.cardStates, [action.key]: 'confirmed' } }
    case 'OVERRIDE':
      return {
        ...state,
        selected: { ...state.selected, [action.key]: action.idx },
        cardStates: { ...state.cardStates, [action.key]: 'overridden' },
      }
    case 'RESET':
      return { activity: '', predictions: emptyPreds(), cardStates: emptyStates(), selected: zeroSelected() }
    default:
      return state
  }
}

export function useInspection() {
  const [state, dispatch] = useReducer(reducer, {
    activity: '',
    predictions: emptyPreds(),
    cardStates: emptyStates(),
    selected: zeroSelected(),
  })
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const stateRef = useRef(state)
  stateRef.current = state

  const setActivity = useCallback((value: string) => {
    dispatch({ type: 'SET_ACTIVITY', value })
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!value.trim()) {
      dispatch({ type: 'RESET' })
      return
    }
    dispatch({ type: 'ALL_LOADING' })
    debounceRef.current = setTimeout(async () => {
      try {
        const result = await recommend(value, {})
        dispatch({ type: 'SET_PREDICTIONS', predictions: result.predictions as Record<StepKey, Prediction[]> })
        STEPS.forEach((s, i) => {
          setTimeout(() => dispatch({ type: 'SET_CARD_STATE', key: s.key, state: 'predicted' }), i * 120)
        })
      } catch {
        STEPS.forEach(s => dispatch({ type: 'SET_CARD_STATE', key: s.key, state: 'empty' }))
      }
    }, 500)
  }, [])

  const confirmCard = useCallback((key: StepKey) => {
    dispatch({ type: 'CONFIRM', key })
  }, [])

  const overrideCard = useCallback(async (key: StepKey, idx: number) => {
    dispatch({ type: 'OVERRIDE', key, idx })
    const current = stateRef.current
    const thisIdx = STEPS.findIndex(s => s.key === key)
    const downstream = STEPS.slice(thisIdx + 1)

    // Build selections: all confirmed/overridden steps up to and including this one
    const selections: Record<string, string> = {}
    STEPS.slice(0, thisIdx + 1).forEach(s => {
      const selIdx = s.key === key ? idx : current.selected[s.key]
      const preds = current.predictions[s.key]
      if (preds[selIdx]) selections[s.key] = preds[selIdx].label
    })

    downstream.forEach(s => dispatch({ type: 'SET_CARD_STATE', key: s.key, state: 'loading' }))

    try {
      const result = await recommend(current.activity, selections)
      dispatch({ type: 'SET_PREDICTIONS', predictions: result.predictions as Record<StepKey, Prediction[]> })
      downstream.forEach((s, i) => {
        setTimeout(() => dispatch({ type: 'SET_CARD_STATE', key: s.key, state: 'predicted' }), 500 + i * 140)
      })
    } catch {
      downstream.forEach(s => dispatch({ type: 'SET_CARD_STATE', key: s.key, state: 'predicted' }))
    }
  }, [])

  const reset = useCallback(() => dispatch({ type: 'RESET' }), [])

  const allConfirmed = STEPS.every(s =>
    state.cardStates[s.key] === 'confirmed' || state.cardStates[s.key] === 'overridden'
  )

  const getSelectedLabel = (key: StepKey) => state.predictions[key][state.selected[key]]?.label ?? ''

  return { ...state, setActivity, confirmCard, overrideCard, reset, allConfirmed, getSelectedLabel }
}
