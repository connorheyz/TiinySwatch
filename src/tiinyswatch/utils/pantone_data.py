import json
import os
import sys
import pickle
import numpy as np

class PantoneData:
    """
    Manages Pantone color data for the application.
    
    Provides access to Pantone color names and XYZ values.
    """
    # Class variables to hold data
    names = None
    xyz_values = None
    _is_initialized = False
    _np_mmap = None  # Reference to memory-mapped file
    
    @classmethod
    def initialize(cls):
        """
        Initialize class metadata but don't load data yet.
        This allows fast startup while still keeping the same API.
        """
        # We don't load data immediately
        cls._is_initialized = False
    
    @classmethod
    def _ensure_loaded(cls):
        """Ensure data is loaded before accessing it."""
        if not cls._is_initialized:
            cls._load_data()
            cls._is_initialized = True
        
    @staticmethod
    def _get_data_dir():
        """Resolve the data directory, handling frozen (PyInstaller/cx_Freeze) builds."""
        if getattr(sys, '_MEIPASS', None):
            return os.path.join(sys._MEIPASS, 'tiinyswatch', 'utils')
        return os.path.dirname(os.path.abspath(__file__))

    @classmethod
    def _load_data(cls):
        """
        Load Pantone data using the fastest available method.
        Order of preference: numpy mmap > pickle > JSON.
        """
        utils_dir = cls._get_data_dir()
        np_path = os.path.join(utils_dir, 'pantone-xyz-colors.npz')  # Use .npz instead of .npy
        old_np_path = os.path.join(utils_dir, 'pantone-xyz-colors.npy')  # Legacy format
        pickle_path = os.path.join(utils_dir, 'pantone-xyz-colors.pkl')
        json_path = os.path.join(utils_dir, 'pantone-xyz-colors.json')
        
        # Try to load using numpy's memory mapping (fastest for large arrays) - new format
        if os.path.exists(np_path):
            try:
                # Memory map the numpy arrays (minimal load time, lazy evaluation)
                cls._np_mmap = np.load(np_path, mmap_mode='r')
                
                # Extract data from numpy arrays
                cls.names = cls._np_mmap['names'].tolist()
                cls.xyz_values = cls._np_mmap['xyz_values'].tolist()
                
                # Verify data integrity
                if cls.names and cls.xyz_values and len(cls.names) == len(cls.xyz_values):
                    return
                else:
                    print("Malformed numpy data: names/values length mismatch or empty")
            except Exception as e:
                print(f"Error loading numpy data: {e}, trying pickle")
        # Try the old format if new format doesn't exist
        elif os.path.exists(old_np_path):
            try:
                # Memory map the numpy array (minimal load time, lazy evaluation)
                cls._np_mmap = np.load(old_np_path, mmap_mode='r')
                # Extract data from numpy array carefully to avoid shape issues
                if isinstance(cls._np_mmap, np.ndarray) and 'names' in cls._np_mmap.dtype.names and 'xyz_values' in cls._np_mmap.dtype.names:
                    cls.names = cls._np_mmap['names'].item() if cls._np_mmap['names'].ndim == 0 else cls._np_mmap['names'].tolist()
                    cls.xyz_values = cls._np_mmap['xyz_values'].item() if cls._np_mmap['xyz_values'].ndim == 0 else cls._np_mmap['xyz_values'].tolist()
                    # Verify data integrity
                    if cls.names and cls.xyz_values and len(cls.names) == len(cls.xyz_values):
                        return
                    else:
                        print("Malformed numpy data: names/values length mismatch or empty")
                else:
                    print("Malformed numpy file: missing expected fields")
            except Exception as e:
                print(f"Error loading numpy data: {e}, trying pickle")
        
        # Try to load from pickle (fast but loads all at once)
        if os.path.exists(pickle_path):
            try:
                with open(pickle_path, 'rb') as f:
                    data = pickle.load(f)
                    cls.names = data['names']
                    cls.xyz_values = data['xyz_values']
                    return
            except Exception as e:
                print(f"Error loading pickle data: {e}, falling back to JSON")
        
        # Fall back to JSON (slowest but most compatible)
        with open(json_path, 'r') as f:
            data = json.load(f)
            cls.names = data['names']
            cls.xyz_values = data['xyz_values']
        
        # Save in faster formats for next time
        try:
            # Save as numpy array (fastest loading)
            # Use a simpler, more robust structure for the numpy array
            cls._save_as_numpy(np_path.replace('.npz', ''))
            
            # Also save as pickle (backup)
            with open(pickle_path, 'wb') as f:
                pickle.dump({'names': cls.names, 'xyz_values': cls.xyz_values}, f, 
                           protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print(f"Could not save optimized data: {e}")

    @classmethod
    def _save_as_numpy(cls, np_path):
        """Save data as numpy array with proper structure for color processing."""
        try:
            # Convert Python lists to numpy arrays for better memory mapping
            names_array = np.array(cls.names)
            
            # Convert XYZ values to a proper numpy 2D array
            xyz_array = np.array(cls.xyz_values, dtype=np.float64)
            
            # Save each array separately for better memory mapping
            np.savez(np_path, names=names_array, xyz_values=xyz_array)
            
            print(f"Saved memory-mappable numpy arrays with {len(names_array)} colors")
        except Exception as e:
            print(f"Error saving numpy arrays: {e}")
            
            # Fallback to the old method
            dt = np.dtype([
                ('names', object),
                ('xyz_values', object)
            ])
            np_data = np.array([(cls.names, cls.xyz_values)], dtype=dt)
            np.save(np_path, np_data)

    @classmethod
    def get_xyz(cls, name):
        """Get XYZ values for a Pantone color by name."""
        cls._ensure_loaded()
        try:
            index = cls.names.index(name)
            return cls.xyz_values[index]
        except ValueError:
            return None

    @classmethod
    def get_names(cls):
        """Get a list of all Pantone color names."""
        cls._ensure_loaded()
        return cls.names

    @classmethod
    def get_xyz_values(cls):
        """Get a list of all Pantone XYZ values."""
        cls._ensure_loaded()
        return cls.xyz_values

    @classmethod
    def generate_xyz_json(cls):
        """
        Generate a JSON file with Pantone XYZ values.
        This is a utility method used during development.
        """
        import json
        from colormath.color_objects import sRGBColor, XYZColor
        from colormath.color_conversions import convert_color
        
        # Load the Pantone colors from the JSON file
        json_path = os.path.join(cls._get_data_dir(), 'pantone-colors.json')
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        # Check if the data has the correct structure
        if 'names' in data and 'values' in data:
            # Make sure we have matching names and values
            names = data.get('names', [])
            hex_values = data.get('values', [])
            
            if len(names) != len(hex_values):
                print(f"Error: Mismatch between names ({len(names)}) and values ({len(hex_values)})")
                return
                
            # Extract names and convert hex values to XYZ
            xyz_values = []
            
            for i, (name, hex_color) in enumerate(zip(names, hex_values)):
                try:
                    # Convert hex to RGB values (0-1 range)
                    hex_color = hex_color.lstrip('#')
                    if len(hex_color) == 6:
                        r = int(hex_color[0:2], 16) / 255.0
                        g = int(hex_color[2:4], 16) / 255.0
                        b = int(hex_color[4:6], 16) / 255.0
                    else:
                        print(f"Warning: Invalid hex color for {name}: {hex_color}")
                        continue
                    
                    # Convert RGB to XYZ
                    rgb_color = sRGBColor(r, g, b)
                    xyz_color = convert_color(rgb_color, XYZColor)
                    
                    # Store the XYZ values
                    xyz_values.append([xyz_color.xyz_x, xyz_color.xyz_y, xyz_color.xyz_z])
                except Exception as e:
                    print(f"Error converting color {name} (#{hex_color}): {e}")
                    xyz_values.append([0, 0, 0])  # Add placeholder
            
            # Filter out any names that didn't convert properly
            if len(names) != len(xyz_values):
                print(f"Warning: Some colors were skipped. Original: {len(names)}, Converted: {len(xyz_values)}")
                # Rebuild names list to match remaining xyz values
                valid_indices = [i for i, xyz in enumerate(xyz_values) if xyz != [0, 0, 0]]
                names = [names[i] for i in valid_indices]
                xyz_values = [xyz for xyz in xyz_values if xyz != [0, 0, 0]]
        else:
            print("Error: Unexpected format in pantone-colors.json. Needs 'names' and 'values' keys.")
            return
        
        # If we got no colors, abort
        if not names or not xyz_values:
            print("Error: No valid colors found or converted in the pantone-colors.json file")
            return
            
        print(f"Successfully processed {len(names)} Pantone colors")
            
        # Save in multiple formats
        utils_dir = cls._get_data_dir()
        
        # Save as JSON (most compatible)
        xyz_json_path = os.path.join(utils_dir, 'pantone-xyz-colors.json')
        with open(xyz_json_path, 'w') as f:
            json.dump({'names': names, 'xyz_values': xyz_values}, f)
            
        # Save as pickle (faster loading)
        pkl_path = os.path.join(utils_dir, 'pantone-xyz-colors.pkl')
        with open(pkl_path, 'wb') as f:
            pickle.dump({'names': names, 'xyz_values': xyz_values}, f,
                       protocol=pickle.HIGHEST_PROTOCOL)
                       
        # Save as numpy array (fastest loading via mmap)
        np_path = os.path.join(utils_dir, 'pantone-xyz-colors')
        cls.names = names
        cls.xyz_values = xyz_values
        cls._save_as_numpy(np_path)
        
        return f"Generated Pantone data files with {len(names)} colors" 