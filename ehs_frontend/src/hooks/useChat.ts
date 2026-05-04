import { useReducer, useCallback, useRef } from 'react'
import { sendChat } from '../api/chat'

export interface ChatMessage { role: 'user' | 'assistant'; content: string; ts: number; imagePreview?: string }
interface State { messages: ChatMessage[]; input: string; isStreaming: boolean }
type Action =
  | { type: 'SET_INPUT'; value: string }
  | { type: 'ADD_USER'; content: string; imagePreview?: string }
  | { type: 'ADD_ASSISTANT' }
  | { type: 'STREAM_TOKEN'; token: string }
  | { type: 'DONE' }
  | { type: 'CLEAR' }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'SET_INPUT': return { ...state, input: action.value }
    case 'ADD_USER': return { ...state, messages: [...state.messages, { role: 'user', content: action.content, ts: Date.now(), imagePreview: action.imagePreview }], input: '', isStreaming: true }
    case 'ADD_ASSISTANT': return { ...state, messages: [...state.messages, { role: 'assistant', content: '', ts: Date.now() }] }
    case 'STREAM_TOKEN': {
      const msgs = [...state.messages]
      msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content: msgs[msgs.length - 1].content + action.token }
      return { ...state, messages: msgs }
    }
    case 'DONE': return { ...state, isStreaming: false }
    case 'CLEAR': return { messages: [], input: '', isStreaming: false }
    default: return state
  }
}

export function useChat() {
  const [state, dispatch] = useReducer(reducer, { messages: [], input: '', isStreaming: false })
  const stateRef = useRef(state)
  stateRef.current = state

  const send = useCallback(async (text: string, image?: File) => {
    if ((!text.trim() && !image) || stateRef.current.isStreaming) return
    const history = stateRef.current.messages.map(m => ({ role: m.role, content: m.content }))

    let imagePreview: string | undefined
    if (image) {
      imagePreview = await new Promise<string>(resolve => {
        const reader = new FileReader()
        reader.onload = e => resolve(e.target?.result as string)
        reader.readAsDataURL(image)
      })
    }

    dispatch({ type: 'ADD_USER', content: text, imagePreview })
    try {
      const result = await sendChat(text, history, image)
      dispatch({ type: 'ADD_ASSISTANT' })
      const words = result.reply.split(/(\s+)/)
      let i = 0
      const tick = () => {
        i++
        dispatch({ type: 'STREAM_TOKEN', token: words.slice(0, i).join('') !== '' ? words[i-1] : '' })
        if (i < words.length) setTimeout(tick, 18 + Math.random() * 20)
        else dispatch({ type: 'DONE' })
      }
      setTimeout(tick, 200)
    } catch (err: unknown) {
      dispatch({ type: 'ADD_ASSISTANT' })
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      dispatch({ type: 'STREAM_TOKEN', token: detail ? `Error: ${detail}` : 'Failed to get response. Check backend connection.' })
      dispatch({ type: 'DONE' })
    }
  }, [])

  const setInput = useCallback((value: string) => dispatch({ type: 'SET_INPUT', value }), [])
  const clear = useCallback(() => dispatch({ type: 'CLEAR' }), [])

  return { ...state, send, setInput, clear }
}
