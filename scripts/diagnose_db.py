#!/usr/bin/env python
"""
Database diagnosis script for CI environments.
This script verifies the database setup and migration state.
"""
import os
import sys

# Add the parent directory to the Python path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
print(f"Added to Python path: {parent_dir}")
print(f"Current sys.path: {sys.path}")

import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
try:
    django.setup()
    print("Django setup successful")
except Exception as e:
    print(f"Django setup failed: {e}")
    # Try to diagnose the import issue
    try:
        import core
        print("Core module can be imported")
    except ImportError as e:
        print(f"Cannot import core module: {e}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Directory contents: {os.listdir()}")
        sys.exit(1)

from django.db import connection
from django.conf import settings
from django.apps import apps
from django.db.migrations.recorder import MigrationRecorder

def check_database_connection():
    """Check if we can connect to the database."""
    print("Checking database connection...")
    try:
        connection.cursor()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    return True

def list_tables():
    """List all tables in the database."""
    print("\nChecking database tables...")
    try:
        with connection.cursor() as cursor:
            if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            elif 'postgresql' in settings.DATABASES['default']['ENGINE']:
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            else:
                print("❓ Unknown database engine")
                return
            
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                print("❌ No tables found in database")
                return False
            
            print(f"Found {len(tables)} tables:")
            for table in sorted(tables):
                print(f"  - {table}")
            return True
    except Exception as e:
        print(f"❌ Error listing tables: {e}")
        return False

def check_migrations():
    """Check the migration state."""
    print("\nChecking migration records...")
    try:
        recorder = MigrationRecorder(connection)
        applied_migrations = recorder.applied_migrations()
        
        if not applied_migrations:
            print("❌ No migrations have been applied")
            return False
        
        print(f"Found {len(applied_migrations)} applied migrations")
        
        # Check that each app has at least one migration
        for app_config in apps.get_app_configs():
            if app_config.name in ('django.contrib.admin', 'django.contrib.auth', 
                                 'django.contrib.contenttypes', 'django.contrib.sessions', 
                                 'django.contrib.messages', 'django.contrib.staticfiles',
                                 'rest_framework', 'cloudinary', 'cloudinary_storage',
                                 'drf_spectacular', 'rest_framework_simplejwt.token_blacklist'):
                continue  # Skip Django built-ins and third-party apps
                
            app_migrations = [m for m in applied_migrations if m[0] == app_config.label]
            if not app_migrations:
                print(f"❌ No migrations applied for {app_config.label}")
            else:
                print(f"✅ {app_config.label}: {len(app_migrations)} migrations")
        
        return True
    except Exception as e:
        print(f"❌ Error checking migrations: {e}")
        return False

if __name__ == "__main__":
    print("=== Database Diagnosis Tool ===")
    print(f"Django version: {django.get_version()}")
    print(f"Database engine: {settings.DATABASES['default']['ENGINE']}")
    print(f"Database name: {settings.DATABASES['default']['NAME']}")
    print()
    
    all_checks_passed = all([
        check_database_connection(),
        list_tables(),
        check_migrations()
    ])
    
    if all_checks_passed:
        print("\n✅ All database checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Some database checks failed. See details above.")
        sys.exit(1)
