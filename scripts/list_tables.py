#!/usr/bin/env python3
"""
Script to list all tables in the database.
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.db import connection

def list_tables():
    """List all tables in the database."""
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"Database contains {len(tables)} tables:")
    for table in tables:
        print(f"- {table[0]}")

if __name__ == "__main__":
    list_tables()
