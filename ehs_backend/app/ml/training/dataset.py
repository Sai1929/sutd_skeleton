"""
Dataset loader and label encoder for DistilBERT fine-tuning.

Expected CSV columns:
  activity, hazard_type, severity_likelihood, moc_ppe, remarks
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import Dataset
from transformers import DistilBertTokenizerFast

from app.ml.distilbert.model import STEP_NAMES
from app.ml.distilbert.tokenizer import build_input_text

STEP_TO_COL = {
    "hazard_type": "hazard_type",
    "severity_likelihood": "severity_likelihood",
    "moc_ppe": "moc_ppe",
    "remarks": "remarks",
}


class EHSDataset(Dataset):
    """
    Each row in the CSV becomes up to 4 training examples (one per step).
    For step N, input = [activity + col_1 .. col_{N-1}], label = col_N.
    """

    def __init__(
        self,
        records: list[dict],  # list of {"input_text", "step_name", "label_index"}
        tokenizer: DistilBertTokenizerFast,
        max_length: int = 128,
    ) -> None:
        self.records = records
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> dict:
        rec = self.records[idx]
        enc = self.tokenizer(
            rec["input_text"],
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "labels": rec["label_index"],
            "step_name": rec["step_name"],
        }


class EHSDatasetBuilder:
    def __init__(self, csv_path: str) -> None:
        self.df = pd.read_csv(csv_path).dropna(
            subset=["activity", "hazard_type", "severity_likelihood", "moc_ppe", "remarks"]
        )
        self.encoders: dict[str, LabelEncoder] = {}
        self.label_vocab: dict[str, list[str]] = {}

    def fit_encoders(self) -> None:
        for step in STEP_NAMES:
            col = STEP_TO_COL[step]
            le = LabelEncoder()
            le.fit(self.df[col].astype(str))
            self.encoders[step] = le
            self.label_vocab[step] = list(le.classes_)

    def build_records(self) -> list[dict]:
        records = []
        for _, row in self.df.iterrows():
            activity = str(row["activity"])
            selections: dict[str, str] = {}

            for step in STEP_NAMES:
                col = STEP_TO_COL[step]
                label_str = str(row[col])
                label_index = int(self.encoders[step].transform([label_str])[0])
                input_text = build_input_text(activity, selections)

                records.append(
                    {
                        "input_text": input_text,
                        "step_name": step,
                        "label_index": label_index,
                        "label_str": label_str,
                    }
                )
                selections[step] = label_str  # feed forward for next step

        return records

    def save_vocab(self, output_dir: str) -> None:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        with open(path / "label_vocab.json", "w") as f:
            json.dump(self.label_vocab, f, indent=2)
        with open(path / "label_encoders.pkl", "wb") as f:
            pickle.dump(self.encoders, f)

    @staticmethod
    def load_vocab(model_dir: str) -> dict[str, list[str]]:
        with open(Path(model_dir) / "label_vocab.json") as f:
            return json.load(f)
