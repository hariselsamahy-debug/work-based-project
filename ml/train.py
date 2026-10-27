"""Train one YOLO detector. Same settings as the notebook run that produced the PPE model.

    python ml/train.py --data ml/configs/ppe.yaml --name ppe
"""
import argparse
from pathlib import Path

import torch
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--name", required=True, help="task name, e.g. ppe / fire_smoke / fall")
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    device = 0 if torch.cuda.is_available() else "cpu"
    print("Training device:", device)

    YOLO(args.model).train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        workers=4,
        device=device,
        patience=10,
        project=str(ROOT / "runs"),
        name=args.name,
        seed=42,
        plots=True,
        fliplr=0.5,
        degrees=10,
        translate=0.1,
        scale=0.3,
        hsv_h=0.015,
        hsv_s=0.5,
        hsv_v=0.3,
        mosaic=0.5,
        close_mosaic=10,
    )
    print(f"Done. Copy runs/{args.name}/weights/best.pt to models/{args.name}.pt")


if __name__ == "__main__":
    main()
