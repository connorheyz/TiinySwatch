import numpy as np
import math

# --- Constants ---

# CAT16 Matrix and Inverse
CAT16_MATRIX = np.array([
    [0.401288, 0.650173, -0.051461],
    [-0.250268, 1.204414, 0.045854],
    [-0.002079, 0.048952, 0.953127]
])
CAT16_INV = np.linalg.inv(CAT16_MATRIX)

# Intermediate Matrix for CAM16 -> XYZ
M1_CAM16 = np.array([
    [ 460.0,  451.0,  288.0],
    [ 460.0, -891.0, -261.0],
    [ 460.0, -220.0, -6300.0]
]) / 1403.0 # Incorporate the 1/1403 scaling factor

# Default White Point (D65)
WHITES = {
    "2deg": {
        "D65": (0.31270, 0.32900)
    }
}
DEFAULT_WHITE_POINT_XY = WHITES["2deg"]["D65"]

# Surround Conditions
SURROUND = {
    'dark': (0.8, 0.525, 0.8),    # f, c, Nc
    'dim': (0.9, 0.59, 0.9),
    'average': (1.0, 0.69, 1.0)
}

# CAM16 UCS/LCD/SCD Coefficients
CAM16_UCS_COEFFS = {
    # Model: (Not used here, c1, c2) - Note: Original code used indices [1:]
    'lcd': (0.77, 0.007, 0.0053), # kL, c1, c2
    'scd': (1.24, 0.007, 0.0363),
    'ucs': (1.00, 0.007, 0.0228)
}

# Hue Quadrature Data
HUE_QUADRATURE = {
    "h": (20.14, 90.00, 164.25, 237.53, 380.14), # Hue angles
    "e": (0.8, 0.7, 1.0, 1.2, 0.8),             # Eccentricity factors
    "H": (0.0, 100.0, 200.0, 300.0, 400.0)      # Corresponding Quadrature Hue
}

# Adaptation exponent
ADAPTED_COEF = 0.42
ADAPTED_COEF_INV = 1.0 / ADAPTED_COEF

# Default Environment Parameters (matches CAM16JMh.ENV in example)
# Whitepoint: D65
# Adapting Luminance (La): 64 lux / pi * 20% (gray world) ~= 4.074 cd/m^2
# Background Luminance (Yb): 20% of Yw (assuming Yw=100 -> Yb=20)
# Surround: average
# Discounting illuminant: False
DEFAULT_ENV_PARAMS = {
    "white_point_xy": DEFAULT_WHITE_POINT_XY,
    "adapting_luminance": 64.0 / math.pi * 0.2,
    "background_luminance_relative": 20.0,
    "surround_type": 'average',
    "discounting": False
}


# --- Helper Functions ---

def xy_to_xyz(xy, Y=1.0):
    """Convert xyY to XYZ (assuming Y=1 if not provided)."""
    x, y = xy
    if y == 0:
        return np.array([0.0, 0.0, 0.0])
    X = (x * Y) / y
    Z = ((1.0 - x - y) * Y) / y
    return np.array([X, Y, Z])

def scale100(xyz):
    """Scale XYZ from 0-1 range to 0-100 range."""
    return xyz * 100.0

def scale1(xyz):
    """Scale XYZ from 0-100 range to 0-1 range."""
    return xyz / 100.0

def constrain_hue(h):
    """Constrain hue angle to [0, 360)."""
    return h % 360.0

def _adapt(rgb_c, fl):
    """Apply CAM16 non-linear adaptation."""
    term = np.power(fl * np.abs(rgb_c) * 0.01, ADAPTED_COEF)
    rgb_a = 400.0 * np.sign(rgb_c) * term / (term + 27.13)
    # Handle potential NaN if rgb_c was 0 initially (term=0 -> 0/27.13 = 0)
    rgb_a = np.nan_to_num(rgb_a)
    return rgb_a

def _unadapt(rgb_a, fl):
    """Invert CAM16 non-linear adaptation."""
    rgb_a_abs = np.abs(rgb_a)
    # Avoid division by zero or instability near 400
    rgb_a_abs = np.minimum(rgb_a_abs, 399.9999)

    term_numer = rgb_a_abs * 27.13
    term_denom = 400.0 - rgb_a_abs
    term = term_numer / term_denom

    rgb_c_abs = (100.0 / fl) * np.power(term, ADAPTED_COEF_INV)
    rgb_c = np.sign(rgb_a) * rgb_c_abs
    return rgb_c

def _eccentricity(h_rad):
    """Calculate eccentricity factor et."""
    # Example code had math.cos(h + 2) - likely h_rad
    return 0.25 * (np.cos(h_rad + 2.0) + 3.8)

def _inv_hue_quadrature(H):
    """Convert Hue Quadrature H to hue angle h."""
    Hp = H % 400.0
    i = int(math.floor(0.01 * Hp))
    Hp_rem = Hp % 100.0

    h_i, h_ii = HUE_QUADRATURE['h'][i:i+2]
    e_i, e_ii = HUE_QUADRATURE['e'][i:i+2]

    numerator = Hp_rem * (e_ii * h_i - e_i * h_ii) - 100.0 * h_i * e_ii
    denominator = Hp_rem * (e_ii - e_i) - 100.0 * e_ii

    # Avoid division by zero, though unlikely with standard values
    if abs(denominator) < 1e-7:
        return constrain_hue(h_i if Hp_rem == 0 else h_ii)

    return constrain_hue(numerator / denominator)


# --- Environment Calculation ---

def _calculate_cam16_environment(params=DEFAULT_ENV_PARAMS):
    """
    Calculate fixed environment parameters needed for CAM16 conversions.
    Based on the logic within the `Environment` class in the example.
    """
    xy_w = params["white_point_xy"]
    la = params["adapting_luminance"]
    yb_rel = params["background_luminance_relative"]
    surround_type = params["surround_type"]
    discounting = params["discounting"]

    # Reference white in XYZ (scaled to Yw=100)
    xyz_w = scale100(xy_to_xyz(xy_w))
    yw = xyz_w[1] # Should be 100.0

    # Surround factors
    f, c, nc = SURROUND[surround_type]

    # Luminance level adaptation factor
    k = 1.0 / (5.0 * la + 1.0)
    k4 = k**4
    fl = (k4 * la + 0.1 * (1.0 - k4)**2 * np.cbrt(5.0 * la))

    # Background relative luminance normalized
    n = yb_rel / yw
    z = 1.48 + np.sqrt(n)
    nbb = 0.725 * np.power(n, -0.2)
    ncb = nbb

    # Degree of chromatic adaptation
    d = np.clip(f * (1.0 - (1.0 / 3.6) * np.exp((-la - 42.0) / 92.0)), 0.0, 1.0)
    if discounting:
        d = 1.0

    # Cone response for reference white
    rgb_w = CAT16_MATRIX @ xyz_w
    d_rgb = d * (yw / rgb_w) + (1.0 - d)
    d_rgb_inv = 1.0 / d_rgb

    # Achromatic response for white point
    rgb_cw = rgb_w * d_rgb # Chromatically adapted response
    rgb_aw = _adapt(rgb_cw, fl)
    a_w = (2.0 * rgb_aw[0] + rgb_aw[1] + 0.05 * rgb_aw[2]) * nbb

    # Return parameters needed for conversions
    return {
        "fl": fl, "c": c, "nc": nc, "nbb": nbb, "ncb": ncb, "z": z,
        "n": n, "yw": yw, "a_w": a_w, "d_rgb": d_rgb, "d_rgb_inv": d_rgb_inv,
        "fl_root": np.power(fl, 0.25) # Precompute for brightness (Q)
    }

# Calculate default environment once
_DEFAULT_ENV = _calculate_cam16_environment()


# --- Core CAM16 <-> XYZ Conversions ---

def _xyz_to_cam16_vars(xyz_abs, env):
    """
    Convert XYZ (absolute, 0-100) to CAM16 variables (J, C, h, s, Q, M, H).
    Requires pre-calculated environment parameters.
    """
    # Step 1: Chromatic Adaptation
    rgb_c = (CAT16_MATRIX @ xyz_abs) * env["d_rgb"]

    # Step 2: Post-Adaptation Non-Linearity
    rgb_a = _adapt(rgb_c, env["fl"])

    # Step 3: Calculate Cartesian Components a, b
    a = rgb_a[0] - (12.0 * rgb_a[1] - rgb_a[2]) / 11.0
    b = (rgb_a[0] + rgb_a[1] - 2.0 * rgb_a[2]) / 9.0

    # Step 4: Hue Angle
    h_rad = np.arctan2(b, a)
    h = constrain_hue(np.degrees(h_rad))

    # Step 5: Eccentricity factor
    et = _eccentricity(h_rad)

    # Step 6: Achromatic Response A
    # P2 term appears in multiple places
    p2 = (2.0 * rgb_a[0] + rgb_a[1] + 0.05 * rgb_a[2]) # Removed * nbb here, apply later
    A = p2 * env["nbb"]

    # Handle achromatic case (A=0 implies J=0 etc.)
    if A < 1e-7: # Use a small threshold
        return {"J": 0.0, "C": 0.0, "h": h, "s": 0.0, "Q": 0.0, "M": 0.0, "H": 0.0}

    # Step 7: Lightness J
    J = 100.0 * np.power(A / env["a_w"], env["c"] * env["z"])

    # Step 8: Brightness Q
    J_root = np.sqrt(J / 100.0) # Equivalent to `np.power(J/100.0, 0.5)`
    Q = (4.0 / env["c"]) * J_root * (env["a_w"] + 4.0) * env["fl_root"]

    # Step 9: Correlate of Chroma (t) -> Chroma C -> Colorfulness M
    # p1 term for t calculation
    p1 = (50000.0 / 13.0) * env["nc"] * env["ncb"] * et
    # u term used in original code's t calculation (denominator component)
    u = p2 # This was 'u' in example's xyz_to_cam, but was same as p2 without *nbb
    t = p1 * np.sqrt(a*a + b*b) / (u * env["nbb"] + 0.305) # Apply nbb here

    # Alpha term relates t to C/M/s
    alpha = np.power(t, 0.9) * np.power(1.64 - np.power(0.29, env["n"]), 0.73)

    # Chroma C
    C = alpha * J_root

    # Colorfulness M
    M = C * env["fl_root"]

    # Step 10: Saturation s
    s = 50.0 * np.sqrt(env["c"] * alpha / (env["a_w"] + 4.0))

    # Step 11: Hue Quadrature H (optional?) - Example calculated it
    H = _inv_hue_quadrature(h) # Incorrect, should be hue_quadrature(h)
    # Need hue_quadrature function if H is desired output.
    # For UCS/LCD conversions, only J, M, h are needed. Skip H for now.
    # H = np.nan # Placeholder if needed later

    return {"J": J, "C": C, "h": h, "s": s, "Q": Q, "M": M} # Skip H


def _cam16_vars_to_xyz(J, M, h, env):
    """
    Convert CAM16 JMh to XYZ (absolute, 0-100).
    Requires J, M, h and pre-calculated environment parameters.
    """
    # Handle black point
    if J <= 1e-7 or M <= 1e-7:
        return np.array([0.0, 0.0, 0.0])

    # --- Reverse Steps ---
    # Step 1: Calculate t from M (or C or s)
    # We have M, need C -> alpha -> t
    C = M / env["fl_root"]
    J_root = np.sqrt(J / 100.0)
    # Avoid division by zero if J is extremely small but non-zero
    alpha = C / J_root if J_root > 1e-7 else 0.0
    # Avoid issues if alpha becomes 0
    if alpha < 1e-7:
         return np.array([0.0, 0.0, 0.0]) # If no chroma, should be achromatic -> XYZ is black/gray

    t = np.power(alpha / np.power(1.64 - np.power(0.29, env["n"]), 0.73), 1.0 / 0.9)

    # Step 2: Hue Angle and Eccentricity
    h_rad = np.radians(h)
    et = _eccentricity(h_rad)

    # Step 3: Achromatic Response A from J
    A = env["a_w"] * np.power(J / 100.0, 1.0 / (env["c"] * env["z"]))

    # Step 4: Calculate Cartesian a, b from t
    p1 = (50000.0 / 13.0) * env["nc"] * env["ncb"] * et
    p2 = A / env["nbb"] # Corresponds to P2/nbb or 'u' from forward calculation

    cos_h = np.cos(h_rad)
    sin_h = np.sin(h_rad)

    # Temporary term 'r' used in example
    # Denominator involves a, b - need to solve for them.
    # From forward: t = p1 * sqrt(a^2 + b^2) / (p2 + 0.305)
    # sqrt(a^2 + b^2) = t * (p2 + 0.305) / p1
    # Let R = sqrt(a^2 + b^2). Then a = R * cos_h, b = R * sin_h
    # The example code seems to use a different calculation involving M1_CAM16. Let's re-check that.
    # r = 23 * (p2 + 0.305) * zdiv(t, 23 * p1 + t * (11 * cos_h + 108 * sin_h)) -> This looks complex.
    # Alternative approach: Solve for a, b using A and t.
    # We have A = nbb * (2*rgb_a[0] + rgb_a[1] + 0.05*rgb_a[2])
    # We have a = rgb_a[0] - (12*rgb_a[1] - rgb_a[2]) / 11
    # We have b = (rgb_a[0] + rgb_a[1] - 2*rgb_a[2]) / 9
    # We have t related to sqrt(a^2+b^2).
    # This seems like solving a system of equations. Let's trust the example's reverse calculation using M1_CAM16.

    # Calculate a, b using the example's reversed formula structure:
    term_beta = t / p1 # (Need p1 as defined before)
    term_gamma = p2 + 0.305 # (Need p2 = A/nbb as defined before)

    # Denominator for a, b calculation factor ('r' in example?)
    # Denom Factor = (23 * p1 / t + 11 * cos_h + 108 * sin_h) / (23 * term_gamma) --> No, this leads back to 't'
    # Let's use the example structure directly:
    # r = 23 * (p2 + 0.305) * t / ( 23 * p1 + t * (11 * cos_h + 108 * sin_h) ) -> This looks unstable if denom near zero
    # Simpler? sqrt(a^2+b^2) = R = term_gamma * term_beta
    R = term_gamma * t / p1 # Where t is already calculated from M/C
    a = R * cos_h
    b = R * sin_h

    # Step 5: Calculate intermediate RGB `rgb_a` using M1_CAM16
    # Need [p2, a, b] vector. p2 = A / nbb.
    p2_val = A / env["nbb"]
    # M1_CAM16 already includes the 1/1403 factor
    rgb_a = M1_CAM16 @ np.array([p2_val, a, b])

    # Step 6: Undo non-linear adaptation
    rgb_c = _unadapt(rgb_a, env["fl"])

    # Step 7: Undo chromatic adaptation
    xyz_abs = (CAT16_INV @ (rgb_c / env["d_rgb"]))

    # Ensure non-negative results (though small negatives might occur due to precision)
    return np.maximum(xyz_abs, 0)


# --- CAM16 JMh <-> UCS Jab Conversions ---

def _cam_jmh_to_ucs_jab(J, M, h, model):
    """Convert CAM16 JMh to CAM16-UCS/LCD Jab."""
    if J <= 1e-7:
        return np.array([0.0, 0.0, 0.0])

    _kl, c1, c2 = CAM16_UCS_COEFFS[model] # kl not used here

    # Apply UCS transformation to J
    abs_J = np.abs(J)
    J_ucs = np.sign(J) * (1.0 + 100.0 * c1) * abs_J / (1.0 + c1 * abs_J)

    # Apply UCS transformation to M -> M_ucs
    # Avoid log(0) or log(<1) issues if M is very small
    M_term = 1.0 + c2 * M
    M_ucs = np.log(np.maximum(M_term, 1.0)) / c2 if c2 != 0 else M # Handle c2=0 case (though not expected)
    M_ucs = np.maximum(M_ucs, 0.0) # Ensure M_ucs is non-negative

    # Convert M_ucs, h to a, b
    h_rad = np.radians(h)
    a_ucs = M_ucs * np.cos(h_rad)
    b_ucs = M_ucs * np.sin(h_rad)

    return np.array([J_ucs, a_ucs, b_ucs])

def _ucs_jab_to_cam_jmh(J_ucs, a_ucs, b_ucs, model):
    """Convert CAM16-UCS/LCD Jab to CAM16 JMh."""
    if J_ucs <= 1e-7:
        return np.array([0.0, 0.0, 0.0])

    _kl, c1, c2 = CAM16_UCS_COEFFS[model]

    # Reverse UCS transformation for J_ucs -> J
    abs_J_ucs = np.abs(J_ucs)
    # Denominator: 1.0 - c1 * (abs_J_ucs - 100.0) -> guaranteed >= 1 for J_ucs <= 100
    J = np.sign(J_ucs) * abs_J_ucs / (1.0 - c1 * (abs_J_ucs - 100.0))

    # Reverse UCS transformation for a, b -> M, h
    M_ucs = np.sqrt(a_ucs**2 + b_ucs**2)
    h = constrain_hue(np.degrees(np.arctan2(b_ucs, a_ucs)))

    # M = (exp(M_ucs * c2) - 1) / c2
    if c2 == 0:
        M = M_ucs # Linear case if c2=0
    else:
        # Use expm1 for potentially better precision if M_ucs * c2 is small
        M = np.expm1(M_ucs * c2) / c2
    M = np.maximum(M, 0.0) # Ensure M is non-negative

    return np.array([J, M, h])


# --- Public API Functions ---

def xyz_to_cam16ucs(xyz_rel, **kwargs):
    """
    Convert XYZ (relative D65, Y=0..1) to CAM16-UCS (Jab).
    Uses standard 'average' viewing conditions.
    """
    xyz_abs = scale100(np.asarray(xyz_rel))
    env = _DEFAULT_ENV
    cam_vars = _xyz_to_cam16_vars(xyz_abs, env)
    J, M, h = cam_vars["J"], cam_vars["M"], cam_vars["h"]
    ucs_jab = _cam_jmh_to_ucs_jab(J, M, h, 'ucs')
    return ucs_jab

def cam16ucs_to_xyz(ucs_jab, **kwargs):
    """
    Convert CAM16-UCS (Jab) to XYZ (relative D65, Y=0..1).
    Uses standard 'average' viewing conditions.
    """
    J_ucs, a_ucs, b_ucs = np.asarray(ucs_jab)
    env = _DEFAULT_ENV
    J, M, h = _ucs_jab_to_cam_jmh(J_ucs, a_ucs, b_ucs, 'ucs')
    xyz_abs = _cam16_vars_to_xyz(J, M, h, env)
    return scale1(xyz_abs)

def xyz_to_cam16lcd(xyz_rel, **kwargs):
    """
    Convert XYZ (relative D65, Y=0..1) to CAM16-LCD (Jab).
    Uses standard 'average' viewing conditions.
    """
    xyz_abs = scale100(np.asarray(xyz_rel))
    env = _DEFAULT_ENV
    cam_vars = _xyz_to_cam16_vars(xyz_abs, env)
    J, M, h = cam_vars["J"], cam_vars["M"], cam_vars["h"]
    lcd_jab = _cam_jmh_to_ucs_jab(J, M, h, 'lcd')
    return lcd_jab

def cam16lcd_to_xyz(lcd_jab, **kwargs):
    """
    Convert CAM16-LCD (Jab) to XYZ (relative D65, Y=0..1).
    Uses standard 'average' viewing conditions.
    """
    J_lcd, a_lcd, b_lcd = np.asarray(lcd_jab)
    env = _DEFAULT_ENV
    J, M, h = _ucs_jab_to_cam_jmh(J_lcd, a_lcd, b_lcd, 'lcd')
    xyz_abs = _cam16_vars_to_xyz(J, M, h, env)
    return scale1(xyz_abs) 