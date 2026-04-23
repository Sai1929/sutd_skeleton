"""
FrequencyRecommendationEngine — 2-tier recommendation (no ML model required):
  Tier 1: label_vocab table  →  valid labels per step (allowlist)
  Tier 2: inspection_submissions  →  historical frequency rank per activity

No model weights, no training needed. Works from day 1 with seed data.
"""
from __future__ import annotations

from dataclasses import dataclass

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

log = structlog.get_logger()

# Step names — order defines the 4-step popup sequence
STEP_NAMES: list[str] = [
    "hazard_type",
    "severity_likelihood",
    "moc_ppe",
    "remarks",
]

# Maps step_name → column in inspection_submissions (safe allowlist, not user input)
_STEP_TO_COL: dict[str, str] = {
    "hazard_type": "hazard_type",
    "severity_likelihood": "severity_likelihood",
    "moc_ppe": "moc_ppe",
    "remarks": "remarks",
}


@dataclass
class RankedOption:
    label: str
    score: float
    rank: int


class RecommendationEngine:
    """
    Stateless frequency-based engine.
    No startup loading required — always ready.
    """

    @property
    def is_ready(self) -> bool:
        return True

    async def get_ranked_options(
        self,
        db: AsyncSession,
        activity: str,
        selections: dict[str, str],
        step_name: str,
        top_k: int | None = None,
    ) -> list[RankedOption]:
        col = _STEP_TO_COL.get(step_name)
        if col is None:
            log.warning("engine.unknown_step", step_name=step_name)
            return []

        # col is from a hardcoded allowlist dict — safe to interpolate
        limit_clause = f"LIMIT {int(top_k)}" if top_k else ""
        rows = (
            await db.execute(
                text(f"""
                    SELECT lv.label_value,
                           COUNT(s.{col}) AS freq
                    FROM   label_vocab lv
                    LEFT JOIN inspection_submissions s
                           ON s.{col} = lv.label_value
                          AND s.activity_name = :activity
                    WHERE  lv.step = :step
                    GROUP BY lv.label_value
                    ORDER BY freq DESC, lv.label_value ASC
                    {limit_clause}
                """),
                {"activity": activity, "step": step_name},
            )
        ).fetchall()

        if not rows:
            log.warning("engine.no_labels", step_name=step_name,
                        hint="Seed label_vocab table first")
            return []

        total = sum(r.freq for r in rows) or 1
        return [
            RankedOption(
                label=r.label_value,
                score=round(r.freq / total, 4),
                rank=i + 1,
            )
            for i, r in enumerate(rows)
        ]
