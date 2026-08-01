import unittest
import numpy as np
from spherical_maze.geometry import normalize
from spherical_maze.projection import build_tangent_basis, project_point, project_geodesic

class TestProjection(unittest.TestCase):

    def test_tangent_basis_orthonormality(self):
        pos = normalize(np.array([1.0, 1.0, 1.0]))
        fwd_raw = np.array([0.0, 0.0, 1.0])
        p, f, r = build_tangent_basis(pos, fwd_raw)
        
        self.assertAlmostEqual(np.linalg.norm(p), 1.0)
        self.assertAlmostEqual(np.linalg.norm(f), 1.0)
        self.assertAlmostEqual(np.linalg.norm(r), 1.0)
        
        self.assertAlmostEqual(np.dot(p, f), 0.0, places=6)
        self.assertAlmostEqual(np.dot(p, r), 0.0, places=6)
        self.assertAlmostEqual(np.dot(f, r), 0.0, places=6)

    def test_project_point_at_center(self):
        pos = np.array([1.0, 0.0, 0.0])
        fwd = np.array([0.0, 1.0, 0.0])
        p, f, r = build_tangent_basis(pos, fwd)
        
        center = (500.0, 500.0)
        scale = 200.0
        
        proj = project_point(p, f, r, pos, scale, center)
        self.assertIsNotNone(proj)
        px, py, dist = proj
        self.assertAlmostEqual(px, 500.0)
        self.assertAlmostEqual(py, 500.0)
        self.assertAlmostEqual(dist, 0.0)

    def test_project_geodesic_samples(self):
        pos = np.array([1.0, 0.0, 0.0])
        fwd = np.array([0.0, 1.0, 0.0])
        p, f, r = build_tangent_basis(pos, fwd)
        
        a = normalize(np.array([1.0, 0.2, 0.0]))
        b = normalize(np.array([1.0, -0.2, 0.0]))
        
        pts = project_geodesic(a, b, p, f, r, scale=200.0, center=(500.0, 500.0), samples=5)
        self.assertEqual(len(pts), 6)

if __name__ == "__main__":
    unittest.main()
