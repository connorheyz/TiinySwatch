#!/usr/bin/env python
"""
Script to update all colormath_wrapper calls to use string-based approach.
This helps improve startup performance by delaying imports.
"""

import os
import re
import sys
from pathlib import Path

def process_file(file_path):
    """Process a single file to update colormath_wrapper calls."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Define a pattern to match colormath_wrapper calls with class arguments
    pattern = r'@colormath_wrapper\(([A-Za-z0-9_]+), ([A-Za-z0-9_]+)\)'
    
    # Replace with string-based version
    updated_content = re.sub(pattern, r"@colormath_wrapper('\1', '\2')", content)
    
    # Check if any changes were made
    if content != updated_content:
        print(f"Updating {file_path}")
        with open(file_path, 'w') as f:
            f.write(updated_content)
        return True
    return False

def update_imports(file_path):
    """Update imports to match the new string-based approach."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if this file imports colormath classes directly
    if 'from colormath.color_objects import' in content:
        # Keep imports for colormath wrapper file, remove for others
        if 'colormath_wrapper.py' not in str(file_path):
            # Replace imports with a comment
            pattern = r'from colormath\.color_objects import.*?\n'
            updated_content = re.sub(pattern, 
                '# Imports moved to colormath_wrapper for lazy loading\n', 
                content, flags=re.DOTALL)
            
            if content != updated_content:
                print(f"Removing direct imports from {file_path}")
                with open(file_path, 'w') as f:
                    f.write(updated_content)
                return True
    return False

def main():
    """Main entry point for the script."""
    # Find the conversions directory
    current_dir = Path(__file__).parent
    conversions_dir = (current_dir / '..' / 'src' / 'tiinyswatch' / 'color' / 'conversions').resolve()
    
    if not conversions_dir.exists():
        print(f"Error: Conversions directory not found at {conversions_dir}")
        return 1
    
    # Process all Python files in the conversions directory
    count = 0
    for file_path in conversions_dir.glob('*.py'):
        if process_file(file_path):
            count += 1
        
        if update_imports(file_path):
            count += 1
    
    print(f"Updated {count} files.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 