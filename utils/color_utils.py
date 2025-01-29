from PySide6.QtGui import QColor
from colormath.color_conversions import convert_color
from colormath.color_objects import (
    LabColor, sRGBColor,
    XYZColor, xyYColor, LuvColor,
    AdobeRGBColor
)


class QColorEnhanced:
    """
    This class wraps a standard QColor (treated as sRGB) and provides
    editable color values in multiple color spaces (Lab, XYZ, xyY, Luv, AdobeRGB),
    using a "dirty flag" approach for each space:
    
    - If a color space is dirty, we re-derive it from the underlying QColor (sRGB)
      when needed.
    - If you set a color space, we convert it to sRGB immediately and update QColor.
      We do *not* re-derive that space from QColor, so incremental changes won't
      round-trip away.
    - All other color spaces are marked dirty whenever one space is set.
    """

    def __init__(self, qcolor: QColor):
        self.qcolor = qcolor

        # A dictionary containing our supported color spaces.
        # Each entry defines:
        #   - 'components': dict of component names/values
        #   - 'dirty': bool
        #   - 'to_srgb': func(components_dict) -> sRGBColor
        #   - 'from_srgb': func(srgb: sRGBColor) -> dict of new components
        #
        # If a space has special parameters like observer/illuminant or is_upscaled,
        # store them here so they're used properly in conversion. 
        self._color_spaces = {
            'lab': {
                'components': {'L': 0.0, 'a': 0.0, 'b': 0.0},
                'dirty': True,
                'observer': '2',
                'illuminant': 'd50',
                'to_srgb': self._lab_to_srgb,
                'from_srgb': self._srgb_to_lab,
            },
            'xyz': {
                'components': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                'dirty': True,
                'observer': '2',
                'illuminant': 'd50',
                'to_srgb': self._xyz_to_srgb,
                'from_srgb': self._srgb_to_xyz,
            },
            'xyy': {
                'components': {'x': 0.0, 'y': 0.0, 'Y': 0.0},
                'dirty': True,
                'observer': '2',
                'illuminant': 'd50',
                'to_srgb': self._xyy_to_srgb,
                'from_srgb': self._srgb_to_xyy,
            },
            'luv': {
                'components': {'L': 0.0, 'u': 0.0, 'v': 0.0},
                'dirty': True,
                'observer': '2',
                'illuminant': 'd50',
                'to_srgb': self._luv_to_srgb,
                'from_srgb': self._srgb_to_luv,
            },
            'adobe_rgb': {
                'components': {'r': 0.0, 'g': 0.0, 'b': 0.0},
                'dirty': True,
                'is_upscaled': False,  # default
                'to_srgb': self._adobe_to_srgb,
                'from_srgb': self._srgb_to_adobe,
            },
        }

    # -----------------------------------------------------------
    # Internal conversion helpers to/from sRGB
    # -----------------------------------------------------------

    def _lab_to_srgb(self, comps):
        """
        Convert stored Lab -> sRGB using colormath.
        """
        # You can override observer/illuminant if you like; using stored values here.
        cspace = LabColor(
            lab_l=comps['L'],
            lab_a=comps['a'],
            lab_b=comps['b'],
            observer=self._color_spaces['lab']['observer'],
            illuminant=self._color_spaces['lab']['illuminant']
        )
        return convert_color(cspace, sRGBColor)

    def _srgb_to_lab(self, srgb):
        """
        Convert from sRGB -> Lab. Return dict of {L, a, b}.
        """
        # Same observer/illuminant usage
        lab_obj = convert_color(srgb,LabColor)

        return {
            'L': lab_obj.lab_l,
            'a': lab_obj.lab_a,
            'b': lab_obj.lab_b
        }

    def _xyz_to_srgb(self, comps):
        """
        Convert stored XYZ -> sRGB.
        """
        cspace = XYZColor(
            xyz_x=comps['x'],
            xyz_y=comps['y'],
            xyz_z=comps['z'],
            observer=self._color_spaces['xyz']['observer'],
            illuminant=self._color_spaces['xyz']['illuminant']
        )
        return convert_color(cspace, sRGBColor)

    def _srgb_to_xyz(self, srgb):
        """
        Convert sRGB -> XYZ.
        """
        xyz_obj = convert_color(
            srgb,
            XYZColor
        )
        return {
            'x': xyz_obj.xyz_x,
            'y': xyz_obj.xyz_y,
            'z': xyz_obj.xyz_z
        }

    def _xyy_to_srgb(self, comps):
        """
        Convert xyY -> sRGB.
        """
        cspace = xyYColor(
            xyy_x=comps['x'],
            xyy_y=comps['y'],
            xyy_Y=comps['Y'],
            observer=self._color_spaces['xyy']['observer'],
            illuminant=self._color_spaces['xyy']['illuminant']
        )
        return convert_color(cspace, sRGBColor)

    def _srgb_to_xyy(self, srgb):
        """
        Convert sRGB -> xyY.
        """
        xyy_obj = convert_color(
            srgb,
            xyYColor
        )
        return {
            'x': xyy_obj.xyy_x,
            'y': xyy_obj.xyy_y,
            'Y': xyy_obj.xyy_Y
        }

    def _luv_to_srgb(self, comps):
        """
        Convert Luv -> sRGB.
        """
        cspace = LuvColor(
            luv_l=comps['L'],
            luv_u=comps['u'],
            luv_v=comps['v'],
            observer=self._color_spaces['luv']['observer'],
            illuminant=self._color_spaces['luv']['illuminant']
        )
        return convert_color(cspace, sRGBColor)

    def _srgb_to_luv(self, srgb):
        """
        Convert sRGB -> Luv.
        """
        luv_obj = convert_color(
            srgb,
            LuvColor
        )
        return {
            'L': luv_obj.luv_l,
            'u': luv_obj.luv_u,
            'v': luv_obj.luv_v
        }

    def _adobe_to_srgb(self, comps):
        """
        Convert AdobeRGB -> sRGB.
        """
        # Note that AdobeRGBColor has an is_upscaled flag that indicates whether
        # r, g, b are in [0..1] or [0..255]. Here, we store them as [0..1], so we typically
        # won't need upscaling. If you want [0..255], just adapt as needed.
        cspace = AdobeRGBColor(
            rgb_r=comps['r'],
            rgb_g=comps['g'],
            rgb_b=comps['b'],
            is_upscaled=self._color_spaces['adobe_rgb']['is_upscaled']
        )
        return convert_color(cspace, sRGBColor)

    def _srgb_to_adobe(self, srgb):
        """
        Convert sRGB -> AdobeRGB.
        """
        adobe_obj = convert_color(
            srgb,
            AdobeRGBColor,
        )
        return {
            'r': adobe_obj.rgb_r,
            'g': adobe_obj.rgb_g,
            'b': adobe_obj.rgb_b
        }

    # -----------------------------------------------------------
    # Dirty / sync logic
    # -----------------------------------------------------------

    def _mark_others_dirty(self, except_space):
        """
        Mark all color spaces dirty except the given one.
        """
        for space_name, space_data in self._color_spaces.items():
            if space_name != except_space:
                space_data['dirty'] = True

    def _syncQColorFromSpace(self, space_name):
        """
        Convert the stored components in `space_name` -> sRGB,
        update self.qcolor (clamped to 0..255),
        and mark all other color spaces dirty.
        """
        space_data = self._color_spaces[space_name]
        srgb = space_data['to_srgb'](space_data['components'])

        # Convert to 0..255 and clamp
        r = max(min(int(round(srgb.rgb_r * 255)), 255), 0)
        g = max(min(int(round(srgb.rgb_g * 255)), 255), 0)
        b = max(min(int(round(srgb.rgb_b * 255)), 255), 0)

        self.qcolor.setRgb(r, g, b)
        # This space is not dirty since it's the source of truth
        space_data['dirty'] = False

        # All other spaces become dirty
        self._mark_others_dirty(space_name)

    def _ensureSpaceInSync(self, space_name):
        """
        If the space is dirty, re-derive it from self.qcolor (treated as sRGB).
        """
        space_data = self._color_spaces[space_name]
        if space_data['dirty']:
            r = self.qcolor.red()
            g = self.qcolor.green()
            b = self.qcolor.blue()
            # Scale 0..255 -> 0..1
            srgb = sRGBColor(r / 255.0, g / 255.0, b / 255.0)
            new_comps = space_data['from_srgb'](srgb)
            space_data['components'].update(new_comps)
            space_data['dirty'] = False

    # -----------------------------------------------------------
    # Lab getters and setters
    # -----------------------------------------------------------
    # (Preserve your existing interface, just route through the new dict.)

    def getLab(self):
        self._ensureSpaceInSync('lab')
        return self._color_spaces['lab']['components']

    def setLab(self, L=None, a=None, b=None):
        lab_data = self._color_spaces['lab']['components']
        lab_data['L'] = L or lab_data['L']
        lab_data['a'] = a or lab_data['a']
        lab_data['b'] = b or lab_data['b']

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

    # If you need to toggle is_upscaled for Adobe, you can add a setter here:
    def setAdobeUpscaled(self, flag: bool):
        self._color_spaces['adobe_rgb']['is_upscaled'] = flag
        # Mark dirty so next read from AdobeRGB reconverts from sRGB with new scaling
        self._color_spaces['adobe_rgb']['dirty'] = True

    # -----------------------------------------------------------
    # Wrapped QColor getters and setters
    # (same as before)
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
