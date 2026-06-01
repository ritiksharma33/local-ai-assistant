import time
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_http_client
from app.db.database import get_db_session
from app.db.models import InferenceTelemetry
from app.schemas.chat import BasePromptRequest, BaseGenerationResponse
from app.schemas.structured import StructuredAnalysisRequest, GeneralInsight 
from app.services.ollama_client import OllamaClientService
from app.services.validator import StructuredValidatorService
from app.services.agent_dispatcher import AgentDispatcherService

router = APIRouter()

@router.post("/generate", response_model=BaseGenerationResponse, summary="Generate text using a local SLM")
async def generate_text(
    payload: BasePromptRequest,
    http_client: httpx.AsyncClient = Depends(get_http_client),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Executes standard text generation and logs performance metrics to the telemetry database.
    """
    service = OllamaClientService(http_client)
    
    try:
        response_data = await service.execute_generation(payload)
        
        # Log successful telemetry
        telemetry = InferenceTelemetry(
            endpoint_type="standard",
            model_used=payload.model,
            prompt_length=len(payload.prompt),
            tokens_per_second=response_data.tokens_per_second,
            total_time_seconds=response_data.total_time_seconds,
            execution_status="SUCCESS"
        )
        db.add(telemetry)
        return response_data
        
    except Exception as e:
        # Log failed telemetry
        telemetry = InferenceTelemetry(
            endpoint_type="standard",
            model_used=payload.model,
            prompt_length=len(payload.prompt),
            tokens_per_second=0.0,
            total_time_seconds=0.0,
            execution_status=f"FAILED: {str(e)[:40]}"
        )
        db.add(telemetry)
        raise e


@router.post("/generate/structured", response_model=GeneralInsight, summary="Generate strict schema-validated JSON")
async def generate_structured_data(
    payload: StructuredAnalysisRequest,
    http_client: httpx.AsyncClient = Depends(get_http_client),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Executes JSON validation retry loops and stores the resulting performance profile.
    """
    start_time = time.time()
    service = StructuredValidatorService(http_client)
    
    try:
        result = await service.analyze_with_retry(payload)
        latency = time.time() - start_time
        
        telemetry = InferenceTelemetry(
            endpoint_type="structured",
            model_used=payload.model,
            prompt_length=len(payload.text_to_analyze),
            tokens_per_second=0.0, # Structured validator handles multiple internal validation hops
            total_time_seconds=round(latency, 2),
            execution_status="SUCCESS"
        )
        db.add(telemetry)
        return result
        
    except Exception as e:
        latency = time.time() - start_time
        telemetry = InferenceTelemetry(
            endpoint_type="structured",
            model_used=payload.model,
            prompt_length=len(payload.text_to_analyze),
            tokens_per_second=0.0,
            total_time_seconds=round(latency, 2),
            execution_status=f"FAILED: {str(e)[:40]}"
        )
        db.add(telemetry)
        raise e


@router.post("/stream", summary="Stream text using Server-Sent Events (SSE)")
async def stream_text(
    payload: BasePromptRequest,
    http_client: httpx.AsyncClient = Depends(get_http_client),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Streams generation tokens step-by-step while capturing baseline metadata.
    """
    service = OllamaClientService(http_client)
    
    # Track stream initialization baseline
    telemetry = InferenceTelemetry(
        endpoint_type="stream",
        model_used=payload.model,
        prompt_length=len(payload.prompt),
        tokens_per_second=0.0,
        total_time_seconds=0.0,
        execution_status="STREAM_STARTED"
    )
    db.add(telemetry)
    
    return StreamingResponse(
        service.stream_generation(payload),
        media_type="text/event-stream"
    )


@router.post("/agent/run", summary="Execute prompt through the agentic tool calling loop")
async def run_agent(
    payload: BasePromptRequest,
    http_client: httpx.AsyncClient = Depends(get_http_client),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Evaluates requests dynamically, enabling local tool routing and logging execution speed.
    """
    start_time = time.time()
    dispatcher = AgentDispatcherService(http_client)
    
    try:
        execution_result = await dispatcher.execute_agent_loop(
            user_prompt=payload.prompt, 
            model_name=payload.model
        )
        latency = time.time() - start_time
        
        telemetry = InferenceTelemetry(
            endpoint_type="agent",
            model_used=payload.model,
            prompt_length=len(payload.prompt),
            tokens_per_second=0.0,
            total_time_seconds=round(latency, 2),
            execution_status="SUCCESS"
        )
        db.add(telemetry)
        
        return BaseGenerationResponse(
            response=execution_result,
            tokens_per_second=0.0,
            total_time_seconds=round(latency, 2),
            model_used=payload.model
        )
        
    except Exception as e:
        latency = time.time() - start_time
        telemetry = InferenceTelemetry(
            endpoint_type="agent",
            model_used=payload.model,
            prompt_length=len(payload.prompt),
            tokens_per_second=0.0,
            total_time_seconds=round(latency, 2),
            execution_status=f"FAILED: {str(e)[:40]}"
        )
        db.add(telemetry)
        raise e
@router.get("/telemetry", summary="Fetch all historical inference performance records")
async def get_telemetry_data(db: AsyncSession = Depends(get_db_session)):
    """
    Retrieves execution history profiles sorted by time to feed monitoring dashboards.
    """
    result = await db.execute(
        select(InferenceTelemetry).order_by(InferenceTelemetry.timestamp.desc()).limit(100)
    )
    records = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat(),
            "endpoint_type": r.endpoint_type,
            "model_used": r.model_used,
            "prompt_length": r.prompt_length,
            "tokens_per_second": r.tokens_per_second,
            "total_time_seconds": r.total_time_seconds,
            "execution_status": r.execution_status
        }
        for r in records
    ]