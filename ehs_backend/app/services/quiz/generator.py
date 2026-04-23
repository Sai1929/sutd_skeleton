"""
QuizGenerator — generates EHS quiz questions from inspection summary using Azure GPT-4o mini.
All questions are multiple-choice (MCQ).
"""
from __future__ import annotations

import json

import structlog
from openai import AsyncAzureOpenAI

from app.config import settings
from app.db.models.inspection import InspectionSubmission
from app.db.models.quiz import Quiz, QuizQuestion

log = structlog.get_logger()

QUIZ_PROMPT = """\
You are an EHS safety officer generating a pre-work physical readiness checklist for the activity below.
The worker has already submitted an inspection report with recommendations. Before they start the actual \
work, they must confirm they are physically prepared — correct tools present, PPE on, site conditions \
safe, permits in place.

Inspection Report:
  Activity:          {activity_name}
  Hazard Identified: {hazard_type}
  Risk Level:        {severity_likelihood}
  Controls / PPE:    {moc_ppe}
  Remarks:           {remarks}

Generate exactly {n_questions} multiple-choice readiness-check questions for the activity "{activity_name}".
Each question must confirm a specific physical preparation the worker must have done or have in place \
RIGHT NOW before starting work — based directly on the hazard, risk level, and controls above.

Use these 5 readiness categories (one question each):
1. Equipment / tool check — Are the specific tools required for this activity present and in working order?
   (e.g. "Is an insulated screwdriver and voltage tester available?", "Is the ladder rated for the working height?")
2. PPE check — Is the required PPE physically being worn right now?
   (e.g. "Are rubber-insulated gloves and safety shoes on?", "Is a full-face shield worn and undamaged?")
3. Site / environment check — Is the work area in a safe condition to begin?
   (e.g. "Has the circuit been isolated and locked out?", "Is the area barricaded and signage posted?")
4. Personnel / supervision check — Are the right people present?
   (e.g. "Is a second person present as a spotter?", "Has the supervisor signed off?")
5. Permit / sign-off check — Is the required permit or authorisation obtained?
   (e.g. "Has a Permit-to-Work been issued?", "Has a toolbox talk been conducted?")

Rules for every question:
- Ask in present tense: "Is... ?", "Has... ?", "Are... ?" — NOT past tense or theoretical
- Provide exactly 4 options labelled A, B, C, D with specific, realistic values (not vague "yes/no")
- The CORRECT answer must match what the submitted controls and remarks require
- Other 3 options must be plausible but wrong (partial measures, wrong tool, missing step)
- Explanation must be 1 sentence stating WHY this specific check matters for the hazard above

Return ONLY a valid JSON object with a "questions" key (no markdown, no text outside JSON):
{{
  "questions": [
    {{
      "question_number": 1,
      "question_type": "mcq",
      "question_text": "...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "A",
      "explanation": "..."
    }}
  ]
}}
"""


class QuizGenerator:
    def __init__(self, client: AsyncAzureOpenAI) -> None:
        self._client = client

    async def generate(
        self,
        submission: InspectionSubmission,
        session_id,
        db,
    ) -> Quiz:
        n = settings.QUIZ_NUM_QUESTIONS

        prompt = QUIZ_PROMPT.format(
            n_questions=n,
            activity_name=submission.activity_name,
            hazard_type=submission.hazard_type or "Not specified",
            severity_likelihood=submission.severity_likelihood or "Not specified",
            moc_ppe=submission.moc_ppe or "Not specified",
            remarks=submission.remarks or "None",
        )

        log.info("quiz.generating", session_id=str(session_id))

        response = await self._client.chat.completions.create(
            model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"},
            timeout=60,
        )

        raw = response.choices[0].message.content
        log.info("quiz.raw_response", session_id=str(session_id), length=len(raw))
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            questions_data = parsed.get("questions", parsed.get("items", list(parsed.values())[0]))
        else:
            questions_data = parsed

        quiz = Quiz(
            session_id=session_id,
            prompt_used=prompt,
            total_questions=len(questions_data),
            status="pending",
        )
        db.add(quiz)
        await db.flush()

        for q in questions_data:
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_number=q["question_number"],
                question_type=q["question_type"],
                question_text=q["question_text"],
                options=q.get("options"),
                correct_answer=q["correct_answer"],
                explanation=q.get("explanation"),
            )
            db.add(question)

        await db.commit()
        log.info("quiz.generated", quiz_id=str(quiz.id), num_questions=len(questions_data))
        return quiz
