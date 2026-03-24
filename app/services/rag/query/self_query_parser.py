"""
SelfQueryParser — extracts structured metadata filters from natural language queries
using GPT-4o mini, enabling push-down WHERE filtering before vector/BM25 search.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from openai import AsyncAzureOpenAI

from app.config import settings

SELF_QUERY_PROMPT = """\
Extract structured search filters from this EHS (Environment, Health, Safety) query.
Return a JSON object with these exact keys (use null if not present):
{{
  "activity_name": string or null,   // e.g. "Welding", "Cleaning"
  "hazard_type": string or null,     // e.g. "Arc Flash", "Chemical Burn"
  "date_from": "YYYY-MM-DD" or null, // start of date range
  "date_to": "YYYY-MM-DD" or null,   // end of date range
  "semantic_query": string           // cleaned query for vector/BM25 search
}}

Examples:
  Query: "How many welding requests in March 2026?"
  → {{"activity_name": "Welding", "hazard_type": null, "date_from": "2026-03-01", "date_to": "2026-03-31", "semantic_query": "welding requests"}}

  Query: "What PPE is required for chemical handling?"
  → {{"activity_name": null, "hazard_type": null, "date_from": null, "date_to": null, "semantic_query": "PPE required for chemical handling"}}

Query: "{query}"
"""


@dataclass
class SelfQueryResult:
    activity_name: str | None
    hazard_type: str | None
    date_from: str | None
    date_to: str | None
    semantic_query: str  # always present


class SelfQueryParser:
    def __init__(self, client: AsyncAzureOpenAI) -> None:
        self._client = client

    async def parse(self, query: str) -> SelfQueryResult:
        prompt = SELF_QUERY_PROMPT.format(query=query)
        resp = await self._client.chat.completions.create(
            model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        try:
            data = json.loads(resp.choices[0].message.content)
        except (json.JSONDecodeError, KeyError):
            data = {}

        return SelfQueryResult(
            activity_name=data.get("activity_name"),
            hazard_type=data.get("hazard_type"),
            date_from=data.get("date_from"),
            date_to=data.get("date_to"),
            semantic_query=data.get("semantic_query") or query,
        )

    def to_filter_dict(self, result: SelfQueryResult) -> dict:
        filters: dict = {}
        if result.activity_name:
            filters["activity_name"] = result.activity_name
        if result.hazard_type:
            filters["hazard_type"] = result.hazard_type
        if result.date_from:
            filters["submitted_at__gte"] = result.date_from
        if result.date_to:
            filters["submitted_at__lte"] = result.date_to
        return filters
