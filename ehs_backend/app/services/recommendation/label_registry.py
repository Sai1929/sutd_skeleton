"""
Label registry — loads and caches the label vocabulary per popup step.
Reads from DB (label_vocab table) or falls back to JSON file saved during training.
"""
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.distilbert.model import STEP_NAMES


class LabelRegistry:
    def __init__(self) -> None:
        self._vocab: dict[str, list[str]] = {}  # step_name -> ordered labels

    @property
    def vocab(self) -> dict[str, list[str]]:
        return self._vocab

    def num_labels(self) -> list[int]:
        return [len(self._vocab.get(s, [])) for s in STEP_NAMES]

    async def load_from_db(self, db: AsyncSession) -> None:
        from app.db.models.inspection import LabelVocab

        result = await db.execute(
            select(LabelVocab).order_by(LabelVocab.step, LabelVocab.label_index)
        )
        rows = result.scalars().all()

        vocab: dict[str, list[str]] = {s: [] for s in STEP_NAMES}
        for row in rows:
            if row.step in vocab:
                # Ensure index-aligned list
                while len(vocab[row.step]) <= row.label_index:
                    vocab[row.step].append("")
                vocab[row.step][row.label_index] = row.label_value

        # Remove empty placeholders
        self._vocab = {k: [v for v in vs if v] for k, vs in vocab.items()}

    def load_from_file(self, model_path: str) -> None:
        vocab_file = Path(model_path) / "label_vocab.json"
        if not vocab_file.exists():
            raise FileNotFoundError(f"label_vocab.json not found in {model_path}")
        with open(vocab_file) as f:
            self._vocab = json.load(f)

    def get_labels(self, step_name: str) -> list[str]:
        return self._vocab.get(step_name, [])
