"""
Dataset loader and label encoder for DistilBERT fine-tuning.

Supports two CSV formats automatically:

Format A — training_data.csv (pre-processed):
  activity, hazard_type, severity_likelihood, moc_ppe, remarks

Format B — sample.csv (raw):
  Main Activity, Sub-Activity, Hazard, Initial_L, Initial_S, Initial_Risk,
  Control_Measures, Residual_L, Residual_S, Residual_Risk
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

# ── Conversion helpers for sample.csv (Format B) ─────────────────────────────

HAZARD_KEYWORDS = [
    (["arc flash", "arc-flash", "arc blast", "arc eye", "arc burn",
      "arc rated", "arc injury", "arc fire"],                                "Arc Flash"),
    (["uv ", "ultraviolet", "infrared", "bright light", "eye damage",
      "eye injury", "eye from arc", "welding helmet", "welding shield",
      "face shield", "exposure to bright"],                                  "UV Radiation"),
    (["electric shock", "electr", "live wire", "live cable", "energiz",
      "short circuit", "overload", "circuit", "wiring", "earthing",
      "grounding", "insulation", "voltage", "cable", "panel", "terminal",
      "fuse", "phase", "isolation", "loto", "lockout", "lock-out"],         "Electric Shock"),
    (["fire", "explosion", "explosive", "flammable", "ignit", "flashback",
      "backfire", "flash fire", "spark", "flame", "gas explosion",
      "vapor ignit", "vapour ignit", "cylinder", "gas leak", "gas hose",
      "gas backflow", "cylinder rupture", "cylinder storage"],               "Fire/Explosion"),
    (["fume", "toxic", "gas", "inhal", "respirat", "oxygen", "asphyxia",
      "vapour", "vapor", "dust", "silica", "asbestos", "lead paint",
      "solvent", "methane", "hydrogen", "carbon",
      "nitrogen", "contaminat", "atmosphere", "air quality", "heat stress",
      "confined", "engulf", "ozone", "air contamin"],                        "Fume Inhalation"),
    (["noise", "vibrat", "hearing", "sound", "decibel"],                    "Noise"),
    (["burn", "cement burn", "concrete burn", "skin burn", "skin irritat",
      "skin absorpt", "skin contact", "skin sensitiz", "chemical",
      "acid", "alkali", "corros", "eye irritat", "eye splash",
      "eye contact", "eye exposure", "contact dermatit", "allergic",
      "chronic exposure", "ingest", "sensitiz", "paint", "toxic inhal",
      "inhalation toxic", "health effect", "voc", "hydraulic fluid",
      "resin", "epoxy", "concrete splash", "cement splash"],                 "Chemical Burn"),
    (["slip", "trip", "slippery", "wet surface", "wet floor", "wet roof",
      "housekeep", "uneven ground", "uneven surface", "uneven terrain",
      "loose gravel", "loose surface", "polished"],                          "Slip/Trip"),
    (["fall from height", "fall from", "falling from", "fall through",
      "fall due", "fall off", "fall into", "fall on", "roof", "scaffold",
      "ladder", "height", "edge", "opening", "skylight", "fragile",
      "platform", "guardrail", "toe board", "mid-rail", "anchorage",
      "harness", "lifeline", "overreach", "loss of balance",
      "improper ladder", "defective ladder", "slippery rung"],               "Fall from Height"),
]


def _map_hazard(hazard: str) -> str:
    h = hazard.lower()
    for keywords, label in HAZARD_KEYWORDS:
        if any(kw in h for kw in keywords):
            return label
    return "Crush Injury"


def _map_severity(l: int, s: int) -> str:
    severity   = "High" if s >= 4 else ("Medium" if s == 3 else "Low")
    likelihood = "Likely" if l >= 3 else "Unlikely"
    return f"{severity} x {likelihood}"


def _map_ppe(controls_str: str) -> str:
    text = controls_str.lower()
    if any(x in text for x in ["harness", "lifeline", "fall arrest", "lanyard", "crawl board"]):
        return "Safety Harness + Lanyard"
    if any(x in text for x in ["lockout", "loto", "lock-out", "isolation", "insulated tool",
                                "insulated glove"]):
        return "Insulated Gloves + Lock-Out Tag-Out"
    if any(x in text for x in ["respirator", "ventilation", "gas test", "gas monitor",
                                "air monitor", "air test", "gas detect", "oxygen monitor"]):
        return "Respiratory Mask + Goggles"
    if any(x in text for x in ["chemical", "apron", "washing facilit", "barrier cream",
                                "protective cloth", "protective suit"]):
        return "Chemical Resistant Gloves + Apron"
    if any(x in text for x in ["welding shield", "arc-rated", "face shield", "fr jacket",
                                "arc ppe", "arc rated", "welding helmet"]):
        return "Full Face Shield + FR Jacket"
    if any(x in text for x in ["hearing", "ear plug", "ear protect", "ear defender", "ear"]):
        return "Hearing Protection + Goggles"
    if any(x in text for x in ["flashback", "fire extinguish", "hot work permit",
                                "fire watch", "fire blanket"]):
        return "Fire Extinguisher + Hot Work Permit"
    return "Hard Hat + Safety Boots"


def _map_remark(hazard: str) -> str:
    """Maps hazard description to seed_db.py remark values."""
    h = hazard.lower()
    if any(x in h for x in ["gas", "toxic", "fume", "oxygen", "confined", "vapour",
                             "vapor", "inhal", "atmosphere", "contamin"]):
        return "Ensure buddy system in place"
    if any(x in h for x in ["chemical", "solvent", "paint", "acid", "skin", "eye",
                             "sds", "hazardous"]):
        return "Check SDS before starting work"
    if any(x in h for x in ["fire", "explosion", "flashback", "ignit", "flammable",
                             "spark", "flame"]):
        return "Ensure area is barricaded and signage posted"
    if any(x in h for x in ["fall", "height", "ladder", "scaffold", "roof", "edge"]):
        return "Obtain permit-to-work before proceeding"
    if any(x in h for x in ["electric", "arc", "wire", "circuit", "shock", "energi"]):
        return "Obtain permit-to-work before proceeding"
    if any(x in h for x in ["noise", "vibrat", "hearing", "dust", "uv", "radiation"]):
        return "Verify all PPE is in serviceable condition"
    if any(x in h for x in ["collapse", "trench", "formwork", "structural", "ground",
                             "crush", "struck", "hit", "collision", "falling"]):
        return "Conduct toolbox talk before operation"
    return "Conduct toolbox talk before operation"


def _convert_sample_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Convert sample.csv or Excel (Format B) to training format (Format A).

    Handles both column naming variants:
      sample.csv : Initial_L, Initial_S, Control_Measures
      Excel      : Initial Likelihood, Initial Severity, Control Measures
    Also strips trailing ' - Zone N' from activity names in the Excel data.
    """
    # Normalise column names so both variants work identically
    col_remap = {
        "Initial Likelihood": "Initial_L",
        "Initial Severity":   "Initial_S",
        "Control Measures":   "Control_Measures",
    }
    df = df.rename(columns=col_remap)

    out = pd.DataFrame()
    # Strip ' - Zone N' suffix (e.g. "Electrical Works - Zone 3" -> "Electrical Works")
    out["activity"]            = df["Main Activity"].str.replace(
        r"\s*-\s*Zone\s+\d+", "", regex=True
    ).str.strip()
    out["hazard_type"]         = df["Hazard"].apply(_map_hazard)
    out["severity_likelihood"] = df.apply(
        lambda r: _map_severity(int(r["Initial_L"]), int(r["Initial_S"])), axis=1
    )
    out["moc_ppe"]             = df["Control_Measures"].apply(_map_ppe)
    out["remarks"]             = df["Hazard"].apply(_map_remark)
    return out


# ── Dataset & Builder ─────────────────────────────────────────────────────────

class EHSDataset(Dataset):
    """
    Each row in the CSV becomes up to 4 training examples (one per step).
    For step N, input = [activity + col_1 .. col_{N-1}], label = col_N.
    """

    def __init__(
        self,
        records: list[dict],
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


def _load_file(path: str) -> pd.DataFrame:
    """Load a CSV or Excel file and convert to training format if needed."""
    p = Path(path)
    if p.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)

    if "Main Activity" in df.columns:
        print(f"  '{p.name}': detected raw format — converting...")
        df = _convert_sample_csv(df)
        print(f"  '{p.name}': {len(df)} rows after conversion.")
    return df


class EHSDatasetBuilder:
    def __init__(self, csv_path: "str | list[str]") -> None:
        paths = [csv_path] if isinstance(csv_path, str) else list(csv_path)

        frames = []
        for p in paths:
            print(f"Loading: {p}")
            frames.append(_load_file(p))

        df = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]
        print(f"Combined dataset: {len(df)} rows from {len(paths)} file(s).")

        self.df = df.dropna(
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
                selections[step] = label_str

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
