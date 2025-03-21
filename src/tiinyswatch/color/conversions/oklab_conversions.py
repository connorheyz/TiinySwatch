import numpy as np

# XYZ to LMS matrix
M1 = np.array([
    [0.8189330101, 0.3618667424, -0.1288597137],
    [0.0329845436, 0.9293118715, 0.0361456387],
    [0.0482003018, 0.2643662691, 0.6338517070]
])

# LMS to XYZ matrix (inverse of M1)
M1_INV = np.linalg.inv(M1)

# LMS to Oklab matrix
M2 = np.array([
    [0.2104542553, 0.7936177850, -0.0040720468],
    [1.9779984951, -2.4285922050, 0.4505937099],
    [0.0259040371, 0.7827717662, -0.8086757660]
])

# Oklab to LMS matrix (inverse of M2)
M2_INV = np.linalg.inv(M2)

def xyz_to_oklab(xyz, observer="2", illuminant="d65"):
    # Ensure xyz is a column vector
    xyz = np.asarray(xyz)
    if xyz.shape != (3, 1):
        xyz = xyz.reshape(3, 1)

    # XYZ to cone responses (LMS)
    lms = M1 @ xyz

    # Non-linear compression
    lms_ = np.cbrt(lms)

    # LMS to Oklab
    lab = M2 @ lms_
    
    # Return in the same shape as input
    return lab.reshape(-1)

def oklab_to_xyz(lab, observer="2", illuminant="d65"):
    # Ensure lab is a column vector
    lab = np.asarray(lab)
    if lab.shape != (3, 1):
        lab = lab.reshape(3, 1)

    # Oklab to LMS
    lms_ = M2_INV @ lab

    # Non-linear decompression
    lms = lms_ * lms_ * lms_

    # LMS to XYZ
    xyz = M1_INV @ lms
    
    # Return in the same shape as input
    return xyz.reshape(-1) 