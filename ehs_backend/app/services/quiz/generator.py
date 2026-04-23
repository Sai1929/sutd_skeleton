"""
QuizGenerator — generates EHS understanding-check questions from inspection data
using Groq/Llama. Stateless: no DB, returns question list directly.
"""
from __future__ import annotations

import json

import structlog
from groq import AsyncGroq

from app.config import settings
from app.schemas.quiz import QuestionOut

log = structlog.get_logger()

QUIZ_PROMPT = """\
You are an EHS safety assessor. A student has just submitted an inspection report. \
Your job is to generate questions that help an admin understand how well this student \
grasps the hazard, its consequences, and the controls they selected.

Inspection Report:
  Activity:          {activity}
  Hazard Identified: {hazard_type}
  Risk Level:        {severity_likelihood}
  Controls / PPE:    {moc_ppe}
  Remarks:           {remarks}

Generate exactly {n_questions} multiple-choice questions that probe the student's \
understanding of this specific inspection. Each question should test whether the \
student genuinely understands what they submitted — not just that they can repeat it.

Use these 5 understanding categories (one question each):
1. Hazard comprehension — Why is this hazard dangerous for this activity? \
   What could actually happen if it is not controlled?
2. Risk reasoning — Why was this severity/likelihood rating appropriate? \
   What factors make this risk higher or lower?
3. Control effectiveness — Why were these specific controls chosen? \
   What would happen if one of them was missing?
4. Alternative scenarios — What other hazards could arise from this activity? \
   What would change if conditions were different?
5. Regulatory awareness — Which WSH regulation or standard applies here? \
   What is the legal requirement?

Rules for every question:
- Ask questions that reveal understanding, not just memorisation
- Provide exactly 4 options labelled A, B, C, D with specific, realistic values
- The CORRECT answer should demonstrate genuine understanding of the hazard and controls
- Wrong options should be plausible misconceptions a student might have
- Explanation must state WHY the correct answer demonstrates proper understanding

Return ONLY a valid JSON object with a "questions" key (no markdown, no text outside JSON):
{{
  "questions": [
    {{
      "question_number": 1,
      "question_text": "...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "A",
      "explanation": "..."
    }}
  ]
}}
"""


class QuizGenerator:
    def __init__(self, client: AsyncGroq) -> None:
        self._client = client
        self._model = settings.GROQ_MODEL

    async def generate(
        self,
        activity: str,
        hazard_type: str,
        severity_likelihood: str,
        moc_ppe: str,
        remarks: str,
    ) -> list[QuestionOut]:
        n = settings.QUIZ_NUM_QUESTIONS

        prompt = QUIZ_PROMPT.format(
            n_questions=n,
            activity=activity,
            hazard_type=hazard_type or "Not specified",
            severity_likelihood=severity_likelihood or "Not specified",
            moc_ppe=moc_ppe or "Not specified",
            remarks=remarks or "None",
        )

        log.info("quiz.generating", activity=activity)

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            questions_data = parsed.get("questions", parsed.get("items", list(parsed.values())[0]))
        else:
            questions_data = parsed

        log.info("quiz.generated", activity=activity, num_questions=len(questions_data))

        return [
            QuestionOut(
                question_number=q["question_number"],
                question_text=q["question_text"],
                options=q.get("options"),
                correct_answer=q["correct_answer"],
                explanation=q.get("explanation"),
            )
            for q in questions_data
        ]
