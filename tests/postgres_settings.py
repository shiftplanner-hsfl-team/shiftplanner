"""Isolierte PostgreSQL-Testdatenbank für die Produktionsabfragen (REQ-11)."""

import os

from shiftplanner.settings import *  # noqa: F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('PGDATABASE', 'shiftplanner_test'),
        'USER': os.environ.get('PGUSER', 'shiftplanner'),
        'PASSWORD': os.environ['PGPASSWORD'],
        'HOST': os.environ.get('PGHOST', '127.0.0.1'),
        'PORT': os.environ.get('PGPORT', '5432'),
    }
}
