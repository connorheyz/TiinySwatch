#!/usr/bin/env python
"""
Script to optimize Python modules for faster loading.
This compiles .py files to bytecode and can create a zip file
of all modules for faster loading.
"""

import os
import sys
import py_compile
import compileall
import shutil
import zipfile
import argparse
from pathlib import Path

def compile_python_files(directory, force=False):
    """Compile all Python files in directory to bytecode."""
    print(f"Compiling Python files in {directory}...")
    success = compileall.compile_dir(
        directory, 
        force=force,
        quiet=0,  # 0=normal output, 1=quiet, 2=extra quiet
        legacy=False,  # Use PEP 3147 location for compiled files
        optimize=2,  # 0=no optimization, 1=remove asserts, 2=full optimization
        workers=0  # 0=auto-detect number of workers
    )
    return success

def create_zip_archive(source_dir, zip_path):
    """Create a zip archive of the compiled files."""
    print(f"Creating zip archive at {zip_path}...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Skip __pycache__ directories since we want the compiled files
            # that are in the original directories
            if '__pycache__' in root:
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                # Only include .py, .pyc, and .pyo files
                if file.endswith(('.py', '.pyc', '.pyo')):
                    # Get the relative path from source_dir
                    rel_path = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, rel_path)
    
    print(f"Zip archive created at {zip_path}")
    return True

def main():
    """Main entry point with command line arguments."""
    parser = argparse.ArgumentParser(description="Optimize Python modules for faster loading")
    parser.add_argument('--force', action='store_true', help='Force recompilation even if timestamps suggest it is not needed')
    parser.add_argument('--zip', action='store_true', help='Create a zip archive of compiled modules')
    args = parser.parse_args()
    
    # Determine the source directory
    current_dir = Path(__file__).parent
    src_dir = (current_dir / '..' / 'src').resolve()
    
    # Compile Python files
    success = compile_python_files(src_dir, force=args.force)
    
    if not success:
        print("Compilation failed. See error messages above.")
        return 1
    
    # Create zip archive if requested
    if args.zip:
        zip_path = (current_dir / '..' / 'tiinyswatch_compiled.zip').resolve()
        success = create_zip_archive(src_dir, zip_path)
        if not success:
            print("Zip archive creation failed.")
            return 1
    
    print("Optimization completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 