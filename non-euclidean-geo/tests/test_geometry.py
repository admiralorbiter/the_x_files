import unittest
import numpy as np
from spherical_maze.geometry import normalize, spherical_distance, slerp, rotate_about_axis, parallel_transport

class TestGeometry(unittest.TestCase):

    def test_normalize(self):
        v = np.array([3.0, 4.0, 0.0])
        norm_v = normalize(v)
        self.assertAlmostEqual(np.linalg.norm(norm_v), 1.0)
        np.testing.assert_allclose(norm_v, [0.6, 0.8, 0.0])

    def test_spherical_distance(self):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        dist = spherical_distance(a, b)
        self.assertAlmostEqual(dist, np.pi / 2.0)
        
        c = np.array([1.0, 0.0, 0.0])
        self.assertAlmostEqual(spherical_distance(a, c), 0.0)

    def test_slerp(self):
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        
        mid = slerp(a, b, 0.5)
        expected = normalize(np.array([1.0, 1.0, 0.0]))
        np.testing.assert_allclose(mid, expected, atol=1e-6)

    def test_rotate_about_axis(self):
        v = np.array([1.0, 0.0, 0.0])
        axis = np.array([0.0, 0.0, 1.0])
        rotated = rotate_about_axis(v, axis, np.pi / 2.0)
        np.testing.assert_allclose(rotated, [0.0, 1.0, 0.0], atol=1e-6)

    def test_parallel_transport(self):
        start = np.array([1.0, 0.0, 0.0])
        end = np.array([0.0, 1.0, 0.0])
        
        # Tangent vector at start pointing in Z direction
        v = np.array([0.0, 0.0, 1.0])
        
        # Transporting along equator (X to Y) shouldn't affect Z-pointing tangent vector
        transported = parallel_transport(v, start, end)
        np.testing.assert_allclose(transported, [0.0, 0.0, 1.0], atol=1e-6)

if __name__ == "__main__":
    unittest.main()
