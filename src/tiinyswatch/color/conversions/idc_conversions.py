import numpy as np

_M1_IDC = np.array([
    [  0.097351,   4.014714,   0.237031,   0.000000],
    [  0.784176,   2.173841,   1.391079,   0.000000],
    [  0.758643,   3.154623,   0.435830,   0.000000],
    [  7.609619,  -3.512767,  -0.747756,   1.000000],
])

_M2_IDC = np.array([
    [  0.239367,   0.231305,   0.242876,   0.000000],
    [ -0.144462,   0.002229,   0.142234,   0.000000],
    [ -0.142531,  -0.069322,   0.211852,   0.000000],
    [ -1.075238,  -1.158153,   1.946939,   1.000000],
])

_M1_IDC_inv = np.linalg.inv(_M1_IDC)
_M2_IDC_inv = np.linalg.inv(_M2_IDC)

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
    numerator = c1 + c2 * np.sign(y) * np.power(np.abs(y), m)
    denominator = 1 + c3 * np.sign(y) * np.power(np.abs(y), m)
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

def xyz_to_idc(xyz_array, **kwargs):

    denormalized_xyz = xyz_array / REF_WHITE 
    xyz_h = np.append(denormalized_xyz, 1.0).reshape(4, 1)
    transformed_xyz = _M1_IDC @ xyz_h
    transformed_xyz /= transformed_xyz[3, 0]
    lms = transformed_xyz[:3, 0]
    lms_prime = _sa_pq_transfer(lms)
    lms_prime_h = np.append(lms_prime, 1.0).reshape(4, 1)
        
    transformed_lms = _M2_IDC @ lms_prime_h
    transformed_lms /= transformed_lms[3, 0]
        
    idc = transformed_lms[:3, 0]
    return idc


def idc_to_xyz(idc_array, **kwargs):

    # Convert idc coordinates to homogeneous column vector
    idc_h = np.append(np.array(idc_array), 1.0).reshape(4, 1)
        
    # Invert the second transformation (M2)
    lms_prime_h = _M2_IDC_inv @ idc_h
    lms_prime_h /= lms_prime_h[3, 0]
    lms_prime = lms_prime_h[:3, 0]
        
    # Invert the SA-PQ transfer function
    lms = _sa_pq_transfer_inverse(lms_prime)
        
    # Convert LMS back to homogeneous coordinates
    lms_h = np.append(lms, 1.0).reshape(4, 1)
        
    xyz_h = _M1_IDC_inv @ lms_h
    xyz_h /= xyz_h[3, 0]
        
    xyz_normalized = xyz_h[:3, 0]
        
    recovered_xyz = xyz_normalized * REF_WHITE 
        
    return recovered_xyz