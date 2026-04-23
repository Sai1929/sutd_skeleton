"""
Quick test script for the trained EHSRecommender model.
Auto-detects whether shared or per-step model was trained.
Tests all 4 steps for multiple activities.

Usage:
    python scripts/test_model.py
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml.distilbert.predictor import EHSPredictor, EHSMultiStepPredictor
from app.ml.training.dataset import EHSDatasetBuilder

MODEL_DIR = "models/ehs_distilbert"

TEST_CASES = [
    {
        "activity": "Work at Height",
        "selections": {},
        "step": "hazard_type",
    },
    {
        "activity": "Work at Height",
        "selections": {"hazard_type": "Fall from Height"},
        "step": "severity_likelihood",
    },
    {
        "activity": "Work at Height",
        "selections": {"hazard_type": "Fall from Height", "severity_likelihood": "High x Likely"},
        "step": "moc_ppe",
    },
    {
        "activity": "Work at Height",
        "selections": {"hazard_type": "Fall from Height", "severity_likelihood": "High x Likely", "moc_ppe": "Safety Harness + Lanyard"},
        "step": "remarks",
    },
    {
        "activity": "Electrical Works",
        "selections": {},
        "step": "hazard_type",
    },
    {
        "activity": "Electrical Works",
        "selections": {"hazard_type": "Electric Shock"},
        "step": "severity_likelihood",
    },
    {
        "activity": "Chemical Handling",
        "selections": {},
        "step": "hazard_type",
    },
    {
        "activity": "Welding",
        "selections": {},
        "step": "hazard_type",
    },
]


async def main():
    label_vocab = EHSDatasetBuilder.load_vocab(MODEL_DIR)

    # Auto-detect: per-step model has step_hazard_type/ subdirectory
    per_step_dir = Path(MODEL_DIR) / "step_hazard_type"
    if per_step_dir.exists():
        print(f"Detected: per-step model")
        print(f"Loading from: {MODEL_DIR}/step_*/\n")
        predictor = EHSMultiStepPredictor.from_checkpoint(MODEL_DIR, label_vocab)
    else:
        print(f"Detected: shared-backbone model")
        print(f"Loading from: {MODEL_DIR}\n")
        predictor = EHSPredictor.from_checkpoint(MODEL_DIR, label_vocab)

    print("Model loaded successfully!\n")
    print("=" * 60)

    current_activity = None

    for case in TEST_CASES:
        activity   = case["activity"]
        selections = case["selections"]
        step       = case["step"]

        if activity != current_activity:
            print(f"\nActivity: {activity}")
            print("-" * 40)
            current_activity = activity

        context = " > ".join(selections.values()) if selections else "(no prior selections)"
        print(f"\n  Step: {step}")
        print(f"  Context: {context}")

        ranked = await predictor.predict(
            activity=activity,
            selections=selections,
            step_name=step,
            top_k=3,
        )

        print(f"  Top 3 predictions:")
        for opt in ranked:
            bar = "#" * int(opt.score * 20)
            print(f"    {opt.rank}. {opt.label:<45} {opt.score:.3f} |{bar}")

    print("\n" + "=" * 60)
    print("Test complete.")


if __name__ == "__main__":
    asyncio.run(main())
