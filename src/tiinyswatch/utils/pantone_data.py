import json
import os

class PantoneData:
    """
    Manages Pantone color data for the application.
    
    Provides access to Pantone color names and XYZ values.
    """
    
    @classmethod
    def initialize(cls):
        """Initialize the Pantone data by loading from JSON files."""
        cls.names = []
        cls.xyz_values = []
        cls._load_data()
        
    @classmethod
    def _load_data(cls):
        """Load Pantone data from JSON files."""
        xyz_json_path = os.path.join(os.path.dirname(__file__), 'pantone-xyz-colors.json')
        with open(xyz_json_path, 'r') as f:
            data = json.load(f)
            cls.names = data['names']
            cls.xyz_values = data['xyz_values']

    @classmethod
    def get_xyz(cls, name):
        """Get XYZ values for a Pantone color by name."""
        try:
            index = cls.names.index(name)
            return cls.xyz_values[index]
        except ValueError:
            return None

    @classmethod
    def get_names(cls):
        """Get a list of all Pantone color names."""
        return cls.names

    @classmethod
    def get_xyz_values(cls):
        """Get a list of all Pantone XYZ values."""
        return cls.xyz_values

    @classmethod
    def generate_xyz_json(cls):
        """
        Generate a JSON file with Pantone XYZ values.
        This is a utility method used during development.
        """
        import json
        from colormath.color_objects import LabColor, XYZColor
        from colormath.color_conversions import convert_color
        
        # Load the Pantone colors from the JSON file
        json_path = os.path.join(os.path.dirname(__file__), 'pantone-colors.json')
        with open(json_path, 'r') as f:
            pantone_colors = json.load(f)
        
        # Extract names and Lab values
        names = []
        xyz_values = []
        
        for color in pantone_colors:
            name = color['name']
            lab = color['lab']
            
            # Convert Lab to XYZ
            lab_color = LabColor(lab_l=lab[0], lab_a=lab[1], lab_b=lab[2])
            xyz_color = convert_color(lab_color, XYZColor)
            
            # Store the name and XYZ values
            names.append(name)
            xyz_values.append([xyz_color.xyz_x, xyz_color.xyz_y, xyz_color.xyz_z])
        
        # Save to a new JSON file
        xyz_json_path = os.path.join(os.path.dirname(__file__), 'pantone-xyz-colors.json')
        with open(xyz_json_path, 'w') as f:
            json.dump({'names': names, 'xyz_values': xyz_values}, f) 