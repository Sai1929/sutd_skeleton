"""
EHSRecommender — DistilBERT with 4 classification heads (one per popup step).

Steps:
  0 → hazard_type
  1 → severity_likelihood
  2 → moc_ppe
  3 → remarks
"""
from __future__ import annotations

import torch
import torch.nn as nn
from transformers import DistilBertModel, DistilBertPreTrainedModel


STEP_NAMES = ["hazard_type", "severity_likelihood", "moc_ppe", "remarks"]
STEP_TO_IDX = {name: i for i, name in enumerate(STEP_NAMES)}


class EHSRecommender(DistilBertPreTrainedModel):
    """
    Multi-head DistilBERT classifier.

    During inference, pass `step_name` to select the correct head.
    During training, `step_name` determines which head's loss is used.
    """

    def __init__(self, config, num_labels_per_step: list[int]):
        super().__init__(config)
        self.num_labels_per_step = num_labels_per_step

        self.distilbert = DistilBertModel(config)
        self.pre_classifier = nn.Linear(config.dim, config.dim)
        self.dropout = nn.Dropout(config.seq_classif_dropout)

        self.classifiers = nn.ModuleList(
            [nn.Linear(config.dim, n_labels) for n_labels in num_labels_per_step]
        )

        self.post_init()

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        step_name: str,
        labels: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        head_idx = STEP_TO_IDX[step_name]

        outputs = self.distilbert(input_ids=input_ids, attention_mask=attention_mask)
        hidden = outputs.last_hidden_state[:, 0]  # [CLS] token
        hidden = self.pre_classifier(hidden)
        hidden = nn.functional.relu(hidden)
        hidden = self.dropout(hidden)

        logits = self.classifiers[head_idx](hidden)

        result: dict[str, torch.Tensor] = {"logits": logits}

        if labels is not None:
            loss_fn = nn.CrossEntropyLoss()
            result["loss"] = loss_fn(logits, labels)

        return result

    @classmethod
    def from_pretrained_with_heads(
        cls,
        model_path: str,
        num_labels_per_step: list[int],
    ) -> "EHSRecommender":
        """
        Load from a saved checkpoint directory or HuggingFace hub.
        num_labels_per_step must match the saved config.
        """
        from transformers import DistilBertConfig

        config = DistilBertConfig.from_pretrained(model_path)
        config.num_labels_per_step = num_labels_per_step
        model = cls.from_pretrained(model_path, config=config, num_labels_per_step=num_labels_per_step)
        return model
