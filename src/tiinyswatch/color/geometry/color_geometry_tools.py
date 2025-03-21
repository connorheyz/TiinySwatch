import numpy as np

class ColorGeometryTools:
    @staticmethod
    def rotation_matrix(axis: np.ndarray, theta: float) -> np.ndarray:
        """
        Compute the rotation matrix using Rodrigues' rotation formula.
        """
        axis = np.asarray(axis, dtype=float)
        axis /= np.linalg.norm(axis)
        a = np.cos(theta)
        b = np.sin(theta)
        K = np.array([[0, -axis[2], axis[1]],
                      [axis[2], 0, -axis[0]],
                      [-axis[1], axis[0], 0]])
        I = np.eye(3)
        return a * I + b * K + (1 - a) * np.outer(axis, axis)

    @staticmethod
    def rotate_points(points: np.ndarray, pivot: np.ndarray, axis: np.ndarray, theta: float) -> np.ndarray:
        """
        Rotate an array of points (n x 3) around a pivot along the specified axis
        using Rodrigues' rotation formula.
        """
        v = points - pivot
        cos_r = np.cos(theta)
        sin_r = np.sin(theta)
        dot_vals = np.sum(v * axis, axis=1, keepdims=True)
        cross_vals = np.cross(axis, v)
        rotated_v = v * cos_r + cross_vals * sin_r + axis * dot_vals * (1 - cos_r)
        return pivot + rotated_v

    @staticmethod
    def rotate_point(point: np.ndarray, pivot: np.ndarray, axis: np.ndarray, theta: float) -> np.ndarray:
        """
        Rotate a single point around a pivot along the specified axis using Rodrigues' rotation formula.
        """
        return ColorGeometryTools.rotate_points(point.reshape(1, 3), pivot, axis, theta).reshape(3)

    @staticmethod
    def get_perpendicular_vector(vector: np.ndarray) -> np.ndarray:
        """
        Given a normalized vector, return another unit vector perpendicular to it.
        """
        arbitrary = np.array([0.0, 0.0, 1.0])
        if np.abs(np.dot(vector, arbitrary)) > 0.99:
            arbitrary = np.array([0.0, 1.0, 0.0])
        perp = arbitrary - np.dot(arbitrary, vector) * vector
        norm = np.linalg.norm(perp)
        if norm < 1e-12:
            return np.array([1.0, 0.0, 0.0])
        return perp / norm

    @staticmethod
    def get_normalized_axis(vA: np.ndarray, vB: np.ndarray) -> np.ndarray:
        """
        Compute a normalized axis perpendicular to vA and vB by taking their cross product.
        If the two vectors are nearly parallel (or one is zero), returns a default axis.
        """
        axis = np.cross(vA, vB)
        norm_axis = np.linalg.norm(axis)
        if norm_axis < 1e-12:
            return np.array([1.0, 0.0, 0.0])
        return axis / norm_axis
