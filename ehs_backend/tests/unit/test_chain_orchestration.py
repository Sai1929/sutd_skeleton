"""Unit tests for recommendation chain orchestration logic."""
import pytest
from app.services.recommendation.chain import STEPS, TOTAL_STEPS
from app.ml.distilbert.tokenizer import build_input_text


def test_step_count():
    assert TOTAL_STEPS == 4


def test_step_names():
    names = [name for _, name in STEPS]
    assert names == ["hazard_type", "severity_likelihood", "moc_ppe", "remarks"]


def test_build_input_text_step1():
    text = build_input_text("Welding", {})
    assert text == "Welding"


def test_build_input_text_step2():
    text = build_input_text("Welding", {"hazard_type": "Arc Flash"})
    assert "Welding" in text
    assert "Arc Flash" in text
    assert "[SEP]" in text


def test_build_input_text_full():
    selections = {
        "hazard_type": "Arc Flash",
        "severity_likelihood": "High x Likely",
        "moc_ppe": "Full Face Shield",
    }
    text = build_input_text("Welding", selections)
    parts = text.split(" [SEP] ")
    assert len(parts) == 4
    assert parts[0] == "Welding"
    assert parts[1] == "Arc Flash"
