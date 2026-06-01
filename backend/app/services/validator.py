import json
import httpx
from fastapi import HTTPException
from pydantic import ValidationError
from app.schemas.structured import GeneralInsight, StructuredAnalysisRequest

class StructuredValidatorService:
    def __init__(self, http_client: httpx.AsyncClient):
        self.client = http_client

    async def analyze_with_retry(self, payload: StructuredAnalysisRequest) -> GeneralInsight:
        # Generate schema instructions using the new GeneralInsight schema
        schema_json = json.dumps(GeneralInsight.model_json_schema(), indent=2)
        
        system_instruction = (
            "You are an analytical assistant. Read the user's text and output a JSON object "
            f"that precisely matches this JSON Schema:\n{schema_json}\n"
            "Do not include markdown formatting or extra text. Output raw JSON only."
        )

        conversation = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Analyze this text:\n{payload.text_to_analyze}"}
        ]

        for attempt in range(1, payload.max_retries + 1):
            try:
                native_payload = {
                    "model": payload.model,
                    "messages": conversation,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": payload.temperature  # Now explicitly passing down temperature!
                    }
                }

                response = await self.client.post("/api/chat", json=native_payload)
                response.raise_for_status()
                result_data = response.json()
                
                raw_content = result_data["message"]["content"]
                parsed_json = json.loads(raw_content)
                
                # Validate against GeneralInsight
                return GeneralInsight(**parsed_json)

            except (json.JSONDecodeError, ValidationError) as e:
                if attempt == payload.max_retries:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Failed validation after {payload.max_retries} tries. Error: {str(e)}"
                    )
                
                conversation.append({"role": "assistant", "content": raw_content})
                conversation.append({
                    "role": "user", 
                    "content": f"Correction required. JSON validation failed: {str(e)}. Provide valid schema matching JSON."
                })