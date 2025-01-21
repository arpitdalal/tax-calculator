FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set up poetry in a separate directory
WORKDIR /deps
RUN pip install --no-cache-dir poetry

# Copy project files needed for poetry install
COPY pyproject.toml poetry.lock README.md ./
COPY app app/

# Install dependencies as root without creating virtualenv
ENV POETRY_VIRTUALENVS_CREATE=false
RUN poetry install --no-interaction --no-ansi

# Switch to app directory and set up for running
WORKDIR /app
RUN chown -R appuser:appuser /app /deps

# Switch to appuser for running the application
USER appuser

# Copy only necessary application code
COPY --chown=appuser:appuser app app/
COPY --chown=appuser:appuser wsgi.py ./

# Set environment variables
ENV FLASK_APP=app/__init__.py
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:$PYTHONPATH 