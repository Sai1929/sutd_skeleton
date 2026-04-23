import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ChatMessage } from '../../hooks/useChat'

interface Props { msg: ChatMessage }

export function MessageBubble({ msg }: Props) {
  const isUser = msg.role === 'user'
  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', gap: 10 }}>
      {!isUser && (
        <div style={{
          width: 28, height: 28, borderRadius: 6, background: '#E8ECF7',
          color: '#1F3A8A', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: '"Source Serif 4", serif', fontWeight: 700, fontSize: 13,
          fontStyle: 'italic', flexShrink: 0, marginTop: 2,
        }}>A</div>
      )}
      <div style={{
        maxWidth: '82%', padding: isUser ? '10px 16px' : '14px 18px',
        background: isUser ? '#0B1220' : '#FFFFFF',
        color: isUser ? '#FFFFFF' : '#0B1220',
        border: isUser ? 'none' : '1px solid #E4DFD3',
        borderRadius: isUser ? '10px 10px 2px 10px' : '10px 10px 10px 2px',
        fontFamily: 'Inter, system-ui', fontSize: 14, lineHeight: 1.55,
      }}>
        {isUser ? (
          <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
        ) : (
          <div className="md-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {msg.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
