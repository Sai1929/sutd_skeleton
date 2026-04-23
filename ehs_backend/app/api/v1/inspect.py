"""
Stateless inspection recommendation endpoint.
Given an activity and any confirmed selections, predicts remaining fields.
Uses the trained DistilBERT model (or frequency fallback).
"""
from fastapi import APIRouter, Depends, Request

from app.schemas.inspect import RankedOption, RecommendRequest, RecommendResponse
from app.ml.distilbert.model import STEP_NAMES

router = APIRouter(prefix="/inspect", tags=["inspect"])


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(
    body: RecommendRequest,
    request: Request,
) -> RecommendResponse:
    predictor = request.app.state.predictor

    # Determine which steps still need prediction:
    # everything AFTER the last provided selection
    provided_steps = set(body.selections.keys())
    predict_from = 0
    for i, step in enumerate(STEP_NAMES):
        if step in provided_steps:
            predict_from = i + 1

    # Build selections for model input (ordered)
    ordered_selections: dict[str, str] = {}
    for step in STEP_NAMES[:predict_from]:
        if step in body.selections:
            ordered_selections[step] = body.selections[step]

    # Predict remaining steps sequentially — each uses prior predictions
    predictions: dict[str, list[RankedOption]] = {}
    current_selections = dict(ordered_selections)

    for step in STEP_NAMES[predict_from:]:
        ranked = await predictor.predict(
            activity=body.activity,
            selections=current_selections,
            step_name=step,
            top_k=10,
        )
        predictions[step] = [
            RankedOption(label=r.label, score=r.score, rank=r.rank)
            for r in ranked
        ]
        # Use top prediction as input for next step
        if ranked:
            current_selections[step] = ranked[0].label

    return RecommendResponse(
        activity=body.activity,
        selections=ordered_selections,
        predictions=predictions,
    )
