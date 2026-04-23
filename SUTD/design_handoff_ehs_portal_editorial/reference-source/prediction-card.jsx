// PredictionCard — shared logic, three visual variants.
// Owns local UI state (expanded dropdown). State machine:
//   empty -> loading -> predicted -> confirmed | overridden
// "predicted": top prediction previewed, user hasn't touched yet
// "confirmed": user clicked top prediction, card is locked, green accent
// "overridden": user picked a non-top option, amber accent, downstream re-predicts

function PredictionCard({
  step, title, options, state, selectedIndex,
  onConfirm, onOverride, palette, variant = 'editorial',
}) {
  const [expanded, setExpanded] = useState(false);

  // State derivatives
  const isEmpty = state === 'empty';
  const isLoading = state === 'loading';
  const isConfirmed = state === 'confirmed';
  const isOverridden = state === 'overridden';
  const hasResult = state === 'predicted' || isConfirmed || isOverridden;

  const topIdx = selectedIndex ?? 0;
  const top = hasResult ? options[topIdx] : null;
  const runnersUp = hasResult
    ? options.filter((_, i) => i !== topIdx).slice(0, 2)
    : [];
  const moreCount = hasResult ? Math.max(0, options.length - 1 - runnersUp.length) : 0;

  // Border/accent per state
  const accent = isConfirmed ? TOKENS.state.confirmed
               : isOverridden ? TOKENS.state.overridden
               : palette.rule;
  const borderWidth = (isConfirmed || isOverridden) ? 1.5 : 1;

  // Variant-specific shell styling
  const shellStyle = {
    editorial: {
      background: palette.card,
      border: `${borderWidth}px solid ${accent}`,
      borderRadius: 4,
      padding: '20px 22px 22px',
      transition: 'border-color .25s, box-shadow .25s',
      boxShadow: isConfirmed
        ? `0 0 0 3px ${TOKENS.state.confirmed}12`
        : `0 1px 2px ${palette.ink}08`,
      position: 'relative',
    },
    technical: {
      background: palette.card,
      border: `${borderWidth}px solid ${accent}`,
      borderRadius: 6,
      padding: '18px 20px 20px',
      transition: 'border-color .25s, box-shadow .25s',
      boxShadow: isConfirmed
        ? `0 0 0 3px ${TOKENS.state.confirmed}12`
        : `0 1px 2px ${palette.ink}06`,
      position: 'relative',
    },
    stacked: {
      background: palette.card,
      border: `${borderWidth}px solid ${accent}`,
      borderRadius: 2,
      padding: '22px 28px',
      transition: 'border-color .25s',
      position: 'relative',
    },
  }[variant];

  return (
    <div style={shellStyle}>
      {/* Header row */}
      <div style={{
        display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
        marginBottom: variant === 'stacked' ? 14 : 16,
      }}>
        <div>
          {variant === 'editorial' && (
            <StepNumber n={step} palette={palette}
              state={isConfirmed ? 'confirmed' : isOverridden ? 'overridden' : 'default'} />
          )}
          {variant === 'technical' && (
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10, color: palette.mute, letterSpacing: '0.12em',
              fontWeight: 500,
            }}>
              <span style={{
                display: 'inline-block', width: 18, height: 18, borderRadius: 3,
                background: isConfirmed ? TOKENS.state.confirmed + '18' : palette.bg,
                color: isConfirmed ? TOKENS.state.confirmed : palette.mute,
                textAlign: 'center', lineHeight: '18px',
                fontSize: 10, fontWeight: 600,
              }}>{String(step).padStart(2, '0')}</span>
              STEP
            </div>
          )}
          {variant === 'stacked' && (
            <div style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 10, color: palette.mute,
              letterSpacing: '0.14em', fontWeight: 500,
            }}>
              {String(step).padStart(2, '0')} / 04
            </div>
          )}
          <div style={{
            fontFamily: variant === 'editorial' ? "'Source Serif 4', serif" : "'Inter', system-ui",
            fontSize: variant === 'stacked' ? 20 : 17,
            fontWeight: variant === 'editorial' ? 600 : 600,
            color: palette.ink, marginTop: 4,
            letterSpacing: variant === 'editorial' ? '-0.015em' : '-0.01em',
          }}>
            {title}
          </div>
        </div>

        {/* Status badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {isConfirmed && (
            <div style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '3px 9px', borderRadius: 999,
              background: TOKENS.state.confirmed + '18',
              color: TOKENS.state.confirmed,
              fontFamily: "'Inter', system-ui", fontSize: 11,
              fontWeight: 600, letterSpacing: '0.02em',
            }}>
              <CheckIcon size={11} color={TOKENS.state.confirmed} />
              Confirmed
            </div>
          )}
          {isOverridden && (
            <div style={{
              padding: '3px 9px', borderRadius: 999,
              background: TOKENS.state.overridden + '18',
              color: TOKENS.state.overridden,
              fontFamily: "'Inter', system-ui", fontSize: 11,
              fontWeight: 600, letterSpacing: '0.02em',
            }}>
              Overridden
            </div>
          )}
          {hasResult && !isConfirmed && (
            <button onClick={() => setExpanded(e => !e)}
              style={{
                display: 'flex', alignItems: 'center', gap: 5,
                background: 'transparent', border: 'none',
                color: palette.mute, cursor: 'pointer',
                fontFamily: "'Inter', system-ui", fontSize: 12,
                padding: '3px 6px', borderRadius: 4,
              }}>
              <EditIcon size={11} color={palette.mute} />
              Override
            </button>
          )}
        </div>
      </div>

      {/* Body */}
      {isEmpty && (
        <div style={{
          fontFamily: "'Inter', system-ui", fontSize: 13,
          color: palette.mute, lineHeight: 1.5,
          padding: '12px 0',
        }}>
          <Shimmer height={12} width="60%" palette={palette} />
          <div style={{ height: 8 }} />
          <Shimmer height={8} width="40%" palette={palette} />
          <div style={{
            marginTop: 14, fontSize: 12, fontStyle: 'italic',
            color: palette.mute, opacity: 0.7,
          }}>
            Awaiting activity…
          </div>
        </div>
      )}

      {isLoading && (
        <div>
          <Shimmer height={14} width="70%" palette={palette} />
          <div style={{ height: 10 }} />
          <Shimmer height={6} width="100%" palette={palette} />
          <div style={{ height: 14 }} />
          <Shimmer height={10} width="55%" palette={palette} />
          <div style={{ height: 6 }} />
          <Shimmer height={6} width="75%" palette={palette} />
        </div>
      )}

      {hasResult && (
        <div>
          {/* Top prediction — clickable to confirm */}
          <div
            onClick={() => !isConfirmed && onConfirm(topIdx)}
            style={{
              padding: '12px 14px',
              borderRadius: 4,
              background: isConfirmed
                ? TOKENS.state.confirmed + '10'
                : isOverridden
                  ? TOKENS.state.overridden + '10'
                  : palette.accentSoft,
              cursor: isConfirmed ? 'default' : 'pointer',
              transition: 'background .2s',
              marginBottom: 12,
              border: `1px solid ${
                isConfirmed ? TOKENS.state.confirmed + '30'
                : isOverridden ? TOKENS.state.overridden + '30'
                : palette.accent + '20'
              }`,
            }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8,
              marginBottom: 8,
            }}>
              <span style={{
                width: 7, height: 7, borderRadius: '50%',
                background: isConfirmed ? TOKENS.state.confirmed
                          : isOverridden ? TOKENS.state.overridden
                          : palette.accent,
                flexShrink: 0,
              }} />
              <span style={{
                fontFamily: variant === 'editorial' ? "'Source Serif 4', serif" : "'Inter', system-ui",
                fontSize: 15, fontWeight: variant === 'editorial' ? 600 : 600,
                color: palette.ink, lineHeight: 1.3,
                letterSpacing: '-0.005em',
              }}>
                {top.label}
              </span>
            </div>
            <ConfidenceBar value={top.score} top palette={palette} />
            {!isConfirmed && (
              <div style={{
                marginTop: 8, fontFamily: "'Inter', system-ui",
                fontSize: 11, color: palette.mute, fontStyle: 'italic',
              }}>
                Click to confirm
              </div>
            )}
          </div>

          {/* Runner-ups */}
          {!isConfirmed && runnersUp.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {runnersUp.map((o, i) => {
                const realIdx = options.findIndex(x => x.label === o.label);
                return (
                  <div key={o.label}
                    onClick={() => onOverride(realIdx)}
                    style={{
                      padding: '6px 14px',
                      cursor: 'pointer',
                      borderRadius: 3,
                      transition: 'background .15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = palette.bg}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <div style={{
                      fontFamily: "'Inter', system-ui",
                      fontSize: 13, color: palette.mute,
                      marginBottom: 5, lineHeight: 1.3,
                    }}>
                      {o.label}
                    </div>
                    <ConfidenceBar value={o.score} palette={palette} />
                  </div>
                );
              })}
            </div>
          )}

          {/* +N more expandable */}
          {!isConfirmed && moreCount > 0 && (
            <button onClick={() => setExpanded(e => !e)}
              style={{
                marginTop: 12,
                background: 'transparent', border: 'none',
                color: palette.mute, cursor: 'pointer',
                fontFamily: "'Inter', system-ui", fontSize: 12,
                padding: '4px 0', display: 'flex', alignItems: 'center', gap: 4,
              }}>
              <ChevronIcon size={10} color={palette.mute} dir={expanded ? 'up' : 'down'} />
              {expanded ? 'Hide' : `+ ${moreCount} more alternative${moreCount > 1 ? 's' : ''}`}
            </button>
          )}

          {/* Expanded full list */}
          {expanded && !isConfirmed && (
            <div style={{
              marginTop: 10, paddingTop: 10,
              borderTop: `1px solid ${palette.rule}`,
              display: 'flex', flexDirection: 'column', gap: 6,
              maxHeight: 220, overflowY: 'auto',
            }}>
              {options.map((o, i) => {
                if (i === topIdx) return null;
                const picked = i === selectedIndex;
                return (
                  <div key={o.label}
                    onClick={() => { onOverride(i); setExpanded(false); }}
                    style={{
                      padding: '6px 10px',
                      cursor: 'pointer',
                      borderRadius: 3,
                      display: 'flex', alignItems: 'center', gap: 10,
                      background: picked ? palette.accentSoft : 'transparent',
                      transition: 'background .15s',
                    }}
                    onMouseEnter={e => { if (!picked) e.currentTarget.style.background = palette.bg; }}
                    onMouseLeave={e => { if (!picked) e.currentTarget.style.background = 'transparent'; }}
                  >
                    <span style={{
                      flex: 1, fontFamily: "'Inter', system-ui",
                      fontSize: 12, color: palette.ink,
                    }}>{o.label}</span>
                    <span style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 10, color: palette.mute,
                      fontVariantNumeric: 'tabular-nums',
                    }}>{Math.round(o.score * 100)}%</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

window.PredictionCard = PredictionCard;
