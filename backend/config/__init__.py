"""Expose Celery app for `celery -A config worker` discovery."""

from .celery import app as celery_app

__all__ = ("celery_app",)
