"""
ISL ML Configuration & Central Constants
=========================================
Author: Parth (Data & ML Track)

This module defines all shared constants, directory paths, landmark vector dimensions,
and runtime thresholds used throughout the ISL data processing, model training,
and evaluation pipeline.

Centralizing these values ensures consistency across all Python scripts and matches
the Integration Contracts defined in AGENTS.md (Section 7) and AGENTS_PARTH_ML.md.
"""

import os
import json

# -----------------------------------------------------------------------------
# 1. Project Directory & File Paths
# -----------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
CLASSES_PATH = os.path.join(DATA_DIR, "classes.json")
METADATA_PATH = os.path.join(DATA_DIR, "metadata.csv")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

ARTIFACTS_DIR = os.path.join(BASE_DIR, "ml", "artifacts")
MODEL_CHECKPOINT = os.path.join(ARTIFACTS_DIR, "isl_model.keras")
SAMPLE_IO_JSON = os.path.join(BASE_DIR, "ml", "sample_io.json")
SAMPLE_IO_NPZ = os.path.join(ARTIFACTS_DIR, "sample_io.npz")


# -----------------------------------------------------------------------------
# 2. Dynamic Vocabulary Resolution
# -----------------------------------------------------------------------------
def load_classes(classes_file: str = CLASSES_PATH) -> list:
    """Loads the list of gesture classes from classes.json."""
    if os.path.exists(classes_file):
        with open(classes_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("classes", [])
    # Fallback to standard 70 classes if file not found
    return ["IDLE"]


CLASSES = load_classes()
NUM_CLASSES = len(CLASSES) if CLASSES else 70


# -----------------------------------------------------------------------------
# 3. MediaPipe Landmark Vector Specifications (Contract 7.1)
# -----------------------------------------------------------------------------
# Frame layout:
# - Pose:       33 points * 4 values (x, y, z, visibility) = 132
# - Left Hand:  21 points * 3 values (x, y, z)             =  63
# - Right Hand: 21 points * 3 values (x, y, z)             =  63
# Total feature dimension = 258 values per frame
FEAT_DIM = 258
SEQ_LEN = 30  # Fixed number of frames per video sequence

# Landmark indices for shoulder midpoint calculation
POSE_LEFT_SHOULDER_IDX = 11   # landmarks 11: left shoulder
POSE_RIGHT_SHOULDER_IDX = 12  # landmarks 12: right shoulder
EPSILON = 1e-6                # Prevent division by zero during scaling


# -----------------------------------------------------------------------------
# 4. Default Signer Split Configuration (Signer-Wise Partitioning)
# -----------------------------------------------------------------------------
DEFAULT_TRAIN_SIGNERS = ["p01", "p02", "p03"]
DEFAULT_VAL_SIGNERS = ["p04"]
DEFAULT_TEST_SIGNERS = ["p05"]


# -----------------------------------------------------------------------------
# 5. Runtime Inference & Temporal Smoothing Thresholds
# -----------------------------------------------------------------------------
CONFIDENCE_THRESHOLD = 0.80  # Minimum softmax probability to consider a prediction valid
VOTING_WINDOW = 5            # Number of consecutive predictions examined for consensus
VOTING_CONSENSUS = 4         # Required matching predictions out of VOTING_WINDOW
COOLDOWN_FRAMES = 30         # Refractory period (~1.0s at 30fps) after accepting a sign
PAUSE_THRESHOLD_MS = 1500    # Inactivity duration (no hands) triggering sentence commit
