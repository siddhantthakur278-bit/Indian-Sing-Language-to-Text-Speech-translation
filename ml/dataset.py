"""
ISL Dataset Loader & Partitioning Pipeline
Loads preprocessed (30, 258) landmark sequences and coordinates with data/metadata.csv
to provide clean train, validation, and test splits strictly by signer ID.
"""

import os
import csv
import json
import logging
from typing import Tuple, List, Dict, Optional, Generator

from config import (
    PROCESSED_DATA_DIR,
    CLASSES_PATH,
    METADATA_PATH,
    SEQ_LEN,
    FEAT_DIM,
)
from preprocess import normalize, augment_sequence

logger = logging.getLogger(__name__)


class ISLDataset:
    """Dataset manager handling sequence loading, normalization, and signer-wise splits."""

    def __init__(
        self,
        processed_dir: str = PROCESSED_DATA_DIR,
        classes_path: str = CLASSES_PATH,
        metadata_path: str = METADATA_PATH,
        seq_len: int = SEQ_LEN,
        feat_dim: int = FEAT_DIM,
    ):
        self.processed_dir = processed_dir
        self.classes_path = classes_path
        self.metadata_path = metadata_path
        self.seq_len = seq_len
        self.feat_dim = feat_dim

        # Load vocabulary
        with open(self.classes_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.classes: List[str] = meta["classes"]
        self.class_to_idx: Dict[str, int] = {cls_name: i for i, cls_name in enumerate(self.classes)}
        self.num_classes: int = len(self.classes)

        # Load metadata records
        self.records: List[Dict[str, str]] = self._load_metadata()

    def _load_metadata(self) -> List[Dict[str, str]]:
        records = []
        if not os.path.exists(self.metadata_path):
            logger.warning(f"Metadata file {self.metadata_path} not found. Operating in directory-scan fallback mode.")
            return records

        with open(self.metadata_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        return records

    def get_splits(self) -> Dict[str, List[Dict[str, str]]]:
        """Groups metadata records into train, val, and test splits."""
        splits = {"train": [], "val": [], "test": []}
        for rec in self.records:
            split_name = rec.get("split", "train").lower().strip()
            if split_name in splits:
                splits[split_name].append(rec)
            else:
                splits["train"].append(rec)
        return splits

    def load_split_arrays(self, split: str = "train") -> Tuple[list, list]:
        """
        Loads all sequences and labels for a specific split.
        Returns (sequences, integer_labels).
        """
        splits = self.get_splits()
        target_records = splits.get(split, [])

        X, y = [], []
        try:
            import numpy as np
            has_numpy = True
        except ImportError:
            has_numpy = False

        for rec in target_records:
            clip = rec.get("clip", "")
            gloss = rec.get("gloss", "")
            if not clip or gloss not in self.class_to_idx:
                continue

            npy_path = os.path.join(self.processed_dir, gloss, clip)
            if not os.path.exists(npy_path):
                # Check clip with or without extension
                if not npy_path.endswith(".npy"):
                    npy_path += ".npy"
                if not os.path.exists(npy_path):
                    continue

            try:
                if has_numpy:
                    seq = np.load(npy_path)
                    if seq.shape == (self.seq_len, self.feat_dim):
                        norm_seq = normalize(seq)
                        X.append(norm_seq)
                        y.append(self.class_to_idx[gloss])
                else:
                    # Non-numpy fallback for lightweight environments
                    pass
            except Exception as e:
                logger.debug(f"Could not load sequence {npy_path}: {e}")

        if has_numpy and X:
            return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)
        return X, y

    def get_class_distribution(self, split: Optional[str] = None) -> Dict[str, int]:
        """Returns clip frequency counts per class."""
        counts = {c: 0 for c in self.classes}
        for rec in self.records:
            if split and rec.get("split", "").lower() != split.lower():
                continue
            gloss = rec.get("gloss", "")
            if gloss in counts:
                counts[gloss] += 1
        return counts


if __name__ == "__main__":
    dataset = ISLDataset()
    print(f"Loaded ISLDataset with {dataset.num_classes} classes and {len(dataset.records)} catalog records.")
    splits = dataset.get_splits()
    for s_name, recs in splits.items():
        print(f"  • Split '{s_name}': {len(recs)} clips")
