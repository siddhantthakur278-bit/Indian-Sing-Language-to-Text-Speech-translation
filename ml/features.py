"""
Kinematic Landmark Feature Engineering
Computes first-order (velocity) and second-order (acceleration) temporal derivatives
from 30x258 normalized landmark sequences to improve distinction between
visually similar signs with distinct motion profiles.
Supports both NumPy and pure Python fallback.
"""

from typing import Union, List

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def compute_velocity(sequence):
    """
    Computes backward finite difference velocity across frames:
    v(t) = p(t) - p(t-1) with v(0) = 0.
    """
    if HAS_NUMPY and isinstance(sequence, np.ndarray):
        T, D = sequence.shape
        velocity = np.zeros_like(sequence, dtype=np.float32)
        if T > 1:
            velocity[1:] = sequence[1:] - sequence[:-1]
        return velocity
    else:
        # Pure Python fallback
        T = len(sequence)
        if T == 0:
            return []
        D = len(sequence[0])
        vel = [[0.0] * D]
        for t in range(1, T):
            vel.append([sequence[t][d] - sequence[t - 1][d] for d in range(D)])
        return vel


def compute_acceleration(velocity):
    """
    Computes second-order temporal difference (acceleration):
    a(t) = v(t) - v(t-1) with a(0) = 0.
    """
    if HAS_NUMPY and isinstance(velocity, np.ndarray):
        T, D = velocity.shape
        accel = np.zeros_like(velocity, dtype=np.float32)
        if T > 1:
            accel[1:] = velocity[1:] - velocity[:-1]
        return accel
    else:
        # Pure Python fallback
        T = len(velocity)
        if T == 0:
            return []
        D = len(velocity[0])
        accel = [[0.0] * D]
        for t in range(1, T):
            accel.append([velocity[t][d] - velocity[t - 1][d] for d in range(D)])
        return accel


def extract_multistream_features(normalized_seq, include_accel: bool = False):
    """
    Concatenates normalized joint coordinates with velocity streams.
    """
    vel = compute_velocity(normalized_seq)
    if HAS_NUMPY and isinstance(normalized_seq, np.ndarray):
        if include_accel:
            acc = compute_acceleration(vel)
            return np.concatenate([normalized_seq, vel, acc], axis=-1)
        return np.concatenate([normalized_seq, vel], axis=-1)
    else:
        T = len(normalized_seq)
        combined = []
        acc = compute_acceleration(vel) if include_accel else None
        for t in range(T):
            row = list(normalized_seq[t]) + list(vel[t])
            if acc:
                row.extend(acc[t])
            combined.append(row)
        return combined
