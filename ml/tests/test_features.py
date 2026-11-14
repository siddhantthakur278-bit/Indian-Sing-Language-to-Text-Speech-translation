"""
Unit Tests for Kinematic and Spatial Feature Extraction
======================================================
Verifies:
- First-order velocity calculation v(t) = p(t) - p(t-1) with v(0) = 0.
- Second-order acceleration calculation a(t) = v(t) - v(t-1).
- Spatial hand-to-nose relative displacement vector shape (T, 6).
- Multistream feature concatenation shapes and backward compatibility.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from ml.features import (
    compute_velocity,
    compute_acceleration,
    compute_hand_relative_displacement,
    extract_multistream_features,
)

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class TestKinematicFeatures(unittest.TestCase):

    def setUp(self):
        # 10 frames, 258 dimensions
        self.seq_len = 10
        self.feat_dim = 258
        self.seq_list = [[float(t * 1.5 + c * 0.01) for c in range(self.feat_dim)] for t in range(self.seq_len)]

    def test_compute_velocity_initial_frame_is_zero(self):
        vel = compute_velocity(self.seq_list)
        self.assertEqual(len(vel), self.seq_len)
        self.assertTrue(all(v == 0.0 for v in vel[0]), "Initial velocity frame must be zero.")

    def test_compute_velocity_linear_derivative(self):
        vel = compute_velocity(self.seq_list)
        # Difference between t and t-1 is 1.5
        for t in range(1, self.seq_len):
            for c in range(self.feat_dim):
                self.assertAlmostEqual(vel[t][c], 1.5, delta=1e-5)

    def test_compute_acceleration_initial_frames(self):
        vel = compute_velocity(self.seq_list)
        acc = compute_acceleration(vel)
        self.assertEqual(len(acc), self.seq_len)
        self.assertTrue(all(a == 0.0 for a in acc[0]), "Initial acceleration frame must be zero.")

    def test_hand_relative_displacement_shape(self):
        disp = compute_hand_relative_displacement(self.seq_list)
        self.assertEqual(len(disp), self.seq_len)
        self.assertEqual(len(disp[0]), 6, "Spatial displacement should be 6-dimensional (dx, dy, dz for both hands).")

    def test_multistream_feature_shapes(self):
        # Base: 258, with velocity: 258 * 2 = 516
        stream_vel = extract_multistream_features(self.seq_list, include_accel=False, include_spatial=False)
        self.assertEqual(len(stream_vel[0]), 516)

        # With acceleration: 258 * 3 = 774
        stream_acc = extract_multistream_features(self.seq_list, include_accel=True, include_spatial=False)
        self.assertEqual(len(stream_acc[0]), 774)

        # With spatial displacement: 516 + 6 = 522
        stream_spat = extract_multistream_features(self.seq_list, include_accel=False, include_spatial=True)
        self.assertEqual(len(stream_spat[0]), 522)


if __name__ == "__main__":
    unittest.main()
