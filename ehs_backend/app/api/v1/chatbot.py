from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.dependencies import get_current_user, get_db, get_rag_chain
from app.schemas.chatbot import ChatQuery, ChatResponse, ChatTurn

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    body: ChatQuery,
    current_user: User = Depends(get_current_user),
    rag_chain=Depends(get_rag_chain),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    # Rebuild chain with request-scoped DB session
    from app.services.rag.chain import HybridRAGChain
    chain = HybridRAGChain(
        azure_client=rag_chain._client,
        langchain_llm=rag_chain._llm,
        reranker=rag_chain._reranker,
        db=db,
    )

    manual_filters: dict = {}
    if body.filters:
        if body.filters.activity_name:
            manual_filters["activity_name"] = body.filters.activity_name
        if body.filters.hazard_type:
            manual_filters["hazard_type"] = body.filters.hazard_type
        if body.filters.date_from:
            manual_filters["submitted_at__gte"] = str(body.filters.date_from)
        if body.filters.date_to:
            manual_filters["submitted_at__lte"] = str(body.filters.date_to)

    return await chain.query(
        query=body.query,
        conversation_id=body.conversation_id,
        manual_filters=manual_filters or None,
    )


@router.get("/history", response_model=list[ChatTurn])
async def get_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    rag_chain=Depends(get_rag_chain),
) -> list[ChatTurn]:
    from app.services.rag.chain import HybridRAGChain
    turns = await rag_chain.get_history(conversation_id)
    return [ChatTurn(role=t["role"], content=t["content"]) for t in turns]


@router.delete("/history", status_code=204)
async def clear_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    rag_chain=Depends(get_rag_chain),
) -> None:
    await rag_chain.clear_history(conversation_id)
