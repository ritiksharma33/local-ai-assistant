from fastapi import APIRouter, Depends
import httpx
from app.api.deps import get_http_client
from app.schemas.chat import BasePromptRequest, BaseGenerationResponse

# 1. FIX: Change the import here to GeneralInsight
from app.schemas.structured import StructuredAnalysisRequest, GeneralInsight 

from app.services.ollama_client import OllamaClientService

# 2. FIX: Ensure this import points to your updated validator service
from app.services.validator import StructuredValidatorService 

router = APIRouter()

@router.post("/generate", response_model=BaseGenerationResponse, summary="Generate text using a local SLM")
async def generate_text(
    payload: BasePromptRequest,
    http_client: httpx.AsyncClient = Depends(get_http_client)
):
    service = OllamaClientService(http_client)
    return await service.execute_generation(payload)


# 3. FIX: Update the response_model here to GeneralInsight
@router.post("/generate/structured", response_model=GeneralInsight, summary="Generate strict schema-validated JSON")
async def generate_structured_data(
    payload: StructuredAnalysisRequest,
    http_client: httpx.AsyncClient = Depends(get_http_client)
):
    service = StructuredValidatorService(http_client)
    return await service.analyze_with_retry(payload)