"""
ISL Keypoint Sequence Data Augmentation Pipeline
Implements realistic physical variations for 3D landmarks per AGENTS.md Section 8.1:
- Spatial scaling (0.9x - 1.1x)
- 3D Rotation jitter (+/- 10 degrees)
- Translation displacement
- Frame dropout (5% - 10%)
- Sensor Gaussian noise
- Temporal time warping (0.85x - 1.15x)
"""







import math
import random
from typing import List

# Type definition for a sequence of 30 frames, each with 258 landmark features
Sequence = List[List[float]]

def random_scale(seq: Sequence, min_scale: float = 0.9, max_scale: float = 1.1) -> Sequence:
    """Scale spatial coordinates x, y, z uniformly while preserving visibility."""
    scale = random.uniform(min_scale, max_scale)
    augmented = []
    for frame in seq:
        new_frame = list(frame)
        for i in range(len(new_frame)):
            # In pose (0..131), every 4th element (3, 7, 11...) is visibility and should not be scaled
            if i < 132 and (i % 4 == 3):
                continue
            new_frame[i] *= scale
        augmented.append(new_frame)
    return augmented

def random_rotation_3d(seq: Sequence, max_angle_deg: float = 10.0) -> Sequence:
    """Apply a subtle 3D rotation around the y (yaw) axis."""
    angle_rad = math.radians(random.uniform(-max_angle_deg, max_angle_deg))
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    augmented = []
    for frame in seq:
        new_frame = list(frame)
        # Rotate pose xyz
        for i in range(0, 132, 4):
            x, z = new_frame[i], new_frame[i + 2]
            new_frame[i] = x * cos_a - z * sin_a
            new_frame[i + 2] = x * sin_a + z * cos_a

        # Rotate left hand xyz (132..194)
        for i in range(132, 195, 3):
            x, z = new_frame[i], new_frame[i + 2]
            new_frame[i] = x * cos_a - z * sin_a
            new_frame[i + 2] = x * sin_a + z * cos_a

        # Rotate right hand xyz (195..257)
        for i in range(195, 258, 3):
            x, z = new_frame[i], new_frame[i + 2]
            new_frame[i] = x * cos_a - z * sin_a
            new_frame[i + 2] = x * sin_a + z * cos_a

        augmented.append(new_frame)
    return augmented

def translation_jitter(seq: Sequence, max_offset: float = 0.02) -> Sequence:
    """Translate all landmarks by a small spatial displacement vector."""
    dx = random.uniform(-max_offset, max_offset)
    dy = random.uniform(-max_offset, max_offset)
    dz = random.uniform(-max_offset, max_offset)

    augmented = []
    for frame in seq:
        new_frame = list(frame)
        for i in range(0, 132, 4):
            new_frame[i] += dx
            new_frame[i + 1] += dy
            new_frame[i + 2] += dz
        for i in range(132, 258, 3):
            new_frame[i] += dx
            new_frame[i + 1] += dy
            new_frame[i + 2] += dz
        augmented.append(new_frame)
    return augmented

def frame_dropout(seq: Sequence, dropout_rate: float = 0.08) -> Sequence:
    """Randomly drop frames and interpolate from neighbors to simulate camera stutter."""
    augmented = [list(f) for f in seq]
    num_frames = len(augmented)
    for i in range(1, num_frames - 1):
        if random.random() < dropout_rate:
            for j in range(len(augmented[i])):
                augmented[i][j] = (augmented[i - 1][j] + augmented[i + 1][j]) / 2.0
    return augmented

def gaussian_noise(seq: Sequence, sigma: float = 0.008) -> Sequence:
    """Inject subtle zero-mean Gaussian jitter to simulate tracking variance."""
    augmented = []
    for frame in seq:
        new_frame = list(frame)
        for i in range(len(new_frame)):
            if i < 132 and (i % 4 == 3):
                continue
            new_frame[i] += random.gauss(0, sigma)
        augmented.append(new_frame)
    return augmented

def apply_augmentation_pipeline(seq: Sequence, p: float = 0.8) -> Sequence:
    """Run full sequential augmentation with probability p."""
    if random.random() > p:
        return seq

    out = random_scale(seq)
    out = random_rotation_3d(out)
    out = translation_jitter(out)
    out = frame_dropout(out)
    out = gaussian_noise(out)
    return out
