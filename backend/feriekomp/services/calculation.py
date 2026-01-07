import logging
import re
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)


def _valider_dato_format(d: Any) -> date:
    """Validerer datoformat og returnerer parsert dato som date-objekt."""
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d

    if not isinstance(d, str):
        raise ValueError("Dato må være en streng eller dato-objekt")

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        raise ValueError("Dato må være i YYYY-MM-DD format")

    try:
        return datetime.strptime(d, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError("Ugyldig dato") from e


def _valider_numerisk_input(
    verdi: Any, feltnavn: str, min_verdi: float | None = None, maks_verdi: float | None = None, er_float: bool = False
) -> int | float:
    """Validerer numeriske inputfelt."""
    try:
        num_verdi = float(verdi) if er_float else int(verdi)
    except (ValueError, TypeError) as e:
        raise ValueError(f"{feltnavn} må være et gyldig tall") from e

    if min_verdi is not None and num_verdi < min_verdi:
        raise ValueError(f"{feltnavn} må være minst {min_verdi}")

    if maks_verdi is not None and num_verdi > maks_verdi:
        raise ValueError(f"{feltnavn} må være maksimalt {maks_verdi}")

    return num_verdi


def beregn_feriekompensasjon(data: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Kjerneberegning for feriekompensasjon."""
    required_fields = [
        "startdato_ferie",
        "sluttdato_ferie",
        "total_reisebelop",
        "antall_personer",
        "antall_dager_sengeleie",
        "ekstra_dag_for_legebesok",
        "dato_legebesok",
    ]

    if not isinstance(data, dict):
        return {"error": "Input må være et JSON-objekt"}, 400

    manglende_felt = [field for field in required_fields if field not in data]
    if manglende_felt:
        return {"error": f"Manglende påkrevde felt: {', '.join(manglende_felt)}"}, 400

    try:
        start = _valider_dato_format(data["startdato_ferie"])
        slutt = _valider_dato_format(data["sluttdato_ferie"])
        dato_legebesok = _valider_dato_format(data["dato_legebesok"])

        if slutt <= start:
            return {"error": "Sluttdato må være etter startdato"}, 400

        if not (start <= dato_legebesok <= slutt):
            return {"error": "Dato for legebesøk må være innenfor ferieperioden"}, 400

        total_feriedager = (slutt - start).days + 1

        if total_feriedager > 35:
            return {"error": "Ferie kan ikke overstige 35 dager (5 uker)"}, 400

        reisebelop = _valider_numerisk_input(
            data["total_reisebelop"], "Totalt reisebeløp", min_verdi=0, maks_verdi=1_000_000, er_float=True
        )

        personer = _valider_numerisk_input(data["antall_personer"], "Antall personer", min_verdi=1, maks_verdi=10)

        sykedager = _valider_numerisk_input(
            data["antall_dager_sengeleie"], "Antall sykedager", min_verdi=0, maks_verdi=35
        )

        if not isinstance(data["ekstra_dag_for_legebesok"], bool):
            return {"error": "Ekstra dag for legebesøk må være sant eller usant"}, 400

        ekstra_dag = data["ekstra_dag_for_legebesok"]

        if sykedager < 1:
            gyldige_dager = 0
        else:
            dager_etter_legebesok = (slutt - dato_legebesok).days + 1
            ekstra_dag_tillegg = 1 if ekstra_dag else 0
            gyldige_dager = min(sykedager + ekstra_dag_tillegg, dager_etter_legebesok, 10)

        dekkede_personer = min(personer, 2)

        dagspris = min(reisebelop / total_feriedager, 2000)

        total_kompensasjon = round(dagspris * gyldige_dager * dekkede_personer, 2)

        logger.info("Beregning fullført: %s NOK for %s dager", total_kompensasjon, gyldige_dager)

        return {
            "gyldige_dager": gyldige_dager,
            "dagspris_per_person": round(dagspris, 2),
            "dekkede_personer": dekkede_personer,
            "total_kompensasjon": total_kompensasjon,
            "total_feriedager": total_feriedager,
            "maks_dagspris": 2000.0,
        }, 200

    except ValueError as e:
        logger.warning("Valideringsfeil: %s", str(e))
        return {"error": "Ugyldig data i ett eller flere felt"}, 400
    except Exception as e:
        logger.error("Uventet feil i beregning: %s", str(e), exc_info=True)
        return {"error": "En uventet feil oppstod under beregning. Prøv igjen senere."}, 500
