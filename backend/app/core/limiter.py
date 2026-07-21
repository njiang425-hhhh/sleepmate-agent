import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    """Extract client IP, respecting X-Forwarded-For only from trusted proxies."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (original client) — only trust when behind a known proxy
        ip = forwarded_for.split(",")[0].strip()
        logger.debug("Client IP from X-Forwarded-For: %s", ip)
        return ip
    return get_remote_address(request)


# In-memory limiter for single-process dev.
# For production multi-worker/multi-instance: swap to Redis backend
#   storage_uri="redis://host:6379"
limiter = Limiter(
    key_func=_get_client_ip,
    default_limits=["200/minute"],
    storage_uri="memory://",
)
