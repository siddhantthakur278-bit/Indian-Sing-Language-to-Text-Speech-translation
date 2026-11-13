"""
ISL Dataset Audit & Statistics Script
Analyzes data/raw, data/processed, and data/metadata.csv to report class distributions,
clip counts, signer distributions, split ratios, and class imbalances.
"""

import os
import re
import csv
import json
import argparse
from collections import defaultdict, Counter


def audit_metadata(metadata_path: str = "data/metadata.csv"):
    """Audits the metadata.csv catalog for split distribution and quality flags."""
    if not os.path.exists(metadata_path):
        print(f"[Warning] Metadata file {metadata_path} not found.")
        return

    print("\n" + "=" * 65)
    print(f"METADATA CATALOG AUDIT: {metadata_path}")
    print("=" * 65)

    split_counts = defaultdict(int)
    signer_splits = defaultdict(set)
    quality_flags = defaultdict(int)
    source_counts = defaultdict(int)
    gloss_counts = defaultdict(int)

    with open(metadata_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            split = row.get("split", "unknown")
            signer = row.get("signer_id", "unknown")
            flag = row.get("quality_flag", "valid")
            source = row.get("source", "unknown")
            gloss = row.get("gloss", "unknown")

            split_counts[split] += 1
            signer_splits[split].add(signer)
            quality_flags[flag] += 1
            source_counts[source] += 1
            gloss_counts[gloss] += 1

    total = sum(split_counts.values())
    print(f"Total Registered Samples : {total}")
    print(f"Unique Gloss Classes     : {len(gloss_counts)}")
    print("-" * 65)
    print("Dataset Split Distribution:")
    for split, count in sorted(split_counts.items()):
        signers = sorted(list(signer_splits[split]))
        pct = (count / total * 100) if total > 0 else 0
        print(f"  * {split.upper():<6}: {count:>4} samples ({pct:>5.1f}%) | Signers: {', '.join(signers)}")
    print("-" * 65)
    print("Quality & Source Summary:")
    print(f"  * Sources : {dict(source_counts)}")
    print(f"  * Quality : {dict(quality_flags)}")
    print("=" * 65)


def audit_dataset(data_dir: str = "data/raw", classes_path: str = "data/classes.json"):
    if not os.path.exists(classes_path):
        print(f"Error: {classes_path} not found.")
        return

    with open(classes_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    classes = meta["classes"]

    print("=" * 65)
    print(f"ISL DATASET AUDIT SUMMARY: {data_dir}")
    print("=" * 65)

    if not os.path.exists(data_dir):
        print(f"Directory {data_dir} does not exist yet. Create and populate it with recordings.")
        return

    found_classes = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    
    class_counts = {}
    signer_distribution = defaultdict(int)
    missing_classes = []

    for cls in classes:
        cls_dir = os.path.join(data_dir, cls)
        if os.path.exists(cls_dir):
            files = [f for f in os.listdir(cls_dir) if f.endswith(".mp4") or f.endswith(".npy")]
            class_counts[cls] = len(files)
            for f in files:
                m = re.search(r'[pP](\d+)', f)
                if m:
                    signer_id = f"p{int(m.group(1)):02d}"
                    signer_distribution[signer_id] += 1
        else:
            missing_classes.append(cls)
            class_counts[cls] = 0

    total_clips = sum(class_counts.values())
    print(f"Total Vocabulary Classes Expected : {len(classes)}")
    print(f"Classes with Active Data          : {len(found_classes)}")
    print(f"Classes with 0 Samples            : {len(missing_classes)}")
    print(f"Total Video/Sequence Clips        : {total_clips}")
    print("-" * 65)
    
    if signer_distribution:
        print("Signer Distribution:")
        for s_id, count in sorted(signer_distribution.items()):
            print(f"  • Signer {s_id}: {count} clips ({count / total_clips * 100:.1f}%)")
        print("-" * 65)

    sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
    print("Class Representation Overview:")
    for cls, count in sorted_classes[:10]:
        status = "✅ OK" if count >= 30 else ("⚠️ Low" if count > 0 else "❌ Empty")
        print(f"  {cls:<20} : {count:>4} clips  [{status}]")
    if len(sorted_classes) > 10:
        print("  ...")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit ISL dataset")
    parser.add_argument("--dir", type=str, default="data/raw", help="Folder to audit (data/raw or data/processed)")
    parser.add_argument("--classes", type=str, default="data/classes.json", help="Path to classes.json")
    parser.add_argument("--metadata", type=str, default="data/metadata.csv", help="Path to metadata.csv")
    args = parser.parse_args()
    audit_dataset(args.dir, args.classes)
    if os.path.exists(args.metadata):
        audit_metadata(args.metadata)
