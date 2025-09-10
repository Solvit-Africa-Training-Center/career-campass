#!/usr/bin/env python3
"""
Script to verify that core modules can be imported.
"""
import os
import sys

def main():
    """Verify that core modules can be imported."""
    modules_to_check = ['core', 'catalog', 'applications']
    
    print(f"Verifying modules can be imported: {', '.join(modules_to_check)}")
    
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"✅ Successfully imported {module}")
        except ImportError as e:
            print(f"❌ Failed to import {module}: {e}")
            print(f"Current PYTHONPATH: {sys.path}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Directory contents: {os.listdir()}")
            sys.exit(1)
    
    print("All modules imported successfully!")

if __name__ == "__main__":
    main()
