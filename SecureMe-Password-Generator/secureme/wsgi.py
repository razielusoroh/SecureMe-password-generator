"""WSGI entry point, used when deploying to a production web server."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secureme.settings")

application = get_wsgi_application()
