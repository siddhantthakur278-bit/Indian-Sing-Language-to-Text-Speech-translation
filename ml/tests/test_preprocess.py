"""
Unit tests for ML preprocessing, normalization, and signer-wise splitting.
==========================================================================
Author: Parth (Data & ML Track)

These unit tests verify Contract 7.1 compliance without requiring heavy dependencies:
- Output vector shape (30, 258)
- Mid-shoulder translation to (0, 0, 0)
- Scale invariance
- Zero-fill preservation for absent hands (no NaNs or Infs)
- Parity with ml/sample_io.json
- Signer ID extraction and signer-wise dataset partitioning
"""

import unittest
import sys
import os
import math
import json

# Add parent directory to path so ml modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from preprocess import normalize, extract_signer_id, signer_wise_split
from features import compute_velocity, compute_acceleration


class TestMLPreprocessing(unittest.TestCase):

    def setUp(self):
        """Builds a deterministic test sequence with known landmark values."""
        self.seq_len = 30
        self.feat_dim = 258
        self.test_seq = [[0.0] * self.feat_dim for _ in range(self.seq_len)]

        for f in range(self.seq_len):
            # Left shoulder (landmark 11): x=0.6, y=0.4, z=0.0, visibility=1.0
            self.test_seq[f][44] = 0.6
            self.test_seq[f][45] = 0.4
            self.test_seq[f][46] = 0.0
            self.test_seq[f][47] = 1.0

            # Right shoulder (landmark 12): x=0.4, y=0.4, z=0.0, visibility=1.0
            self.test_seq[f][48] = 0.4
            self.test_seq[f][49] = 0.4
            self.test_seq[f][50] = 0.0
            self.test_seq[f][51] = 1.0

            # Left hand (landmark 0: wrist at 132..134): present
            self.test_seq[f][132] = 0.5
            self.test_seq[f][133] = 0.7
            self.test_seq[f][134] = 0.1

            # Right hand (indices 195 to 257): absent (all 0.0)

    def test_normalize_output_shape(self):
        """Verifies that normalization returns exactly (30, 258) elements."""
        normalized = normalize(self.test_seq)
        self.assertEqual(len(normalized), self.seq_len)
        self.assertEqual(len(normalized[0]), self.feat_dim)

    def test_normalize_mid_shoulder_centered(self):
        """Verifies that the mid-shoulder midpoint is centered at (0, 0, 0)."""
        normalized = normalize(self.test_seq)
        f0 = normalized[0]

        ls_x, ls_y, ls_z = f0[44], f0[45], f0[46]
        rs_x, rs_y, rs_z = f0[48], f0[49], f0[50]

        mid_x = (ls_x + rs_x) / 2.0
        mid_y = (ls_y + rs_y) / 2.0
        mid_z = (ls_z + rs_z) / 2.0

        self.assertAlmostEqual(mid_x, 0.0, places=5)
        self.assertAlmostEqual(mid_y, 0.0, places=5)
        self.assertAlmostEqual(mid_z, 0.0, places=5)

    def test_normalize_scale_invariance(self):
        """Verifies that scaling input coordinates yields identical normalized coordinates."""
        scale_factor = 2.5
        scaled_seq = [[v * scale_factor for v in frame] for frame in self.test_seq]
        # Preserve visibility unchanged
        for f in range(self.seq_len):
            scaled_seq[f][47] = 1.0
            scaled_seq[f][51] = 1.0

        norm_original = normalize(self.test_seq)
        norm_scaled = normalize(scaled_seq)

        for f in range(self.seq_len):
            for c in range(self.feat_dim):
                # Coordinates should be invariant within tolerance
                self.assertAlmostEqual(norm_original[f][c], norm_scaled[f][c], delta=1e-4)

    def test_normalize_missing_hands_remain_strictly_zero(self):
        """Ensures absent hands remain 0.0 without introducing NaN or infinity values."""
        normalized = normalize(self.test_seq)
        f0 = normalized[0]

        # Right hand landmarks (indices 195 to 257) were all zero in input
        for idx in range(195, 258):
            self.assertEqual(f0[idx], 0.0, f"Absent hand index {idx} was modified to {f0[idx]}")

        # Check that no NaNs or Infinities exist anywhere in the output
        for f in range(self.seq_len):
            for c in range(self.feat_dim):
                val = normalized[f][c]
                self.assertFalse(math.isnan(val), f"NaN detected at frame {f}, index {c}")
                self.assertFalse(math.isinf(val), f"Inf detected at frame {f}, index {c}")

    def test_normalize_sample_io_parity(self):
        """Verifies normalization against precomputed sample_io.json with tolerance < 1e-4."""
        sample_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sample_io.json"))
        if not os.path.exists(sample_path):
            self.skipTest("sample_io.json not found")

        with open(sample_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_list = data["raw"]
        expected_list = data["normalized"]

        for s_idx in range(len(raw_list)):
            actual = normalize(raw_list[s_idx])
            expected = expected_list[s_idx]
            for f in range(len(actual)):
                for c in range(len(actual[f])):
                    diff = abs(actual[f][c] - expected[f][c])
                    self.assertLess(diff, 1e-4, f"Mismatch at seq {s_idx}, frame {f}, dim {c}")

    def test_signer_id_parsing(self):
        """Verifies extraction of signer IDs from various filename patterns."""
        self.assertEqual(extract_signer_id("HELLO_p01_003.npy"), "p01")
        self.assertEqual(extract_signer_id("WATER_P5_01.mp4"), "p05")
        self.assertEqual(extract_signer_id("HOSPITAL_P12_042.npy"), "p12")
        self.assertEqual(extract_signer_id("RANDOM_SIGN.npy"), "p00")

    def test_signer_wise_split(self):
        """Verifies that signer-wise splitting partitions files without identity leakage."""
        files = [
            "HELLO_p01_001.npy", "HELLO_p01_002.npy",
            "HELLO_p02_001.npy",
            "HELLO_p03_001.npy",
            "HELLO_p04_001.npy",
            "HELLO_p05_001.npy",
        ]
        train_s = ["p01", "p02", "p03"]
        val_s = ["p04"]
        test_s = ["p05"]

        train_files, val_files, test_files = signer_wise_split(files, train_s, val_s, test_s)

        self.assertEqual(len(train_files), 4)  # 2 for p01, 1 for p02, 1 for p03
        self.assertEqual(len(val_files), 1)    # 1 for p04
        self.assertEqual(len(test_files), 1)   # 1 for p05

        # Check zero overlap
        self.assertTrue(set(train_files).isdisjoint(set(val_files)))
        self.assertTrue(set(train_files).isdisjoint(set(test_files)))
        self.assertTrue(set(val_files).isdisjoint(set(test_files)))

    def test_velocity_zero_at_initial_frame(self):
        """Verifies that first-order difference is zero at frame 0."""
        seq = [[float(t * 2) for _ in range(10)] for t in range(5)]
        vel = compute_velocity(seq)
        self.assertEqual(vel[0], [0.0] * 10)
        self.assertEqual(vel[1], [2.0] * 10)

    def test_normalize_zero_shoulder_distance(self):
        """Edge case: shoulders are at identical coordinates (scale = 0 + 1e-6 epsilon)."""
        seq = [[0.0] * self.feat_dim for _ in range(self.seq_len)]
        for f in range(self.seq_len):
            # Identical left and right shoulder coordinates
            seq[f][44], seq[f][45], seq[f][46] = 0.5, 0.5, 0.5
            seq[f][48], seq[f][49], seq[f][50] = 0.5, 0.5, 0.5
        norm = normalize(seq)
        for f in range(self.seq_len):
            for c in range(self.feat_dim):
                val = norm[f][c]
                self.assertFalse(math.isnan(val), f"NaN at frame {f}, dim {c}")
                self.assertFalse(math.isinf(val), f"Inf at frame {f}, dim {c}")

    def test_normalize_all_landmarks_zero(self):
        """Edge case: completely black/undetected frame where all 258 landmarks are 0.0."""
        zero_seq = [[0.0] * self.feat_dim for _ in range(self.seq_len)]
        norm = normalize(zero_seq)
        for f in range(self.seq_len):
            for c in range(self.feat_dim):
                val = norm[f][c]
                self.assertFalse(math.isnan(val))
                self.assertFalse(math.isinf(val))
            # Absent hands must remain strictly 0.0
            for idx in range(132, 258):
                self.assertEqual(norm[f][idx], 0.0)

    def test_normalize_both_hands_missing(self):
        """Edge case: pose is valid but both left and right hands are missing (0.0)."""
        seq = [[0.0] * self.feat_dim for _ in range(self.seq_len)]
        for f in range(self.seq_len):
            seq[f][44], seq[f][45], seq[f][46] = 0.6, 0.4, 0.0
            seq[f][48], seq[f][49], seq[f][50] = 0.4, 0.4, 0.0
        norm = normalize(seq)
        for f in range(self.seq_len):
            for idx in range(132, 258):
                self.assertEqual(norm[f][idx], 0.0)

    def test_normalize_right_hand_only(self):
        """Edge case: left hand absent, right hand present."""
        seq = [[0.0] * self.feat_dim for _ in range(self.seq_len)]
        for f in range(self.seq_len):
            seq[f][44], seq[f][45], seq[f][46] = 0.6, 0.4, 0.0
            seq[f][48], seq[f][49], seq[f][50] = 0.4, 0.4, 0.0
            # Right hand wrist at idx 195: present
            seq[f][195], seq[f][196], seq[f][197] = 0.4, 0.6, 0.2
        norm = normalize(seq)
        for f in range(self.seq_len):
            # Left hand (132..194) must remain strictly 0.0
            for idx in range(132, 195):
                self.assertEqual(norm[f][idx], 0.0)
            # Right hand (195..197) must be normalized
            self.assertNotEqual(norm[f][195], 0.0)

    def test_normalize_variable_sequence_lengths(self):
        """Verifies normalization handles arbitrary valid sequence lengths (T=1, T=15, T=45)."""
        for t in [1, 15, 45]:
            seq = [[0.0] * self.feat_dim for _ in range(t)]
            for f in range(t):
                seq[f][44], seq[f][45], seq[f][46] = 0.6, 0.4, 0.0
                seq[f][48], seq[f][49], seq[f][50] = 0.4, 0.4, 0.0
            norm = normalize(seq)
            self.assertEqual(len(norm), t)
            self.assertEqual(len(norm[0]), self.feat_dim)

    def test_normalize_invalid_inputs(self):
        """Verifies that invalid input shapes and empty sequences raise appropriate errors."""
        with self.assertRaises((ValueError, TypeError)):
            normalize([])
        with self.assertRaises((ValueError, TypeError)):
            normalize(None)
        with self.assertRaises((ValueError, TypeError)):
            normalize([[0.0] * 100])  # Invalid dimension (100 != 258)


if __name__ == "__main__":
    unittest.main()
