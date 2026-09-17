"""Coolify/gunicorn a veces arranca app.api:app."""

from app.main import app

__all__ = ["app"]
