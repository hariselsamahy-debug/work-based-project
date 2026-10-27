"""Check every YOLO label file in a dataset and print per-class box counts.

    python ml/validate_labels.py ml/datasets/PPE-DETECTION-14-PREPROCESSED --names Gloves Hard_hat Mask Person Safety_boots Vest
"""
import argparse
import os
from collections import Counter

DEFAULT_NAMES = ["Gloves", "Hard_hat", "Mask", "Person", "Safety_boots", "Vest"]


def check_line(line, num_classes):
    """Returns (class_id, None) for a valid box line, or (None, reason)."""
    parts = line.split()
    if len(parts) != 5:
        return None, f"expected 5 values, got {len(parts)}"
    try:
        class_id = int(parts[0])
        x, y, w, h = map(float, parts[1:])
    except ValueError:
        return None, "non-numeric value (class id must be an integer)"
    if not 0 <= class_id < num_classes:
        return None, f"invalid class ID {class_id}"
    if not all(0 <= v <= 1 for v in (x, y, w, h)):
        return None, "coordinate outside [0,1]"
    if w <= 0 or h <= 0:
        return None, "non-positive box size"
    if x - w / 2 < -1e-6 or x + w / 2 > 1 + 1e-6 or y - h / 2 < -1e-6 or y + h / 2 > 1 + 1e-6:
        return None, "box outside image bounds"
    return class_id, None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    parser.add_argument("--names", nargs="+", default=DEFAULT_NAMES)
    args = parser.parse_args()

    errors, counts = [], Counter()
    checked = empty = 0
    for split in ["train", "valid", "test"]:
        image_dir = os.path.join(args.root, split, "images")
        label_dir = os.path.join(args.root, split, "labels")
        if not os.path.isdir(image_dir):
            continue
        for image in os.listdir(image_dir):
            stem = os.path.splitext(image)[0]
            label_path = os.path.join(label_dir, stem + ".txt")
            if not os.path.isfile(label_path):
                errors.append(f"{split}: missing label for {stem}")
                continue
            checked += 1
            with open(label_path, encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
            if not lines:
                empty += 1
            for line_no, line in enumerate(lines, start=1):
                class_id, reason = check_line(line, len(args.names))
                if reason:
                    errors.append(f"{split}/{stem}.txt:{line_no} {reason}")
                else:
                    counts[(split, class_id)] += 1

    print("Label files checked:", checked)
    print("Empty label files:", empty)
    print("Valid boxes:", sum(counts.values()))
    for split in ["train", "valid", "test"]:
        print(f"\n{split}:")
        for class_id, name in enumerate(args.names):
            print(f"  {name}: {counts[(split, class_id)]}")
    print("\nValidation errors:", len(errors))
    for error in errors[:20]:
        print("-", error)
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
