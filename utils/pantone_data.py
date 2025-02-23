import json
import os

class PantoneData:

    @classmethod
    def initialize(cls):
        cls.names = []
        cls.xyz_values = []
        cls._load_data()
        
    @classmethod
    def _load_data(cls):
        xyz_json_path = os.path.join(os.path.dirname(__file__), 'pantone-xyz-colors.json')
        with open(xyz_json_path, 'r') as f:
            data = json.load(f)
            cls.names = data['names']
            cls.xyz_values = data['xyz_values']

    @classmethod
    def get_xyz(cls, name):
        if name in cls.names:
            index = cls.names.index(name)
            return cls.xyz_values[index]
        return None
    
    @classmethod
    def get_names(cls):
        return cls.names
    
    @classmethod
    def get_xyz_values(cls):
        return cls.xyz_values
   
    @classmethod
    def generate_xyz_json(cls):
        from color import QColorEnhanced
        from PySide6.QtGui import QColor
        #Convert hex values to xyz and create optimized JSON structure.
        original_path = os.path.join(os.path.dirname(__file__), 'pantone-colors.json')
        output_path = os.path.join(os.path.dirname(__file__), 'pantone-xyz-colors.json')

        with open(original_path, 'r') as f:
            data = json.load(f)
        
        colors = []
        for name, hex_value in zip(data['names'], data['values']):
            # Convert hex to xyz (D65 illuminant)
            srgb = QColorEnhanced(QColor(hex_value))
            
            xyz = srgb.getXYZ()
            
            colors.append((name, [xyz["x"], xyz["y"], xyz["z"]]))
        
        # Create sorted output structure
        output = {
            'names': [c[0] for c in colors],
            'xyz_values': [c[1] for c in colors]
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f)