import { useState } from 'react'
import { ConfidenceBar } from './ConfidenceBar'
import type { Prediction } from '../../api/inspect'
import type { CardState, StepKey } from '../../hooks/useInspection'

interface Props {
  step: number
  title: string
  stepKey: StepKey
  options: Prediction[]
  state: CardState
  selectedIndex: number
  onConfirm: () => void
  onOverride: (idx: number) => void
}

function CheckIcon({ size = 14, color = '#1F7A3A' }) {
  return <svg width={size} height={size} viewBox="0 0 16 16" fill="none"><path d="M3 8.5l3 3 7-7" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
}
function EditIcon({ size = 13, color = '#5A6272' }) {
  return <svg width={size} height={size} viewBox="0 0 16 16" fill="none"><path d="M11 2.5l2.5 2.5-8 8H3v-2.5l8-8z" stroke={color} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" /></svg>
}
function ChevronIcon({ size = 12, color = '#5A6272', dir = 'down' }: { size?: number; color?: string; dir?: 'down'|'up' }) {
  return <svg width={size} height={size} viewBox="0 0 12 12" fill="none" style={{ transform: `rotate(${dir === 'up' ? 180 : 0}deg)`, transition: 'transform .2s' }}><path d="M2.5 4.5L6 8l3.5-3.5" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
}

export function PredictionCard({ step, title, options, state, selectedIndex, onConfirm, onOverride }: Props) {
  const [expanded, setExpanded] = useState(false)

  const isEmpty = state === 'empty'
  const isLoading = state === 'loading'
  const isConfirmed = state === 'confirmed'
  const isOverridden = state === 'overridden'
  const hasResult = ['predicted', 'confirmed', 'overridden'].includes(state)

  const top = hasResult && options.length > 0 ? options[selectedIndex] ?? options[0] : null
  const runnersUp = hasResult ? options.filter((_, i) => i !== selectedIndex).slice(0, 2) : []
  const moreCount = hasResult ? Math.max(0, options.length - 1 - runnersUp.length) : 0

  const borderColor = isConfirmed ? '#1F7A3A' : isOverridden ? '#B26A00' : '#E4DFD3'
  const borderWidth = (isConfirmed || isOverridden) ? '1.5px' : '1px'

  return (
    <div style={{
      background: '#FFFFFF',
      border: `${borderWidth} solid ${borderColor}`,
      borderRadius: 4,
      padding: '20px 22px 22px',
      transition: 'border-color .25s, box-shadow .25s',
      boxShadow: isConfirmed ? `0 0 0 3px rgba(31,122,58,0.07)` : '0 1px 2px rgba(11,18,32,0.08)',
      position: 'relative',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <div style={{ fontFamily: '"Source Serif 4", serif', fontSize: 11, fontStyle: 'italic', color: isConfirmed ? '#1F7A3A' : isOverridden ? '#B26A00' : '#5A6272' }}>
            Step {String(step).padStart(2, '0')}
          </div>
          <div style={{ fontFamily: '"Source Serif 4", serif', fontSize: 17, fontWeight: 600, color: '#0B1220', marginTop: 4, letterSpacing: '-0.015em' }}>
            {title}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {isConfirmed && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '3px 9px', borderRadius: 999, background: 'rgba(31,122,58,0.09)', color: '#1F7A3A', fontFamily: 'Inter, system-ui', fontSize: 11, fontWeight: 600 }}>
              <CheckIcon size={11} color="#1F7A3A" /> Confirmed
            </div>
          )}
          {isOverridden && (
            <div style={{ padding: '3px 9px', borderRadius: 999, background: 'rgba(178,106,0,0.09)', color: '#B26A00', fontFamily: 'Inter, system-ui', fontSize: 11, fontWeight: 600 }}>
              Overridden
            </div>
          )}
          {hasResult && !isConfirmed && !isOverridden && (
            <button onClick={() => setExpanded(e => !e)} style={{ display: 'flex', alignItems: 'center', gap: 5, background: 'transparent', border: 'none', color: '#5A6272', cursor: 'pointer', fontFamily: 'Inter, system-ui', fontSize: 12, padding: '3px 6px', borderRadius: 4 }}>
              <EditIcon size={11} /> Override
            </button>
          )}
        </div>
      </div>

      {/* Empty state */}
      {isEmpty && (
        <div>
          <div className="shimmer-bar" style={{ height: 12, width: '60%' }} />
          <div style={{ height: 8 }} />
          <div className="shimmer-bar" style={{ height: 8, width: '40%' }} />
          <div style={{ marginTop: 14, fontFamily: 'Inter, system-ui', fontSize: 12, fontStyle: 'italic', color: '#5A6272', opacity: 0.7 }}>Awaiting activity…</div>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div>
          <div className="shimmer-bar" style={{ height: 14, width: '70%' }} />
          <div style={{ height: 10 }} />
          <div className="shimmer-bar" style={{ height: 6, width: '100%' }} />
          <div style={{ height: 14 }} />
          <div className="shimmer-bar" style={{ height: 10, width: '55%' }} />
          <div style={{ height: 6 }} />
          <div className="shimmer-bar" style={{ height: 6, width: '75%' }} />
        </div>
      )}

      {/* Has result */}
      {hasResult && top && (
        <div>
          {/* Top prediction */}
          <div
            onClick={() => !isConfirmed && !isOverridden && onConfirm()}
            style={{
              padding: '12px 14px', borderRadius: 4,
              background: isConfirmed ? 'rgba(31,122,58,0.06)' : isOverridden ? 'rgba(178,106,0,0.06)' : '#E8ECF7',
              border: `1px solid ${isConfirmed ? 'rgba(31,122,58,0.19)' : isOverridden ? 'rgba(178,106,0,0.19)' : 'rgba(31,58,138,0.13)'}`,
              cursor: isConfirmed ? 'default' : 'pointer',
              transition: 'background .2s',
              marginBottom: 12,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: isConfirmed ? '#1F7A3A' : isOverridden ? '#B26A00' : '#1F3A8A', flexShrink: 0 }} />
              <span style={{ fontFamily: '"Source Serif 4", serif', fontSize: 15, fontWeight: 600, color: '#0B1220', lineHeight: 1.3, letterSpacing: '-0.005em' }}>
                {top.label}
              </span>
            </div>
            <ConfidenceBar value={top.score} top />
            {!isConfirmed && !isOverridden && (
              <div style={{ marginTop: 8, fontFamily: 'Inter, system-ui', fontSize: 11, color: '#5A6272', fontStyle: 'italic' }}>Click to confirm</div>
            )}
          </div>

          {/* Runner-ups */}
          {!isConfirmed && runnersUp.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {runnersUp.map(o => {
                const realIdx = options.findIndex(x => x.label === o.label)
                return (
                  <div key={o.label} onClick={() => onOverride(realIdx)}
                    style={{ padding: '6px 14px', cursor: 'pointer', borderRadius: 3, transition: 'background .15s' }}
                    onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.background = '#F5F2EC'}
                    onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.background = 'transparent'}
                  >
                    <div style={{ fontFamily: 'Inter, system-ui', fontSize: 13, color: '#5A6272', marginBottom: 5, lineHeight: 1.3 }}>{o.label}</div>
                    <ConfidenceBar value={o.score} />
                  </div>
                )
              })}
            </div>
          )}

          {/* +N more */}
          {!isConfirmed && moreCount > 0 && (
            <button onClick={() => setExpanded(e => !e)} style={{
              marginTop: 12, background: 'transparent', border: 'none', color: '#5A6272', cursor: 'pointer',
              fontFamily: 'Inter, system-ui', fontSize: 12, padding: '4px 0',
              display: 'flex', alignItems: 'center', gap: 4,
            }}>
              <ChevronIcon size={10} dir={expanded ? 'up' : 'down'} />
              {expanded ? 'Hide' : `+ ${moreCount} more alternative${moreCount > 1 ? 's' : ''}`}
            </button>
          )}

          {/* Expanded list */}
          {expanded && !isConfirmed && (
            <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid #E4DFD3', display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 220, overflowY: 'auto' }}>
              {options.map((o, i) => {
                if (i === selectedIndex) return null
                return (
                  <div key={o.label} onClick={() => { onOverride(i); setExpanded(false) }}
                    style={{ padding: '6px 10px', cursor: 'pointer', borderRadius: 3, display: 'flex', alignItems: 'center', gap: 10, transition: 'background .15s' }}
                    onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.background = '#F5F2EC'}
                    onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.background = 'transparent'}
                  >
                    <span style={{ flex: 1, fontFamily: 'Inter, system-ui', fontSize: 12, color: '#0B1220' }}>{o.label}</span>
                    <span style={{ fontFamily: '"JetBrains Mono", monospace', fontSize: 10, color: '#5A6272', fontVariantNumeric: 'tabular-nums' }}>{Math.round(o.score * 100)}%</span>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
