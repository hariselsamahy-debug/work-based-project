"""Download a Roboflow dataset in YOLOv8 format. The API key comes from .env, never from code."""
import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from roboflow import Roboflow

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", type=int, required=True)
    parser.add_argument("--out", default=str(ROOT / "ml" / "datasets"))
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        raise SystemExit("ROBOFLOW_API_KEY is not set in .env")

    os.makedirs(args.out, exist_ok=True)
    os.chdir(args.out)
    project = Roboflow(api_key=api_key).workspace(args.workspace).project(args.project)
    dataset = project.version(args.version).download("yolov8")
    print("Downloaded to:", dataset.location)


if __name__ == "__main__":
    main()
