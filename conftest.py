"""
Global pytest fixtures and configuration.
"""
import os
import sys
import django
import pytest
from django.conf import settings

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Use the current DJANGO_SETTINGS_MODULE or set it if not defined
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Explicitly initialize Django settings to avoid any loading issues
django.setup()

@pytest.fixture(scope='session')
def django_db_setup(django_db_blocker):
    """Configure Django database for tests."""
    from django.core.management import call_command
    
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',  # Use in-memory database for tests
        }
    }
    
    # Unblock the database and run migrations
    with django_db_blocker.unblock():
        # Run migrations for all apps
        call_command('migrate', '--no-input')
        
        # Explicitly run migrations for specific apps
        call_command('migrate', 'catalog', '--no-input')
        call_command('migrate', 'applications', '--no-input')
