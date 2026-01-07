"""
AI forklarings modul for feriekompensasjon beregninger.
"""

import logging
import time
from typing import Any

from ..config import settings

logger = logging.getLogger(__name__)


def _kr(n: Any, default: float = 0.0) -> str:
    try:
        val = float(n)
    except Exception:
        val = float(default)
    s = f"{val:,.0f}".replace(",", " ")
    return s


try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore

try:
    import importlib.util
    REQUESTS_AVAILABLE = importlib.util.find_spec("requests") is not None
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class AIConfig:
    OPENAI_API_KEY = settings.openai_api_key
    OPENAI_MODEL = settings.openai_model
    OPENAI_BASE_URL = settings.openai_base_url

    OLLAMA_URL = settings.ollama_url
    OLLAMA_MODEL = settings.ollama_model

    OPENROUTER_API_KEY = settings.openrouter_api_key
    OPENROUTER_MODEL = settings.openrouter_model
    OPENROUTER_BASE_URL = settings.openrouter_base_url

    AI_ENABLED = settings.ai_enabled
    AI_TIMEOUT = settings.ai_timeout

    @classmethod
    def is_openai_available(cls) -> bool:
        return OPENAI_AVAILABLE and bool(cls.OPENAI_API_KEY)

    @classmethod
    def is_ollama_available(cls) -> bool:
        return REQUESTS_AVAILABLE and bool(cls.OLLAMA_URL)

    @classmethod
    def is_openrouter_available(cls) -> bool:
        return REQUESTS_AVAILABLE and bool(cls.OPENROUTER_API_KEY)


def bygg_promt(beregning_data: dict[str, Any], beregning_resultat: dict[str, Any]) -> str:
    total_feriedager = beregning_resultat.get("total_feriedager", 0)
    gyldige_dager = beregning_resultat.get("gyldige_dager", 0)
    antall_personer = beregning_data.get("antall_personer", 1)
    total_reisebelop = beregning_data.get("total_reisebelop", 0)
    dagspris = beregning_resultat.get("dagspris_per_person", 0)
    dekkede_personer = beregning_resultat.get("dekkede_personer", antall_personer)
    total_komp = beregning_resultat.get("total_kompensasjon", 0)

    return f"""Du er en ekspert på norske ferierettigheter og feriekompensasjon. Lag en kort, vennlig forklaring (3-5 setninger) på norsk.

FERIEDATA:
• Periode: {beregning_data.get("startdato_ferie")} til {beregning_data.get("sluttdato_ferie")} ({total_feriedager} dager)
• Sykedager: {gyldige_dager} dager
• Personer: {antall_personer}
• Reisekostnader: {_kr(total_reisebelop)} kr
• Ekstra legebesøk: {"Ja" if beregning_data.get("ekstra_dag_for_legebesok") else "Nei"}

RESULTAT:
• Dagspris: {_kr(dagspris)} kr/person
• Dekkede personer: {dekkede_personer}
• Total: {float(total_komp):.2f} kr

Forklar kort regelverket og beregningen. Vær konkret og hjelpsom."""


def openai_provider(beregning_data: dict[str, Any], beregning_resultat: dict[str, Any]) -> str:
    if not OPENAI_AVAILABLE or OpenAI is None:
        raise Exception("OpenAI bibliotek ikke installert")
    if not AIConfig.is_openai_available():
        raise Exception("OpenAI ikke tilgjengelig eller API-nøkkel mangler")

    if AIConfig.OPENAI_BASE_URL:
        client = OpenAI(api_key=AIConfig.OPENAI_API_KEY, base_url=AIConfig.OPENAI_BASE_URL)
    else:
        client = OpenAI(api_key=AIConfig.OPENAI_API_KEY)

    client_to = client.with_options(timeout=AIConfig.AI_TIMEOUT)

    response = client_to.chat.completions.create(
        model=AIConfig.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "Du er en hjelpsom assistent som forklarer feriekompensasjon på norsk."},
            {"role": "user", "content": bygg_promt(beregning_data, beregning_resultat)},
        ],
        max_tokens=400,
        temperature=0.3,
    )
    content = response.choices[0].message.content if response and response.choices else None
    if not content or not content.strip():
        raise Exception("Tom respons fra OpenAI")
    return content.strip()


def openrouter_provider(beregning_data: dict[str, Any], beregning_resultat: dict[str, Any]) -> str:
    if not REQUESTS_AVAILABLE:
        raise Exception("requests bibliotek ikke installert")

    if not AIConfig.is_openrouter_available():
        raise Exception("OpenRouter ikke tilgjengelig eller API-nøkkel mangler")

    import requests

    url = f"{AIConfig.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {AIConfig.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": AIConfig.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "Du er en hjelpsom assistent som forklarer feriekompensasjon på norsk."},
            {"role": "user", "content": bygg_promt(beregning_data, beregning_resultat)},
        ],
        "temperature": 0.3,
        "max_tokens": 400,
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=AIConfig.AI_TIMEOUT)
    except requests.exceptions.RequestException as e:
        raise Exception(f"OpenRouter nettverksfeil: {e}") from e

    if r.status_code != 200:
        raise Exception(f"OpenRouter API-feil: {r.status_code} {r.text[:200]}")

    data = r.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception as e:
        raise Exception("OpenRouter respons uventet format") from e

    if not content or not content.strip():
        raise Exception("Tom respons fra OpenRouter")
    return content.strip()


def _try_ollama_provider(beregning_data: dict[str, Any], beregning_resultat: dict[str, Any]) -> str:
    if not REQUESTS_AVAILABLE:
        raise Exception("requests bibliotek ikke installert")

    if not AIConfig.is_ollama_available():
        raise Exception("Ollama ikke tilgjengelig")

    import requests

    try:
        test_response = requests.get(f"{AIConfig.OLLAMA_URL}/api/tags", timeout=3)
        if test_response.status_code != 200:
            raise Exception(f"Ollama ikke tilgjengelig: {test_response.status_code}")
        try:
            tags = test_response.json().get("models", [])
            model_names = [m.get("name", "") for m in tags]
            if AIConfig.OLLAMA_MODEL and not any(AIConfig.OLLAMA_MODEL in n for n in model_names):
                raise Exception(f"Modellen '{AIConfig.OLLAMA_MODEL}' er ikke lastet i Ollama (pull den først)")
        except Exception as e:
            logger.debug(f"Ignorerer Ollama modell-sjekk feil: {e}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Kan ikke nå Ollama: {e}") from e

    prompt = f"""Forklar denne feriekompensasjonsberegningen kort på norsk:

Ferie: {beregning_data.get("startdato_ferie")} til {beregning_data.get("sluttdato_ferie")}
Sykedager: {beregning_resultat.get("gyldige_dager", 0)} av {beregning_resultat.get("total_feriedager", 0)} dager
Dagspris: {_kr(beregning_resultat.get("dagspris_per_person", 0))} kr × {beregning_resultat.get("dekkede_personer", beregning_data.get("antall_personer", 1))} personer
Total: {float(beregning_resultat.get("total_kompensasjon", 0)):.2f} kr

Gi en kort, hjelpsom forklaring på norsk (2-4 setninger)."""

    response = requests.post(
        f"{AIConfig.OLLAMA_URL}/api/generate",
        json={
            "model": AIConfig.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 200},
        },
        timeout=AIConfig.AI_TIMEOUT,
    )

    if response.status_code != 200:
        raise Exception(f"Ollama API feil: {response.status_code}")

    result = response.json()
    content = result.get("response", "").strip()

    if not content:
        raise Exception("Tom respons fra Ollama")

    return content


def fallback_respons(beregning_data: dict[str, Any], beregning_resultat: dict[str, Any]) -> str:
    """Genererer en fallback-forklaring."""
    ekstra_dag = "ja" if beregning_data.get("ekstra_dag_for_legebesok") else "nei"
    legebesok_info = (
        f" (legebesøk: {beregning_data.get('dato_legebesok')})" if beregning_data.get("dato_legebesok") else ""
    )
    sengeleie_info = (
        f" inkludert {beregning_data.get('antall_dager_sengeleie', 0)} dager sengeleie"
        if beregning_data.get("antall_dager_sengeleie", 0) > 0
        else ""
    )

    total_feriedager = beregning_resultat.get("total_feriedager", 0)
    gyldige_dager = beregning_resultat.get("gyldige_dager", 0)
    dagspris = beregning_resultat.get("dagspris_per_person", 0)
    dekkede_personer = beregning_resultat.get("dekkede_personer", beregning_data.get("antall_personer", 1))
    total_komp = beregning_resultat.get("total_kompensasjon", 0)
    maks_dagspris = beregning_resultat.get("maks_dagspris")
    maks_txt = f" (maks {_kr(maks_dagspris)} kr/dag)" if maks_dagspris is not None else ""

    return f"""Feriekompensasjon beregning

Ferieperiode: {beregning_data.get("startdato_ferie")} til {beregning_data.get("sluttdato_ferie")} ({total_feriedager} dager)
Total reisebeløp: {_kr(beregning_data.get("total_reisebelop", 0))} kr
Antall personer: {beregning_data.get("antall_personer", 1)}

Beregningsgrunnlag:
• Godkjente sykedager: {gyldige_dager} dager{sengeleie_info}
• Dagspris per person: {_kr(dagspris)} kr{maks_txt}
• Dekkede personer: {dekkede_personer}
• Ekstra dag for legebesøk: {ekstra_dag}{legebesok_info}

Totalt: {gyldige_dager} × {_kr(dagspris)} kr × {dekkede_personer} = {float(total_komp):.2f} kr

Info: Feriekompensasjon dekker dokumenterte utgifter til sykdom under ferie, begrenset av regelverket og faktiske kostnader."""


# Når AI er aktivert, sendes beregningsdata (ferieperiode, sykedager, reisekostnader, etc.)
# til tredjepart (OpenAI, OpenRouter, eller Ollama). Dette kan inneholde personopplysninger.
# For produksjon: Vurder å informere brukere om databehandling i personvernpolicy,
# vurder databehandleravtale med AI-leverandører, og vurder å deaktivere AI som standard (ENABLE_AI=false).
def generer_forklaring(
    beregning_data: dict[str, Any], beregning_resultat: dict[str, Any], ai_debug: bool = False
) -> tuple[str, dict[str, Any] | None]:
    """Genererer en AI-basert forklaring av feriekompensjonsberegningen."""
    start_time = time.time()

    debug_info: dict[str, Any] = {
        "provider": "fallback",
        "model": "none",
        "duration_ms": None,
        "error": "AI deaktivert eller ingen leverandør tilgjengelig" if not AIConfig.AI_ENABLED else None,
        "errors": [],
        "notes": [],
        "base_url": None,
        "ai_enabled": AIConfig.AI_ENABLED,
    }

    if AIConfig.AI_ENABLED:
        if AIConfig.is_openrouter_available():
            try:
                result = openrouter_provider(beregning_data, beregning_resultat)
                debug_info.update(
                    {
                        "provider": "openrouter",
                        "model": AIConfig.OPENROUTER_MODEL,
                        "base_url": AIConfig.OPENROUTER_BASE_URL,
                        "error": None,
                    }
                )
                debug_info["duration_ms"] = int((time.time() - start_time) * 1000)
                return result, debug_info if ai_debug else None
            except Exception as e:
                logger.error("Feil ved henting av OpenRouter-respons: %s", e, exc_info=True)
                debug_info["errors"].append("OpenRouter: Klarte ikke å hente AI-svar")
                debug_info["error"] = "; ".join(debug_info["errors"])

        if AIConfig.is_openai_available():
            try:
                result = openai_provider(beregning_data, beregning_resultat)
                debug_info.update(
                    {
                        "provider": "openai",
                        "model": AIConfig.OPENAI_MODEL,
                        "base_url": AIConfig.OPENAI_BASE_URL,
                        "error": None,
                    }
                )
                debug_info["duration_ms"] = int((time.time() - start_time) * 1000)
                return result, debug_info if ai_debug else None
            except Exception as e:
                logger.error("Feil ved henting av OpenAI-respons: %s", e, exc_info=True)
                debug_info["errors"].append("OpenAI: Klarte ikke å hente AI-svar")
                debug_info["error"] = "; ".join(debug_info["errors"])

        if AIConfig.is_ollama_available():
            try:
                result = _try_ollama_provider(beregning_data, beregning_resultat)
                debug_info.update(
                    {
                        "provider": "ollama",
                        "model": AIConfig.OLLAMA_MODEL,
                        "base_url": AIConfig.OLLAMA_URL,
                        "error": None,
                    }
                )
                debug_info["duration_ms"] = int((time.time() - start_time) * 1000)
                return result, debug_info if ai_debug else None
            except Exception as e:
                logger.error("Feil ved henting av Ollama-respons: %s", e, exc_info=True)
                debug_info["errors"].append("Ollama: Klarte ikke å hente AI-svar")
                debug_info["error"] = "; ".join(debug_info["errors"])

    fallback_result = fallback_respons(beregning_data, beregning_resultat)
    debug_info["duration_ms"] = int((time.time() - start_time) * 1000)

    if debug_info.get("errors") and not debug_info.get("error"):
        debug_info["error"] = "; ".join(debug_info["errors"])

    return fallback_result, debug_info if ai_debug else None
