from PySide6.QtGui import QColor
from colormath.color_objects import XYZColor
import numpy as np
import math
from utils.pantone_data import PantoneData
from .color_conversion import ColorConversion



class QColorEnhanced:
    """
    Maintains a color’s state in several color spaces.
    Each space’s data is stored as a NumPy array. Conversions (in
    ColorConversion) are deferred: when setting a color space (other than XYZ),
    we update only that space and mark XYZ as “dirty” (and all others).
    Then, when a different space is requested, we lazily update XYZ (from the
    canonical space—the one last updated) and use it to convert.
    """

    COLOR_SPACES = {
        'lab': {
            'keys': ['L', 'a', 'b'],
            'ranges': {'L': (0, 100), 'a': (-127, 128), 'b': (-127, 128)},
            'to_xyz': ColorConversion.lab_to_xyz,
            'from_xyz': ColorConversion.xyz_to_lab,
            'default_observer': '2',
            'default_illuminant': 'd50',
            'has_dirty': True
        },
        'xyz': {
            'keys': ['x', 'y', 'z'],
            'ranges': {'x': (0.0, 1.0), 'y': (0.0, 1.0), 'z': (0.0, 1.0)},
            'default_observer': '2',
            'default_illuminant': 'd65',
            'has_dirty': False  # always considered up–to–date when set
        },
        'xyy': {
            'keys': ['x', 'y', 'Y'],
            'ranges': {'x': (0.0, 1.0), 'y': (0.0, 1.0), 'Y': (0.0, 1.0)},
            'to_xyz': ColorConversion.xyy_to_xyz,
            'from_xyz': ColorConversion.xyz_to_xyy,
            'default_observer': '2',
            'default_illuminant': 'd50',
            'has_dirty': True
        },
        'luv': {
            'keys': ['L', 'u', 'v'],
            'ranges': {'L': (0.0, 1.0), 'u': (0.0, 1.0), 'v': (0.0, 1.0)},
            'to_xyz': ColorConversion.luv_to_xyz,
            'from_xyz': ColorConversion.xyz_to_luv,
            'default_observer': '2',
            'default_illuminant': 'd50',
            'has_dirty': True
        },
        'adobe_rgb': {
            'keys': ['r', 'g', 'b'],
            'ranges': {'r': (0.0, 1.0), 'g': (0.0, 1.0), 'b': (0.0, 1.0)},
            'to_xyz': ColorConversion.adobe_to_xyz,
            'from_xyz': ColorConversion.xyz_to_adobe,
            'has_dirty': True
        },
        'itp': {
            'keys': ['i', 't', 'p'],
            'ranges': {'i': (0.0, 1.0), 't': (-0.5, 0.5), 'p': (-0.5, 0.5)},
            'to_xyz': ColorConversion.itp_to_xyz,
            'from_xyz': ColorConversion.xyz_to_itp,
            'has_dirty': True
        },
        'ipt': {
            'keys': ['i', 'p', 't'],
            'ranges': {'i': (0.0, 1.0), 'p': (-0.5, 0.5), 't': (-0.5, 0.5)},
            'to_xyz': ColorConversion.ipt_to_xyz,
            'from_xyz': ColorConversion.xyz_to_ipt,
            'has_dirty': True
        },
        'hsv': {
            'keys': ['h', 's', 'v'],
            'ranges': {'h': (0, 359), 's': (0.0, 1.0), 'v': (0.0, 1.0)},
            'to_xyz': ColorConversion.hsv_to_xyz,
            'from_xyz': ColorConversion.xyz_to_hsv,
            'has_dirty': True
        },
        'hsl': {
            'keys': ['h', 's', 'l'],
            'ranges': {'h': (0.0, 360.0), 's': (0.0, 1.0), 'l': (0.0, 1.0)},
            'to_xyz': ColorConversion.hsl_to_xyz,
            'from_xyz': ColorConversion.xyz_to_hsl,
            'has_dirty': True
        },
        'cmyk': {
            'keys': ['c', 'm', 'y', 'k'],
            'ranges': {'c': (0.0, 1.0), 'm': (0.0, 1.0), 'y': (0.0, 1.0), 'k': (0.0, 1.0)},
            'to_xyz': ColorConversion.cmyk_to_xyz,
            'from_xyz': ColorConversion.xyz_to_cmyk,
            'has_dirty': True
        },
        'srgb': {
            'keys': ['r', 'g', 'b'],
            'ranges': {'r': (0.0, 1.0), 'g': (0.0, 1.0), 'b': (0.0, 1.0)},
            'to_xyz': ColorConversion.srgb_to_xyz,
            'from_xyz': ColorConversion.xyz_to_srgb,
            'has_dirty': True
        }
    }

    def __init__(self, qcolor: QColor = None):
        # Create per-instance state for each color space.
        self._color_spaces = {}
        for space, spec in type(self).COLOR_SPACES.items():
            num_components = len(spec['keys'])
            self._color_spaces[space] = {
                'components': np.zeros(num_components, dtype=float),
                'dirty': spec.get('has_dirty', True),
            }
            if 'default_observer' in spec:
                self._color_spaces[space]['observer'] = spec['default_observer']
            if 'default_illuminant' in spec:
                self._color_spaces[space]['illuminant'] = spec['default_illuminant']

        # If no QColor provided, default to white.
        if qcolor is None:
            r = 0.0
            g = 0.0
            b = 0.0
            self._alpha = 1.0
        else:
            self._alpha = qcolor.alpha()
            r = qcolor.red()
            g = qcolor.green()
            b = qcolor.blue()
        
        srgb_array = np.array([r, g, b], dtype=float) / 255.0

        # We use sRGB as the canonical (authoritative) color space on init.
        self._color_spaces['srgb']['components'] = srgb_array.copy()
        self._color_spaces['srgb']['dirty'] = False

        # Mark XYZ dirty so that it will be updated on demand.
        self._color_spaces['xyz']['dirty'] = True

        # Mark all other spaces (except our canonical) dirty.
        self._mark_others_dirty(except_space=['srgb'])

        # Record the current canonical space.
        self._current_source = 'srgb'

    def _update_array_from_dict(self, space, updates: dict):
        keys = type(self).COLOR_SPACES[space]['keys']
        for i, key in enumerate(keys):
            if key in updates:
                self._color_spaces[space]['components'][i] = updates[key]

    def _mark_others_dirty(self, except_space=[]):
        for space, data in self._color_spaces.items():
            # Only mark spaces that support "dirty" state.
            if space not in except_space and type(self).COLOR_SPACES[space].get('has_dirty', True):
                data['dirty'] = True

    def _ensureXYZIsCurrent(self):
        """
        Ensure that the canonical XYZ components are up to date. If XYZ is dirty,
        update it using the canonical color space's to_xyz conversion.
        """
        if not self._color_spaces['xyz']['dirty']:
            return

        # If the canonical is already XYZ, mark it as clean.
        if self._current_source == 'xyz':
            self._color_spaces['xyz']['dirty'] = False
            return

        canonical = self._current_source
        spec = type(self).COLOR_SPACES[canonical]
        observer = self._color_spaces[canonical].get('observer', spec.get('default_observer'))
        illuminant = self._color_spaces[canonical].get('illuminant', spec.get('default_illuminant'))
        to_xyz_func = spec['to_xyz']
        comp_array = self._color_spaces[canonical]['components']
        xyz_color = to_xyz_func(comp_array, observer, illuminant)
        self._color_spaces['xyz']['components'] = np.array(
            [xyz_color.xyz_x, xyz_color.xyz_y, xyz_color.xyz_z], dtype=float
        )
        self._color_spaces['xyz']['dirty'] = False

    def _ensureSpaceInSync(self, space):
        """
        When a color space is requested, ensure its components are updated from XYZ
        (which itself is updated from the canonical source if needed).
        """
        # If the requested space is the canonical (most recently updated) one,
        # it's already up to date.
        if space == self._current_source:
            return

        if space == 'xyz':
            if self._color_spaces['xyz']['dirty']:
                self._ensureXYZIsCurrent()
            return

        if self._color_spaces[space]['dirty']:
            # Ensure our canonical XYZ is current.
            self._ensureXYZIsCurrent()

            xyz_arr = self._color_spaces['xyz']['components']
            xyz_color = XYZColor(
                xyz_arr[0],
                xyz_arr[1],
                xyz_arr[2],
                observer=self._color_spaces['xyz'].get(
                    'observer', type(self).COLOR_SPACES['xyz'].get('default_observer')
                ),
                illuminant=self._color_spaces['xyz'].get(
                    'illuminant', type(self).COLOR_SPACES['xyz'].get('default_illuminant')
                )
            )
            spec = type(self).COLOR_SPACES[space]
            observer = self._color_spaces[space].get('observer', spec.get('default_observer'))
            illuminant = self._color_spaces[space].get('illuminant', spec.get('default_illuminant'))
            new_vals = spec['from_xyz'](xyz_color, observer, illuminant)
            self._color_spaces[space]['components'] = new_vals
            self._color_spaces[space]['dirty'] = False

    def _update_from_space(self, space, new_values: dict):
        """
        Update the components for a given space with new_values.
        For non–XYZ spaces, we do not immediately convert to XYZ.
        Instead, we mark XYZ (and other spaces) dirty and record this space
        as the new canonical source.
        """
        self._update_array_from_dict(space, new_values)
        if space == 'xyz':
            # If updating XYZ directly, update immediately.
            self._color_spaces['xyz']['dirty'] = False
            self._current_source = 'xyz'
        else:
            # For any other space, record it as the canonical source
            # and mark XYZ as dirty.
            self._color_spaces[space]['dirty'] = False
            self._current_source = space
            self._color_spaces['xyz']['dirty'] = True

        self._mark_others_dirty(except_space=[space])

    def _update_tuple_from_space(self, space, new_values: list):
        self._color_spaces[space]['components'] = new_values
        if space == 'xyz':
            self._color_spaces['xyz']['dirty'] = False
            self._current_source = 'xyz'
        else:
            self._color_spaces[space]['dirty'] = False
            self._current_source = space
            self._color_spaces['xyz']['dirty'] = True

        self._mark_others_dirty(except_space=[space])

    def getAlpha(self):
        return self._alpha

    def setAlpha(self, value):
        self._alpha = value

    def get(self, space, component=None):
        if space not in self._color_spaces:
            return None
        self._ensureSpaceInSync(space)
        comps = self._color_spaces[space]['components']
        keys = type(self).COLOR_SPACES[space]['keys']
        if component is None:
            return dict(zip(keys, comps))
        else:
            try:
                idx = keys.index(component)
                return comps[idx]
            except ValueError:
                return None
    
    @classmethod
    def _clampValues(cls, values, space):
        ranges = list(cls.COLOR_SPACES[space]['ranges'].values())
        clamped_components = []
        for value, range in zip (values, ranges):
            clamped_components.append(min(max(range[0], value), range[1]))
        return clamped_components

    
    def getTuple(self, space, clamped=False):
        self._ensureSpaceInSync(space)
        if (clamped):
            return QColorEnhanced._clampValues(self._color_spaces[space]['components'].copy(), space)
        return self._color_spaces[space]['components'].copy()
    
    def setTuple(self, space, new_values):
        if (space not in self._color_spaces):
            return
        self._update_tuple_from_space(space, new_values)
        

    @classmethod
    def getRange(cls, space, component=None):
        if space in cls.COLOR_SPACES:
            if component is None:
                return cls.COLOR_SPACES[space]['ranges']
            else:
                return cls.COLOR_SPACES[space]['ranges'].get(component)
        return None
    
    @classmethod
    def getKeys(cls, space):
        if space in cls.COLOR_SPACES:
            return cls.COLOR_SPACES[space]['keys']

    def set(self, space, component=None, value=None, **kwargs):
        if space not in self._color_spaces:
            return
        updates = {}
        if component is not None and value is not None:
            if component in type(self).COLOR_SPACES[space]['keys']:
                updates[component] = value
        for comp, val in kwargs.items():
            if comp in type(self).COLOR_SPACES[space]['keys']:
                updates[comp] = val
        if updates:
            self._update_from_space(space, updates)

    @property
    def qcolor(self):
        # Getting the QColor uses the sRGB values.
        srgb = self.get("srgb")
        r = max(min(int(round(srgb['r'] * 255)), 255), 0)
        g = max(min(int(round(srgb['g'] * 255)), 255), 0)
        b = max(min(int(round(srgb['b'] * 255)), 255), 0)
        return QColor(r, g, b)

    def isValid(self):
        return np.all(np.isfinite(self._color_spaces['xyz']['components']))

    def name(self, *args):
        return self.qcolor.name(*args)

    def clone(self):
        new_color = QColorEnhanced()
        for space, data in self._color_spaces.items():
            new_color._color_spaces[space]['components'] = data['components'].copy()
            new_color._color_spaces[space]['dirty'] = data['dirty']
            for key in ['observer', 'illuminant']:
                if key in data:
                    new_color._color_spaces[space][key] = data[key]
        new_color._alpha = self._alpha
        new_color._current_source = self._current_source
        return new_color
    
    def copyValues(self, other):
        for space, data in other._color_spaces.items():
            self._color_spaces[space]['components'] = data['components'].copy()
            self._color_spaces[space]['dirty'] = data['dirty']
            for key in ['observer', 'illuminant']:
                if key in data:
                    other._color_spaces[space][key] = data[key]
        self._alpha = other._alpha
        self._current_source = other._current_source

    # -----------------------------------------------------------
    # Pantone getters and setters
    # -----------------------------------------------------------
    def getPantone(self):
        """
        Finds and returns the name of the closest Pantone color based on Lab distance.
        """
        # Ensure XYZ is up-to-date.
        xyz = self.get("xyz")
        closest_name = QColorEnhanced.find_closest_pantone(np.array([xyz["x"], xyz["y"], xyz["z"]]))
        return closest_name

    def setPantone(self, name):
        xyz_value = PantoneData.get_xyz(name)
        if xyz_value:
            self.set("xyz", x=xyz_value[0], y=xyz_value[1], z=xyz_value[2])

    _pantone_itp_values = None

    @classmethod
    def _initialize_pantone_itp(cls):
        if cls._pantone_itp_values is None:
            xyz_candidates = np.array(PantoneData.xyz_values)
            cls._pantone_itp_values = ColorConversion._compute_itp_from_xyz(xyz_candidates)

    @classmethod
    def find_closest_pantone(cls, target_xyz):
        cls._initialize_pantone_itp()
        target_xyz = np.asarray(target_xyz)
        xyz_color = XYZColor(*target_xyz, illuminant='d65')
        target_itp = ColorConversion.xyz_to_itp(xyz_color)
        diff = cls._pantone_itp_values - target_itp
        distances = np.linalg.norm(diff, axis=1)
        best_index = np.argmin(distances)
        return PantoneData.names[best_index]
    
    BLACK_ITP = np.array([7.30955903e-07, -7.95644352e-23, 1.23146514e-22])
    WHITE_ITP = np.array([1.49945672e-01, -2.18083895e-06,  4.03363671e-06])

    def getBWComplement(self):
        itp = self.getTuple("itp")
        # Compute squared distances to avoid expensive sqrt operations
        dist_black = np.sum((itp - QColorEnhanced.BLACK_ITP) ** 2)
        dist_white = np.sum((itp - QColorEnhanced.WHITE_ITP) ** 2)
        return 0 if dist_black < dist_white else 1
