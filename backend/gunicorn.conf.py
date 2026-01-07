"""
Gunicorn-konfigurasjon for produksjon.

MERK: Dette brukes når Gunicorn kjøres (via Procfile/Dockerfile CMD).
I utvikling brukes uvicorn med --reload for hot-reload (via package.json start:backend).

For produksjon:
- Sett WEB_CONCURRENCY til antall workers (anbefalt: 2-4 × CPU-kjerner)
- Sett GUNICORN_TIMEOUT hvis du har langsomme forespørsler
- Sett GUNICORN_LOG_LEVEL til "info" eller "warning" for produksjon
"""
import os

bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")
