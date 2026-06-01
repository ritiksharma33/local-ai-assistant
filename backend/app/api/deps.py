from typing import AsyncGenerator
import httpx
from app.core.config import settings

# A singleton container for the HTTP client lifecycle
class HTTPClientProvider:
    _client: httpx.AsyncClient | None = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None or cls._client.is_closed:
            # Configure pooling limits suitable for high-throughput local inference loops
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=20)
            cls._client = httpx.AsyncClient(
                base_url=settings.OLLAMA_BASE_URL,
                limits=limits,
                timeout=settings.OLLAMA_TIMEOUT_SECONDS
            )
        return cls._client

    @classmethod
    async def close_client(cls) -> None:
        if cls._client and not cls._client.is_closed:
            await cls._client.aclose()

# Dependency function to inject the long-lived client into endpoints cleanly
async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    yield HTTPClientProvider.get_client()