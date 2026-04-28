from fastapi import APIRouter

from app.api.v1 import admin, hazard, inspect, quiz, ra

router = APIRouter(prefix="/api/v1")

# Req 1: Activity text → RA JSON (DB lookup + LLM fallback)
router.include_router(inspect.router)

# Req 2: Project description → Generate full RA → Download Word doc
router.include_router(ra.router)

# Req 3: Upload .docx → Extract + generate RA JSON (handled in inspect router)

# Req 4: RA details → Compliance quiz
router.include_router(quiz.router)

# Req 5: Text/image → Hazard analysis + risk control measures
router.include_router(hazard.router)

# Admin — token usage reporting
router.include_router(admin.router)
