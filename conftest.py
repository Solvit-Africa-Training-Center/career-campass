"""
Global pytest fixtures and configuration.
"""
import os
import django
import pytest
from django.conf import settings

# Use the current DJANGO_SETTINGS_MODULE or set it if not defined
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Explicitly initialize Django settings to avoid any loading issues
django.setup()

@pytest.fixture(scope='session')
def django_db_setup():
    """Configure Django database for tests."""
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
