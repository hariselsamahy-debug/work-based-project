"""Resize + augment a YOLO dataset (moved from the Colab notebook).

Polygon (segmentation) labels are converted to boxes. Class ids are written as
integers, which fixes the "5.0 0.50 ..." labels the notebook had to repair afterwards.

    python ml/preprocess.py --src ml/datasets/PPE-DETECTION-14 --dst ml/datasets/PPE-DETECTION-14-PREPROCESSED
"""
import argparse
import os
import shutil

import albumentations as A
import cv2
import numpy as np
from tqdm import tqdm

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


class YoloPreprocessor:
    def __init__(self, image_dir, annot_dir, save_image_dir, save_label_dir,
                 num_classes, img_size=640, apply_aug=True, num_augmented=2):
        self.image_dir = image_dir
        self.annot_dir = annot_dir
        self.save_image_dir = save_image_dir
        self.save_label_dir = save_label_dir
        self.num_classes = num_classes
        self.img_size = img_size
        self.apply_aug = apply_aug
        self.num_augmented = num_augmented

        os.makedirs(save_image_dir, exist_ok=True)
        os.makedirs(save_label_dir, exist_ok=True)

        self.transform = self._build_transform()
        self.resize_transform = A.Compose(
            [A.Resize(img_size, img_size)],
            bbox_params=A.BboxParams(format="yolo", label_fields=["category_ids"], min_visibility=0.0),
        )

    def _build_transform(self):
        aug_list = []
        if self.apply_aug:
            aug_list.extend([
                A.HorizontalFlip(p=0.5),
                A.RandomBrightnessContrast(p=0.4),
                A.Rotate(limit=10, p=0.3, border_mode=cv2.BORDER_CONSTANT),
                A.MotionBlur(p=0.1),
            ])
        aug_list.append(A.Resize(self.img_size, self.img_size))
        return A.Compose(
            aug_list,
            bbox_params=A.BboxParams(format="yolo", label_fields=["category_ids"],
                                     min_visibility=0.2, min_area=1.0),
        )

    def _load_labels(self, label_path):
        """Reads YOLO boxes (`cls x y w h`) and polygons (`cls x1 y1 ... xn yn`) as boxes."""
        bboxes, class_ids = [], []
        with open(label_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                parts = line.strip().split()
                if not parts:
                    continue
                where = f"{label_path}, line {line_number}"

                class_id = int(float(parts[0]))
                values = list(map(float, parts[1:]))
                if not 0 <= class_id < self.num_classes:
                    raise ValueError(f"Unexpected class ID {class_id} in {where}")
                if not np.isfinite(values).all():
                    raise ValueError(f"Non-finite coordinates in {where}")

                if len(values) == 4:
                    x, y, w, h = values
                elif len(values) >= 6 and len(values) % 2 == 0:
                    points = np.asarray(values, dtype=np.float64).reshape(-1, 2)
                    if ((points < 0) | (points > 1)).any():
                        raise ValueError(f"Polygon coordinates outside [0, 1] in {where}")
                    x_min, y_min = points.min(axis=0)
                    x_max, y_max = points.max(axis=0)
                    x, y = (x_min + x_max) / 2, (y_min + y_max) / 2
                    w, h = x_max - x_min, y_max - y_min
                else:
                    raise ValueError(f"Unsupported annotation in {where}: {len(values)} values")

                if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
                    raise ValueError(f"Invalid bounding box in {where}: {[x, y, w, h]}")
                if (x - w / 2 < -1e-6 or x + w / 2 > 1 + 1e-6
                        or y - h / 2 < -1e-6 or y + h / 2 > 1 + 1e-6):
                    raise ValueError(f"Bounding box exceeds image bounds in {where}")

                bboxes.append([float(x), float(y), float(w), float(h)])
                class_ids.append(class_id)
        return bboxes, class_ids

    def _save_sample(self, image, bboxes, class_ids, filename):
        image_path = os.path.join(self.save_image_dir, filename)
        label_path = os.path.join(self.save_label_dir, os.path.splitext(filename)[0] + ".txt")
        if not cv2.imwrite(image_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR)):
            raise IOError(f"Could not save image: {image_path}")
        with open(label_path, "w", encoding="utf-8") as f:
            for class_id, box in zip(class_ids, bboxes):
                f.write(f"{int(class_id)} " + " ".join(f"{v:.6f}" for v in box) + "\n")

    def process(self):
        filenames = sorted(f for f in os.listdir(self.image_dir) if f.lower().endswith(IMAGE_EXTENSIONS))
        stats = dict(original_images_saved=0, augmented_images_saved=0, missing_labels=0,
                     unreadable_images=0, empty_label_files=0)

        for filename in tqdm(filenames, desc=f"Processing {self.image_dir}"):
            label_path = os.path.join(self.annot_dir, os.path.splitext(filename)[0] + ".txt")
            if not os.path.isfile(label_path):
                stats["missing_labels"] += 1
                continue
            image_bgr = cv2.imread(os.path.join(self.image_dir, filename))
            if image_bgr is None:
                stats["unreadable_images"] += 1
                continue
            image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

            bboxes, class_ids = self._load_labels(label_path)
            if not bboxes:
                stats["empty_label_files"] += 1

            original = self.resize_transform(image=image, bboxes=bboxes, category_ids=class_ids)
            self._save_sample(original["image"], original["bboxes"], original["category_ids"], filename)
            stats["original_images_saved"] += 1

            if self.apply_aug:
                stem = os.path.splitext(filename)[0]
                for i in range(self.num_augmented):
                    aug = self.transform(image=image, bboxes=bboxes, category_ids=class_ids)
                    self._save_sample(aug["image"], aug["bboxes"], aug["category_ids"], f"{stem}_aug{i + 1}.jpg")
                    stats["augmented_images_saved"] += 1
        return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True, help="Roboflow YOLO export (has train/valid/test)")
    parser.add_argument("--dst", required=True)
    parser.add_argument("--num-classes", type=int, default=6)
    parser.add_argument("--img-size", type=int, default=640)
    parser.add_argument("--num-augmented", type=int, default=2)
    args = parser.parse_args()

    if os.path.exists(args.dst):
        shutil.rmtree(args.dst)

    for split in ["train", "valid", "test"]:
        src_images = os.path.join(args.src, split, "images")
        if not os.path.isdir(src_images):
            print(f"Skipping {split}: no images folder")
            continue
        is_train = split == "train"
        stats = YoloPreprocessor(
            image_dir=src_images,
            annot_dir=os.path.join(args.src, split, "labels"),
            save_image_dir=os.path.join(args.dst, split, "images"),
            save_label_dir=os.path.join(args.dst, split, "labels"),
            num_classes=args.num_classes,
            img_size=args.img_size,
            apply_aug=is_train,
            num_augmented=args.num_augmented if is_train else 0,
        ).process()
        print(split, stats)


if __name__ == "__main__":
    main()
