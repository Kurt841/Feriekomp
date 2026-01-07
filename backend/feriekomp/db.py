import logging
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, scoped_session, sessionmaker

from .config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base-klasse for ORM-modeller."""


def _ensure_sqlite_dir() -> None:
    """Sikrer at SQLite-mappen eksisterer for lokal utvikling."""
    try:
        db_path = Path(settings.effective_database_url.replace("sqlite:///", ""))
        if db_path.suffix and not db_path.exists():
            db_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.debug(f"Ignorerer database path opprettelse feil: {e}")


_ensure_sqlite_dir()

engine = create_engine(settings.effective_database_url, future=True)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False))


def get_session() -> Generator[Session, None, None]:
    """FastAPI-avhengighet som gir en SQLAlchemy-sesjon."""
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Oppretter tabeller ved oppstart."""
    if not settings.allow_auto_create_db:
        logger.info("Automatisk database-opprettelse deaktivert; sett AUTO_CREATE_DB=true for å aktivere.")
        return
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
