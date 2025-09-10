#!/usr/bin/env python3
"""
Script to verify that specific tables exist in the database.
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.db import connection

def check_tables():
    """Verify that required tables exist in the database."""
    cursor = connection.cursor()
    tables_to_check = ['catalog_institution', 'applications_application']
    
    print(f"Checking for required tables: {', '.join(tables_to_check)}")
    
    for table in tables_to_check:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
        result = cursor.fetchone()
        if result:
            print(f"✅ Table {table} exists")
        else:
            print(f"❌ Table {table} does NOT exist")
            sys.exit(1)
    
    print("All required tables exist!")

if __name__ == "__main__":
    check_tables()
