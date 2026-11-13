"""
ISL Dataset Audit & Statistics Script
Analyzes data/raw, data/processed, and data/metadata.csv to report class distributions,
clip counts, signer distributions, split ratios, and class imbalances.
"""

import os
import re
import csv
import json
import math
import struct
import argparse
from collections import defaultdict, Counter
from typing import Tuple, Dict, Any, Optional


def read_npy_metadata(file_path: str) -> Dict[str, Any]:
    """
    Reads shape, dtype, and integrity of a .npy file without external dependencies.
    Checks for file corruption, NaNs, and Infs using standard library struct/math.
    """
    with open(file_path, "rb") as f:
        magic = f.read(6)
        if magic != b"\x93NUMPY":
            return {"valid": False, "error": "Invalid .npy magic header"}

        major, minor = f.read(2)
        if major == 1:
            header_len = struct.unpack("<H", f.read(2))[0]
        elif major == 2:
            header_len = struct.unpack("<I", f.read(4))[0]
        else:
            return {"valid": False, "error": f"Unsupported .npy version {major}.{minor}"}

        header_bytes = f.read(header_len)
        header_str = header_bytes.decode("latin1").strip()

        # Parse shape from header string: e.g. 'shape': (30, 258),
        shape_match = re.search(r"'shape':\s*\(([^)]*)\)", header_str)
        if not shape_match:
            return {"valid": False, "error": "Unable to parse shape from .npy header"}

        shape_parts = [p.strip() for p in shape_match.group(1).split(",") if p.strip()]
        shape = tuple(int(p) for p in shape_parts)

        # Parse dtype: e.g. 'descr': '<f4'
        descr_match = re.search(r"'descr':\s*'([^']+)'", header_str)
        descr = descr_match.group(1) if descr_match else "unknown"

        # Verify numeric content (no NaNs or Infs)
        num_elements = 1
        for dim in shape:
            num_elements *= dim

        raw_payload = f.read()
        expected_bytes = num_elements * 4  # for float32 (4 bytes per element)
        has_nan = False
        has_inf = False

        if descr in ("<f4", "f4") and len(raw_payload) == expected_bytes:
            values = struct.unpack(f"<{num_elements}f", raw_payload)
            for v in values:
                if math.isnan(v):
                    has_nan = True
                    break
                if math.isinf(v):
                    has_inf = True
                    break

        return {
            "valid": True,
            "shape": shape,
            "descr": descr,
            "has_nan": has_nan,
            "has_inf": has_inf,
        }


def validate_dataset(data_dir: str = "data/processed",
                     classes_path: str = "data/classes.json",
                     expected_shape: Tuple[int, int] = (30, 258)) -> bool:
    """
    Validates all landmark sequence files in data_dir against Contract 7.1:
    - Files have valid .npy format
    - Shape matches expected_shape (default: 30, 258)
    - Zero NaNs or Infs
    - Directory names map directly to classes.json
    """
    print("\n" + "=" * 65)
    print(f"ISL DATASET INTEGRITY VALIDATION: {data_dir}")
    print("=" * 65)

    if not os.path.exists(classes_path):
        print(f"[FAIL] Classes file not found: {classes_path}")
        return False

    with open(classes_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    classes_set = set(meta.get("classes", []))

    if not os.path.exists(data_dir):
        print(f"[FAIL] Data directory not found: {data_dir}")
        return False

    total_scanned = 0
    valid_count = 0
    shape_mismatch = 0
    nan_inf_count = 0
    corrupt_count = 0
    uncataloged_classes = set()

    for root, _, files in os.walk(data_dir):
        cls_name = os.path.basename(root)
        if root == data_dir:
            continue
        if cls_name not in classes_set:
            uncataloged_classes.add(cls_name)

        for f in files:
            if not f.endswith(".npy"):
                continue
            total_scanned += 1
            f_path = os.path.join(root, f)
            meta_info = read_npy_metadata(f_path)

            if not meta_info.get("valid"):
                corrupt_count += 1
            elif meta_info.get("shape") != expected_shape:
                shape_mismatch += 1
            elif meta_info.get("has_nan") or meta_info.get("has_inf"):
                nan_inf_count += 1
            else:
                valid_count += 1

    print(f"Total .npy Files Scanned : {total_scanned}")
    print(f"Valid Contract Sequences : {valid_count} (shape: {expected_shape})")
    print(f"Shape Mismatches         : {shape_mismatch}")
    print(f"Corrupt / Unreadable     : {corrupt_count}")
    print(f"NaN or Inf Values        : {nan_inf_count}")
    if uncataloged_classes:
        print(f"Uncataloged Directories  : {uncataloged_classes}")
    print("-" * 65)

    all_passed = (total_scanned > 0 and
                  valid_count == total_scanned and
                  shape_mismatch == 0 and
                  nan_inf_count == 0 and
                  corrupt_count == 0)

    verdict = "PASSED" if all_passed else "FAILED"
    print(f"Integrity Validation Verdict: [{verdict}]")
    print("=" * 65)
    return all_passed


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
    parser = argparse.ArgumentParser(description="Audit and validate ISL dataset")
    parser.add_argument("--dir", type=str, default="data/raw", help="Folder to audit (data/raw or data/processed)")
    parser.add_argument("--classes", type=str, default="data/classes.json", help="Path to classes.json")
    parser.add_argument("--metadata", type=str, default="data/metadata.csv", help="Path to metadata.csv")
    parser.add_argument("--validate", action="store_true", help="Perform deep shape and numeric validation on .npy files")
    args = parser.parse_args()

    if args.validate:
        validate_dataset(args.dir, args.classes)
    else:
        audit_dataset(args.dir, args.classes)
        if os.path.exists(args.metadata):
            audit_metadata(args.metadata)
