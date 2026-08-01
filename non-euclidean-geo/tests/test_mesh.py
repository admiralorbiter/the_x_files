import unittest
import numpy as np
from spherical_maze.icosphere import create_icosahedron, subdivide_mesh, build_face_adjacency, face_center
from spherical_maze.maze import build_cells, generate_maze

class TestMesh(unittest.TestCase):

    def test_icosphere_subdivision_level_2(self):
        verts, faces = create_icosahedron()
        self.assertEqual(len(faces), 20)
        
        verts_sub, faces_sub = subdivide_mesh(verts, faces, levels=2)
        # Level 1 = 80 faces, Level 2 = 320 faces
        self.assertEqual(len(faces_sub), 320)
        
        # Verify all vertices are normalized unit vectors
        norms = np.linalg.norm(verts_sub, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-6)

    def test_face_adjacency(self):
        verts, faces = create_icosahedron()
        verts_sub, faces_sub = subdivide_mesh(verts, faces, levels=2)
        adj = build_face_adjacency(faces_sub)
        
        # Every face in a closed triangular mesh must have exactly 3 neighbors sharing edges
        for face_id, neighbors in adj.items():
            self.assertEqual(len(neighbors), 3, f"Face {face_id} has {len(neighbors)} neighbors instead of 3")

    def test_maze_connectivity(self):
        verts, faces = create_icosahedron()
        verts_sub, faces_sub = subdivide_mesh(verts, faces, levels=2)
        cells = build_cells(verts_sub, faces_sub)
        generate_maze(cells, seed=42, loop_prob=0.1)
        
        # Verify open_neighbors reciprocity
        for cell in cells:
            for neigh in cell.open_neighbors:
                self.assertIn(cell.id, cells[neigh].open_neighbors)

if __name__ == "__main__":
    unittest.main()
