#!/usr/bin/env python3
"""
CLI training script for the EHS DistilBERT recommendation model.

Strategies:
  shared      — original: one shared backbone + 4 heads, basic training
  shared_v2   — improved: shared backbone + uncertainty weighting + two-phase
                + label smoothing + oversampling (~80-83% expected)
  per_step    — best accuracy: one separate DistilBERT per step (~82-87% expected)

Usage:
    # Improved single model (shared_v2):
    python scripts/train_distilbert.py --data_path sample.csv --strategy shared_v2

    # Best accuracy (per_step):
    python scripts/train_distilbert.py --data_path sample.csv --strategy per_step

    # Original:
    python scripts/train_distilbert.py --data_path sample.csv --strategy shared --epochs 10
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml.training.trainer import train, train_improved, train_per_step


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune EHS DistilBERT")
    parser.add_argument("--data_path", required=True, nargs="+",
                        help="One or more CSV/Excel data files")
    parser.add_argument("--output_dir", default="models/ehs_distilbert",
                        help="Model save directory")
    parser.add_argument("--base_model", default="distilbert-base-uncased",
                        help="HuggingFace base model")
    parser.add_argument("--strategy", default="shared_v2",
                        choices=["shared", "shared_v2", "per_step"],
                        help="Training strategy (default: shared_v2)")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--batch_size", type=int,   default=16)
    parser.add_argument("--val_split",  type=float, default=0.1)

    # shared (original) args
    parser.add_argument("--epochs", type=int,   default=10)
    parser.add_argument("--lr",     type=float, default=2e-5)

    # shared_v2 and per_step args
    parser.add_argument("--freeze_epochs",   type=int,   default=3,
                        help="Epochs with frozen backbone")
    parser.add_argument("--unfreeze_epochs", type=int,   default=12,
                        help="Epochs with full fine-tuning")
    parser.add_argument("--backbone_lr",     type=float, default=1e-5,
                        help="LR for DistilBERT backbone (phase 2)")
    parser.add_argument("--head_lr",         type=float, default=5e-5,
                        help="LR for classification heads (phase 1)")
    parser.add_argument("--label_smoothing", type=float, default=0.1,
                        help="Label smoothing factor")

    args = parser.parse_args()
    csv_input = args.data_path if len(args.data_path) > 1 else args.data_path[0]

    print(f"Training on : {', '.join(args.data_path)}")
    print(f"Output dir  : {args.output_dir}")
    print(f"Strategy    : {args.strategy}")
    print(f"Device      : {args.device}")
    print()

    if args.strategy == "shared_v2":
        train_improved(
            csv_path=csv_input,
            output_dir=args.output_dir,
            base_model=args.base_model,
            freeze_epochs=args.freeze_epochs,
            unfreeze_epochs=args.unfreeze_epochs,
            batch_size=args.batch_size,
            backbone_lr=args.backbone_lr,
            head_lr=args.head_lr,
            val_split=args.val_split,
            label_smoothing=args.label_smoothing,
            device=args.device,
        )
    elif args.strategy == "per_step":
        train_per_step(
            csv_path=csv_input,
            output_dir=args.output_dir,
            base_model=args.base_model,
            freeze_epochs=args.freeze_epochs,
            unfreeze_epochs=args.unfreeze_epochs,
            batch_size=args.batch_size,
            backbone_lr=args.backbone_lr,
            head_lr=args.head_lr,
            val_split=args.val_split,
            label_smoothing=args.label_smoothing,
            device=args.device,
        )
    else:
        train(
            csv_path=csv_input,
            output_dir=args.output_dir,
            base_model=args.base_model,
            epochs=args.epochs,
            batch_size=args.batch_size,
            lr=args.lr,
            val_split=args.val_split,
            device=args.device,
        )


if __name__ == "__main__":
    main()
