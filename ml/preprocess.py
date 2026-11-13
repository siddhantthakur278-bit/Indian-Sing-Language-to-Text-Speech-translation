"""
ISL Landmark Preprocessing, Normalization and Data Augmentation Module

Implements Contract 7.1:
- Normalization: translates coordinates relative to the mid-shoulder center (landmarks 11 & 12)
  and scales by Euclidean shoulder distance.
- Sequence shape: (seq_len, 258)
- Signer-wise dataset partitioning to prevent identity data leakage.
"""

import os
import glob
import re
import argparse
import numpy as np
from typing import Tuple, List, Dict


def normalize_landmarks(seq: np.ndarray) -> np.ndarray:
    """
    Normalizes a sequence of shape (T, 258) according to Integration Contract 7.1:
    - 0:132   : Pose (33 points * 4 values: x, y, z, visibility)
    - 132:195 : Left Hand (21 points * 3 values: x, y, z)
    - 195:258 : Right Hand (21 points * 3 values: x, y, z)

    Transforms:
    1. Center: midpoint of left shoulder (idx 11) and right shoulder (idx 12)
    2. Scale: Euclidean distance between left and right shoulders (+ 1e-6)
    3. Center-subtraction and scale-division for pose (x, y, z) and both hands (x, y, z)
    4. Visibility column is preserved unmodified.
    """
    out = seq.copy()
    num_frames = len(seq)

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

    # Apply normalization only to detected hand points (non-zero points)
    lh_mask = (np.abs(lh).sum(axis=-1, keepdims=True) > 1e-5).astype(np.float32)
    rh_mask = (np.abs(rh).sum(axis=-1, keepdims=True) > 1e-5).astype(np.float32)

    lh_norm = ((lh - center[:, None, :]) / scale[:, None, :]) * lh_mask
    rh_norm = ((rh - center[:, None, :]) / scale[:, None, :]) * rh_mask

    # Flatten and concatenate back to (T, 258)
    norm_seq = np.concatenate([
        pose.reshape(num_frames, 132),
        lh_norm.reshape(num_frames, 63),
        rh_norm.reshape(num_frames, 63)
    ], axis=1).astype(np.float32)

    return norm_seq


# Alias for contract compliance
normalize = normalize_landmarks


def augment_sequence(seq: np.ndarray,
                     scale_range: Tuple[float, float] = (0.9, 1.1),
                     rotation_range_deg: float = 10.0,
                     jitter_std: float = 0.015,
                     time_warp_range: Tuple[float, float] = (0.85, 1.15),
                     frame_dropout_prob: float = 0.08,
                     noise_std: float = 0.008) -> np.ndarray:
    """Applies realistic data augmentations to a normalized (30, 258) sequence."""
    aug = seq.copy()
    T, D = aug.shape

    # 1. Random Spatial Scaling
    scale_factor = np.random.uniform(scale_range[0], scale_range[1])
    aug[:, :132] = aug[:, :132] * scale_factor  # Note: visibility also scaled slightly, or we scale only xyz
    # Rescale xyz specifically:
    pose = aug[:, :132].reshape(-1, 33, 4)
    pose[:, :, :3] *= scale_factor
    aug[:, :132] = pose.reshape(-1, 132)
    aug[:, 132:] *= scale_factor

    # 2. Random 2D Rotation (in X-Y plane around center 0,0)
    theta = np.radians(np.random.uniform(-rotation_range_deg, rotation_range_deg))
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    rot_mat = np.array([[cos_t, -sin_t], [sin_t, cos_t]], dtype=np.float32)

    # Rotate Pose X-Y
    pose_xy = pose[:, :, :2].reshape(-1, 2)
    pose[:, :, :2] = (pose_xy @ rot_mat).reshape(-1, 33, 2)
    aug[:, :132] = pose.reshape(-1, 132)

    # Rotate Hands X-Y
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

    # 5. Frame Dropout (simulate tracking dropouts)
    dropout_mask = np.random.rand(T) < frame_dropout_prob
    if np.any(dropout_mask) and not np.all(dropout_mask):
        valid_indices = np.where(~dropout_mask)[0]
        for col in range(D):
            aug[dropout_mask, col] = np.interp(np.where(dropout_mask)[0], valid_indices, aug[valid_indices, col])

    # 6. Subtle Gaussian Noise
    noise = np.random.normal(0, noise_std, size=aug.shape).astype(np.float32)
    aug += noise

    return aug


def extract_signer_id(filename: str) -> str:
    """Extracts signer identifier from filenames like 'HELLO_p01_003.npy' or 'P2_WATER_01.npy'."""
    basename = os.path.basename(filename)
    match = re.search(r'[pP](\d+)', basename)
    if match:
        return f"p{int(match.group(1)):02d}"
    return "p00"  # default fallback


def signer_wise_split(file_list: List[str],
                      train_signers: List[str],
                      val_signers: List[str],
                      test_signers: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """Splits file paths strictly based on signer ID."""
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
            # If unspecified signer, place in train
            train_files.append(f)

    return train_files, val_files, test_files
