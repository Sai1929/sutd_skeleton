"""
QuizGenerator — generates EHS quiz questions from inspection summary using Azure GPT-4o mini.
"""
from __future__ import annotations

import json
import math

import structlog
from openai import AsyncAzureOpenAI

from app.config import settings
from app.db.models.inspection import InspectionSubmission
from app.db.models.quiz import Quiz, QuizQuestion

log = structlog.get_logger()

QUIZ_PROMPT = """\
You are an EHS (Environment, Health, Safety) educator. Generate exactly {n_questions} quiz \
questions based on the following inspection record.

Inspection Summary:
  Activity:          {activity_name}
  Hazard Type:       {hazard_type}
  Risk Assessment:   {severity_likelihood}
  Control Measures:  {moc_ppe}
  Remarks:           {remarks}

Requirements:
- Generate {n_mcq} multiple-choice questions (MCQ) and {n_sa} short-answer questions.
- MCQ: provide exactly 4 options labelled "A", "B", "C", "D". One is clearly correct.
- Short-answer: require a 1-3 sentence explanation.
- Questions must test WHY the identified hazard/controls matter — not just recall.
- Provide a 1-2 sentence explanation per correct answer.

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
    }},
    {{
      "question_number": 2,
      "question_type": "short_answer",
      "question_text": "...",
      "options": null,
      "correct_answer": "...",
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
        n_mcq = math.ceil(n * settings.QUIZ_MCQ_RATIO)
        n_sa = n - n_mcq

        prompt = QUIZ_PROMPT.format(
            n_questions=n,
            n_mcq=n_mcq,
            n_sa=n_sa,
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
