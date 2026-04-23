// Chat page — WSH Risk Advisor.
// Sidebar (about + suggestions) + conversation area + sticky input.
// Streams responses word-by-word using mocked canned answers.

const CHAT_SUGGESTIONS = [
  'What PPE is required for welding near flammables?',
  'When is a Permit-to-Work required for electrical work?',
  'Confined space entry — gas monitoring thresholds?',
  'Arc flash protection categories explained',
  'WSH Act 2006 — employer penalties overview',
  'Working at height — harness inspection checklist',
];

const CHAT_CANNED = {
  welding: `For welding near flammable materials, Singapore WSH requires:

**1. Hot-Work Permit (PTW)** — Mandatory before any ignition source is introduced. The PTW must be signed by a competent issuing authority and kept on-site.

**2. PPE (minimum):**
• Welding helmet with shade 10 or higher (shade 12–14 for TIG/MIG above 200A)
• Flame-retardant leather apron, sleeves, and gauntlets
• Respiratory protection if fume extraction is inadequate
• Safety goggles under the helmet

**3. Fire precautions:**
• Clear 11m radius of all flammable materials, or shield with flame-retardant curtains
• Class ABC fire extinguisher within 3m
• Fire watch during work AND 30 minutes after completion
• Gas cylinders upright, secured, with flashback arrestors

**4. Ventilation:** Local exhaust ventilation (LEV) for galvanized, coated, or stainless steel welding due to metal fume risk.

Source: WSH (General Provisions) Regulations, WSH Council Welding CoP.`,

  ptw: `A Permit-to-Work (PTW) is required under Singapore's WSH framework for any work classified as high-risk, including:

**Always requires PTW:**
• Hot work (welding, cutting, grinding in non-designated areas)
• Confined space entry
• Work at height above 3 metres
• Excavation beyond 1.5m depth
• Live electrical work above 50V
• Work on pressurised systems

**PTW must specify:**
— Scope of work, location, duration
— Specific hazards identified
— Control measures and PPE required
— Competent persons authorised to perform the work
— Emergency procedures

**Validity:** A PTW is typically valid for one shift (max 12 hours). It must be re-issued or extended by the issuing authority for longer work.

The PTW holder bears on-site responsibility; the issuing authority bears legal accountability for validity.`,

  confined: `**Confined space entry — atmospheric thresholds (Singapore WSH):**

Before entry, test in this order: oxygen → flammability → toxicity.

| Parameter | Safe threshold |
|-----------|----------------|
| Oxygen (O₂) | 19.5 – 23.5% |
| Lower Explosive Limit (LEL) | < 10% |
| Carbon Monoxide (CO) | < 25 ppm |
| Hydrogen Sulphide (H₂S) | < 10 ppm |

**Re-test frequency:** Every 2 hours during entry, or continuous monitoring preferred.

**Additional controls:**
• Ventilate with ≥ 5 air-volume changes before entry
• Supplied-air respirator if atmosphere cannot be made safe
• Rescue harness + tripod/winch for retrieval
• Standby attendant outside the space at all times
• Two-way communication every 15 minutes
• Rescue plan rehearsed before entry begins

Under no circumstances enter for rescue without supplied air — 60% of confined-space fatalities are would-be rescuers.`,

  default: `I'm the WSH Risk Advisor — I can help with workplace safety questions related to Singapore's regulatory framework, including the WSH Act, WSH Council Codes of Practice, hazard identification, PPE selection, permit requirements, and control measures.

Try asking about:
• Specific activities (welding, electrical work, confined spaces, working at height)
• PPE requirements for a given hazard
• Permit-to-Work triggers
• Regulatory references (WSH Act, SS 508, SS 668)

What would you like to know?`,
};

function matchCanned(q) {
  const s = q.toLowerCase();
  if (s.includes('weld')) return CHAT_CANNED.welding;
  if (s.includes('ptw') || s.includes('permit')) return CHAT_CANNED.ptw;
  if (s.includes('confined')) return CHAT_CANNED.confined;
  if (s.includes('arc flash') || s.includes('electrical')) return `**Arc flash protection (NFPA 70E, adopted under WSH):**

Arc-rated PPE is categorised by incident energy tolerance (cal/cm²):

• **Category 1** — 4 cal/cm² — Long-sleeve AR shirt + AR pants OR coverall, AR face shield, hard hat, safety glasses, hearing protection, leather work gloves
• **Category 2** — 8 cal/cm² — Cat 1 requirements + AR balaclava or flash hood
• **Category 3** — 25 cal/cm² — AR flash suit (jacket, pants, hood), AR gloves
• **Category 4** — 40 cal/cm² — Multi-layer AR flash suit, hood with internal fan

**Approach boundaries (50–300V phase-to-phase):**
— Limited approach: 1.07m (unqualified personnel boundary)
— Restricted approach: Avoid contact
— Prohibited approach: Treat as direct contact

An arc flash risk assessment must be completed and labels affixed to all equipment where arc flash hazards exist.`;
  if (s.includes('height') || s.includes('harness')) return `**Work at height — harness inspection daily checklist:**

Before each use:

1. **Webbing** — Check for cuts, fraying, burns, chemical damage, abrasion
2. **Stitching** — All load-bearing stitches intact; no loose or missing threads
3. **Buckles and D-rings** — No deformation, cracks, corrosion; smooth operation
4. **Lanyard connectors** — Snap hooks close automatically and lock; no bent gates
5. **Shock absorber** — Pack intact, not deployed or torn open
6. **Labels** — Manufacturer, certification, date of manufacture legible

**Retire the harness if:** any damage found, after a fall arrest event (even if no visible damage), or after 5 years from manufacture (manufacturer-dependent).

Full inspection by competent person: every 6 months minimum, recorded in log.

Reference: MOM Work-at-Height Safety Guide, SS 528.`;
  if (s.includes('penalt') || s.includes('act')) return `**WSH Act 2006 — employer penalties:**

The Workplace Safety and Health Act empowers MOM to issue:

**1. Composition fines** — Up to S$5,000 per offence for minor breaches (settled without prosecution).

**2. Prosecution under Section 12:** General duty of employers
— Corporate: fine up to **S$500,000** per breach (first offence)
— Corporate repeat offender: up to **S$1,000,000**
— Individual directors/officers: fine up to **S$200,000** and/or **up to 2 years imprisonment**

**3. Stop-Work Orders (SWO)** — MOM can halt operations at a site pending safety rectification. Non-compliance with SWO is a separate offence.

**4. Demerit points / licence conditions** for factories under the Factory Act framework.

Directors have personal liability under Section 48 where the offence was committed with their consent or neglect.`;
  return CHAT_CANNED.default;
}

function ChatPage({ palette, variant }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  const isSerif = variant === 'editorial' || variant === 'stacked';

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = (text) => {
    if (!text.trim() || isStreaming) return;
    const userMsg = { role: 'user', content: text, ts: Date.now() };
    setMessages(m => [...m, userMsg]);
    setInput('');
    setIsStreaming(true);

    // Typing delay, then stream words
    setTimeout(() => {
      const full = matchCanned(text);
      const words = full.split(/(\s+)/);
      let i = 0;
      setMessages(m => [...m, { role: 'assistant', content: '', ts: Date.now() }]);
      const tick = () => {
        i += 1;
        setMessages(m => {
          const last = m[m.length - 1];
          const next = [...m.slice(0, -1), {
            ...last, content: words.slice(0, i).join(''),
          }];
          return next;
        });
        if (i < words.length) {
          setTimeout(tick, 18 + Math.random() * 20);
        } else {
          setIsStreaming(false);
        }
      };
      tick();
    }, 600);
  };

  const clearConvo = () => setMessages([]);

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '300px 1fr',
      height: 'calc(100% - 68px)',
      background: palette.bg,
    }}>
      {/* Sidebar */}
      <aside style={{
        background: palette.card,
        borderRight: `1px solid ${palette.rule}`,
        padding: '32px 24px',
        display: 'flex', flexDirection: 'column',
        overflow: 'auto',
      }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10,
          marginBottom: 14,
        }}>
          <div style={{
            width: 32, height: 32, borderRadius: 6,
            background: palette.accentSoft,
            color: palette.accent,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: "'Source Serif 4', serif", fontWeight: 700,
            fontSize: 16, fontStyle: 'italic',
          }}>A</div>
          <div>
            <div style={{
              fontFamily: isSerif ? "'Source Serif 4', serif" : "'Inter', system-ui",
              fontSize: 15, fontWeight: 600,
              color: palette.ink, letterSpacing: '-0.01em',
            }}>WSH Risk Advisor</div>
          </div>
        </div>
        <p style={{
          fontFamily: "'Inter', system-ui", fontSize: 13,
          color: palette.mute, lineHeight: 1.55, margin: 0,
          marginBottom: 24,
        }}>
          Workplace safety guidance grounded in Singapore WSH Act and Council
          Codes of Practice. Ask about hazards, PPE, permits, or regulatory
          references.
        </p>

        <div style={{
          fontFamily: "'Inter', system-ui", fontSize: 10,
          letterSpacing: '0.14em', textTransform: 'uppercase',
          color: palette.mute, fontWeight: 500, marginBottom: 10,
        }}>
          Try Asking
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {CHAT_SUGGESTIONS.map(s => (
            <button key={s} onClick={() => sendMessage(s)}
              disabled={isStreaming}
              style={{
                textAlign: 'left',
                padding: '9px 12px',
                fontFamily: "'Inter', system-ui", fontSize: 12,
                color: palette.ink, background: palette.bg,
                border: `1px solid ${palette.rule}`,
                borderRadius: 4, cursor: isStreaming ? 'not-allowed' : 'pointer',
                lineHeight: 1.4,
                transition: 'background .15s, border-color .15s',
              }}
              onMouseEnter={e => {
                if (!isStreaming) {
                  e.currentTarget.style.background = palette.accentSoft;
                  e.currentTarget.style.borderColor = palette.accent + '30';
                }
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = palette.bg;
                e.currentTarget.style.borderColor = palette.rule;
              }}>
              {s}
            </button>
          ))}
        </div>

        <div style={{ flex: 1 }} />

        {messages.length > 0 && (
          <button onClick={clearConvo}
            style={{
              marginTop: 24,
              padding: '9px 12px',
              fontFamily: "'Inter', system-ui", fontSize: 12,
              color: palette.mute, background: 'transparent',
              border: `1px solid ${palette.rule}`,
              borderRadius: 4, cursor: 'pointer',
            }}>
            Clear Conversation
          </button>
        )}

        <div style={{
          marginTop: 24, paddingTop: 16,
          borderTop: `1px solid ${palette.rule}`,
          fontFamily: "'JetBrains Mono', monospace", fontSize: 10,
          color: palette.mute, letterSpacing: '0.06em', lineHeight: 1.6,
        }}>
          Model · llama-4-scout<br />
          Context · WSH Act, SS 508, SS 668
        </div>
      </aside>

      {/* Conversation + input */}
      <div style={{
        display: 'flex', flexDirection: 'column',
        minWidth: 0, overflow: 'hidden',
      }}>
        <div ref={scrollRef} style={{
          flex: 1, overflowY: 'auto',
          padding: '32px 48px 16px',
        }}>
          {messages.length === 0 ? (
            <div style={{
              height: '100%', display: 'flex',
              flexDirection: 'column', alignItems: 'center',
              justifyContent: 'center', textAlign: 'center',
              maxWidth: 460, margin: '0 auto',
            }}>
              <div style={{
                width: 52, height: 52, borderRadius: 10,
                background: palette.accentSoft,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                marginBottom: 22,
              }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L4 6v6c0 5 3.4 9.3 8 10 4.6-.7 8-5 8-10V6l-8-4z"
                    stroke={palette.accent} strokeWidth="1.6"
                    strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <h2 style={{
                fontFamily: isSerif ? "'Source Serif 4', serif" : "'Inter', system-ui",
                fontSize: 26, fontWeight: isSerif ? 500 : 600,
                color: palette.ink, margin: 0,
                letterSpacing: '-0.015em',
              }}>
                How can I help with workplace safety today?
              </h2>
              <p style={{
                fontFamily: "'Inter', system-ui", fontSize: 14,
                color: palette.mute, lineHeight: 1.55,
                marginTop: 12, marginBottom: 0,
              }}>
                Ask about hazards, PPE selection, permits, or specific clauses in
                the Singapore WSH Act.
              </p>
            </div>
          ) : (
            <div style={{
              display: 'flex', flexDirection: 'column', gap: 18,
              maxWidth: 720, margin: '0 auto',
            }}>
              {messages.map((m, i) => (
                <MessageBubble key={i} msg={m} palette={palette} variant={variant} />
              ))}
              {isStreaming && messages[messages.length - 1]?.role === 'user' && (
                <TypingIndicator palette={palette} />
              )}
            </div>
          )}
        </div>

        {/* Input bar */}
        <div style={{
          borderTop: `1px solid ${palette.rule}`,
          background: palette.card,
          padding: '16px 48px 24px',
        }}>
          <div style={{
            maxWidth: 720, margin: '0 auto',
            display: 'flex', alignItems: 'flex-end', gap: 10,
          }}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage(input);
                }
              }}
              placeholder="Ask about workplace safety, hazards, or WSH regulations…"
              rows={1}
              disabled={isStreaming}
              style={{
                flex: 1, resize: 'none',
                padding: '12px 14px',
                fontFamily: "'Inter', system-ui", fontSize: 14,
                color: palette.ink, background: palette.bg,
                border: `1px solid ${palette.rule}`,
                borderRadius: 6, outline: 'none',
                lineHeight: 1.45, minHeight: 22, maxHeight: 120,
              }}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={!input.trim() || isStreaming}
              style={{
                width: 44, height: 44, borderRadius: 6,
                background: input.trim() && !isStreaming ? palette.accent : palette.rule,
                color: palette.card,
                border: 'none',
                cursor: input.trim() && !isStreaming ? 'pointer' : 'not-allowed',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M2 8l12-5-5 12-2-5-5-2z" stroke="currentColor"
                  strokeWidth="1.6" strokeLinejoin="round" fill="currentColor" />
              </svg>
            </button>
          </div>
          <div style={{
            maxWidth: 720, margin: '8px auto 0',
            fontFamily: "'Inter', system-ui", fontSize: 11,
            color: palette.mute,
          }}>
            Enter to send · Shift+Enter for a new line · Responses may require verification against source regulations.
          </div>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ msg, palette, variant }) {
  const isUser = msg.role === 'user';
  return (
    <div style={{
      display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start',
      gap: 10,
    }}>
      {!isUser && (
        <div style={{
          width: 28, height: 28, borderRadius: 6,
          background: palette.accentSoft,
          color: palette.accent,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: "'Source Serif 4', serif", fontWeight: 700,
          fontSize: 13, fontStyle: 'italic', flexShrink: 0, marginTop: 2,
        }}>A</div>
      )}
      <div style={{
        maxWidth: '82%',
        padding: '12px 16px',
        background: isUser ? palette.ink : palette.card,
        color: isUser ? palette.card : palette.ink,
        border: isUser ? 'none' : `1px solid ${palette.rule}`,
        borderRadius: isUser ? '10px 10px 2px 10px' : '10px 10px 10px 2px',
        fontFamily: "'Inter', system-ui", fontSize: 14,
        lineHeight: 1.55,
        whiteSpace: 'pre-wrap',
      }}>
        {formatMarkdown(msg.content)}
      </div>
    </div>
  );
}

function formatMarkdown(text) {
  // Super-light markdown: **bold**, leading • bullets, | tables preserved.
  if (!text) return null;
  const lines = text.split('\n');
  return lines.map((line, i) => {
    const parts = line.split(/(\*\*[^*]+\*\*)/g);
    const content = parts.map((p, j) => {
      if (p.startsWith('**') && p.endsWith('**')) {
        return <strong key={j}>{p.slice(2, -2)}</strong>;
      }
      return <React.Fragment key={j}>{p}</React.Fragment>;
    });
    return <div key={i} style={{ minHeight: '1.2em' }}>{content}</div>;
  });
}

function TypingIndicator({ palette }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{
        width: 28, height: 28, borderRadius: 6,
        background: palette.accentSoft,
        color: palette.accent,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontFamily: "'Source Serif 4', serif", fontWeight: 700,
        fontSize: 13, fontStyle: 'italic',
      }}>A</div>
      <div style={{
        padding: '12px 16px',
        background: palette.card,
        border: `1px solid ${palette.rule}`,
        borderRadius: '10px 10px 10px 2px',
        display: 'flex', gap: 4,
      }}>
        {[0, 1, 2].map(i => (
          <span key={i} style={{
            width: 6, height: 6, borderRadius: '50%',
            background: palette.mute,
            animation: `dotBounce 1.2s infinite ${i * 0.16}s`,
          }} />
        ))}
      </div>
    </div>
  );
}

window.ChatPage = ChatPage;
