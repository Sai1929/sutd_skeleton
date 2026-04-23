// App shell — composes a variation's inspection page + chat + quiz overlay.
// Owns tab state and quiz-open state.

function EHSApp({ variant }) {
  const palette = TOKENS[variant];
  const [tab, setTab] = useState('Inspection');
  const [quizOpen, setQuizOpen] = useState(false);
  const [submittedActivity, setSubmittedActivity] = useState('');

  const handleSubmit = (activity) => {
    setSubmittedActivity(activity);
    setQuizOpen(true);
  };

  const InspectionCmp =
    variant === 'editorial' ? InspectionEditorial
    : variant === 'technical' ? InspectionTechnical
    : InspectionStacked;

  return (
    <div style={{
      height: '100%', width: '100%',
      background: palette.bg,
      overflow: 'auto',
      position: 'relative',
    }}>
      <NavBar palette={palette} activeTab={tab} onTab={setTab} variant={variant} />
      {tab === 'Inspection' && <InspectionCmp onSubmit={handleSubmit} />}
      {tab === 'Chat' && <ChatPage palette={palette} variant={variant} />}
      <QuizOverlay
        open={quizOpen}
        onClose={() => setQuizOpen(false)}
        activity={submittedActivity}
        palette={palette}
        variant={variant}
      />
    </div>
  );
}

window.EHSApp = EHSApp;
