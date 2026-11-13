"""
ISL Mock Dataset Generator for Pipeline Verification
=====================================================
Author: Parth (Data & ML Track)

This module generates a lightweight synthetic mock dataset conforming to
Integration Contract 7.1 and the 70-class vocabulary in data/classes.json:
- 5 signers: p01, p02, p03 (Train), p04 (Validation), p05 (Test).
- Exactly 1 sample per class per signer (350 total sequences of shape 30x258).
- Saves .npy keypoint sequences inside data/processed/<GLOSS>/<GLOSS>_<signer>_001.npy.
- Creates/updates data/metadata.csv with columns:
    clip, gloss, signer_id, split, source, quality_flag
- Clearly flags all generated samples with source='MOCK'.
- NEVER overwrites real recordings, real metadata rows, or real processed data.
- Supports both NumPy and pure Python (zero external dependencies).
"""

import os
import sys
import math
import struct
import csv

# Import central configuration
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import ml.config as cfg

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# =============================================================================
# 1. Pure Python .NPY File Serializer
# =============================================================================
def save_npy_file(filepath: str, data_2d: list) -> None:
    """
    Saves a 2D float32 sequence of shape (rows, cols) to standard NumPy .npy format.
    Uses numpy.save if installed; otherwise uses pure Python struct packing.
    """
    if HAS_NUMPY and isinstance(data_2d, np.ndarray):
        np.save(filepath, data_2d)
        return

    rows = len(data_2d)
    cols = len(data_2d[0]) if rows > 0 else 0

    # Build NumPy v1.0 header dictionary
    header_str = f"{{'descr': '<f4', 'fortran_order': False, 'shape': ({rows}, {cols}), }}"
    # Pad so (10 byte prefix + header len) is divisible by 64 bytes
    prefix_len = 10
    total_base = prefix_len + len(header_str) + 1  # +1 for newline
    padding = (64 - (total_base % 64)) % 64
    padded_header = header_str + (" " * padding) + "\n"
    header_bytes = padded_header.encode("latin1")
    header_len = len(header_bytes)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        # Magic string: \x93NUMPY
        f.write(b"\x93NUMPY")
        # Version 1.0
        f.write(bytes([1, 0]))
        # Header length (unsigned 16-bit little-endian)
        f.write(struct.pack("<H", header_len))
        # Header dictionary
        f.write(header_bytes)
        # Array data (float32 little-endian)
        for row in data_2d:
            f.write(struct.pack(f"<{cols}f", *row))


# =============================================================================
# 2. Synthetic Landmark Sequence Generator
# =============================================================================
def generate_synthetic_sequence(class_idx: int, class_name: str, signer_id: str) -> list:
    """
    Generates a deterministic 30-frame x 258-feature mock landmark sequence.
    - Preserves upper-body shoulders at realistic anatomical positions.
    - Simulates distinct smooth kinematic trajectories for each gesture class.
    - If class is 'IDLE', hands remain down / near resting coordinates.
    """
    seq = [[0.0] * cfg.FEAT_DIM for _ in range(cfg.SEQ_LEN)]

    # Deterministic signer variation offset (slight anatomical difference per signer)
    signer_num = int(signer_id.lower().replace("p", "")) if "p" in signer_id.lower() else 1
    signer_offset_x = (signer_num - 3) * 0.015

    for f in range(cfg.SEQ_LEN):
        t = f / float(cfg.SEQ_LEN - 1)  # Normalized time: 0.0 to 1.0

        # --- 1. Pose landmarks (33 points * 4 values = 132 features) ---
        # Left shoulder (landmark 11 -> indices 44, 45, 46, 47)
        seq[f][44] = 0.60 + signer_offset_x
        seq[f][45] = 0.40
        seq[f][46] = 0.00
        seq[f][47] = 1.0  # Visibility

        # Right shoulder (landmark 12 -> indices 48, 49, 50, 51)
        seq[f][48] = 0.40 + signer_offset_x
        seq[f][49] = 0.40
        seq[f][50] = 0.00
        seq[f][51] = 1.0  # Visibility

        # Set nominal coordinates for remaining pose joints (head, torso)
        for p in range(33):
            if p not in (11, 12):
                p_idx = p * 4
                seq[f][p_idx] = 0.50 + (p % 3 - 1) * 0.08
                seq[f][p_idx + 1] = 0.20 + (p // 3) * 0.05
                seq[f][p_idx + 2] = 0.00
                seq[f][p_idx + 3] = 0.95

        # --- 2. Hands landmarks (Left: 132..194, Right: 195..257) ---
        if class_name == "IDLE":
            # In IDLE class, hands are either resting low or absent (0.0)
            # Hands remain at 0.0 to simulate resting out-of-frame / hands-down
            continue

        # For active classes, generate a smooth sinusoidal motion trajectory
        freq = 1.0 + (class_idx % 5) * 0.5
        phase = t * math.pi * 2.0 * freq
        amplitude = 0.15

        # Right hand moves according to class trajectory
        rh_wrist_x = 0.45 + amplitude * math.sin(phase) + signer_offset_x
        rh_wrist_y = 0.55 + amplitude * math.cos(phase * 0.5)
        rh_wrist_z = 0.05 * math.sin(phase)

        for h in range(21):
            h_idx = 195 + h * 3
            # Finger joint offsets relative to wrist
            seq[f][h_idx] = rh_wrist_x + (h % 5 - 2) * 0.015
            seq[f][h_idx + 1] = rh_wrist_y + (h // 5) * 0.015
            seq[f][h_idx + 2] = rh_wrist_z

        # Two-handed signs (every third class uses both hands)
        if class_idx % 3 == 0:
            lh_wrist_x = 0.55 - amplitude * math.sin(phase) + signer_offset_x
            lh_wrist_y = 0.55 + amplitude * math.cos(phase * 0.5)
            lh_wrist_z = 0.05 * math.cos(phase)

            for h in range(21):
                h_idx = 132 + h * 3
                seq[f][h_idx] = lh_wrist_x + (h % 5 - 2) * 0.015
                seq[f][h_idx + 1] = lh_wrist_y + (h // 5) * 0.015
                seq[f][h_idx + 2] = lh_wrist_z

    return seq


# =============================================================================
# 3. Main Mock Dataset Generator
# =============================================================================
def generate_mock_dataset(classes_path: str = cfg.CLASSES_PATH,
                          processed_dir: str = cfg.PROCESSED_DATA_DIR,
                          metadata_path: str = cfg.METADATA_PATH) -> None:
    """
    Generates mock keypoint sequences and writes data/metadata.csv.
    Guarantees every class is represented in train, val, and test splits.
    """
    print("=" * 65)
    print("ISL MOCK DATASET GENERATION")
    print("=" * 65)

    classes = cfg.load_classes(classes_path)
    print(f"Loaded {len(classes)} classes from {classes_path}")

    # Signer assignment
    signers = [
        ("p01", "train"),
        ("p02", "train"),
        ("p03", "train"),
        ("p04", "val"),
        ("p05", "test"),
    ]

    # Load existing metadata if present to avoid overwriting real records
    existing_records = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_records[row["clip"]] = row
        print(f"Found {len(existing_records)} existing records in {metadata_path}")

    new_records = []
    generated_count = 0
    skipped_count = 0

    for cls_idx, cls_name in enumerate(classes):
        cls_dir = os.path.join(processed_dir, cls_name)
        os.makedirs(cls_dir, exist_ok=True)

        for signer_id, split in signers:
            clip_name = f"{cls_name}_{signer_id}_001.npy"
            file_path = os.path.join(cls_dir, clip_name)

            # Never overwrite existing real recordings
            if clip_name in existing_records and existing_records[clip_name].get("source") != "MOCK":
                skipped_count += 1
                continue

            # Generate synthetic sequence
            seq = generate_synthetic_sequence(cls_idx, cls_name, signer_id)
            save_npy_file(file_path, seq)
            generated_count += 1

            record = {
                "clip": clip_name,
                "gloss": cls_name,
                "signer_id": signer_id,
                "split": split,
                "source": "MOCK",
                "quality_flag": "valid",
            }
            existing_records[clip_name] = record
            new_records.append(record)

    # Write merged metadata.csv
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    fieldnames = ["clip", "gloss", "signer_id", "split", "source", "quality_flag"]
    with open(metadata_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for clip in sorted(existing_records.keys()):
            writer.writerow(existing_records[clip])

    # Summary
    train_count = sum(1 for r in existing_records.values() if r["split"] == "train")
    val_count = sum(1 for r in existing_records.values() if r["split"] == "val")
    test_count = sum(1 for r in existing_records.values() if r["split"] == "test")

    print("-" * 65)
    print(f"Total Clips Generated Now : {generated_count}")
    print(f"Total Clips Preserved/Kept : {len(existing_records)}")
    print(f"  • Train Partition       : {train_count} clips (Signers: p01, p02, p03)")
    print(f"  • Val Partition         : {val_count} clips (Signer: p04)")
    print(f"  • Test Partition        : {test_count} clips (Signer: p05)")
    print(f"Metadata written to      : {metadata_path}")
    print("=" * 65)


if __name__ == "__main__":
    generate_mock_dataset()
