"""
Fine-tuning script for EHSRecommender.
Not used at inference time — only called via scripts/train_distilbert.py.
"""
from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader, Subset
from transformers import DistilBertConfig, DistilBertTokenizerFast, get_cosine_schedule_with_warmup

from app.ml.distilbert.model import EHSRecommender, STEP_NAMES
from app.ml.training.dataset import EHSDataset, EHSDatasetBuilder


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def custom_collate(batch: list[dict]) -> dict:
    """Collate only samples from the same step (same classification head)."""
    step = batch[0]["step_name"]
    return {
        "input_ids": torch.stack([b["input_ids"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
        "labels": torch.tensor([b["labels"] for b in batch], dtype=torch.long),
        "step_name": step,
    }


def train(
    csv_path: str,
    output_dir: str,
    base_model: str = "distilbert-base-uncased",
    epochs: int = 5,
    batch_size: int = 16,
    lr: float = 2e-5,
    val_split: float = 0.1,
    device: str = "cpu",
) -> None:
    set_seed(42)

    # ── Dataset ────────────────────────────────────────────────────
    builder = EHSDatasetBuilder(csv_path)
    builder.fit_encoders()
    builder.save_vocab(output_dir)

    records = builder.build_records()
    random.shuffle(records)
    val_n = max(1, int(len(records) * val_split))
    train_records, val_records = records[val_n:], records[:val_n]

    tokenizer = DistilBertTokenizerFast.from_pretrained(base_model)
    tokenizer.save_pretrained(output_dir)

    train_ds = EHSDataset(train_records, tokenizer)
    val_ds = EHSDataset(val_records, tokenizer)

    # ── Model ──────────────────────────────────────────────────────
    config = DistilBertConfig.from_pretrained(base_model)
    config.seq_classif_dropout = 0.2
    num_labels = [len(builder.label_vocab[s]) for s in STEP_NAMES]

    model = EHSRecommender(config, num_labels_per_step=num_labels)
    # Load pretrained DistilBERT weights (shared trunk)
    pretrained = torch.hub.load("huggingface/pytorch-transformers", "model", base_model)
    model.distilbert.load_state_dict(pretrained.state_dict(), strict=False)
    model = model.to(device)

    # ── Per-step DataLoaders ───────────────────────────────────────
    def step_loader(records, step):
        step_recs = [r for r in records if r["step_name"] == step]
        ds = EHSDataset(step_recs, tokenizer)
        return DataLoader(ds, batch_size=batch_size, shuffle=True, collate_fn=custom_collate)

    # ── Optimizer / Scheduler ──────────────────────────────────────
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total_steps = (len(train_records) // batch_size + 1) * epochs
    scheduler = get_cosine_schedule_with_warmup(
        optimizer, num_warmup_steps=total_steps // 10, num_training_steps=total_steps
    )

    best_val_acc = 0.0

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        steps = 0

        for step in STEP_NAMES:
            loader = step_loader(train_records, step)
            for batch in loader:
                optimizer.zero_grad()
                out = model(
                    input_ids=batch["input_ids"].to(device),
                    attention_mask=batch["attention_mask"].to(device),
                    step_name=batch["step_name"],
                    labels=batch["labels"].to(device),
                )
                out["loss"].backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                total_loss += out["loss"].item()
                steps += 1

        avg_loss = total_loss / max(steps, 1)

        # Validation
        val_acc = evaluate(model, val_records, tokenizer, device)
        print(f"Epoch {epoch}/{epochs} | loss={avg_loss:.4f} | val_acc={val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            model.save_pretrained(output_dir)
            print(f"  ✓ Saved best checkpoint (val_acc={val_acc:.4f})")

    print(f"Training complete. Best val_acc={best_val_acc:.4f}")


def evaluate(model, records: list[dict], tokenizer, device: str) -> float:
    model.eval()
    correct = total = 0

    for step in STEP_NAMES:
        step_recs = [r for r in records if r["step_name"] == step]
        if not step_recs:
            continue
        ds = EHSDataset(step_recs, tokenizer)
        loader = DataLoader(ds, batch_size=32, collate_fn=custom_collate)

        with torch.no_grad():
            for batch in loader:
                out = model(
                    input_ids=batch["input_ids"].to(device),
                    attention_mask=batch["attention_mask"].to(device),
                    step_name=batch["step_name"],
                )
                preds = out["logits"].argmax(dim=-1).cpu()
                correct += (preds == batch["labels"]).sum().item()
                total += len(batch["labels"])

    return correct / total if total > 0 else 0.0
