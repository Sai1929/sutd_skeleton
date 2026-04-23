"""
High-level inference API for the EHSRecommender model.
Thread-safe — all GPU/CPU ops are offloaded via asyncio.to_thread.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import torch
import torch.nn.functional as F

from transformers import DistilBertForSequenceClassification, DistilBertTokenizerFast

from app.ml.distilbert.model import EHSRecommender, STEP_NAMES
from app.ml.distilbert.tokenizer import build_input_text, load_tokenizer, tokenize_inputs


@dataclass
class RankedOption:
    label: str
    score: float
    rank: int


@dataclass
class PredictorOutput:
    step_name: str
    input_text: str
    ranked_options: list[RankedOption] = field(default_factory=list)


class EHSPredictor:
    def __init__(
        self,
        model: EHSRecommender,
        tokenizer,
        label_vocab: dict[str, list[str]],  # step_name -> ordered list of labels
        device: str = "cpu",
        max_seq_len: int = 128,
    ) -> None:
        self.model = model.to(device)
        self.model.eval()
        self.tokenizer = tokenizer
        self.label_vocab = label_vocab
        self.device = device
        self.max_seq_len = max_seq_len

    def _predict_sync(
        self,
        input_texts: list[str],
        step_name: str,
        top_k: int,
    ) -> list[list[RankedOption]]:
        encoded = tokenize_inputs(input_texts, self.tokenizer, self.max_seq_len, self.device)
        labels_for_step = self.label_vocab[step_name]

        with torch.no_grad():
            output = self.model(
                input_ids=encoded["input_ids"],
                attention_mask=encoded["attention_mask"],
                step_name=step_name,
            )
            probs = F.softmax(output["logits"], dim=-1).cpu().numpy()

        results = []
        for prob_row in probs:
            top_k_actual = min(top_k, len(labels_for_step))
            top_indices = prob_row.argsort()[::-1][:top_k_actual]
            ranked = [
                RankedOption(
                    label=labels_for_step[idx],
                    score=float(prob_row[idx]),
                    rank=rank + 1,
                )
                for rank, idx in enumerate(top_indices)
            ]
            results.append(ranked)
        return results

    async def predict(
        self,
        activity: str,
        selections: dict[str, str],
        step_name: str,
        top_k: int = 10,
    ) -> list[RankedOption]:
        input_text = build_input_text(activity, selections)
        results = await asyncio.to_thread(
            self._predict_sync, [input_text], step_name, top_k
        )
        return results[0]

    async def predict_batch(
        self,
        input_texts: list[str],
        step_name: str,
        top_k: int = 10,
    ) -> list[list[RankedOption]]:
        return await asyncio.to_thread(
            self._predict_sync, input_texts, step_name, top_k
        )

    @classmethod
    def from_checkpoint(
        cls,
        model_path: str,
        label_vocab: dict[str, list[str]],
        device: str = "cpu",
        max_seq_len: int = 128,
    ) -> "EHSPredictor":
        num_labels_per_step = [len(label_vocab[s]) for s in STEP_NAMES]
        model = EHSRecommender.from_pretrained_with_heads(model_path, num_labels_per_step)
        tokenizer = load_tokenizer(model_path)
        return cls(model, tokenizer, label_vocab, device, max_seq_len)


class EHSMultiStepPredictor:
    """
    Per-step predictor: loads one DistilBertForSequenceClassification per step.
    Used when the model was trained with --strategy per_step.
    """

    def __init__(
        self,
        models: dict[str, DistilBertForSequenceClassification],
        tokenizers: dict[str, DistilBertTokenizerFast],
        label_vocab: dict[str, list[str]],
        device: str = "cpu",
        max_seq_len: int = 128,
    ) -> None:
        self.models    = {s: m.to(device).eval() for s, m in models.items()}
        self.tokenizers = tokenizers
        self.label_vocab = label_vocab
        self.device    = device
        self.max_seq_len = max_seq_len

    def _predict_sync(self, input_text: str, step_name: str, top_k: int) -> list[RankedOption]:
        model     = self.models[step_name]
        tokenizer = self.tokenizers[step_name]
        labels    = self.label_vocab[step_name]

        enc = tokenizer(
            input_text,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_seq_len,
            padding="max_length",
        )
        enc = {k: v.to(self.device) for k, v in enc.items()}

        with torch.no_grad():
            out   = model(**enc)
            probs = F.softmax(out.logits, dim=-1).cpu().numpy()[0]

        top_k_actual = min(top_k, len(labels))
        top_indices  = probs.argsort()[::-1][:top_k_actual]
        return [
            RankedOption(label=labels[idx], score=float(probs[idx]), rank=rank + 1)
            for rank, idx in enumerate(top_indices)
        ]

    async def predict(
        self,
        activity: str,
        selections: dict[str, str],
        step_name: str,
        top_k: int = 10,
    ) -> list[RankedOption]:
        input_text = build_input_text(activity, selections)
        return await asyncio.to_thread(self._predict_sync, input_text, step_name, top_k)

    @classmethod
    def from_checkpoint(
        cls,
        model_dir: str,
        label_vocab: dict[str, list[str]],
        device: str = "cpu",
        max_seq_len: int = 128,
    ) -> "EHSMultiStepPredictor":
        from pathlib import Path
        base = Path(model_dir)
        models: dict[str, DistilBertForSequenceClassification] = {}
        tokenizers: dict[str, DistilBertTokenizerFast] = {}
        for step in STEP_NAMES:
            step_dir = base / f"step_{step}"
            if not step_dir.exists():
                raise FileNotFoundError(
                    f"Per-step model not found: {step_dir}. "
                    "Train with --strategy per_step first."
                )
            models[step]    = DistilBertForSequenceClassification.from_pretrained(str(step_dir))
            tokenizers[step] = DistilBertTokenizerFast.from_pretrained(str(step_dir))
        return cls(models, tokenizers, label_vocab, device, max_seq_len)
