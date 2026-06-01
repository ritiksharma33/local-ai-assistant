import time
from fastapi import APIRouter, Depends, HTTPException
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
import asyncio
# Safe import for active RAM management
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    ollama = None
    OLLAMA_AVAILABLE = False

router = APIRouter()


def enforce_memory_guardrail(target_model: str):
    """
    Inspects active memory layout via Ollama. Ejects any stale or unneeded model 
    occupying RAM immediately to protect hardware.
    """
    if not OLLAMA_AVAILABLE:
        return

    try:
        active_state = ollama.ps()
        for active_model in active_state.get('models', []):
            loaded_model_name = active_model.get('name', '')
            
            if target_model not in loaded_model_name:
                print(f"\n[Memory Guardrail] Ejecting stale model from RAM: {loaded_model_name}")
                # keep_alive=0 unloads it instantly
                ollama.generate(model=loaded_model_name, prompt='', keep_alive=0)
                print(f"[Memory Guardrail] RAM cleared for {target_model}.\n")
    except Exception as e:
        print(f"[Memory Guardrail Warning] Failed to inspect process status: {str(e)}")


@router.post("/generate", response_model=BaseGenerationResponse, summary="Generate text using a local SLM")
async def generate_text(
    payload: BasePromptRequest,
    http_client: httpx.AsyncClient = Depends(get_http_client),
    db: AsyncSession = Depends(get_db_session)
):
    enforce_memory_guardrail(payload.model)
    service = OllamaClientService(http_client)
    
    try:
        # Note: If your service allows passing extra options, ensure it includes keep_alive="1m"
        response_data = await service.execute_generation(payload)
        
        telemetry = InferenceTelemetry(
            endpoint_type="standard",
            model_used=payload.model,
            prompt_length=len(payload.prompt),
            tokens_per_second=response_data.tokens_per_second,
            total_time_seconds=response_data.total_time_seconds,
            execution_status="SUCCESS"
        )
        db.add(telemetry)
        await db.commit()  # Ensure metrics commit to SQLite immediately
        return response_data
        
    except Exception as e:
        telemetry = InferenceTelemetry(
            endpoint_type="standard",
            model_used=payload.model,
            prompt_length=len(payload.prompt),
            tokens_per_second=0.0,
            total_time_seconds=0.0,
            execution_status=f"FAILED: {str(e)[:40]}"
        )
        db.add(telemetry)
        await db.commit()
        raise e


@router.post("/stream", summary="Stream text using Server-Sent Events (SSE)")
async def stream_text(
    payload: BasePromptRequest,
    http_client: httpx.AsyncClient = Depends(get_http_client),
    db: AsyncSession = Depends(get_db_session)
):
    enforce_memory_guardrail(payload.model)
    service = OllamaClientService(http_client)
    
    # 1. Instantly log the stream initialization so the dashboard sees it
    telemetry = InferenceTelemetry(
        endpoint_type="stream",
        model_used=payload.model,
        prompt_length=len(payload.prompt),
        tokens_per_second=0.0,
        total_time_seconds=0.0,
        execution_status="STREAM_STARTED"
    )
    db.add(telemetry)
    await db.commit()
    await db.refresh(telemetry)
    
    record_id = telemetry.id  # Save the database ID to update it later

    async def telemetry_tracked_stream_generator():
        start_time = time.time()
        token_count = 0
        execution_status = "SUCCESS"
        
        try:
            async for chunk in service.stream_generation(payload):
                token_count += 1 
                yield chunk
                
        except asyncio.CancelledError:
            # Captures when you reload the page or close the browser tab mid-stream
            execution_status = "USER_DISCONNECTED"
            raise
        except Exception as e:
            execution_status = f"FAILED: {str(e)[:40]}"
            raise
        finally:
            end_time = time.time()
            total_time = end_time - start_time
            tps = token_count / total_time if total_time > 0 else 0.0
            
            try:
                # 2. Fetch the exact record we made earlier and update it with the final math
                record = await db.get(InferenceTelemetry, record_id)
                if record:
                    record.tokens_per_second = round(tps, 1)
                    record.total_time_seconds = round(total_time, 2)
                    record.execution_status = execution_status
                    await db.commit()
            except Exception as log_err:
                print(f"[Telemetry Logging Error] Could not update stream metrics: {log_err}")

    return StreamingResponse(
        telemetry_tracked_stream_generator(),
        media_type="text/event-stream"
    )


@router.post("/generate/structured", response_model=GeneralInsight, summary="Generate strict schema-validated JSON")
async def generate_structured_data(
    payload: StructuredAnalysisRequest,
    http_client: httpx.AsyncClient = Depends(get_http_client),
    db: AsyncSession = Depends(get_db_session)
):
    enforce_memory_guardrail(payload.model)
    start_time = time.time()
    service = StructuredValidatorService(http_client)
    
    try:
        result = await service.analyze_with_retry(payload)
        latency = time.time() - start_time
        
        telemetry = InferenceTelemetry(
            endpoint_type="structured",
            model_used=payload.model,
            prompt_length=len(payload.text_to_analyze),
            tokens_per_second=0.0, 
            total_time_seconds=round(latency, 2),
            execution_status="SUCCESS"
        )
        db.add(telemetry)
        await db.commit()
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
        await db.commit()
        raise e


@router.post("/agent/run", summary="Execute prompt through the agentic tool calling loop")
async def run_agent(
    payload: BasePromptRequest,
    http_client: httpx.AsyncClient = Depends(get_http_client),
    db: AsyncSession = Depends(get_db_session)
):
    enforce_memory_guardrail(payload.model)
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
        await db.commit()
        
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
        await db.commit()
        raise e


@router.get("/telemetry", summary="Fetch all historical inference performance records")
async def get_telemetry_data(db: AsyncSession = Depends(get_db_session)):
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