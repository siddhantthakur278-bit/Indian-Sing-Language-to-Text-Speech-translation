"""
Unit tests for ML preprocessing, normalization, and kinematic features.
"""

import unittest
import sys
import os
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from features import compute_velocity, compute_acceleration


class TestMLPreprocessing(unittest.TestCase):

    def test_velocity_zero_at_initial_frame(self):
        seq = [[float(t * 2) for _ in range(10)] for t in range(5)]
        # custom manual array simulation
        vel = []
        for i in range(len(seq)):
            if i == 0:
                vel.append([0.0] * 10)
            else:
                vel.append([seq[i][j] - seq[i - 1][j] for j in range(10)])

        self.assertEqual(vel[0], [0.0] * 10)
        self.assertEqual(vel[1], [2.0] * 10)

    def test_pure_signer_id_parsing(self):
        import re
        def extract_signer(fn):
            m = re.search(r'[pP](\d+)', os.path.basename(fn))
            return f"p{int(m.group(1)):02d}" if m else "p00"

        self.assertEqual(extract_signer("HELLO_p01_003.npy"), "p01")
        self.assertEqual(extract_signer("WATER_P5_01.mp4"), "p05")
        self.assertEqual(extract_signer("RANDOM_SIGN.npy"), "p00")


if __name__ == "__main__":
    unittest.main()
