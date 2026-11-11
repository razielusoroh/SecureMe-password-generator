"""
Django settings for the SecureMe Password Generator.

Privacy by design:
- No database: DATABASES is empty and no database-backed apps
  (admin, auth, sessions) are installed.
- No request logging: the django.server and django.request loggers
  only report errors, and never request bodies.
- Every response is marked no-store (see generator_app.middleware).
"""

import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# A fresh random key on each start is fine: the app has no sessions or
# accounts that need to survive a restart. Set DJANGO_SECRET_KEY to fix it.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or secrets.token_urlsafe(50)

# Debug is off so error pages never reveal code or settings.
DEBUG = os.environ.get("DJANGO_DEBUG") == "1"

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "generator_app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "generator_app.middleware.NoStoreMiddleware",
]

ROOT_URLCONF = "secureme.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    },
]

WSGI_APPLICATION = "secureme.wsgi.application"

# No database - passwords are never stored.
DATABASES = {}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Security headers
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "no-referrer"
X_FRAME_OPTIONS = "DENY"
CSRF_COOKIE_HTTPONLY = False  # the page reads the token from a meta tag instead
CSRF_COOKIE_SAMESITE = "Strict"

# Keep logs free of request details.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.server": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
