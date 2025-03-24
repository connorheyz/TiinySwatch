#!/usr/bin/env python
"""
Script to test loading the pantone data.
This script tests if the pantone data can be loaded successfully
and verifies that it can convert between formats correctly.
"""

import os
import sys
import time

# Add the src directory to the path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from tiinyswatch.utils.pantone_data import PantoneData
from tiinyswatch.color.color_enhanced import QColorEnhanced

def main():
    """Test loading the pantone data."""
    print("Testing Pantone data loading...")
    
    # Test loading each format
    start_time = time.time()
    PantoneData.initialize()
    print(f"Initialization time: {time.time() - start_time:.4f} seconds")
    
    # Load the data
    start_time = time.time()
    PantoneData._ensure_loaded()
    print(f"Data loading time: {time.time() - start_time:.4f} seconds")
    
    # Check that we have data
    names = PantoneData.get_names()
    xyz_values = PantoneData.get_xyz_values()
    
    if names and xyz_values:
        print(f"Successfully loaded {len(names)} Pantone colors")
        print(f"First few names: {names[:5]}")
        print(f"First few XYZ values: {xyz_values[:2]}")
        
        # Test finding closest pantone color
        print("\nTesting color conversion...")
        try:
            # Create a test color
            test_color = QColorEnhanced(srgb=[1.0, 0.0, 0.0])  # Red
            
            # Get the closest Pantone color
            start_time = time.time()
            pantone_name = test_color.get_pantone()
            conversion_time = time.time() - start_time
            
            print(f"Found closest Pantone color to red: {pantone_name} in {conversion_time:.4f} seconds")
            print("Test successful!")
        except Exception as e:
            print(f"Error during color conversion: {e}")
            import traceback
            traceback.print_exc()
            return 1
    else:
        print("Error: No Pantone data was loaded")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 