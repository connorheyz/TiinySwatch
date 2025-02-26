from PySide6.QtGui import QColor
import numpy as np
from utils.pantone_data import PantoneData
from . import conversions

COLOR_SPACES = {
    'lab': {
        'keys': ['L', 'a', 'b'],
        'ranges': {'L': (0, 100), 'a': (-127, 128), 'b': (-127, 128)},
        'to_xyz': conversions.lab_to_xyz,
        'from_xyz': conversions.xyz_to_lab,
        'default_observer': '2',
        'default_illuminant': 'd50',
        'has_dirty': True
    },
    'xyz': {
        'keys': ['x', 'y', 'z'],
        'ranges': {'x': (0.0, 1.0), 'y': (0.0, 1.0), 'z': (0.0, 1.0)},
        'default_observer': '2',
        'default_illuminant': 'd65',
        'has_dirty': False
    },
    'xyy': {
        'keys': ['x', 'y', 'Y'],
        'ranges': {'x': (0.0, 1.0), 'y': (0.0, 1.0), 'Y': (0.0, 1.0)},
        'to_xyz': conversions.xyy_to_xyz,
        'from_xyz': conversions.xyz_to_xyy,
        'default_observer': '2',
        'default_illuminant': 'd50',
        'has_dirty': True
    },
    'luv': {
        'keys': ['L', 'u', 'v'],
        'ranges': {'L': (0.0, 1.0), 'u': (0.0, 1.0), 'v': (0.0, 1.0)},
        'to_xyz': conversions.luv_to_xyz,
        'from_xyz': conversions.xyz_to_luv,
        'default_observer': '2',
        'default_illuminant': 'd50',
        'has_dirty': True
    },
    'adobe_rgb': {
        'keys': ['r', 'g', 'b'],
        'ranges': {'r': (0.0, 1.0), 'g': (0.0, 1.0), 'b': (0.0, 1.0)},
        'to_xyz': conversions.adobe_to_xyz,
        'from_xyz': conversions.xyz_to_adobe,
        'has_dirty': True
    },
    'itp': {
        'keys': ['i', 't', 'p'],
        'ranges': {'i': (0.0, 1.0), 't': (-0.5, 0.5), 'p': (-0.5, 0.5)},
        'to_xyz': conversions.itp_to_xyz,
        'from_xyz': conversions.xyz_to_itp,
        'has_dirty': True
    },
    'ictcp': {
        'keys': ['i', 't', 'p'],
        'ranges': {'i': (0.0, 1.0), 't': (-0.5, 0.5), 'p': (-0.5, 0.5)},
        'to_xyz': conversions.ictcp_to_xyz,
        'from_xyz': conversions.xyz_to_ictcp,
        'has_dirty': True
    },
    'iab': {
        'keys': ['i', 'a', 'b'],
        'ranges': {'i': (0, 1.0), 'a': (-1.0, 1.0), 'b': (-1.0, 1.0)},
        'to_xyz': conversions.iab_to_xyz,
        'from_xyz': conversions.xyz_to_iab,
        'has_dirty': True
    },
    'ipt': {
        'keys': ['i', 'p', 't'],
        'ranges': {'i': (0.0, 1.0), 'p': (-0.5, 0.5), 't': (-0.5, 0.5)},
        'to_xyz': conversions.ipt_to_xyz,
        'from_xyz': conversions.xyz_to_ipt,
        'has_dirty': True
    },
    'hsv': {
        'keys': ['h', 's', 'v'],
        'ranges': {'h': (0, 359), 's': (0.0, 1.0), 'v': (0.0, 1.0)},
        'to_xyz': conversions.hsv_to_xyz,
        'from_xyz': conversions.xyz_to_hsv,
        'has_dirty': True
    },
    'hsl': {
        'keys': ['h', 's', 'l'],
        'ranges': {'h': (0.0, 360.0), 's': (0.0, 1.0), 'l': (0.0, 1.0)},
        'to_xyz': conversions.hsl_to_xyz,
        'from_xyz': conversions.xyz_to_hsl,
        'has_dirty': True
    },
    'cmyk': {
        'keys': ['c', 'm', 'y', 'k'],
        'ranges': {'c': (0.0, 1.0), 'm': (0.0, 1.0), 'y': (0.0, 1.0), 'k': (0.0, 1.0)},
        'to_xyz': conversions.cmyk_to_xyz,
        'from_xyz': conversions.xyz_to_cmyk,
        'has_dirty': True
    },
    'srgb': {
        'keys': ['r', 'g', 'b'],
        'ranges': {'r': (0.0, 1.0), 'g': (0.0, 1.0), 'b': (0.0, 1.0)},
        'to_xyz': conversions.srgb_to_xyz,
        'from_xyz': conversions.xyz_to_srgb,
        'has_dirty': True
    }
}

class QColorEnhanced:
    """Maintains a color's state in various color spaces with lazy conversions."""

    _pantone_iab_values = None
    BLACK_IAB = np.array([0, 0, 0])
    WHITE_IAB = np.array([1, 0, 0])

    def __init__(self, **kwargs):
        self._color_spaces = {}
        for space, spec in COLOR_SPACES.items():
            num_components = len(spec['keys'])
            self._color_spaces[space] = {
                'components': np.zeros(num_components, dtype=float),
                'dirty': spec.get('has_dirty', True),
            }
            if 'default_observer' in spec:
                self._color_spaces[space]['observer'] = spec['default_observer']
            if 'default_illuminant' in spec:
                self._color_spaces[space]['illuminant'] = spec['default_illuminant']

        color_spaces_in_kwargs = [key for key in kwargs if key in COLOR_SPACES]
        if len(color_spaces_in_kwargs) > 1:
            raise ValueError("Only one color space can be specified for initialization.")
        elif len(color_spaces_in_kwargs) == 1:
            space = color_spaces_in_kwargs[0]
            components = np.array(kwargs[space], dtype=float)
            expected = len(COLOR_SPACES[space]['keys'])
            if components.size != expected:
                raise ValueError(f"Expected {expected} components for {space}, got {components.size}.")
            self.set_tuple(space, components)
        else:
            self.set_tuple('srgb', [0.0, 0.0, 0.0])

        self._alpha = kwargs.get('alpha', 1.0)

    @classmethod
    def from_qcolor(cls, qcolor: QColor):
        return cls(
            srgb=[qcolor.redF(), qcolor.greenF(), qcolor.blueF()],
            alpha=qcolor.alphaF()
        )

    def _update_array_from_dict(self, space, updates: dict):
        for i, key in enumerate(COLOR_SPACES[space]['keys']):
            if key in updates:
                self._color_spaces[space]['components'][i] = updates[key]

    def _mark_others_dirty(self, except_space=None):
        except_space = except_space or []
        for space, data in self._color_spaces.items():
            if space in except_space:
                continue
            if COLOR_SPACES[space].get('has_dirty', True):
                data['dirty'] = True

    def _ensure_xyz_is_current(self):
        if not self._color_spaces['xyz']['dirty']:
            return

        if self._current_source == 'xyz':
            self._color_spaces['xyz']['dirty'] = False
            return

        canonical = self._current_source
        spec = COLOR_SPACES[canonical]
        comp_array = self._color_spaces[canonical]['components']
        observer = self._color_spaces[canonical].get('observer', spec.get('default_observer'))
        illuminant = self._color_spaces[canonical].get('illuminant', spec.get('default_illuminant'))

        args = {}
        if observer:
            args['observer'] = observer
        if illuminant:
            args['illuminant'] = illuminant

        xyz_arr = spec['to_xyz'](comp_array, **args)
        self._color_spaces['xyz']['components'] = xyz_arr
        self._color_spaces['xyz']['dirty'] = False

    def _ensure_space_in_sync(self, space):
        if space == self._current_source:
            return

        if space == 'xyz':
            self._ensure_xyz_is_current()
            return

        if self._color_spaces[space]['dirty']:
            self._ensure_xyz_is_current()
            spec = COLOR_SPACES[space]
            xyz_arr = self._color_spaces['xyz']['components']

            observer = self._color_spaces[space].get('observer', spec.get('default_observer'))
            illuminant = self._color_spaces[space].get('illuminant', spec.get('default_illuminant'))

            args = {}
            if observer:
                args['observer'] = observer
            if illuminant:
                args['illuminant'] = illuminant

            self._color_spaces[space]['components'] = spec['from_xyz'](xyz_arr, **args)
            self._color_spaces[space]['dirty'] = False

    def _update_from_space(self, space, new_values: dict):
        self._update_array_from_dict(space, new_values)
        self._update_space_components(space)

    def _update_tuple_from_space(self, space, new_values):
        self._color_spaces[space]['components'] = np.array(new_values, dtype=float)
        self._update_space_components(space)

    def _update_space_components(self, space):
        if space == 'xyz':
            self._color_spaces['xyz']['dirty'] = False
            self._current_source = 'xyz'
        else:
            self._color_spaces[space]['dirty'] = False
            self._current_source = space
            self._color_spaces['xyz']['dirty'] = True
        self._mark_others_dirty(except_space=[space])

    def get_alpha(self):
        return self._alpha

    def set_alpha(self, value):
        self._alpha = value

    def get(self, space, component=None):
        if space not in self._color_spaces:
            return None
        self._ensure_space_in_sync(space)
        comps = self._color_spaces[space]['components']
        keys = COLOR_SPACES[space]['keys']
        if component is None:
            return dict(zip(keys, comps))
        try:
            idx = keys.index(component)
            return comps[idx]
        except ValueError:
            return None

    @classmethod
    def _clamp_values(cls, values, space):
        ranges = list(COLOR_SPACES[space]['ranges'].values())
        mins = np.array([r[0] for r in ranges])
        maxs = np.array([r[1] for r in ranges])
        return np.clip(values, mins, maxs)

    def get_tuple(self, space, clamped=False):
        self._ensure_space_in_sync(space)
        components = self._color_spaces[space]['components'].copy()
        if clamped:
            return self._clamp_values(components, space)
        return components

    def set_tuple(self, space, new_values):
        if space not in self._color_spaces:
            return
        self._update_tuple_from_space(space, new_values)

    @classmethod
    def get_range(cls, space, component=None):
        if space in COLOR_SPACES:
            ranges = COLOR_SPACES[space]['ranges']
            return ranges[component] if component else ranges
        return None

    @classmethod
    def get_keys(cls, space):
        return COLOR_SPACES.get(space, {}).get('keys', [])

    def set(self, space, component=None, value=None, **kwargs):
        if space not in self._color_spaces:
            return
        valid_keys = COLOR_SPACES[space]['keys']
        updates = {}
        if component in valid_keys and value is not None:
            updates[component] = value
        updates.update({k: v for k, v in kwargs.items() if k in valid_keys})
        if updates:
            self._update_from_space(space, updates)

    @property
    def qcolor(self):
        srgb = self.get_tuple("srgb", clamped=True)
        return QColor.fromRgbF(*srgb, 1.0)
    
    def name(self):
        return self.qcolor.name()

    def is_valid(self):
        return np.all(np.isfinite(self._color_spaces['xyz']['components']))
    
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

    def copy_values(self, other):
        for space, data in other._color_spaces.items():
            self._color_spaces[space]['components'] = data['components'].copy()
            self._color_spaces[space]['dirty'] = data['dirty']
            for key in ['observer', 'illuminant']:
                if key in data:
                    self._color_spaces[space][key] = data[key]
        self._alpha = other._alpha
        self._current_source = other._current_source

    def get_pantone(self):
        xyz = self.get("xyz")
        xyz_array = np.array([xyz['x'], xyz['y'], xyz['z']])
        return self.find_closest_pantone(xyz_array)

    def set_pantone(self, name):
        xyz_value = PantoneData.get_xyz(name)
        if xyz_value:
            self.set_tuple('xyz', xyz_value)

    @classmethod
    def _initialize_pantone_iab(cls):
        if cls._pantone_iab_values is None:
            xyz_candidates = np.array(PantoneData.xyz_values)
            cls._pantone_iab_values = np.array([conversions.xyz_to_iab(c) for c in xyz_candidates])

    @classmethod
    def find_closest_pantone(cls, target_xyz):
        cls._initialize_pantone_iab()
        target_iab = conversions.xyz_to_iab(target_xyz)
        diff = cls._pantone_iab_values - target_iab
        distances = np.linalg.norm(diff, axis=1)
        return PantoneData.names[np.argmin(distances)]

    def get_bw_complement(self):
        iab = self.get_tuple("iab")
        dist_black = np.sum((iab - self.BLACK_IAB) ** 2)
        dist_white = np.sum((iab - self.WHITE_IAB) ** 2)
        return 0 if dist_black < dist_white else 1