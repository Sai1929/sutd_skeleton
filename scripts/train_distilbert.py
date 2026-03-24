#!/usr/bin/env python3
"""
CLI training script for the EHS DistilBERT recommendation model.

Usage:
    python scripts/train_distilbert.py \
        --data_path data/inspection_dataset.csv \
        --output_dir models/ehs_distilbert \
        --epochs 5 \
        --batch_size 16 \
        --lr 2e-5 \
        --device cpu
"""
import argparse
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml.training.trainer import train


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune EHS DistilBERT")
    parser.add_argument("--data_path", required=True, help="Path to inspection CSV")
    parser.add_argument("--output_dir", default="models/ehs_distilbert", help="Model save directory")
    parser.add_argument("--base_model", default="distilbert-base-uncased", help="HuggingFace base model")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--val_split", type=float, default=0.1)
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    args = parser.parse_args()

    print(f"Training on: {args.data_path}")
    print(f"Output dir:  {args.output_dir}")
    print(f"Device:      {args.device}")

    train(
        csv_path=args.data_path,
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
