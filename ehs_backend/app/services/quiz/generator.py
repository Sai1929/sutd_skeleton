"""
QuizGenerator — generates mixed EHS questions (MCQ + descriptive + scenario)
from inspection data using Groq/Llama. Stateless: no DB, returns question list directly.
"""
from __future__ import annotations

import json

import structlog
from groq import AsyncGroq

from app.config import settings
from app.schemas.quiz import QuestionOut

log = structlog.get_logger()

QUIZ_PROMPT = """\
You are an EHS safety assessor. A student has just submitted an inspection report.
Generate exactly {n_questions} questions that test genuine understanding of the hazard, \
its consequences, and the controls selected — not just memorisation.

Inspection Report:
  Activity:          {activity}
  Hazard Identified: {hazard_type}
  Risk Level:        {severity_likelihood}
  Controls / PPE:    {moc_ppe}
  Remarks:           {remarks}

Generate questions using this EXACT distribution:
- Questions 1–2: MCQ (multiple-choice, 4 options A/B/C/D)
- Questions 3–4: Descriptive (open-ended, written answer required)
- Question 5:    Scenario-based (a situation is described, student explains what to do)

Categories to cover (one per question):
1. Hazard comprehension — Why is this hazard dangerous? What happens if uncontrolled? (MCQ)
2. Regulatory awareness — Which WSH regulation/standard applies? What is the legal requirement? (MCQ)
3. Control effectiveness — Why were these specific controls chosen? What if one was missing? (Descriptive)
4. Risk reasoning — Why was this severity/likelihood rating appropriate? (Descriptive)
5. Scenario — Describe a realistic incident scenario related to this activity. Ask the student what \
   immediate actions to take, who to notify, and which WSH regulation governs the response. (Scenario)

Rules:
MCQ:
  - Exactly 4 options labelled "A. ...", "B. ...", "C. ...", "D. ..."
  - correct_answer: single letter "A", "B", "C", or "D"
  - Wrong options must be plausible misconceptions

Descriptive:
  - options: null
  - correct_answer: a 2–4 sentence model answer demonstrating genuine understanding
  - explanation: key points an assessor should look for

Scenario:
  - options: null
  - question_text: set the scene clearly (2–3 sentences) then ask what the student should do
  - correct_answer: model response covering immediate action, escalation, and relevant WSH regulation
  - explanation: key points an assessor should look for

Return ONLY valid JSON, no markdown:
{{
  "questions": [
    {{
      "question_number": 1,
      "question_type": "mcq",
      "question_text": "...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": "A",
      "explanation": "..."
    }},
    {{
      "question_number": 3,
      "question_type": "descriptive",
      "question_text": "...",
      "options": null,
      "correct_answer": "Model answer text here...",
      "explanation": "Key points: ..."
    }},
    {{
      "question_number": 5,
      "question_type": "scenario",
      "question_text": "Scenario: ... What should the worker do?",
      "options": null,
      "correct_answer": "Model response: ...",
      "explanation": "Key points: ..."
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
                question_type=q.get("question_type", "mcq"),
                question_text=q["question_text"],
                options=q.get("options"),
                correct_answer=q["correct_answer"],
                explanation=q.get("explanation"),
            )
            for q in questions_data
        ]
