import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from .api import router
from .config import settings
from .db import init_db
from .rate_limit import limiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("feriekomp")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database tilkobling vellykket")
    yield
    logger.info("Avslutter...")


def create_app() -> FastAPI:
    """
    Oppretter og konfigurerer FastAPI-applikasjonen.
    
    PRODUKSJON:
    - I produksjon: Bruk Gunicorn (via Procfile/Dockerfile CMD), ikke uvicorn med --reload
    - Sett ENV=production (styrer app-oppførsel: database-valg, auto_create_db, etc.)
    - Sett TRUST_PROXY=true hvis bak reverse proxy (Nginx)
    - Sett AUTO_CREATE_DB=false
    - Sett ALLOWED_ORIGINS til din offentlige frontend-domene
    """
    app = FastAPI(
        title="Feriekompensasjon API",
        description="API for beregning av feriekompensasjon",
        version="2.1.0",
        lifespan=lifespan,
    )

    # ProxyHeadersMiddleware: Nødvendig når bak reverse proxy (Nginx)
    # Tillater at applikasjonen stoler på X-Forwarded-* headers for korrekt IP og protokoll
    if settings.trust_proxy:
        app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:  # noqa: ARG001
        """Håndterer rate limit-overskridelser."""
        from slowapi import _rate_limit_exceeded_handler
        return _rate_limit_exceeded_handler(request, exc)

    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):  # noqa: ARG001
        """Logger middleware for innkommende forespørsler og responser."""
        start_time = time.time() if settings.environment == "development" else 0.0
        if settings.environment == "development":
            logger.info(f"Request: {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            if settings.environment == "development":
                process_time = time.time() - start_time
                logger.info(
                    f"Response: {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)"
                )
            return response
        except Exception as exc:
            if settings.environment == "development":
                process_time = time.time() - start_time
                logger.error(f"Error in {request.method} {request.url.path}: {exc} ({process_time:.3f}s)")
            else:
                logger.error(f"Error in {request.method} {request.url.path}: {exc}")
            raise

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):  # noqa: ARG001
        """Legger til sikkerhetsheaders i responser."""
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        if settings.environment == "production" or str(settings.force_https).lower() == "true":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    app.include_router(router)
    return app


app = create_app()
