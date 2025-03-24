#!/usr/bin/env python
"""
Script to inspect the pantone-colors.json file structure.
"""

import json
import os
import sys
from pprint import pprint

def main():
    """Inspect the pantone-colors.json file."""
    json_path = os.path.join('src', 'tiinyswatch', 'utils', 'pantone-colors.json')
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        print(f"Type of data: {type(data)}")
        
        if isinstance(data, dict):
            print(f"Keys in data: {list(data.keys())}")
            
            for key, value in data.items():
                print(f"\nKey: {key}")
                print(f"  Type: {type(value)}")
                
                if isinstance(value, list):
                    print(f"  Length: {len(value)}")
                    if value:
                        print(f"  First element type: {type(value[0])}")
                        print(f"  First few elements: {value[:3]}")
                        
                        # Try to inspect lab values
                        if key == 'values' and isinstance(value[0], list):
                            print(f"  First item characteristics:")
                            item = value[0]
                            print(f"    Length: {len(item)}")
                            print(f"    Values: {item}")
                
                elif isinstance(value, dict):
                    print(f"  Dict keys: {list(value.keys())}")
        
        # Check if this matches the expected structure
        if all(k in data for k in ['names']):
            print("\nData structure check:")
            if 'values' in data:
                if len(data['names']) == len(data['values']):
                    print("✓ names and values have matching lengths")
                else:
                    print(f"✗ Length mismatch: names={len(data['names'])}, values={len(data['values'])}")
            elif 'lab' in data:
                if len(data['names']) == len(data['lab']):
                    print("✓ names and lab have matching lengths")
                else:
                    print(f"✗ Length mismatch: names={len(data['names'])}, lab={len(data['lab'])}")
            else:
                print("✗ Missing values or lab key")
                
    except Exception as e:
        print(f"Error inspecting pantone-colors.json: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 