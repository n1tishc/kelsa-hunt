"""Gunicorn entrypoint; configuration is intentionally required at process start."""

from career_command_centre.app import application_from_environment


application = application_from_environment()
