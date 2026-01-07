# Produksjonsoppstart: Bruker Gunicorn med flere workers (ikke uvicorn med --reload)
# Sett ENV=production og WEB_CONCURRENCY i .env for å kontrollere antall workers
web: bash -lc 'cd backend && gunicorn -c gunicorn.conf.py feriekomp.main:app'
