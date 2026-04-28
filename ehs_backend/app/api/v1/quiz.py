from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.core.rate_limit import limiter
from app.schemas.quiz import QuizGenerateRequest, QuizGenerateResponse
from app.services.quiz.generator import QuizGenerator

router = APIRouter(prefix="/quiz")


@router.post("/generate", tags=["Req4 · RA → Compliance Quiz"], response_model=QuizGenerateResponse)
@limiter.limit(settings.RATE_LIMIT_HEAVY)
async def generate_quiz(body: QuizGenerateRequest, request: Request) -> QuizGenerateResponse:
    chat_client = getattr(request.app.state, "chat_client", None)
    if chat_client is None:
        raise HTTPException(status_code=503, detail="Groq API key not configured")

    generator = QuizGenerator(chat_client._client)
    questions = await generator.generate(
        activity=body.activity,
        hazard_type=body.hazard_type,
        severity_likelihood=body.severity_likelihood,
        moc_ppe=body.moc_ppe,
        remarks=body.remarks,
    )
    return QuizGenerateResponse(questions=questions)
