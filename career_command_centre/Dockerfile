FROM python:3.12-slim

WORKDIR /app
COPY career_command_centre/requirements.txt ./career_command_centre/requirements.txt
RUN pip install --no-cache-dir -r career_command_centre/requirements.txt
COPY job_alert.py ./job_alert.py
COPY growth_guardrail.py ./growth_guardrail.py
COPY career_command_centre ./career_command_centre

CMD exec gunicorn --bind :${PORT:-8080} --workers 1 --threads 4 career_command_centre.wsgi:application
