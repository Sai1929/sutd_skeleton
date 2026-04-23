// Shared UI primitives used across all three variations. Each takes a
// `palette` prop (one of TOKENS.editorial/technical/stacked) so we can
// restyle without duplicating logic.

const { useState, useEffect, useMemo, useRef, useCallback } = React;

// ─── Risk badge ──────────────────────────────────────────────
function RiskBadge({ severityLabel, variant = 'pill' }) {
  // Derive risk bucket from severity label like "High × Likely"
  const level = useMemo(() => {
    if (!severityLabel) return null;
    const s = severityLabel.toLowerCase();
    if (s.startsWith('high')) return 'high';
    if (s.startsWith('medium')) return 'medium';
    return 'low';
  }, [severityLabel]);

  if (!level) return null;
  const r = TOKENS.risk[level];

  if (variant === 'banner') {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '10px 16px', borderRadius: 8,
        background: r.bg, border: `1px solid ${r.base}22`,
        fontFamily: "'Inter', system-ui", fontSize: 13,
        color: r.base, fontWeight: 500,
      }}>
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: r.dot }} />
        <span style={{ letterSpacing: '0.08em', textTransform: 'uppercase', fontWeight: 600, fontSize: 11 }}>
          Risk Level
        </span>
        <span style={{ opacity: 0.5 }}>—</span>
        <span style={{ fontVariant: 'small-caps', letterSpacing: '0.04em' }}>{severityLabel}</span>
      </div>
    );
  }

  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 8,
      padding: '5px 10px', borderRadius: 999,
      background: r.bg, border: `1px solid ${r.base}33`,
      fontFamily: "'Inter', system-ui", fontSize: 12,
      color: r.base, fontWeight: 500,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: r.dot }} />
      <span style={{ letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: 10, fontWeight: 600 }}>
        {r.label} RISK
      </span>
      <span style={{ opacity: 0.5 }}>·</span>
      <span style={{ fontSize: 11 }}>{severityLabel}</span>
    </div>
  );
}

// ─── Confidence bar ──────────────────────────────────────────
function ConfidenceBar({ value, top = false, palette, width = '100%' }) {
  const pct = Math.round(value * 100);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, width }}>
      <div style={{
        flex: 1, height: top ? 8 : 4, borderRadius: 2,
        background: palette.rule,
        overflow: 'hidden', position: 'relative',
      }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: top ? palette.accent : palette.mute,
          opacity: top ? 1 : 0.45,
          transition: 'width 600ms cubic-bezier(.2,.7,.3,1)',
        }} />
      </div>
      <span style={{
        fontFamily: "'JetBrains Mono', ui-monospace, monospace",
        fontSize: 11, fontVariantNumeric: 'tabular-nums',
        color: top ? palette.ink : palette.mute,
        fontWeight: top ? 600 : 500,
        minWidth: 32, textAlign: 'right',
      }}>
        {pct}%
      </span>
    </div>
  );
}

// ─── NavBar ──────────────────────────────────────────────────
function NavBar({ palette, activeTab, onTab, variant = 'editorial' }) {
  const isEditorial = variant === 'editorial';
  return (
    <nav style={{
      height: 68,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 32px',
      background: palette.card,
      borderBottom: `1px solid ${palette.rule}`,
      position: 'sticky', top: 0, zIndex: 40,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{
          width: 28, height: 28, borderRadius: 6,
          background: palette.ink,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: palette.card, fontFamily: "'Source Serif 4', serif",
          fontSize: 15, fontWeight: 700, fontStyle: 'italic',
        }}>E</div>
        <div>
          <div style={{
            fontFamily: isEditorial ? "'Source Serif 4', serif" : "'Inter', system-ui",
            fontSize: 17, fontWeight: isEditorial ? 600 : 600,
            color: palette.ink, letterSpacing: isEditorial ? '-0.01em' : '-0.005em',
            lineHeight: 1,
          }}>EHS Portal</div>
          <div style={{
            fontFamily: "'Inter', system-ui", fontSize: 10,
            letterSpacing: '0.14em', textTransform: 'uppercase',
            color: palette.mute, marginTop: 3, fontWeight: 500,
          }}>Environment · Health · Safety</div>
        </div>
      </div>
      <div style={{
        display: 'flex', background: palette.bg,
        borderRadius: 8, padding: 3, border: `1px solid ${palette.rule}`,
      }}>
        {['Inspection', 'Chat'].map(tab => (
          <button key={tab} onClick={() => onTab(tab)}
            style={{
              padding: '7px 18px', border: 'none', borderRadius: 6,
              background: activeTab === tab ? palette.card : 'transparent',
              boxShadow: activeTab === tab ? `0 1px 2px ${palette.ink}14` : 'none',
              fontFamily: "'Inter', system-ui", fontSize: 13,
              fontWeight: activeTab === tab ? 600 : 500,
              color: activeTab === tab ? palette.ink : palette.mute,
              cursor: 'pointer', letterSpacing: '-0.005em',
            }}>
            {tab}
          </button>
        ))}
      </div>
    </nav>
  );
}

// ─── Step number indicator (editorial style) ────────────────
function StepNumber({ n, palette, state = 'default' }) {
  const color = state === 'confirmed' ? TOKENS.state.confirmed
              : state === 'overridden' ? TOKENS.state.overridden
              : palette.mute;
  return (
    <div style={{
      fontFamily: "'Source Serif 4', serif",
      fontSize: 11, fontStyle: 'italic',
      color, letterSpacing: '0.02em',
    }}>
      Step {String(n).padStart(2, '0')}
    </div>
  );
}

// ─── Shimmer placeholder ─────────────────────────────────────
function Shimmer({ height = 12, width = '100%', palette }) {
  return (
    <div style={{
      width, height, borderRadius: 3,
      background: `linear-gradient(90deg, ${palette.rule} 0%, ${palette.rule}60 50%, ${palette.rule} 100%)`,
      backgroundSize: '200% 100%',
      animation: 'shimmer 1.4s ease-in-out infinite',
    }} />
  );
}

// ─── State icons ─────────────────────────────────────────────
function CheckIcon({ size = 14, color = '#1F7A3A' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M3 8.5l3 3 7-7" stroke={color} strokeWidth="2"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function EditIcon({ size = 13, color }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
      <path d="M11 2.5l2.5 2.5-8 8H3v-2.5l8-8z" stroke={color} strokeWidth="1.4"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function ChevronIcon({ size = 12, color, dir = 'down' }) {
  const rot = { down: 0, up: 180, right: -90, left: 90 }[dir];
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" fill="none"
      style={{ transform: `rotate(${rot}deg)`, transition: 'transform .2s' }}>
      <path d="M2.5 4.5L6 8l3.5-3.5" stroke={color} strokeWidth="1.5"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

Object.assign(window, {
  RiskBadge, ConfidenceBar, NavBar, StepNumber, Shimmer,
  CheckIcon, EditIcon, ChevronIcon,
});
