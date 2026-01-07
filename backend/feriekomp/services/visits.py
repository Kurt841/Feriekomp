import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from ..models import AntallBesokende

logger = logging.getLogger(__name__)


def hent_besokstall(session: Session) -> AntallBesokende:
    """Hent eller initialiser besøksteller."""
    teller = session.query(AntallBesokende).first()
    if not teller:
        teller = AntallBesokende(antall=0)
        session.add(teller)
        session.commit()
        session.refresh(teller)
    return teller


def ok_besok(session: Session) -> AntallBesokende:
    """Øk besøksteller og returner oppdatert modell."""
    try:
        teller = hent_besokstall(session)
        teller.antall += 1
        teller.sist_oppdatert = datetime.now(UTC)
        session.commit()
        session.refresh(teller)
        return teller
    except Exception as e:
        logger.error("Feil ved øking av besøksteller: %s", str(e))
        session.rollback()
        raise
