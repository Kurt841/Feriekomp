from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import settings

# Rate limiting storage
# - memory://: Per-prosess (hver Gunicorn worker har egen teller)
# - redis://...: Delt mellom alle workers (anbefalt for produksjon med flere workers)
# MERK: Med memory:// og 2 workers vil rate limit være 2x (f.eks. 30/min blir 60/min totalt)
storage_uri = settings.rate_limit_storage_uri or "memory://"
limiter = Limiter(key_func=get_remote_address, storage_uri=storage_uri)

__all__ = ["limiter"]
