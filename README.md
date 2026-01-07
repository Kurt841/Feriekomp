# Feriekompensasjon

En feriekompensasjonskalkulator for beregning av kompensasjon ved sykdom under ferie, basert på norske forsikringsselskapers regelverk. Prosjektet består av en FastAPI-backend og en Next.js-frontend. Repostet på GitHub som et offentlig prosjekt, opprinnelig øvingsprosjekt/faktisk bruk.

## Om prosjektet

Dette prosjektet beregner feriekompensasjon i henhold til norske forsikringsselskapers regelverk. Systemet tar inn informasjon om ferieperiode, reisekostnader, antall personer, sykedager og legebesøk, og beregner kompensasjonen basert på:

- Maksimalt 2 000 kr per dag per person
- Maksimalt 2 personer kan dekkes
- Maksimalt 10 dager kan kompenseres
- Kompensasjon gis kun ved akutt sykdom/skade dokumentert av lege
- Gjelder kun for reiser inntil 5 uker

Prosjektet inkluderer også valgfri AI-integrasjon for å generere forklaringer av beregningene.

## Teknologier

- **Backend:** FastAPI, SQLAlchemy, Pydantic
- **Frontend:** Next.js, React, TypeScript, Tailwind CSS
- **Database:** SQLite (lokalt), PostgreSQL/Neon (produksjon)
- **Infrastruktur:** Nginx (reverse proxy)
- **AI (valgfritt):** OpenAI, OpenRouter, eller Ollama for forklaringer

## Kom i gang

### Krav

- Python 3.11+
- Node.js 20+
- Docker (valgfritt)

### Installasjon og kjøring

1. **Opprett og aktiver virtual environment (venv):**

   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. **Installer avhengigheter:**

   ```bash
   npm run setup
   ```

   **Merk:** `npm run setup` krever at Python virtual environment er aktivert.

3. **Start applikasjonen:**

   ```bash
   npm run dev
   ```

4. **Åpne i nettleseren:**
   - Frontend: <http://localhost:3000>
   - Backend: <http://localhost:5000>
   - API-dokumentasjon: <http://localhost:5000/docs> (Swagger UI) eller <http://localhost:5000/redoc> (ReDoc)

**Merk:** Lokalt bruker applikasjonen SQLite automatisk hvis `DEV_DATABASE_URL` ikke er satt.

### Miljøvariabler

Kopier `.env.example` til `.env` og fyll ut verdiene. Se `.env.example` for full oversikt.
Endre dem basert på dine behov.

### Med Docker

```bash
npm run docker:up
```

## Tester

```bash
npm run test:backend  # Backend tester
npm run test:e2e      # Frontend E2E tester
```

**Merk:** Installer avhengigheter først med `npm run setup`.

## API-dokumentasjon

Når backend kjører, er interaktiv API-dokumentasjon tilgjengelig på:

- Swagger UI: <http://localhost:5000/docs>
- ReDoc: <http://localhost:5000/redoc>

## Lisens

MIT-lisens
