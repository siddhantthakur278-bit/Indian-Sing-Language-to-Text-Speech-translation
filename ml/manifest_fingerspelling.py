"""
Manifest Generator & Data Pipeline Validator for ISL Fingerspelling Dataset
Scans data/raw/fingerspelling/ and generates a comprehensive class breakdown and metadata catalog.
"""

import os
import json
import glob
from pathlib import Path

DATA_RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "fingerspelling"
OUTPUT_MANIFEST = Path(__file__).resolve().parent.parent / "data" / "fingerspelling_manifest.json"

def generate_manifest():
    print(f"🔍 Scanning dataset in: {DATA_RAW_DIR}")

    if not DATA_RAW_DIR.exists():
        print(f"❌ Error: {DATA_RAW_DIR} does not exist.")
        return

    classes = sorted([d.name for d in DATA_RAW_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")])
    class_counts = {}
    total_images = 0

    for cls in classes:
        cls_dir = DATA_RAW_DIR / cls
        images = list(cls_dir.glob("*.jpg")) + list(cls_dir.glob("*.jpeg")) + list(cls_dir.glob("*.png"))
        count = len(images)
        class_counts[cls] = count
        total_images += count

    manifest = {
        "dataset_name": "Indian Sign Language (ISL) Character-Level Dataset",
        "author": "Prathum Arikeri (with Stanford Researcher Khaled Jedoui)",
        "source": "https://www.kaggle.com/datasets/prathumarikeri/indian-sign-language-isl",
        "license": "CC BY-SA 4.0",
        "total_classes": len(classes),
        "total_images": total_images,
        "classes": classes,
        "class_distribution": class_counts,
        "classes_alphabet": [c for c in classes if c.isalpha()],
        "classes_numbers": [c for c in classes if c.isdigit()],
        "data_path": "data/raw/fingerspelling/",
        "feature_dimension": 126,
        "pipeline_target": "data/processed/landmark_dataset_with_orientation.csv"
    }

    with open(OUTPUT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"✅ Generated dataset manifest at: {OUTPUT_MANIFEST}")
    print(f"📊 Summary:")
    print(f"   • Total Classes: {len(classes)} ({len(manifest['classes_alphabet'])} Letters + {len(manifest['classes_numbers'])} Numbers)")
    print(f"   • Total Images: {total_images:,}")
    print(f"   • Min / Max per class: {min(class_counts.values())} / {max(class_counts.values())}")

if __name__ == "__main__":
    generate_manifest()
