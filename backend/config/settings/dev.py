"""Development settings."""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0"])

# Loosen CORS in dev if not explicitly set.
if not CORS_ALLOWED_ORIGINS:  # noqa: F405
    CORS_ALLOW_ALL_ORIGINS = True
