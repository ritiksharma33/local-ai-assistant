import json
import time
from typing import AsyncGenerator
import httpx
from fastapi import HTTPException
from app.schemas.chat import BasePromptRequest, BaseGenerationResponse

class OllamaClientService:
    def __init__(self, http_client: httpx.AsyncClient):
        self.client = http_client

    async def execute_generation(self, payload: BasePromptRequest) -> BaseGenerationResponse:
        # Map out the exact schema expectation matching Ollama's /api/generate layout
        native_payload = {
            "model": payload.model,
            "prompt": payload.prompt,
            "stream": False,
            "keep_alive": "2m",  # <-- Added: Forces auto-unload after 120 seconds of idle time
            "options": {
                "temperature": payload.temperature
            }
        }

        start_wall_time = time.time()

        try:
            # Notice the relative route path because the base URL is mounted globally in deps.py
            response = await self.client.post("/api/generate", json=native_payload)
            response.raise_for_status()
            raw_data = response.json()
            
            end_wall_time = time.time()
            total_latency = end_wall_time - start_wall_time

            # Handle the precision math for computing generation throughput
            eval_count = raw_data.get("eval_count", 0)
            eval_duration_ns = raw_data.get("eval_duration", 0)
            
            computed_tps = 0.0
            if eval_duration_ns > 0:
                # Convert nanoseconds cleanly to true floating-point seconds
                eval_duration_sec = eval_duration_ns / 1e9
                computed_tps = eval_count / eval_duration_sec

            return BaseGenerationResponse(
                response=raw_data.get("response", ""),
                tokens_per_second=round(computed_tps, 2),
                total_time_seconds=round(total_latency, 2),
                model_used=payload.model
            )

        except httpx.HTTPStatusError as err:
            # Intercept structural errors returning out of the local inference daemon
            raise HTTPException(
                status_code=err.response.status_code,
                detail=f"Ollama execution exception: {err.response.text}"
            )
        except httpx.RequestError as err:
            # Trap system level connection drops, socket crashes or timeouts
            raise HTTPException(
                status_code=503,
                detail=f"Local engine unreachable. Ensure service is active: {err}"
            )

    async def stream_generation(self, payload: BasePromptRequest) -> AsyncGenerator[str, None]:
        """
        Streams text tokens dynamically as they are calculated by the local SLM engine.
        Uses HTTPX connection stream management to minimize buffer memory retention.
        """
        native_payload = {
            "model": payload.model,
            "prompt": payload.prompt,
            "stream": True,  # Instructs Ollama to push sequential line-delimited events
            "keep_alive": "2m",  # <-- Added: Ensures streaming connections also trigger the idle timer when finished
            "options": {
                "temperature": payload.temperature
            }
        }

        try:
            async with self.client.stream("POST", "/api/generate", json=native_payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line:
                        parsed_chunk = json.loads(line)
                        token = parsed_chunk.get("response", "")
                        if token:
                            yield token

        except httpx.HTTPStatusError as err:
            raise HTTPException(
                status_code=err.response.status_code,
                detail=f"Ollama streaming exception: {err.response.text}"
            )
        except httpx.RequestError as err:
            raise HTTPException(
                status_code=503,
                detail=f"Local engine unreachable during streaming: {err}"
            )