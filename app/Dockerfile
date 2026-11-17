# Start from the official small Python 3.12 image (Debian "slim").
FROM python:3.12-slim

# Build argument: the pipeline passes the version (build number) here.
ARG APP_VERSION=local

# Don't create .pyc files; print logs immediately; make the version visible to the app.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION}

WORKDIR /app

# Create a normal (non-root) user to run the app.
RUN useradd --create-home appuser

# Copy requirements first so this layer is cached until they change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code.
COPY . .

USER appuser
EXPOSE 5000

# Docker checks /health every 30 s.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3)" || exit 1

# Production web server: Gunicorn with 2 workers on port 5000.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
