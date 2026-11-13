"""
ISL Landmark Preprocessing, Normalization and Data Augmentation Module
=====================================================================
Author: Parth (Data & ML Track)

This module implements landmark normalization and data splitting according to
Integration Contract 7.1 (AGENTS.md & AGENTS_PARTH_ML.md):
- Sequence shape: (T, 258) where T is typically 30 frames.
- Vector layout per frame:
    * 0:132   : Pose landmarks (33 points * 4 values: x, y, z, visibility)
    * 132:195 : Left hand landmarks (21 points * 3 values: x, y, z)
    * 195:258 : Right hand landmarks (21 points * 3 values: x, y, z)
- Normalization:
    * Subtracts the mid-shoulder midpoint: (left_shoulder + right_shoulder) / 2
    * Divides by shoulder Euclidean distance (+ 1e-6 epsilon for numerical stability)
    * Leaves visibility values untouched
    * Missing hands (zero-filled) remain strictly 0.0 without NaNs or infinities
- Supports both NumPy vectorization and pure-Python standard library fallback.
"""

import os
import sys
import math
import json
import re
import argparse
from typing import Tuple, List, Union

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# =============================================================================
# 1. Pure Python Normalization (Fallback / Zero-Dependency Mode)
# =============================================================================
def normalize_frame_pure_python(frame: List[float]) -> List[float]:
    """
    Normalizes a single 258-dimensional frame using pure Python arithmetic.
    Ensures missing hands remain strictly 0.0 and no NaNs are produced.
    """
    out = list(frame)
    # Left shoulder: landmark 11 -> indices 44, 45, 46
    # Right shoulder: landmark 12 -> indices 48, 49, 50
    ls_x, ls_y, ls_z = frame[44], frame[45], frame[46]
    rs_x, rs_y, rs_z = frame[48], frame[49], frame[50]

    center_x = (ls_x + rs_x) / 2.0
    center_y = (ls_y + rs_y) / 2.0
    center_z = (ls_z + rs_z) / 2.0

    dx = ls_x - rs_x
    dy = ls_y - rs_y
    dz = ls_z - rs_z
    scale = math.sqrt(dx * dx + dy * dy + dz * dz) + 1e-6

    # 1. Normalize 33 pose landmarks (x, y, z only; visibility at idx+3 unchanged)
    for i in range(33):
        idx = i * 4
        out[idx] = (frame[idx] - center_x) / scale
        out[idx + 1] = (frame[idx + 1] - center_y) / scale
        out[idx + 2] = (frame[idx + 2] - center_z) / scale

    # 2. Normalize 21 left hand landmarks (indices 132 to 194)
    # Absent hands are zero-filled; if magnitude is near zero, keep strictly 0.0
    for i in range(21):
        idx = 132 + i * 3
        hx, hy, hz = frame[idx], frame[idx + 1], frame[idx + 2]
        if abs(hx) > 1e-5 or abs(hy) > 1e-5 or abs(hz) > 1e-5:
            out[idx] = (hx - center_x) / scale
            out[idx + 1] = (hy - center_y) / scale
            out[idx + 2] = (hz - center_z) / scale
        else:
            out[idx] = 0.0
            out[idx + 1] = 0.0
            out[idx + 2] = 0.0

    # 3. Normalize 21 right hand landmarks (indices 195 to 257)
    for i in range(21):
        idx = 195 + i * 3
        hx, hy, hz = frame[idx], frame[idx + 1], frame[idx + 2]
        if abs(hx) > 1e-5 or abs(hy) > 1e-5 or abs(hz) > 1e-5:
            out[idx] = (hx - center_x) / scale
            out[idx + 1] = (hy - center_y) / scale
            out[idx + 2] = (hz - center_z) / scale
        else:
            out[idx] = 0.0
            out[idx + 1] = 0.0
            out[idx + 2] = 0.0

    return out


# =============================================================================
# 2. Vectorized NumPy Normalization (Fast Mode)
# =============================================================================
def normalize_landmarks_numpy(seq: "np.ndarray") -> "np.ndarray":
    """
    Vectorized normalization for a 2D numpy array of shape (T, 258).
    Strictly preserves zeros for absent hands and ensures no NaNs or Infs.
    """
    out = np.array(seq, dtype=np.float32).copy()
    num_frames = len(out)

    # Pose: shape (T, 33, 4)
    pose = out[:, :132].reshape(-1, 33, 4)

    # Shoulders (index 11: left shoulder, index 12: right shoulder)
    ls = pose[:, 11, :3]  # (T, 3)
    rs = pose[:, 12, :3]  # (T, 3)

    center = (ls + rs) / 2.0  # (T, 3)
    scale = np.linalg.norm(ls - rs, axis=1, keepdims=True) + 1e-6  # (T, 1)

    # Normalize Pose (x, y, z) while leaving visibility unchanged
    pose[:, :, :3] = (pose[:, :, :3] - center[:, None, :]) / scale[:, None, :]

    # Hands: Left (T, 21, 3), Right (T, 21, 3)
    lh = out[:, 132:195].reshape(-1, 21, 3)
    rh = out[:, 195:258].reshape(-1, 21, 3)

    # Hand detection masks: true if hand is present (non-zero coordinates)
    lh_mask = (np.abs(lh).sum(axis=-1, keepdims=True) > 1e-5)
    rh_mask = (np.abs(rh).sum(axis=-1, keepdims=True) > 1e-5)

    # Normalize detected points; absent hands are strictly set to 0.0
    lh_norm = np.where(lh_mask, (lh - center[:, None, :]) / scale[:, None, :], 0.0)
    rh_norm = np.where(rh_mask, (rh - center[:, None, :]) / scale[:, None, :], 0.0)

    # Recombine normalized slices back into (T, 258)
    norm_seq = np.concatenate([
        pose.reshape(num_frames, 132),
        lh_norm.reshape(num_frames, 63),
        rh_norm.reshape(num_frames, 63)
    ], axis=1).astype(np.float32)

    # Guard against any numerical edge-case NaNs or infinities
    return np.nan_to_num(norm_seq, nan=0.0, posinf=0.0, neginf=0.0)


# =============================================================================
# 3. Main Normalization Entry Point (Universal)
# =============================================================================
def normalize_landmarks(seq):
    """
    Main normalization entry point supporting NumPy arrays or Python lists.
    Guarantees Integration Contract 7.1 compliance.
    """
    if HAS_NUMPY and isinstance(seq, np.ndarray):
        return normalize_landmarks_numpy(seq)
    else:
        return [normalize_frame_pure_python(frame) for frame in seq]


# Alias for contract compliance
normalize = normalize_landmarks


# =============================================================================
# 4. Data Augmentation (NumPy Only, for Training)
# =============================================================================
def augment_sequence(seq: "np.ndarray",
                     scale_range: Tuple[float, float] = (0.9, 1.1),
                     rotation_range_deg: float = 10.0,
                     jitter_std: float = 0.015,
                     time_warp_range: Tuple[float, float] = (0.85, 1.15),
                     frame_dropout_prob: float = 0.08,
                     noise_std: float = 0.008) -> "np.ndarray":
    """Applies realistic spatial and temporal data augmentations to a normalized sequence."""
    if not HAS_NUMPY or not isinstance(seq, np.ndarray):
        return seq

    aug = seq.copy()
    T, D = aug.shape

    # 1. Random Spatial Scaling
    scale_factor = np.random.uniform(scale_range[0], scale_range[1])
    pose = aug[:, :132].reshape(-1, 33, 4)
    pose[:, :, :3] *= scale_factor
    aug[:, :132] = pose.reshape(-1, 132)
    aug[:, 132:] *= scale_factor

    # 2. Random 2D Rotation (in X-Y plane)
    theta = np.radians(np.random.uniform(-rotation_range_deg, rotation_range_deg))
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    rot_mat = np.array([[cos_t, -sin_t], [sin_t, cos_t]], dtype=np.float32)

    pose_xy = pose[:, :, :2].reshape(-1, 2)
    pose[:, :, :2] = (pose_xy @ rot_mat).reshape(-1, 33, 2)
    aug[:, :132] = pose.reshape(-1, 132)

    for start_idx in (132, 195):
        hand = aug[:, start_idx:start_idx + 63].reshape(-1, 21, 3)
        hand_xy = hand[:, :, :2].reshape(-1, 2)
        hand[:, :, :2] = (hand_xy @ rot_mat).reshape(-1, 21, 2)
        aug[:, start_idx:start_idx + 63] = hand.reshape(-1, 63)

    # 3. Translation Jitter
    shift = np.random.normal(0, jitter_std, size=(1, 3)).astype(np.float32)
    pose[:, :, :3] += shift
    aug[:, :132] = pose.reshape(-1, 132)
    aug[:, 132:195] += np.tile(shift, 21)
    aug[:, 195:258] += np.tile(shift, 21)

    # 4. Temporal Warping (Speed variation)
    warp_rate = np.random.uniform(time_warp_range[0], time_warp_range[1])
    new_len = max(5, int(T * warp_rate))
    warp_indices = np.linspace(0, T - 1, new_len)
    warped = np.zeros((T, D), dtype=np.float32)
    for col in range(D):
        warped[:, col] = np.interp(np.linspace(0, T - 1, T), warp_indices, np.interp(warp_indices, np.arange(T), aug[:, col]))
    aug = warped

    # 5. Frame Dropout
    dropout_mask = np.random.rand(T) < frame_dropout_prob
    if np.any(dropout_mask) and not np.all(dropout_mask):
        valid_indices = np.where(~dropout_mask)[0]
        for col in range(D):
            aug[dropout_mask, col] = np.interp(np.where(dropout_mask)[0], valid_indices, aug[valid_indices, col])

    # 6. Subtle Gaussian Noise
    noise = np.random.normal(0, noise_std, size=aug.shape).astype(np.float32)
    aug += noise

    return aug


# =============================================================================
# 5. Signer Identification & Partitioning Helpers
# =============================================================================
def extract_signer_id(filename: str) -> str:
    """
    Extracts two-digit zero-padded signer identifier from clip filenames.
    Examples: 'HELLO_p01_003.npy' -> 'p01', 'WATER_p5_01.mp4' -> 'p05'.
    """
    basename = os.path.basename(filename)
    match = re.search(r'[pP](\d+)', basename)
    if match:
        return f"p{int(match.group(1)):02d}"
    return "p00"  # default fallback


def signer_wise_split(file_list: List[str],
                      train_signers: List[str],
                      val_signers: List[str],
                      test_signers: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """
    Splits file paths strictly based on signer ID to prevent identity data leakage.
    Never splits randomly by clip.
    """
    train_files, val_files, test_files = [], [], []

    for f in file_list:
        signer = extract_signer_id(f)
        if signer in train_signers:
            train_files.append(f)
        elif signer in val_signers:
            val_files.append(f)
        elif signer in test_signers:
            test_files.append(f)
        else:
            # If signer not explicitly partitioned, assign to train
            train_files.append(f)

    return train_files, val_files, test_files


# =============================================================================
# 6. Self-Verification Routine (--check)
# =============================================================================
def run_normalization_check() -> bool:
    """
    Verifies that the normalization implementation satisfies all Integration
    Contract 7.1 conditions:
    1. Shape is preserved at (30, 258).
    2. Mid-shoulder center translates to (0, 0, 0).
    3. Shoulder scale normalizes shoulder distance to 1.0.
    4. Missing hands remain strictly 0.0 with zero NaNs or infinities.
    5. Parity with sample_io.json reference data if available.
    """
    print("=" * 65)
    print("ISL PREPROCESSING & NORMALIZATION CONTRACT CHECK (--check)")
    print("=" * 65)

    # 1. Create a synthetic test sequence: 30 frames x 258 features
    # Pose: shoulders at known positions
    # Left hand: detected points
    # Right hand: all zeros (absent hand test)
    seq = [[0.0] * 258 for _ in range(30)]
    for f in range(30):
        # Left shoulder (landmark 11): (0.6, 0.4, 0.0, 1.0)
        seq[f][44], seq[f][45], seq[f][46], seq[f][47] = 0.6, 0.4, 0.0, 1.0
        # Right shoulder (landmark 12): (0.4, 0.4, 0.0, 1.0)
        seq[f][48], seq[f][49], seq[f][50], seq[f][51] = 0.4, 0.4, 0.0, 1.0
        # Left hand present: wrist at (0.5, 0.6, 0.1)
        seq[f][132], seq[f][133], seq[f][134] = 0.5, 0.6, 0.1
        # Right hand absent: indices 195 to 257 remain exactly 0.0

    norm_seq = normalize(seq)

    # Test 1: Shape check
    assert len(norm_seq) == 30, f"Expected 30 frames, got {len(norm_seq)}"
    assert len(norm_seq[0]) == 258, f"Expected 258 dimensions, got {len(norm_seq[0])}"
    print("[PASS] Sequence shape verified: (30, 258)")

    # Test 2: Mid-shoulder centering check
    f0 = norm_seq[0]
    ls_norm = [f0[44], f0[45], f0[46]]
    rs_norm = [f0[48], f0[49], f0[50]]
    mid_shoulder = [(ls_norm[i] + rs_norm[i]) / 2.0 for i in range(3)]
    assert all(abs(v) < 1e-5 for v in mid_shoulder), f"Mid-shoulder not centered: {mid_shoulder}"
    print(f"[PASS] Mid-shoulder centered at (0, 0, 0): {mid_shoulder}")

    # Test 3: Shoulder distance normalization check
    dist = math.sqrt(sum((ls_norm[i] - rs_norm[i]) ** 2 for i in range(3)))
    assert abs(dist - 1.0) < 1e-4, f"Normalized shoulder distance {dist} != 1.0"
    print(f"[PASS] Normalized shoulder distance scaled to 1.0: {dist:.6f}")

    # Test 4: Missing hands remain zero (zero-fill guarantee)
    right_hand_vals = [f0[idx] for idx in range(195, 258)]
    assert all(v == 0.0 for v in right_hand_vals), "Absent hand contains non-zero values!"
    assert not any(math.isnan(v) or math.isinf(v) for v in f0), "Normalized sequence contains NaN or Inf!"
    print("[PASS] Absent hand (Right Hand) strictly preserved as 0.0 (no NaNs or Infs)")

    # Test 5: Check parity with sample_io.json if file exists
    sample_io_path = os.path.join(os.path.dirname(__file__), "sample_io.json")
    if os.path.exists(sample_io_path):
        with open(sample_io_path, "r", encoding="utf-8") as f:
            sample_data = json.load(f)
        raw_samples = sample_data.get("raw", [])
        expected_samples = sample_data.get("normalized", [])
        max_diff = 0.0
        for s_idx, raw_s in enumerate(raw_samples):
            actual_norm = normalize(raw_s)
            exp_norm = expected_samples[s_idx]
            for f_idx in range(len(actual_norm)):
                for c_idx in range(len(actual_norm[f_idx])):
                    diff = abs(actual_norm[f_idx][c_idx] - exp_norm[f_idx][c_idx])
                    if diff > max_diff:
                        max_diff = diff
        assert max_diff < 1e-4, f"Parity difference {max_diff} exceeded 1e-4 tolerance!"
        print(f"[PASS] Parity verified against sample_io.json (max diff: {max_diff:.4e} < 1e-4)")

    print("-" * 65)
    print("ALL NORMALIZATION CONTRACT CHECKS PASSED SUCCESSFULLY!")
    print("=" * 65)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ISL Landmark Preprocessing & Verification")
    parser.add_argument("--check", action="store_true", help="Run contract verification self-check")
    args = parser.parse_args()

    if args.check or len(sys.argv) == 1:
        run_normalization_check()
    else:
        parser.print_help()
