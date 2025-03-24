import numpy as np

_M1_IAB = np.array([
    [0.490978, 1.045001, 0.482481, 0],
    [0.517558, 1.256543, 0.240489, 0],
    [1.587132, 0.553389, -0.124257, 0],
    [1.967421, -0.807475, -0.143517, 1]
])

_M2_IAB = np.array([
    [-0.011823, 0.248826, -0.106030, 0],
    [5.055264, -5.937734, 0.881421, 0],
    [1.247189, -3.372989, 2.125450, 0],
    [-0.741126, 1.127297, -1.255019, 1]
])

_M1_IAB_inv = np.linalg.inv(_M1_IAB)
_M2_IAB_inv = np.linalg.inv(_M2_IAB)

REF_WHITE = np.array([0.9504, 1.0000, 1.0888])

# SA-PQ constants: [c1, c2, c3, m, n]
_SA_PQ_CONSTS = np.array([0.7707, 44.4561, 44.2269, 0.2926, 78.2171])

def _sa_pq_transfer(y):
    """
    Apply the SA-PQ transfer function element-wise.
    y is assumed to be the LMS value scaled by LA.
    Equation: f_SA-PQ(Y) = ((c1 + c2 * Y^(m)) / (1 + c3 * Y^(m)))^(n)
    """
    c1, c2, c3, m, n = _SA_PQ_CONSTS
    numerator = c1 + c2 * np.power(y, m)
    denominator = 1 + c3 * np.power(y, m)
    val = numerator / denominator
    result = np.power(val, n)
    return result


def _sa_pq_transfer_inverse(z):
    """
    Inverse of the SA-PQ transfer function.
    Given z = ((c1 + c2 * y^(m)) / (1 + c3 * y^(m)))^(n),
    solve for y.
    """
    c1, c2, c3, m, n = _SA_PQ_CONSTS
    # Remove the exponent n
    val = np.sign(z) * np.power(np.abs(z), 1.0 / n)
    # Solve for y^m
    y_m = (val - c1) / (c2 - c3 * val)
    result = np.sign(y_m) * np.power(np.abs(y_m), 1.0 / m)
    return result


def xyz_to_iab(xyz_array, **kwargs):
    """Convert XYZ to IAB color space."""
    denormalized_xyz = xyz_array / REF_WHITE 
    xyz_h = np.append(denormalized_xyz, 1.0).reshape(4, 1)
    transformed_xyz = _M1_IAB @ xyz_h
    transformed_xyz /= transformed_xyz[3, 0]
    lms = transformed_xyz[:3, 0]
    lms_prime = _sa_pq_transfer(lms)
    lms_prime_h = np.append(lms_prime, 1.0).reshape(4, 1)
    
    transformed_lms = _M2_IAB @ lms_prime_h
    transformed_lms /= transformed_lms[3, 0]
    
    iab = transformed_lms[:3, 0]
    return iab


def iab_to_xyz(iab_array, **kwargs):
    """Convert IAB to XYZ color space."""
    # Convert IAPBP coordinates to homogeneous column vector
    iab_h = np.append(np.array(iab_array), 1.0).reshape(4, 1)
    
    # Invert the second transformation (M2)
    lms_prime_h = _M2_IAB_inv @ iab_h
    lms_prime_h /= lms_prime_h[3, 0]
    lms_prime = lms_prime_h[:3, 0]
    
    # Invert the SA-PQ transfer function
    lms = _sa_pq_transfer_inverse(lms_prime)
    
    # Convert LMS back to homogeneous coordinates
    lms_h = np.append(lms, 1.0).reshape(4, 1)
    
    xyz_h = _M1_IAB_inv @ lms_h
    xyz_h /= xyz_h[3, 0]
    
    xyz_normalized = xyz_h[:3, 0]
    
    recovered_xyz = xyz_normalized * REF_WHITE 
    
    return recovered_xyz