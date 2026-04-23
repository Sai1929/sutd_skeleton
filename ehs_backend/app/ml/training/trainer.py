"""
Fine-tuning script for EHSRecommender.
Not used at inference time — only called via scripts/train_distilbert.py.
"""
from __future__ import annotations

import random
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch.optim import AdamW
from torch.utils.data import DataLoader
from transformers import DistilBertConfig, DistilBertForSequenceClassification, DistilBertModel, DistilBertTokenizerFast, get_cosine_schedule_with_warmup

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


def compute_class_weights(records: list[dict], step: str, num_classes: int) -> torch.Tensor:
    """
    Inverse-frequency weighting per class to handle class imbalance.
    Weight for class i = total_samples / (num_classes * count_i)
    Rare classes get higher weights; dominant classes get lower weights.
    """
    labels = [r["label_index"] for r in records if r["step_name"] == step]
    counts = Counter(labels)
    total = len(labels)
    weights = []
    for i in range(num_classes):
        count = max(counts.get(i, 1), 1)  # avoid division by zero
        weights.append(total / (num_classes * count))
    return torch.tensor(weights, dtype=torch.float)


def train(
    csv_path: "str | list[str]",
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

    print(f"Train examples: {len(train_records)} | Val examples: {len(val_records)}")

    tokenizer = DistilBertTokenizerFast.from_pretrained(base_model)
    tokenizer.save_pretrained(output_dir)

    # ── Model ──────────────────────────────────────────────────────
    config = DistilBertConfig.from_pretrained(base_model)
    config.seq_classif_dropout = 0.2
    num_labels = [len(builder.label_vocab[s]) for s in STEP_NAMES]

    print(f"Labels per step: { {s: n for s, n in zip(STEP_NAMES, num_labels)} }")

    model = EHSRecommender(config, num_labels_per_step=num_labels)

    # Fix: use DistilBertModel.from_pretrained() — reliable HuggingFace loading
    print(f"Loading pretrained weights from: {base_model}")
    pretrained_bert = DistilBertModel.from_pretrained(base_model)
    model.distilbert.load_state_dict(pretrained_bert.state_dict())
    del pretrained_bert  # free memory
    model = model.to(device)

    # ── Per-step class weights (handles class imbalance) ───────────
    step_weights = {
        step: compute_class_weights(train_records, step, num_labels[i])
        for i, step in enumerate(STEP_NAMES)
    }
    print("\nClass weights (higher = rarer class):")
    for step in STEP_NAMES:
        w = step_weights[step]
        print(f"  {step}: min={w.min():.2f}  max={w.max():.2f}  ratio={w.max()/w.min():.1f}x")

    # ── Per-step DataLoaders ───────────────────────────────────────
    def step_loader(recs, step):
        step_recs = [r for r in recs if r["step_name"] == step]
        ds = EHSDataset(step_recs, tokenizer)
        return DataLoader(ds, batch_size=batch_size, shuffle=True, collate_fn=custom_collate)

    # ── Optimizer / Scheduler ──────────────────────────────────────
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    total_steps = (len(train_records) // batch_size + 1) * epochs
    scheduler = get_cosine_schedule_with_warmup(
        optimizer, num_warmup_steps=total_steps // 10, num_training_steps=total_steps
    )

    best_val_acc = 0.0
    print()

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        steps = 0

        for step in STEP_NAMES:
            loader = step_loader(train_records, step)
            w = step_weights[step].to(device)

            for batch in loader:
                optimizer.zero_grad()

                # Forward without labels — compute weighted loss externally
                out = model(
                    input_ids=batch["input_ids"].to(device),
                    attention_mask=batch["attention_mask"].to(device),
                    step_name=batch["step_name"],
                )
                loss = F.cross_entropy(out["logits"], batch["labels"].to(device), weight=w)

                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                total_loss += loss.item()
                steps += 1

        avg_loss = total_loss / max(steps, 1)

        # Validation — per-step accuracy
        per_step_acc = evaluate(model, val_records, tokenizer, device)
        overall_acc = sum(per_step_acc.values()) / len(per_step_acc)

        step_str = "  ".join(f"{s[:4]}={v:.3f}" for s, v in per_step_acc.items())
        print(f"Epoch {epoch}/{epochs} | loss={avg_loss:.4f} | val_acc={overall_acc:.4f} | {step_str}")

        if overall_acc > best_val_acc:
            best_val_acc = overall_acc
            model.save_pretrained(output_dir)
            print(f"  -> Saved best checkpoint (val_acc={overall_acc:.4f})")

    print(f"\nTraining complete. Best val_acc={best_val_acc:.4f}")
    print(f"Model saved to: {output_dir}")


def evaluate(model, records: list[dict], tokenizer, device: str) -> dict[str, float]:
    model.eval()
    per_step: dict[str, tuple[int, int]] = {s: (0, 0) for s in STEP_NAMES}

    for step in STEP_NAMES:
        step_recs = [r for r in records if r["step_name"] == step]
        if not step_recs:
            continue
        ds = EHSDataset(step_recs, tokenizer)
        loader = DataLoader(ds, batch_size=32, collate_fn=custom_collate)

        correct = total = 0
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

        per_step[step] = correct / total if total > 0 else 0.0

    model.train()
    return per_step


# ── Improved Single-Model Training ────────────────────────────────────────────

def _run_epoch_improved(
    model,
    log_vars: torch.Tensor,
    train_records: list[dict],
    val_records: list[dict],
    tokenizer,
    optimizer,
    scheduler,
    batch_size: int,
    device: str,
    label_smoothing: float,
    epoch: int,
    total_epochs: int,
    phase_label: str,
    output_dir: str,
    best_val_acc: float,
) -> float:
    model.train()
    total_loss, steps = 0.0, 0

    for step_idx, step in enumerate(STEP_NAMES):
        step_recs = [r for r in train_records if r["step_name"] == step]
        ds     = EHSDataset(step_recs, tokenizer)
        loader = DataLoader(ds, batch_size=batch_size, shuffle=True, collate_fn=custom_collate)

        for batch in loader:
            optimizer.zero_grad()
            out = model(
                input_ids=batch["input_ids"].to(device),
                attention_mask=batch["attention_mask"].to(device),
                step_name=step,
            )
            # Uncertainty-weighted loss (Kendall et al., 2018)
            # L = exp(-log_var) * task_loss + log_var
            task_loss = F.cross_entropy(
                out["logits"], batch["labels"].to(device),
                label_smoothing=label_smoothing,
            )
            precision = torch.exp(-log_vars[step_idx])
            loss      = precision * task_loss + log_vars[step_idx]

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total_loss += task_loss.item()
            steps += 1

    avg_loss = total_loss / max(steps, 1)
    per_step_acc = evaluate(model, val_records, tokenizer, device)
    overall_acc  = sum(per_step_acc.values()) / len(per_step_acc)

    step_str    = "  ".join(f"{s[:4]}={v:.3f}" for s, v in per_step_acc.items())
    logvar_str  = "  ".join(f"{s[:4]}={log_vars[i].item():.3f}" for i, s in enumerate(STEP_NAMES))
    print(f"[{phase_label}] Epoch {epoch}/{total_epochs} | loss={avg_loss:.4f} | val_acc={overall_acc:.4f} | {step_str}")
    print(f"  log_vars: {logvar_str}")

    if overall_acc > best_val_acc:
        best_val_acc = overall_acc
        model.save_pretrained(output_dir)
        print(f"  -> Saved best checkpoint (val_acc={overall_acc:.4f})")

    return best_val_acc


def train_improved(
    csv_path: "str | list[str]",
    output_dir: str,
    base_model: str = "distilbert-base-uncased",
    freeze_epochs: int = 3,
    unfreeze_epochs: int = 12,
    batch_size: int = 16,
    backbone_lr: float = 1e-5,
    head_lr: float = 5e-5,
    val_split: float = 0.1,
    label_smoothing: float = 0.1,
    device: str = "cpu",
) -> None:
    """
    Improved single shared-backbone training.

    Improvements over the original train():
      1. Two-phase: freeze backbone → unfreeze with layer-wise LR decay
      2. Uncertainty weighting: learnable log-variance per task (Kendall 2018)
      3. Label smoothing: reduces overconfidence
      4. Minority class oversampling: balances rare classes per step
    """
    set_seed(42)

    builder = EHSDatasetBuilder(csv_path)
    builder.fit_encoders()
    builder.save_vocab(output_dir)

    records = builder.build_records()
    random.shuffle(records)
    val_n = max(1, int(len(records) * val_split))
    train_raw, val_records = records[val_n:], records[:val_n]

    # Oversample minority classes per step then merge
    num_labels_list = [len(builder.label_vocab[s]) for s in STEP_NAMES]
    train_records: list[dict] = []
    for step, n_labels in zip(STEP_NAMES, num_labels_list):
        step_recs = [r for r in train_raw if r["step_name"] == step]
        train_records.extend(oversample_records(step_recs, n_labels))
    random.shuffle(train_records)

    print(f"Train (after oversample): {len(train_records)} | Val: {len(val_records)}")
    print(f"freeze_epochs={freeze_epochs} | unfreeze_epochs={unfreeze_epochs}")
    print(f"backbone_lr={backbone_lr} | head_lr={head_lr} | label_smoothing={label_smoothing}\n")

    tokenizer = DistilBertTokenizerFast.from_pretrained(base_model)
    tokenizer.save_pretrained(output_dir)

    config = DistilBertConfig.from_pretrained(base_model)
    config.seq_classif_dropout = 0.2
    model = EHSRecommender(config, num_labels_per_step=num_labels_list)
    pretrained_bert = DistilBertModel.from_pretrained(base_model)
    model.distilbert.load_state_dict(pretrained_bert.state_dict())
    del pretrained_bert
    model = model.to(device)

    print(f"Labels per step: { {s: n for s, n in zip(STEP_NAMES, num_labels_list)} }\n")

    best_val_acc = 0.0

    # ── Phase 1: Freeze backbone, train heads only ────────────────────────────
    print(f"{'='*55}")
    print(f"Phase 1: heads only — {freeze_epochs} epochs, lr={head_lr}")
    print(f"{'='*55}")

    for param in model.distilbert.parameters():
        param.requires_grad = False

    log_vars = torch.zeros(len(STEP_NAMES), device=device, requires_grad=True)
    head_params = [p for p in model.parameters() if p.requires_grad]

    optimizer_p1 = AdamW(
        [{"params": head_params, "lr": head_lr},
         {"params": [log_vars],  "lr": head_lr}],
        weight_decay=0.01,
    )
    total_p1 = max((len(train_records) // batch_size + 1) * freeze_epochs, 1)
    scheduler_p1 = get_cosine_schedule_with_warmup(
        optimizer_p1, num_warmup_steps=max(1, total_p1 // 10),
        num_training_steps=total_p1,
    )

    for epoch in range(1, freeze_epochs + 1):
        best_val_acc = _run_epoch_improved(
            model, log_vars, train_records, val_records, tokenizer,
            optimizer_p1, scheduler_p1, batch_size, device, label_smoothing,
            epoch, freeze_epochs, "P1", output_dir, best_val_acc,
        )

    # ── Phase 2: Unfreeze all, layer-wise LR decay ────────────────────────────
    print(f"\n{'='*55}")
    print(f"Phase 2: full fine-tune — {unfreeze_epochs} epochs, backbone_lr={backbone_lr}")
    print(f"{'='*55}")

    # Reload best checkpoint from Phase 1
    model = EHSRecommender.from_pretrained_with_heads(output_dir, num_labels_list)
    model = model.to(device)
    for param in model.parameters():
        param.requires_grad = True

    # Fresh log_vars for Phase 2
    log_vars = torch.zeros(len(STEP_NAMES), device=device, requires_grad=True)

    # Layer-wise LR: embeddings (lowest) → upper layers → heads (highest)
    optimizer_p2 = AdamW(
        [
            {"params": list(model.distilbert.embeddings.parameters()),
             "lr": backbone_lr * 0.1},
            {"params": list(model.distilbert.transformer.layer[:3].parameters()),
             "lr": backbone_lr * 0.3},
            {"params": list(model.distilbert.transformer.layer[3:].parameters()),
             "lr": backbone_lr},
            {"params": list(model.pre_classifier.parameters()) +
                        list(model.classifiers.parameters()),
             "lr": head_lr},
            {"params": [log_vars], "lr": head_lr},
        ],
        weight_decay=0.01,
    )
    total_p2 = max((len(train_records) // batch_size + 1) * unfreeze_epochs, 1)
    scheduler_p2 = get_cosine_schedule_with_warmup(
        optimizer_p2, num_warmup_steps=max(1, total_p2 // 10),
        num_training_steps=total_p2,
    )

    for epoch in range(1, unfreeze_epochs + 1):
        best_val_acc = _run_epoch_improved(
            model, log_vars, train_records, val_records, tokenizer,
            optimizer_p2, scheduler_p2, batch_size, device, label_smoothing,
            epoch, unfreeze_epochs, "P2", output_dir, best_val_acc,
        )

    print(f"\nTraining complete. Best val_acc={best_val_acc:.4f}")
    print(f"Model saved to: {output_dir}")


# ── Per-Step Training (separate model per step) ───────────────────────────────

def simple_collate(batch: list[dict]) -> dict:
    """Collate for single-step datasets (no step_name filtering needed)."""
    return {
        "input_ids":      torch.stack([b["input_ids"] for b in batch]),
        "attention_mask": torch.stack([b["attention_mask"] for b in batch]),
        "labels":         torch.tensor([b["labels"] for b in batch], dtype=torch.long),
    }


def oversample_records(records: list[dict], num_labels: int, target_ratio: float = 0.5) -> list[dict]:
    """Oversample minority classes so min_count >= target_ratio * max_count."""
    counts = Counter(r["label_index"] for r in records)
    if not counts:
        return records
    max_count = max(counts.values())
    target = max(int(max_count * target_ratio), 5)

    result = list(records)
    for i in range(num_labels):
        cnt = counts.get(i, 0)
        if 0 < cnt < target:
            class_recs = [r for r in records if r["label_index"] == i]
            result.extend(random.choices(class_recs, k=target - cnt))

    random.shuffle(result)
    return result


def _train_phase(
    model,
    train_records: list[dict],
    val_records: list[dict],
    tokenizer,
    epochs: int,
    batch_size: int,
    lr: float,
    device: str,
    label_smoothing: float,
    step_dir: Path,
    phase_label: str,
) -> float:
    """Train one phase (frozen or unfrozen backbone). Returns best val accuracy."""
    train_ds = EHSDataset(train_records, tokenizer)
    val_ds   = EHSDataset(val_records,   tokenizer)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,  collate_fn=simple_collate)
    val_loader   = DataLoader(val_ds,   batch_size=32,         shuffle=False, collate_fn=simple_collate)

    optimizer = AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=lr, weight_decay=0.01,
    )
    total_steps = max(len(train_loader) * epochs, 1)
    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=max(1, total_steps // 10),
        num_training_steps=total_steps,
    )

    best_acc = 0.0

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss, steps = 0.0, 0

        for batch in train_loader:
            optimizer.zero_grad()
            out  = model(
                input_ids=batch["input_ids"].to(device),
                attention_mask=batch["attention_mask"].to(device),
            )
            loss = F.cross_entropy(out.logits, batch["labels"].to(device),
                                   label_smoothing=label_smoothing)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()
            steps += 1

        model.eval()
        correct = total = 0
        with torch.no_grad():
            for batch in val_loader:
                out   = model(
                    input_ids=batch["input_ids"].to(device),
                    attention_mask=batch["attention_mask"].to(device),
                )
                preds = out.logits.argmax(dim=-1).cpu()
                correct += (preds == batch["labels"]).sum().item()
                total   += len(batch["labels"])

        acc      = correct / total if total > 0 else 0.0
        avg_loss = total_loss / max(steps, 1)
        saved    = ""
        if acc > best_acc:
            best_acc = acc
            model.save_pretrained(str(step_dir))
            saved = " -> saved best"
        print(f"    [{phase_label}] Epoch {epoch}/{epochs} | loss={avg_loss:.4f} | acc={acc:.4f}{saved}")

    return best_acc


def train_per_step(
    csv_path: "str | list[str]",
    output_dir: str,
    base_model: str = "distilbert-base-uncased",
    freeze_epochs: int = 3,
    unfreeze_epochs: int = 7,
    batch_size: int = 16,
    backbone_lr: float = 1e-5,
    head_lr: float = 5e-5,
    val_split: float = 0.1,
    label_smoothing: float = 0.1,
    device: str = "cpu",
) -> None:
    """
    Train one DistilBERT classifier per step (no shared backbone).
    Two-phase: freeze backbone first, then unfreeze for fine-tuning.
    Includes label smoothing and minority-class oversampling.
    """
    set_seed(42)

    builder = EHSDatasetBuilder(csv_path)
    builder.fit_encoders()
    builder.save_vocab(output_dir)

    records = builder.build_records()
    random.shuffle(records)
    val_n = max(1, int(len(records) * val_split))
    train_records, val_records = records[val_n:], records[:val_n]

    tokenizer = DistilBertTokenizerFast.from_pretrained(base_model)

    print(f"Train: {len(train_records)} | Val: {len(val_records)}")
    print(f"freeze_epochs={freeze_epochs} | unfreeze_epochs={unfreeze_epochs}")
    print(f"backbone_lr={backbone_lr} | head_lr={head_lr} | label_smoothing={label_smoothing}")

    results: dict[str, float] = {}

    for step in STEP_NAMES:
        num_labels = len(builder.label_vocab[step])
        step_dir   = Path(output_dir) / f"step_{step}"
        step_dir.mkdir(parents=True, exist_ok=True)
        tokenizer.save_pretrained(str(step_dir))

        step_train_raw = [r for r in train_records if r["step_name"] == step]
        step_train     = oversample_records(step_train_raw, num_labels)
        step_val       = [r for r in val_records  if r["step_name"] == step]

        print(f"\n{'='*55}")
        print(f"Step: {step} | labels={num_labels} | train={len(step_train)} | val={len(step_val)}")
        print(f"{'='*55}")

        # Build model with pretrained backbone
        config = DistilBertConfig.from_pretrained(base_model, num_labels=num_labels)
        model  = DistilBertForSequenceClassification(config)
        pretrained_bert = DistilBertModel.from_pretrained(base_model)
        model.distilbert.load_state_dict(pretrained_bert.state_dict())
        del pretrained_bert
        model = model.to(device)

        # Phase 1 — freeze backbone, train head only
        for param in model.distilbert.parameters():
            param.requires_grad = False
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"\nPhase 1 (heads only) | trainable params: {trainable:,}")
        acc1 = _train_phase(model, step_train, step_val, tokenizer,
                            freeze_epochs, batch_size, head_lr,
                            device, label_smoothing, step_dir, "P1")

        # Phase 2 — reload best, unfreeze all, fine-tune
        model = DistilBertForSequenceClassification.from_pretrained(str(step_dir))
        model = model.to(device)
        for param in model.distilbert.parameters():
            param.requires_grad = True
        trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"\nPhase 2 (full fine-tune) | trainable params: {trainable:,}")
        acc2 = _train_phase(model, step_train, step_val, tokenizer,
                            unfreeze_epochs, batch_size, backbone_lr,
                            device, label_smoothing, step_dir, "P2")

        results[step] = max(acc1, acc2)

    overall = sum(results.values()) / len(results)
    print(f"\n{'='*55}")
    print("Per-step training complete!")
    print(f"{'='*55}")
    for step, acc in results.items():
        print(f"  {step:<28} {acc:.4f}")
    print(f"  {'Overall average':<28} {overall:.4f}")
    print(f"\nModels saved under: {output_dir}/step_*/")

