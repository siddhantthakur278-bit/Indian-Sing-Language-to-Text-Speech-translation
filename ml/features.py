"""
Kinematic Landmark Feature Engineering
======================================
Computes first-order (velocity), second-order (acceleration) temporal derivatives,
and spatial hand-relative displacement features from 30x258 normalized landmark
sequences to improve distinction between visually similar signs with distinct motion profiles.
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


def compute_hand_relative_displacement(sequence):
    """
    Computes spatial displacement vectors from nose (landmark 0) to:
    - Left wrist (left hand landmark 0, index 132..134)
    - Right wrist (right hand landmark 0, index 195..197)
    Returns (T, 6) feature matrix: [dx_left, dy_left, dz_left, dx_right, dy_right, dz_right].
    """
    if HAS_NUMPY and isinstance(sequence, np.ndarray):
        nose_xyz = sequence[:, 0:3]
        lh_wrist = sequence[:, 132:135]
        rh_wrist = sequence[:, 195:198]
        disp_lh = lh_wrist - nose_xyz
        disp_rh = rh_wrist - nose_xyz
        return np.concatenate([disp_lh, disp_rh], axis=-1)
    else:
        T = len(sequence)
        features = []
        for t in range(T):
            frame = sequence[t]
            nx, ny, nz = frame[0], frame[1], frame[2]
            lh_x, lh_y, lh_z = frame[132], frame[133], frame[134]
            rh_x, rh_y, rh_z = frame[195], frame[196], frame[197]
            features.append([
                lh_x - nx, lh_y - ny, lh_z - nz,
                rh_x - nx, rh_y - ny, rh_z - nz
            ])
        return features


def extract_multistream_features(normalized_seq, include_accel: bool = False, include_spatial: bool = False):
    """
    Concatenates normalized joint coordinates with velocity, optional acceleration,
    and optional spatial relative displacement streams.
    """
    vel = compute_velocity(normalized_seq)
    spatial = compute_hand_relative_displacement(normalized_seq) if include_spatial else None

    if HAS_NUMPY and isinstance(normalized_seq, np.ndarray):
        streams = [normalized_seq, vel]
        if include_accel:
            streams.append(compute_acceleration(vel))
        if spatial is not None:
            streams.append(spatial)
        return np.concatenate(streams, axis=-1)
    else:
        T = len(normalized_seq)
        combined = []
        acc = compute_acceleration(vel) if include_accel else None
        for t in range(T):
            row = list(normalized_seq[t]) + list(vel[t])
            if acc:
                row.extend(acc[t])
            if spatial:
                row.extend(spatial[t])
            combined.append(row)
        return combined
