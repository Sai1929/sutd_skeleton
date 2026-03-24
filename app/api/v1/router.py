from fastapi import APIRouter

from app.api.v1 import auth, chatbot, quiz, sessions, submissions

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(sessions.router)
router.include_router(submissions.router)
router.include_router(quiz.router)
router.include_router(chatbot.router)
