from typing import Tuple, List, Optional
import numpy as np
from .geometry import normalize, spherical_distance, slerp

def build_tangent_basis(position: np.ndarray, forward: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build an orthonormal basis at position on the unit sphere:
    p: position vector (outward normal)
    f: unit tangent forward vector (perpendicular to p)
    r: unit tangent right vector (perpendicular to p and f)
    """
    p = normalize(position)
    # Ensure forward is orthogonal to p
    f = normalize(forward - np.dot(forward, p) * p)
    # Right vector = f x p (right hand rule for standard 2D screen coordinates)
    r = normalize(np.cross(f, p))
    return p, f, r

def project_point(
    p: np.ndarray,
    f: np.ndarray,
    r: np.ndarray,
    q: np.ndarray,
    scale: float,
    center: Tuple[float, float],
    max_radius: float = 1.5
) -> Optional[Tuple[float, float, float]]:
    """
    Project a 3D unit vector q using Azimuthal Equidistant projection centered at player position p.
    Returns (screen_x, screen_y, dist_rad) or None if point is beyond max_radius.
    """
    d = spherical_distance(p, q)
    if d > max_radius:
        return None
        
    if d < 1e-7:
        return (center[0], center[1], 0.0)
        
    sin_d = np.sin(d)
    t_vec = (q - np.cos(d) * p) / sin_d
    
    x_proj = d * np.dot(t_vec, r)
    y_proj = d * np.dot(t_vec, f)
    
    screen_x = center[0] + scale * x_proj
    screen_y = center[1] - scale * y_proj
    
    return (screen_x, screen_y, d)

def project_geodesic(
    a: np.ndarray,
    b: np.ndarray,
    p: np.ndarray,
    f: np.ndarray,
    r: np.ndarray,
    scale: float,
    center: Tuple[float, float],
    samples: int = 10,
    max_radius: float = 1.5
) -> List[Tuple[float, float, float]]:
    """
    Sample a great-circle arc between a and b into 'samples' points and project each point.
    Returns list of (screen_x, screen_y, dist_rad) tuples.
    """
    projected_pts = []
    for i in range(samples + 1):
        t = i / float(samples)
        q = slerp(a, b, t)
        proj = project_point(p, f, r, q, scale, center, max_radius)
        if proj is not None:
            projected_pts.append(proj)
    return projected_pts
