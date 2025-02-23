from colormath.color_conversions import convert_color
from colormath.color_objects import (
    LabColor, sRGBColor, HSVColor, HSLColor, CMYKColor,
    XYZColor, xyYColor, LuvColor, AdobeRGBColor, IPTColor
)
import numpy as np

class ColorConversion:
    XYZ_DEFAULT_ILLUMINANT = 'd65'
    # Class variable to hold the precomputed Pantone candidate ITP values.
    
    @staticmethod
    def lab_to_xyz(comps_array, observer, illuminant):
        # Expected order: [L, a, b]
        L, a, b = comps_array
        lab = LabColor(lab_l=L, lab_a=a, lab_b=b, observer=observer, illuminant=illuminant)
        return convert_color(lab, XYZColor, target_illuminant=ColorConversion.XYZ_DEFAULT_ILLUMINANT)
    
    @staticmethod
    def xyz_to_lab(xyz_color, observer, illuminant):
        lab = convert_color(xyz_color, LabColor)
        return np.array([lab.lab_l, lab.lab_a, lab.lab_b], dtype=float)
    
    @staticmethod
    def xyy_to_xyz(comps_array, observer, illuminant):
        # Expected order: [x, y, Y]
        x, y, Y = comps_array
        xyy = xyYColor(xyy_x=x, xyy_y=y, xyy_Y=Y, observer=observer, illuminant=illuminant)
        return convert_color(xyy, XYZColor, target_illuminant=ColorConversion.XYZ_DEFAULT_ILLUMINANT)
    
    @staticmethod
    def xyz_to_xyy(xyz_color, observer, illuminant):
        xyy = convert_color(xyz_color, xyYColor)
        return np.array([xyy.xyy_x, xyy.xyy_y, xyy.xyy_Y], dtype=float)
    
    @staticmethod
    def luv_to_xyz(comps_array, observer, illuminant):
        # Expected order: [L, u, v]
        L, u, v = comps_array
        luv = LuvColor(luv_l=L, luv_u=u, luv_v=v, observer=observer, illuminant=illuminant)
        return convert_color(luv, XYZColor, target_illuminant=ColorConversion.XYZ_DEFAULT_ILLUMINANT)
    
    @staticmethod
    def xyz_to_luv(xyz_color, observer, illuminant):
        luv = convert_color(xyz_color, LuvColor)
        return np.array([luv.luv_l, luv.luv_u, luv.luv_v], dtype=float)
    
    @staticmethod
    def adobe_to_xyz(comps_array, *args, **kwargs):
        # Expected order: [r, g, b]
        r, g, b = comps_array
        adobe = AdobeRGBColor(r, g, b)
        return convert_color(adobe, XYZColor, target_illuminant=ColorConversion.XYZ_DEFAULT_ILLUMINANT)
    
    @staticmethod
    def xyz_to_adobe(xyz_color, *args, **kwargs):
        adobe = convert_color(xyz_color, AdobeRGBColor)
        return np.array([adobe.rgb_r, adobe.rgb_g, adobe.rgb_b], dtype=float)
    
    @staticmethod
    def srgb_to_xyz(comps_array, *args, **kwargs):
        # Expected order: [r, g, b]
        r, g, b = comps_array
        srgb = sRGBColor(r, g, b)
        return convert_color(srgb, XYZColor, target_illuminant=ColorConversion.XYZ_DEFAULT_ILLUMINANT)
    
    @staticmethod
    def xyz_to_srgb(xyz_color, *args, **kwargs):
        srgb = convert_color(xyz_color, sRGBColor, target_illuminant=ColorConversion.XYZ_DEFAULT_ILLUMINANT)
        return np.array([srgb.rgb_r, srgb.rgb_g, srgb.rgb_b], dtype=float)
    
    @staticmethod
    def hsv_to_xyz(comps_array, *args, **kwargs):
        # Expected order: [h, s, v]
        h, s, v = comps_array
        hsv = HSVColor(hsv_h=h, hsv_s=s, hsv_v=v)
        return convert_color(hsv, XYZColor, target_illuminant=ColorConversion.XYZ_DEFAULT_ILLUMINANT)
    
    @staticmethod
    def xyz_to_hsv(xyz_color, *args, **kwargs):
        hsv = convert_color(xyz_color, HSVColor)
        return np.array([hsv.hsv_h, hsv.hsv_s, hsv.hsv_v], dtype=float)
    
    @staticmethod
    def hsl_to_xyz(comps_array, *args, **kwargs):
        # Expected order: [h, s, l]
        h, s, l = comps_array
        hsl = HSLColor(hsl_h=h, hsl_s=s, hsl_l=l)
        rgb = convert_color(hsl, sRGBColor)
        return convert_color(rgb, XYZColor, target_illuminant=ColorConversion.XYZ_DEFAULT_ILLUMINANT)
    
    @staticmethod
    def xyz_to_hsl(xyz_color, *args, **kwargs):
        hsl = convert_color(xyz_color, HSLColor)
        return np.array([hsl.hsl_h, hsl.hsl_s, hsl.hsl_l], dtype=float)
    
    @staticmethod
    def cmyk_to_xyz(comps_array, *args, **kwargs):
        # Expected order: [c, m, y, k]
        c, m, y, k = comps_array
        cmyk = CMYKColor(cmyk_c=c, cmyk_m=m, cmyk_y=y, cmyk_k=k)
        return convert_color(cmyk, XYZColor, target_illuminant=ColorConversion.XYZ_DEFAULT_ILLUMINANT)
    
    @staticmethod
    def xyz_to_cmyk(xyz_color, *args, **kwargs):
        cmyk = convert_color(xyz_color, CMYKColor)
        return np.array([cmyk.cmyk_c, cmyk.cmyk_m, cmyk.cmyk_y, cmyk.cmyk_k], dtype=float)
    
    @staticmethod
    def ipt_to_xyz(comps_array, *args, **kwargs):
        # Expected order: [i, p, t]
        i, p, t = comps_array
        ipt = IPTColor(ipt_i=i, ipt_t=t, ipt_p=p)
        return convert_color(ipt, XYZColor, target_illuminant=ColorConversion.XYZ_DEFAULT_ILLUMINANT)
    
    @staticmethod
    def xyz_to_ipt(xyz_color, *args, **kwargs):
        ipt = convert_color(xyz_color, IPTColor)
        return np.array([ipt.ipt_i, ipt.ipt_p, ipt.ipt_t], dtype=float)
    
    # Precompute matrices used in both conversions.
    _M1 = np.array([
        [1.716651187971268, -0.355670783776392, -0.253366281373660],
        [-0.666684351832489, 1.616481236634939, 0.015768545813911],
        [0.017639857445311, -0.042770613257809, 0.942103121235474]
    ])
    _M2 = (1 / 4096.0) * np.array([
        [1688, 2146, 262],
        [683, 2951, 462],
        [99, 309, 3688]
    ])
    _M3 = np.array([
        [0.5, 0.5, 0],
        [6610/8192, -13613/8192, 7003/8192],
        [17933/4096, -17390/4096, -543/4096]
    ])
    # Composite matrix: converts XYZ directly to LMS.
    XYZ_TO_LMS_MATRIX = _M2 @ _M1
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

    @staticmethod
    def itp_to_xyz(itp_array, *args, **kwargs):
        """
        Convert a single ITP color to XYZ.

        Parameters:
        itp_array : numpy.ndarray
            A 1D array with 3 elements: [I, T, P].

        Returns:
        xyz_color : XYZColor
            An instance of XYZColor with the converted values.
        """
        # Make a copy to avoid modifying the original array.
        v = itp_array.copy()
        # Multiply the T component by 2.
        v[1] = v[1] * 2

        # Convert ITP to LMS' via matrix multiplication.
        lms_prime = np.dot(v, ColorConversion.A_inv.T)

        # Apply the non-linear transform elementwise.
        A_val = np.sign(lms_prime) * np.power(np.abs(lms_prime), 1.0 / ColorConversion.m2)
        Z = (ColorConversion.c1 - A_val) / (A_val * ColorConversion.c3 - ColorConversion.c2)
        y = np.sign(Z) * np.power(np.abs(Z), 1.0 / ColorConversion.m1)
        lms = y * 10000.0

        # Convert LMS to XYZ via matrix multiplication.
        xyz = np.dot(lms, ColorConversion.LMS_TO_XYZ.T)
        return XYZColor(*xyz, illuminant=ColorConversion.XYZ_DEFAULT_ILLUMINANT)

    @staticmethod
    def xyz_to_itp(xyz_color, *args, **kwargs):
        """
        Convert many XYZ colors to ITP.

        Parameters:
        xyz_array : numpy.ndarray
            An array of shape (N, 3) where each row is [X, Y, Z].

        Returns:
        itp_array : numpy.ndarray
            An array of shape (N, 3) where each row is [I, T, P].
        """
        xyz_array = np.array(xyz_color.get_value_tuple())
        # Convert XYZ to LMS using the precomputed matrix.
        lms = np.dot(xyz_array, ColorConversion.XYZ_TO_LMS_MATRIX.T)
        y = lms / 10000.0

        # Inverse non-linear transform (elementwise)
        lms_prime = np.power(
            (ColorConversion.c1 + ColorConversion.c2 * np.sign(y) * np.power(np.abs(y), ColorConversion.m1)) /
            (1 + ColorConversion.c3 * np.sign(y) * np.power(np.abs(y), ColorConversion.m1)),
            ColorConversion.m2
        )

        itp = lms_prime @ ColorConversion._M3.T
        return itp
    
    @classmethod
    def _compute_itp_from_xyz(cls, xyz_array):
        lms = xyz_array @ cls.XYZ_TO_LMS_MATRIX.T
        y = lms / 10000.0
        m1 = 0.1593017578125
        m2 = 78.84375
        c1 = 0.8359375
        c2 = 18.8515625
        c3 = 18.6875
        lms_prime = ((c1 + c2 * np.power(y, m1)) / (1 + c3 * np.power(y, m1))) ** m2
        itp = np.empty_like(lms_prime)
        itp[:, 0] = 0.5 * lms_prime[:, 0] + 0.5 * lms_prime[:, 1]
        itp[:, 1] = (6610 * lms_prime[:, 0] - 13613 * lms_prime[:, 1] + 7003 * lms_prime[:, 2]) / 8192.0
        itp[:, 2] = (17933 * lms_prime[:, 0] - 17390 * lms_prime[:, 1] - 543 * lms_prime[:, 2]) / 4096.0
        return itp

