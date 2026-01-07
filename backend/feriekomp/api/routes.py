import json
import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_session
from ..rate_limit import limiter
from ..schemas import BeregnInput, BeregnOutput, BesokOutput, ForklarInput, ForklarOutput
from ..services.ai import generer_forklaring
from ..services.calculation import beregn_feriekompensasjon
from ..services.visits import ok_besok

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", summary="Health check")
def health_check(session: Session = Depends(get_session)) -> dict[str, Any]:
    """Health check-endepunkt."""
    try:
        session.execute(text("SELECT 1"))
        return {"status": "healthy", "timestamp": time.time()}
    except Exception as exc:
        logger.error("Health check failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database health check failed. Sjekk database-tilkobling.",
        ) from exc


@router.post("/besok", response_model=BesokOutput, summary="Legg til besøk")
@limiter.limit("10/minute")
def legg_til_besok(request: Request, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Registrerer besøk."""
    try:
        teller = ok_besok(session)
        logger.info("Antall besøkende: %s", teller.antall)
        return teller.as_dict()
    except Exception as exc:
        logger.error("Feil i legg_til_besok: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kunne ikke registrere besøk. Prøv igjen senere.",
        ) from exc


@router.post("/beregn", response_model=BeregnOutput, summary="Beregn")
@limiter.limit("30/minute")
def beregn(
    request: Request,
    data: BeregnInput,
    with_explanation: bool = Query(False, alias="with_explanation", description="Inkluder AI-forklaring i responsen"),
    ai_debug: bool = Query(False, alias="ai_debug", description="Inkluder debug-informasjon for AI-forklaring"),
) -> dict[str, Any]:
    """Beregner feriekompensasjon."""
    try:
        data_dict = data.model_dump(mode="python")
        resultat, status_code = beregn_feriekompensasjon(data_dict)

        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=resultat)

        logger.info("Beregning fullført")

        if with_explanation:
            try:
                forklaring, meta = generer_forklaring(data_dict, resultat, ai_debug=ai_debug)
                resultat["forklaring"] = forklaring
                if ai_debug and meta:
                    resultat["ai_debug"] = json.dumps(meta, ensure_ascii=False)
            except Exception as exc:
                logger.warning("Generering av forklaring feilet: %s", exc, exc_info=True)

        return resultat
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Feil i beregning: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="En uventet feil oppstod under beregning. Prøv igjen senere.",
        ) from exc


@router.post("/forklar", response_model=ForklarOutput, summary="Forklar")
@limiter.limit("30/minute")
def forklar(
    request: Request,
    payload: ForklarInput,
    ai_debug: bool = Query(False, alias="ai_debug", description="Inkluder debug-informasjon for AI"),
) -> dict[str, Any]:
    """Genererer forklaring for beregning."""
    try:
        data = payload.input
        eksisterende = payload.resultat

        data_dict = data.model_dump(mode="python")

        if not eksisterende:
            beregning, status_code = beregn_feriekompensasjon(data_dict)
            if status_code != 200:
                raise HTTPException(status_code=status_code, detail=beregning)
            eksisterende_dict: dict[str, Any] = beregning
        else:
            eksisterende_dict = eksisterende.model_dump(mode="python") if isinstance(eksisterende, BeregnOutput) else eksisterende

        if ai_debug:
            text, meta = generer_forklaring(data_dict, eksisterende_dict, ai_debug=True)
            response: dict[str, Any] = {"forklaring": text, "resultat": eksisterende}
            if meta:
                response["ai_debug"] = json.dumps(meta, ensure_ascii=False)
            return response
        else:
            text, _ = generer_forklaring(data_dict, eksisterende_dict, ai_debug=False)
            return {"forklaring": text, "resultat": eksisterende}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Feil i forklaring: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Kunne ikke generere forklaring. Prøv igjen senere.",
        ) from exc
