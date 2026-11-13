"""
Indian Sign Language Keypoint Extraction Pipeline
Extracts 258-dimensional MediaPipe Holistic landmark vectors per frame from sign videos
and resamples each video sequence to a fixed length of 30 frames.

Landmark Vector Layout (258 values):
- 0:132   : Pose landmarks (33 points * 4 values: x, y, z, visibility)
- 132:195 : Left hand landmarks (21 points * 3 values: x, y, z)
- 195:258 : Right hand landmarks (21 points * 3 values: x, y, z)
"""

import os
import sys
import glob
import logging
import argparse
from typing import Tuple, List

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import cv2
    import mediapipe as mp
    HAS_CV = True
except ImportError:
    HAS_CV = False

# Import central configuration
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import ml.config as cfg

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def extract_keypoints(results) -> "np.ndarray":
    """Extract and flatten pose and hand landmarks into a 258-dimensional float32 array."""
    if not HAS_NUMPY:
        raise RuntimeError("NumPy is required for landmark extraction.")

    if results.pose_landmarks:
        pose = np.array(
            [[p.x, p.y, p.z, p.visibility] for p in results.pose_landmarks.landmark],
            dtype=np.float32,
        ).flatten()
    else:
        pose = np.zeros(cfg.POSE_LANDMARKS * 4, dtype=np.float32)

    if results.left_hand_landmarks:
        lh = np.array(
            [[p.x, p.y, p.z] for p in results.left_hand_landmarks.landmark],
            dtype=np.float32,
        ).flatten()
    else:
        lh = np.zeros(cfg.HAND_LANDMARKS * 3, dtype=np.float32)

    if results.right_hand_landmarks:
        rh = np.array(
            [[p.x, p.y, p.z] for p in results.right_hand_landmarks.landmark],
            dtype=np.float32,
        ).flatten()
    else:
        rh = np.zeros(cfg.HAND_LANDMARKS * 3, dtype=np.float32)

    return np.concatenate([pose, lh, rh])  # Exactly 258 values


def video_to_sequence(video_path: str, seq_len: int = cfg.SEQUENCE_LENGTH) -> Tuple["np.ndarray", float]:
    """
    Process video file, extract landmarks for all frames, and resample to seq_len.
    Returns (sequence_array of shape (seq_len, 258), hand_missing_ratio).
    """
    if not HAS_CV:
        raise RuntimeError("OpenCV and MediaPipe are required to process video clips.")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Unable to open video: {video_path}")

    raw_frames = []
    missing_hand_count = 0
    mp_holistic = mp.solutions.holistic

    with mp_holistic.Holistic(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1,
    ) as holistic:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(rgb)

            if not results.left_hand_landmarks and not results.right_hand_landmarks:
                missing_hand_count += 1

            raw_frames.append(extract_keypoints(results))

    cap.release()

    total_frames = len(raw_frames)
    if total_frames == 0:
        raise ValueError(f"No valid frames read from {video_path}")

    hand_missing_ratio = missing_hand_count / total_frames

    # Resample using linear space indexing to exactly seq_len frames
    indices = np.linspace(0, total_frames - 1, seq_len).astype(int)
    resampled_seq = np.array(raw_frames, dtype=np.float32)[indices]

    return resampled_seq, hand_missing_ratio


def batch_extract(
    src_dir: str = cfg.RAW_DATA_DIR,
    dst_dir: str = cfg.PROCESSED_DATA_DIR,
    seq_len: int = cfg.SEQUENCE_LENGTH,
    hand_threshold: float = 0.5,
    skip_existing: bool = True,
    log_file: str = "data/quality_audit.log",
):
    """Batch extract keypoints from video directory to numpy arrays with resume capability."""
    os.makedirs(dst_dir, exist_ok=True)
    if not os.path.exists(src_dir):
        logger.warning(f"Source directory {src_dir} does not exist.")
        return

    sign_dirs = [d for d in os.listdir(src_dir) if os.path.isdir(os.path.join(src_dir, d))]

    if not sign_dirs:
        logger.warning(f"No sign subdirectories found in {src_dir}")
        return

    logger.info(f"Found {len(sign_dirs)} sign classes in {src_dir}")

    total_processed = 0
    total_skipped = 0
    warnings_list = []

    for sign in sorted(sign_dirs):
        sign_src = os.path.join(src_dir, sign)
        sign_dst = os.path.join(dst_dir, sign)
        os.makedirs(sign_dst, exist_ok=True)

        video_files = glob.glob(os.path.join(sign_src, "*.mp4")) + glob.glob(os.path.join(sign_src, "*.avi"))
        logger.info(f"Processing class [{sign}] with {len(video_files)} video clips...")

        for v_path in video_files:
            clip_name = os.path.splitext(os.path.basename(v_path))[0]
            out_file = os.path.join(sign_dst, f"{clip_name}.npy")

            if skip_existing and os.path.exists(out_file):
                total_skipped += 1
                continue

            try:
                seq, missing_ratio = video_to_sequence(v_path, seq_len=seq_len)
                np.save(out_file, seq)
                total_processed += 1

                if missing_ratio > hand_threshold:
                    warning_msg = f"{clip_name}: {missing_ratio*100:.1f}% frames missing hands (> threshold {hand_threshold*100:.0f}%)"
                    logger.warning(warning_msg)
                    warnings_list.append(warning_msg)
            except Exception as e:
                logger.error(f"Failed to process {v_path}: {e}")

    logger.info(f"Keypoint extraction finished. Processed: {total_processed}, Skipped existing: {total_skipped}.")
    if warnings_list:
        logger.warning(f"{len(warnings_list)} clips flagged for low hand visibility.")
        with open(log_file, "a", encoding="utf-8") as f:
            for w in warnings_list:
                f.write(w + "\n")
        logger.info(f"Quality warnings logged to {log_file}")


def parse_args():
    parser = argparse.ArgumentParser(description="Extract MediaPipe keypoints from ISL video clips")
    parser.add_argument("--src", type=str, default=cfg.RAW_DATA_DIR, help="Source folder containing per-sign video subdirectories")
    parser.add_argument("--dst", type=str, default=cfg.PROCESSED_DATA_DIR, help="Destination folder for .npy sequence outputs")
    parser.add_argument("--seq_len", type=int, default=cfg.SEQUENCE_LENGTH, help="Fixed sequence length in frames (default: 30)")
    parser.add_argument("--hand_threshold", type=float, default=0.5, help="Flag clips with missing hands above this ratio")
    parser.add_argument("--no_skip", action="store_true", help="Force re-extraction of existing .npy files")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    batch_extract(
        args.src,
        args.dst,
        seq_len=args.seq_len,
        hand_threshold=args.hand_threshold,
        skip_existing=not args.no_skip,
    )
