"""
Kompatibilitets-entrypoint for uvicorn.

Eksempler på uvicorn-kommandoer:
    uvicorn app:app --reload
    uvicorn feriekomp.main:app --reload
"""

from feriekomp import app

__all__ = ["app"]
