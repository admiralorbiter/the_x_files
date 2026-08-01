import math
from typing import List, Tuple, Dict
import numpy as np
from .geometry import normalize

def create_icosahedron() -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
    """Create initial icosahedron vertices and triangular faces."""
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    
    verts = np.array([
        [-1,  phi,  0], [ 1,  phi,  0], [-1, -phi,  0], [ 1, -phi,  0],
        [ 0, -1,  phi], [ 0,  1,  phi], [ 0, -1, -phi], [ 0,  1, -phi],
        [ phi,  0, -1], [ phi,  0,  1], [-phi,  0, -1], [-phi,  0,  1]
    ], dtype=np.float64)
    
    # Normalize initial vertices onto unit sphere
    verts = np.array([normalize(v) for v in verts])
    
    faces = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)
    ]
    
    return verts, faces

def get_middle_point(p1: int, p2: int, verts: List[np.ndarray], middle_point_cache: Dict[Tuple[int, int], int]) -> Tuple[int, List[np.ndarray]]:
    """Helper to find or create a midpoint vertex between p1 and p2 on unit sphere."""
    key = (min(p1, p2), max(p1, p2))
    if key in middle_point_cache:
        return middle_point_cache[key], verts
        
    v1 = verts[p1]
    v2 = verts[p2]
    middle = normalize((v1 + v2) / 2.0)
    
    index = len(verts)
    verts.append(middle)
    middle_point_cache[key] = index
    return index, verts

def subdivide_mesh(verts: np.ndarray, faces: List[Tuple[int, int, int]], levels: int = 2) -> Tuple[np.ndarray, List[Tuple[int, int, int]]]:
    """Subdivide every triangular face 'levels' times. Level 0=20, 1=80, 2=320, 3=1280 cells."""
    verts_list = [v for v in verts]
    current_faces = faces
    
    for _ in range(levels):
        middle_point_cache: Dict[Tuple[int, int], int] = {}
        next_faces = []
        
        for tri in current_faces:
            v0, v1, v2 = tri
            a, verts_list = get_middle_point(v0, v1, verts_list, middle_point_cache)
            b, verts_list = get_middle_point(v1, v2, verts_list, middle_point_cache)
            c, verts_list = get_middle_point(v2, v0, verts_list, middle_point_cache)
            
            next_faces.append((v0, a, c))
            next_faces.append((v1, b, a))
            next_faces.append((v2, c, b))
            next_faces.append((a, b, c))
            
        current_faces = next_faces
        
    return np.array(verts_list, dtype=np.float64), current_faces

def build_face_adjacency(faces: List[Tuple[int, int, int]]) -> Dict[int, List[int]]:
    """
    Build adjacency map where key is face_id and value is list of neighbor face_ids
    that share an edge (2 vertices).
    """
    edge_to_faces: Dict[Tuple[int, int], List[int]] = {}
    
    for face_id, (v0, v1, v2) in enumerate(faces):
        edges = [
            (min(v0, v1), max(v0, v1)),
            (min(v1, v2), max(v1, v2)),
            (min(v2, v0), max(v2, v0))
        ]
        for e in edges:
            if e not in edge_to_faces:
                edge_to_faces[e] = []
            edge_to_faces[e].append(face_id)
            
    adjacency: Dict[int, List[int]] = {i: [] for i in range(len(faces))}
    for edge, face_ids in edge_to_faces.items():
        if len(face_ids) == 2:
            f1, f2 = face_ids
            adjacency[f1].append(f2)
            adjacency[f2].append(f1)
            
    return adjacency

def face_center(verts: np.ndarray, face: Tuple[int, int, int]) -> np.ndarray:
    """Calculate the normalized center vector of a triangular face."""
    v0, v1, v2 = face
    center_raw = verts[v0] + verts[v1] + verts[v2]
    return normalize(center_raw)
