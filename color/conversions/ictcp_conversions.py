from colormath.color_conversions import convert_color
from colormath.color_objects import (
    LabColor, sRGBColor, HSVColor, HSLColor, CMYKColor,
    XYZColor, xyYColor, LuvColor, AdobeRGBColor, IPTColor
)
import numpy as np

# Precompute matrices used in both conversions.
_M1_ITP = np.array([
    [1.716651187971268, -0.355670783776392, -0.253366281373660],
    [-0.666684351832489, 1.616481236634939, 0.015768545813911],
    [0.017639857445311, -0.042770613257809, 0.942103121235474]
])
_M2_ITP = (1 / 4096.0) * np.array([
    [1688, 2146, 262],
    [683, 2951, 462],
    [99, 309, 3688]
])
# Composite matrix: converts XYZ directly to LMS.
XYZ_TO_LMS_MATRIX = _M2_ITP @ _M1_ITP
LMS_TO_XYZ = np.linalg.inv(XYZ_TO_LMS_MATRIX)

# Matrix for the ITP conversion (and its inverse)
A = np.array([
    [0.5, 0.5, 0.0],
    [6610.0 / 4096.0, -13613.0 / 4096.0, 7003.0 / 4096.0],
    [17933.0 / 4096.0, -17390.0 / 4096.0, -543.0 / 4096.0]
])
A_inv = np.linalg.inv(A)

# Constants for the non-linear transforms.
m1 = 0.1593017578125
m2 = 78.84375
c1 = 0.8359375
c2 = 18.8515625
c3 = 18.6875

def ictcp_to_xyz(itp_array, **kwargs):
    v = itp_array.copy()

    # Convert ITP to LMS' via matrix multiplication.
    lms_prime = np.dot(v, A_inv.T)

    # Apply the non-linear transform elementwise.
    A_val = np.sign(lms_prime) * np.power(np.abs(lms_prime), 1.0 / m2)
    Z = (c1 - A_val) / (A_val * c3 - c2)
    y = np.sign(Z) * np.power(np.abs(Z), 1.0 / m1)
    lms = y * 10000.0

    # Convert LMS to XYZ via matrix multiplication.
    xyz = np.dot(lms, LMS_TO_XYZ.T)
    return xyz

def xyz_to_ictcp(xyz_array, **kwargs):

    # Convert XYZ to LMS using the precomputed matrix.
    lms = np.dot(xyz_array.copy(), XYZ_TO_LMS_MATRIX.T)
    y = lms / 10000.0

    # Inverse non-linear transform
    val =  (c1 + c2 * np.sign(y) * np.power(np.abs(y), m1)) / (1 + c3 * np.sign(y) * np.power(np.abs(y), m1))
    lms_prime = np.sign(val) * np.power(np.abs(val),m2)

    itp = lms_prime @ A.T
    return itp