from PySide6.QtGui import QColor
from colormath.color_conversions import convert_color
from colormath.color_objects import (
    LabColor, sRGBColor,
    XYZColor, xyYColor, LuvColor,
    AdobeRGBColor
)
from .pantone_data import PantoneData
import numpy as np
import math

class QColorEnhanced:
    """
    This class wraps a standard QColor (treated as sRGB) and provides
    editable color values in multiple color spaces (Lab, XYZ, xyY, Luv, AdobeRGB),
    using a "dirty flag" approach for each space:
    
    - If a color space is dirty, we re-derive it from the underlying QColor (via XYZ)
      when needed.
    - If you set a color space, we convert it to XYZ immediately, then to sRGB to update QColor.
      We do *not* re-derive that space from QColor, so incremental changes won't
      round-trip away.
    - All other color spaces are marked dirty whenever one space is set.
    """
    _M1 = np.array([
        [1.716651187971268, -0.355670783776392, -0.253366281373660],
        [-0.666684351832489, 1.616481236634939, 0.015768545813911],
        [0.017639857445311, -0.042770613257809, 0.942103121235474]
    ])
    _M2 = (1/4096.0) * np.array([
        [1688, 2146, 262],
        [683, 2951, 462],
        [99, 309, 3688]
    ])
    # Composite matrix: converts XYZ directly to LMS.
    _XYZ_TO_LMS_MATRIX = _M2 @ _M1

    # Class variable to hold the precomputed Pantone candidate ITP values.
    _pantone_itp_values = None

    def __init__(self, qcolor: QColor = None):
        if qcolor == None:
            self.qcolor = QColor(255, 255, 255)
        else:
            self.qcolor = qcolor

        self._color_spaces = {
            'lab': {
                'components': {'L': 0.0, 'a': 0.0, 'b': 0.0},
                'dirty': True,
                'observer': '2',
                'illuminant': 'd50',
                'to_xyz': self._lab_to_xyz,
                'from_xyz': self._xyz_to_lab,
            },
            'xyz': {
                'components': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'dirty': True,
                'observer': '2',
                'illuminant': 'd65',
                'to_xyz': self._xyz_to_xyz,
                'from_xyz': self._xyz_from_xyz,
            },
            'xyy': {
                'components': {'x': 0.0, 'y': 0.0, 'Y': 0.0},
                'dirty': True,
                'observer': '2',
                'illuminant': 'd50',
                'to_xyz': self._xyy_to_xyz,
                'from_xyz': self._xyz_to_xyy,
            },
            'luv': {
                'components': {'L': 0.0, 'u': 0.0, 'v': 0.0},
                'dirty': True,
                'observer': '2',
                'illuminant': 'd50',
                'to_xyz': self._luv_to_xyz,
                'from_xyz': self._xyz_to_luv,
            },
            'adobe_rgb': {
                'components': {'r': 0.0, 'g': 0.0, 'b': 0.0},
                'dirty': True,
                'is_upscaled': False,
                'to_xyz': self._adobe_to_xyz,
                'from_xyz': self._xyz_to_adobe,
            }
        }

    # -----------------------------------------------------------
    # Internal conversion helpers to/from XYZ
    # -----------------------------------------------------------

    def _lab_to_xyz(self, comps):
        lab_color = LabColor(
            lab_l=comps['L'],
            lab_a=comps['a'],
            lab_b=comps['b'],
            observer=self._color_spaces['lab']['observer'],
            illuminant=self._color_spaces['lab']['illuminant']
        )
        return convert_color(lab_color, XYZColor, target_illuminant=self._color_spaces['xyz']['illuminant'])

    def _xyz_to_lab(self, xyz_color):
        lab_color = convert_color(xyz_color, LabColor)
        return {
            'L': lab_color.lab_l,
            'a': lab_color.lab_a,
            'b': lab_color.lab_b
        }

    def _xyz_to_xyz(self, comps):
        return XYZColor(
            xyz_x=comps['x'],
            xyz_y=comps['y'],
            xyz_z=comps['z'],
            observer=self._color_spaces['xyz']['observer'],
            illuminant=self._color_spaces['xyz']['illuminant']
        )

    def _xyz_from_xyz(self, xyz_color):
        return {
            'x': xyz_color.xyz_x,
            'y': xyz_color.xyz_y,
            'z': xyz_color.xyz_z
        }

    def _xyy_to_xyz(self, comps):
        cspace = xyYColor(
            xyy_x=comps['x'],
            xyy_y=comps['y'],
            xyy_Y=comps['Y'],
            observer=self._color_spaces['xyy']['observer'],
            illuminant=self._color_spaces['xyy']['illuminant']
        )
        return convert_color(cspace, XYZColor, target_illuminant=self._color_spaces['xyz']['illuminant'])

    def _xyz_to_xyy(self, xyz_color):
        xyy_obj = convert_color(xyz_color, xyYColor)
        return {
            'x': xyy_obj.xyy_x,
            'y': xyy_obj.xyy_y,
            'Y': xyy_obj.xyy_Y
        }

    def _luv_to_xyz(self, comps):
        cspace = LuvColor(
            luv_l=comps['L'],
            luv_u=comps['u'],
            luv_v=comps['v'],
            observer=self._color_spaces['luv']['observer'],
            illuminant=self._color_spaces['luv']['illuminant']
        )
        return convert_color(cspace, XYZColor, target_illuminant=self._color_spaces['xyz']['illuminant'])

    def _xyz_to_luv(self, xyz_color):
        luv_obj = convert_color(xyz_color, LuvColor)
        return {
            'L': luv_obj.luv_l,
            'u': luv_obj.luv_u,
            'v': luv_obj.luv_v
        }

    def _adobe_to_xyz(self, comps):
        adobe = AdobeRGBColor(
            comps['r'], comps['g'], comps['b'], 
            is_upscaled=self._color_spaces['adobe_rgb']['is_upscaled']
        )
        return convert_color(adobe, XYZColor, target_illuminant=self._color_spaces['xyz']['illuminant'])

    def _xyz_to_adobe(self, xyz_color):
        adobe = convert_color(xyz_color, AdobeRGBColor)
        return {
            'r': adobe.rgb_r,
            'g': adobe.rgb_g,
            'b': adobe.rgb_b
        }

    def _srgb_to_xyz(self, srgb):
        return convert_color(srgb, XYZColor, target_illuminant=self._color_spaces['xyz']['illuminant'])

    def _xyz_to_srgb(self, xyz_color):
        return convert_color(xyz_color, sRGBColor)

    # -----------------------------------------------------------
    # Dirty / sync logic
    # -----------------------------------------------------------

    def _mark_others_dirty(self, except_space):
        for space_name, space_data in self._color_spaces.items():
            if space_name != except_space:
                space_data['dirty'] = True

    def _syncQColorFromSpace(self, space_name):
        space_data = self._color_spaces[space_name]
        xyz = space_data['to_xyz'](space_data['components'])
        srgb = self._xyz_to_srgb(xyz)

        r = max(min(int(round(srgb.rgb_r * 255)), 255), 0)
        g = max(min(int(round(srgb.rgb_g * 255)), 255), 0)
        b = max(min(int(round(srgb.rgb_b * 255)), 255), 0)

        self.qcolor.setRgb(r, g, b)
        space_data['dirty'] = False
        self._mark_others_dirty(space_name)

    def _ensureSpaceInSync(self, space_name):
        space_data = self._color_spaces[space_name]
        if space_data['dirty']:
            r = self.qcolor.red()
            g = self.qcolor.green()
            b = self.qcolor.blue()
            srgb_color = sRGBColor(r / 255.0, g / 255.0, b / 255.0)
            xyz_color = self._srgb_to_xyz(srgb_color)
            new_comps = space_data['from_xyz'](xyz_color)
            space_data['components'].update(new_comps)
            space_data['dirty'] = False

    # -----------------------------------------------------------
    # Lab getters and setters
    # -----------------------------------------------------------

    def getLab(self):
        self._ensureSpaceInSync('lab')
        return self._color_spaces['lab']['components']

    def setLab(self, L=None, a=None, b=None):
        lab_data = self._color_spaces['lab']['components']
        lab_data['L'] = L if L is not None else lab_data['L']
        lab_data['a'] = a if a is not None else lab_data['a']
        lab_data['b'] = b if b is not None else lab_data['b']
        self._syncQColorFromSpace('lab')

    # -----------------------------------------------------------
    # XYZ getters and setters
    # -----------------------------------------------------------
    def getXYZ(self):
        self._ensureSpaceInSync('xyz')
        return self._color_spaces['xyz']['components']

    def setXYZ(self, x=None, y=None, z=None):
        xyz_data = self._color_spaces['xyz']['components']
        xyz_data['x'] = x if x is not None else xyz_data['x']
        xyz_data['y'] = y if y is not None else xyz_data['y']
        xyz_data['z'] = z if z is not None else xyz_data['z']
        self._syncQColorFromSpace('xyz')

    # -----------------------------------------------------------
    # xyY getters and setters
    # -----------------------------------------------------------

    def getxyY(self):
        self._ensureSpaceInSync('xyy')
        return self._color_spaces['xyy']['components']

    def setxyY(self, x=None, y=None, Y=None):
        xyy_data = self._color_spaces['xyy']['components']
        xyy_data['x'] = x if x is not None else xyy_data['x']
        xyy_data['y'] = y if y is not None else xyy_data['y']
        xyy_data['Y'] = Y if Y is not None else xyy_data['Y']
        self._syncQColorFromSpace('xyy')

    # -----------------------------------------------------------
    # Luv getters and setters
    # -----------------------------------------------------------

    def getLuv(self):
        self._ensureSpaceInSync('luv')
        return self._color_spaces['luv']['components']

    def setLuv(self, L=None, u=None, v=None):
        luv_data = self._color_spaces['luv']['components']
        luv_data['L'] = L if L is not None else luv_data['L']
        luv_data['u'] = u if u is not None else luv_data['u']
        luv_data['v'] = v if v is not None else luv_data['v']
        self._syncQColorFromSpace('luv')

    # -----------------------------------------------------------
    # AdobeRGB getters and setters
    # -----------------------------------------------------------

    def getAdobeRGB(self):
        self._ensureSpaceInSync('adobe_rgb')
        return self._color_spaces['adobe_rgb']['components']

    def setAdobeRGB(self, r=None, g=None, b=None):
        adobe_data = self._color_spaces['adobe_rgb']['components']
        adobe_data['r'] = r if r is not None else adobe_data['r']
        adobe_data['g'] = g if g is not None else adobe_data['g']
        adobe_data['b'] = b if b is not None else adobe_data['b']
        self._syncQColorFromSpace('adobe_rgb')

    def setAdobeUpscaled(self, flag: bool):
        self._color_spaces['adobe_rgb']['is_upscaled'] = flag
        # Mark dirty so next read from AdobeRGB reconverts from sRGB with new scaling
        self._color_spaces['adobe_rgb']['dirty'] = True

    # -----------------------------------------------------------
    # BT2020 getters and setters
    # -----------------------------------------------------------

    def getBT2020(self):
        self._ensureSpaceInSync('bt2020')
        return self._color_spaces['bt2020']['components']

    def setBT2020(self, r=None, g=None, b=None):
        adobe_data = self._color_spaces['bt2020']['components']
        adobe_data['r'] = r if r is not None else adobe_data['r']
        adobe_data['g'] = g if g is not None else adobe_data['g']
        adobe_data['b'] = b if b is not None else adobe_data['b']
        self._syncQColorFromSpace('bt2020')

    # -----------------------------------------------------------
    # Pantone getters and setters
    # -----------------------------------------------------------
    def getPantone(self):
        """
        Finds and returns the name of the closest Pantone color based on Lab distance.
        """
        self._ensureSpaceInSync('xyz')
        xyz = self.getXYZ()
        
        closest_name = QColorEnhanced.find_closest_pantone(np.array([xyz["x"], xyz["y"], xyz["z"]]))

        return closest_name

    def setPantone(self, name):
        xyz_value = PantoneData.get_xyz(name)
        if xyz_value:
            self.setXYZ(xyz_value[0], xyz_value[1], xyz_value[2])

    @classmethod
    def _compute_itp_from_xyz(cls, xyz_array):
        """
        Converts an array of XYZ values (shape: [N,3]) to ITP values.
        """
        # Convert XYZ to LMS in one step (vectorized).
        lms = xyz_array @ cls._XYZ_TO_LMS_MATRIX.T

        # Apply the inverse electro-optical transfer function (EOTF) elementwise.
        y = lms / 10000.0
        m1 = 0.1593017578125
        m2 = 78.84375
        c1 = 0.8359375
        c2 = 18.8515625
        c3 = 18.6875
        lms_prime = ((c1 + c2 * np.power(y, m1)) / (1 + c3 * np.power(y, m1))) ** m2

        # Convert LMS' to ITP.
        itp = np.empty_like(lms_prime)
        itp[:, 0] = 0.5 * lms_prime[:, 0] + 0.5 * lms_prime[:, 1]
        itp[:, 1] = (6610 * lms_prime[:, 0] - 13613 * lms_prime[:, 1] + 7003 * lms_prime[:, 2]) / 8192.0
        itp[:, 2] = (17933 * lms_prime[:, 0] - 17390 * lms_prime[:, 1] - 543 * lms_prime[:, 2]) / 4096.0
        return itp

    @classmethod
    def _xyz_to_itp(cls, xyz):
        """
        Converts a single XYZ value (array of shape (3,)) to an ITP value.
        """
        # Convert to LMS.
        lms = cls._XYZ_TO_LMS_MATRIX @ xyz
        y = lms / 10000.0
        m1 = 0.1593017578125
        m2 = 78.84375
        c1 = 0.8359375
        c2 = 18.8515625
        c3 = 18.6875
        lms_prime = ((c1 + c2 * np.power(y, m1)) / (1 + c3 * np.power(y, m1))) ** m2

        # Convert LMS' to ITP.
        itp = np.empty(3)
        itp[0] = 0.5 * lms_prime[0] + 0.5 * lms_prime[1]
        itp[1] = (6610 * lms_prime[0] - 13613 * lms_prime[1] + 7003 * lms_prime[2]) / 8192.0
        itp[2] = (17933 * lms_prime[0] - 17390 * lms_prime[1] - 543 * lms_prime[2]) / 4096.0
        return itp

    @classmethod
    def _initialize_pantone_itp(cls):
        """
        Precompute the Pantone candidate ITP values from the static PantoneData.
        """
        if cls._pantone_itp_values is None:
            xyz_candidates = np.array(PantoneData.xyz_values)  # shape: (N, 3)
            cls._pantone_itp_values = cls._compute_itp_from_xyz(xyz_candidates)

    @classmethod
    def find_closest_pantone(cls, target_xyz):
        """
        Finds the closest Pantone color to the given target XYZ.
        
        Parameters:
            target_xyz (array-like): XYZ values (shape: (3,)) of the target color.
        
        Returns:
            str: The name of the closest Pantone color.
        """
        cls._initialize_pantone_itp()
        # Convert the target XYZ to ITP.
        target_xyz = np.asarray(target_xyz)  # ensure it's a NumPy array of shape (3,)
        target_itp = cls._xyz_to_itp(target_xyz)

        # Compute Euclidean distances in ITP space (vectorized).
        diff = cls._pantone_itp_values - target_itp  # broadcast target_itp to each candidate.
        distances = np.linalg.norm(diff, axis=1)
        best_index = np.argmin(distances)
        return PantoneData.names[best_index]
    # -----------------------------------------------------------
    # Wrapped QColor getters and setters
    # -----------------------------------------------------------
    def red(self):
        return self.qcolor.red()

    def green(self):
        return self.qcolor.green()

    def blue(self):
        return self.qcolor.blue()

    def setRgb(self, *args, **kwargs):
        self.qcolor.setRgb(*args, **kwargs)
        # Mark all color spaces dirty, because sRGB changed externally
        self._mark_others_dirty(except_space=None)

    def value(self):
        return self.qcolor.value()

    def hsvHue(self):
        return self.qcolor.hue()

    def hsvSaturation(self):
        return self.qcolor.saturation()

    def setHsv(self, *args, **kwargs):
        self.qcolor.setHsv(*args, **kwargs)
        self._mark_others_dirty(except_space=None)

    def hslHue(self):
        return self.qcolor.hslHue()

    def hslSaturation(self):
        return self.qcolor.hslSaturation()

    def lightness(self):
        return self.qcolor.lightness()

    def setHsl(self, *args, **kwargs):
        self.qcolor.setHsl(*args, **kwargs)
        self._mark_others_dirty(except_space=None)

    def cyan(self):
        return self.qcolor.cyan()

    def magenta(self):
        return self.qcolor.magenta()

    def yellow(self):
        return self.qcolor.yellow()

    def black(self):
        return self.qcolor.black()
    
    def alpha(self):
        return self.qcolor.alpha()

    def setCmyk(self, *args, **kwargs):
        self.qcolor.setCmyk(*args, **kwargs)
        self._mark_others_dirty(except_space=None)

    def isValid(self):
        return self.qcolor.isValid()
    
    def name(self, *args, **kwargs):
        return self.qcolor.name(*args, **kwargs)

    # -----------------------------------------------------------
    # Clone method
    # -----------------------------------------------------------

    def clone(self):
        """
        Creates a new QColorEnhanced with the same QColor and
        the same values in each color space, preserving dirty flags.
        """
        new_qcolor = QColor(self.qcolor)
        new_color = QColorEnhanced(new_qcolor)

        # Copy over each color space's data
        for space_name, space_data in self._color_spaces.items():
            new_color._color_spaces[space_name]['components'] = dict(space_data['components'])
            new_color._color_spaces[space_name]['dirty'] = space_data['dirty']
            # Also copy any specialized flags:
            if 'observer' in space_data:
                new_color._color_spaces[space_name]['observer'] = space_data['observer']
            if 'illuminant' in space_data:
                new_color._color_spaces[space_name]['illuminant'] = space_data['illuminant']
            if 'is_upscaled' in space_data:
                new_color._color_spaces[space_name]['is_upscaled'] = space_data['is_upscaled']

        return new_color