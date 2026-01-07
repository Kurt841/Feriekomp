from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator


class BeregnInput(BaseModel):
    """Pydantic-skjema for feriekompensasjon beregning input."""

    startdato_ferie: date = Field(..., description="Startdato for ferien (YYYY-MM-DD)")
    sluttdato_ferie: date = Field(..., description="Sluttdato for ferien (YYYY-MM-DD)")
    dato_legebesok: date = Field(..., description="Dato for legebesøk (YYYY-MM-DD)")

    total_reisebelop: float = Field(..., ge=0, le=1_000_000, description="Totalt reisebeløp i NOK")
    antall_personer: int = Field(..., ge=1, le=10, description="Antall personer på reisen")
    antall_dager_sengeleie: int = Field(..., ge=0, le=35, description="Antall dager med sengeleie")
    ekstra_dag_for_legebesok: bool = Field(..., description="Om det skal legges til ekstra dag for legebesøk")

    @field_validator("sluttdato_ferie")
    @classmethod
    def validate_sluttdato(cls, v: date, info) -> date:
        """Validerer at sluttdato er etter startdato."""
        if "startdato_ferie" in info.data:
            start = info.data["startdato_ferie"]
            if v <= start:
                raise ValueError("Sluttdato må være etter startdato")
        return v

    @model_validator(mode="after")
    def validate_dato_legebesok(self) -> "BeregnInput":
        """Validerer at legebesøksdato er innenfor ferieperioden."""
        if not (self.startdato_ferie <= self.dato_legebesok <= self.sluttdato_ferie):
            raise ValueError("Dato for legebesøk må være innenfor ferieperioden")
        return self

    @model_validator(mode="after")
    def validate_max_feriedager(self) -> "BeregnInput":
        """Validerer at ferien ikke overstiger 35 dager (5 uker)."""
        total_feriedager = (self.sluttdato_ferie - self.startdato_ferie).days + 1
        if total_feriedager > 35:
            raise ValueError("Ferie kan ikke overstige 35 dager (5 uker)")
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "startdato_ferie": "2024-07-01",
                    "sluttdato_ferie": "2024-07-14",
                    "dato_legebesok": "2024-07-05",
                    "total_reisebelop": 20000.0,
                    "antall_personer": 2,
                    "antall_dager_sengeleie": 3,
                    "ekstra_dag_for_legebesok": True,
                }
            ]
        }
    }


class BeregnOutput(BaseModel):
    """Pydantic-skjema for feriekompensasjon beregning output."""

    gyldige_dager: int = Field(..., description="Antall gyldige dager for kompensasjon")
    dagspris_per_person: float = Field(..., description="Dagspris per person (maks 2000 NOK)")
    dekkede_personer: int = Field(..., description="Antall personer som dekkes (maks 2)")
    total_kompensasjon: float = Field(..., description="Total kompensasjon i NOK")
    total_feriedager: int = Field(..., description="Totalt antall feriedager")
    maks_dagspris: float | None = Field(2000.0, description="Maksimal dagspris per person")
    forklaring: str | None = Field(None, description="AI-generert forklaring (kun hvis with_explanation=true)")
    ai_debug: str | None = Field(None, description="Debug-informasjon for AI (kun hvis ai_debug=true)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "gyldige_dager": 4,
                    "dagspris_per_person": 1428.57,
                    "dekkede_personer": 2,
                    "total_kompensasjon": 11428.56,
                    "total_feriedager": 14,
                    "maks_dagspris": 2000.0,
                }
            ]
        }
    }


class BesokOutput(BaseModel):
    """Output-skjema for besøksteller."""

    antall: int = Field(..., description="Totalt antall besøk")
    sist_oppdatert: str = Field(..., description="Tidspunkt for siste oppdatering")


class ForklarInput(BaseModel):
    """Input-skjema for forklaring-endepunkt."""

    input: BeregnInput = Field(..., description="Input-data for beregning")
    resultat: BeregnOutput | None = Field(None, description="Eksisterende beregningsresultat (valgfritt)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "input": {
                        "startdato_ferie": "2024-07-01",
                        "sluttdato_ferie": "2024-07-14",
                        "dato_legebesok": "2024-07-05",
                        "total_reisebelop": 20000.0,
                        "antall_personer": 2,
                        "antall_dager_sengeleie": 3,
                        "ekstra_dag_for_legebesok": True,
                    },
                    "resultat": None,
                }
            ]
        }
    }


class ForklarOutput(BaseModel):
    """Output-skjema for forklaring-endepunkt."""

    forklaring: str = Field(..., description="Generert forklaring av beregningen")
    resultat: BeregnOutput = Field(..., description="Beregningsresultatet")
    ai_debug: str | None = Field(None, description="Debug-informasjon for AI (kun hvis ai_debug=true)")

