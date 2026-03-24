"""Input construction helpers for the EHS recommendation model."""
from __future__ import annotations

from transformers import DistilBertTokenizerFast

SEPARATOR = " [SEP] "


def build_input_text(activity: str, selections: dict[str, str]) -> str:
    """
    Concatenate activity and all previous selections into a single string.

    Examples:
      Step 1: "Welding"
      Step 2: "Welding [SEP] Arc Flash"
      Step 3: "Welding [SEP] Arc Flash [SEP] High x Likely"
      Step 4: "Welding [SEP] Arc Flash [SEP] High x Likely [SEP] Full Face Shield"
    """
    parts = [activity] + list(selections.values())
    return SEPARATOR.join(parts)


def load_tokenizer(model_path: str) -> DistilBertTokenizerFast:
    return DistilBertTokenizerFast.from_pretrained(model_path)


def tokenize_inputs(
    texts: list[str],
    tokenizer: DistilBertTokenizerFast,
    max_length: int = 128,
    device: str = "cpu",
) -> dict:
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    return {k: v.to(device) for k, v in encoded.items()}
