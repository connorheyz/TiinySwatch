#!/usr/bin/env python
"""
Script to generate Pantone color data files.
This script converts the pantone-colors.json file to optimized formats
for faster loading in the application.
"""

import os
import sys

# Add the src directory to the path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from tiinyswatch.utils.pantone_data import PantoneData

def main():
    """Generate the Pantone data files."""
    print("Starting Pantone data generation...")
    try:
        result = PantoneData.generate_xyz_json()
        print(result)
        print("Pantone data generation completed successfully.")
    except Exception as e:
        import traceback
        print(f"Error generating Pantone data: {e}")
        traceback.print_exc()
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main()) 