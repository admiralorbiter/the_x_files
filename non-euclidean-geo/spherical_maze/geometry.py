import numpy as np

def normalize(v: np.ndarray) -> np.ndarray:
    """Normalize a vector to unit length."""
    norm = np.linalg.norm(v)
    if norm < 1e-12:
        return np.zeros_like(v)
    return v / norm

def spherical_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Compute spherical distance (in radians) between unit vectors a and b."""
    dot = np.clip(np.dot(a, b), -1.0, 1.0)
    return float(np.arccos(dot))

def slerp(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    """Spherical linear interpolation between unit vectors a and b."""
    dot = np.clip(np.dot(a, b), -1.0, 1.0)
    omega = np.arccos(dot)
    
    if omega < 1e-7:
        # Linear interpolation fallback for near-identical vectors
        return normalize((1.0 - t) * a + t * b)
    
    sin_omega = np.sin(omega)
    weight_a = np.sin((1.0 - t) * omega) / sin_omega
    weight_b = np.sin(t * omega) / sin_omega
    
    return normalize(weight_a * a + weight_b * b)

def rotate_about_axis(v: np.ndarray, axis: np.ndarray, angle: float) -> np.ndarray:
    """Rotate 3D vector v around a unit axis by an angle (in radians) using Rodrigues' formula."""
    axis = normalize(axis)
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)
    
    return v * cos_a + np.cross(axis, v) * sin_a + axis * np.dot(axis, v) * (1.0 - cos_a)

def parallel_transport(v: np.ndarray, start: np.ndarray, end: np.ndarray) -> np.ndarray:
    """
    Parallel transport a tangent vector v from start to end along a geodesic.
    Applies the rotation that carries 'start' to 'end' along their great circle to 'v'.
    """
    axis_raw = np.cross(start, end)
    axis_len = np.linalg.norm(axis_raw)
    
    if axis_len < 1e-7:
        return v.copy()
        
    axis = axis_raw / axis_len
    angle = spherical_distance(start, end)
    return rotate_about_axis(v, axis, angle)
