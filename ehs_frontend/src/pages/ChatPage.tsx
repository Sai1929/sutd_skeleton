import { useRef, useEffect } from 'react'
import { useChat } from '../hooks/useChat'
import { ChatSidebar } from '../components/chat/ChatSidebar'
import { MessageBubble } from '../components/chat/MessageBubble'
import { TypingIndicator } from '../components/chat/TypingIndicator'
import { ChatInput } from '../components/chat/ChatInput'

export function ChatPage() {
  const { messages, input, isStreaming, send, setInput, clear } = useChat()
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [messages])

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', height: 'calc(100vh - 68px)' }}>
      <ChatSidebar onSend={send} hasMessages={messages.length > 0} onClear={clear} isStreaming={isStreaming} />
      <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>
        <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', padding: '32px 48px 16px' }}>
          {messages.length === 0 ? (
            <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', maxWidth: 460, margin: '0 auto' }}>
              <div style={{ width: 52, height: 52, borderRadius: 10, background: '#E8ECF7', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 22 }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L4 6v6c0 5 3.4 9.3 8 10 4.6-.7 8-5 8-10V6l-8-4z" stroke="#1F3A8A" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <h2 style={{ fontFamily: '"Source Serif 4", serif', fontSize: 26, fontWeight: 500, color: '#0B1220', margin: 0, letterSpacing: '-0.015em' }}>
                How can I help with workplace safety today?
              </h2>
              <p style={{ fontFamily: 'Inter, system-ui', fontSize: 14, color: '#5A6272', lineHeight: 1.55, marginTop: 12 }}>
                Ask about hazards, PPE selection, permits, or specific clauses in the Singapore WSH Act.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 720, margin: '0 auto' }}>
              {messages.map((m, i) => <MessageBubble key={i} msg={m} />)}
              {isStreaming && <TypingIndicator />}
            </div>
          )}
        </div>
        <ChatInput value={input} onChange={setInput} onSend={() => send(input)} disabled={isStreaming} />
      </div>
    </div>
  )
}
