from pydantic import BaseModel, Field

class BasePromptRequest(BaseModel):
    prompt: str = Field(..., description="The main system or user prompt string.")
    model: str = Field(default="llama3.2", description="The exact local target model identifier (e.g., 'llama3.2' or 'dolphin-llama3').")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Sampling temperature.")

class BaseGenerationResponse(BaseModel):
    response: str = Field(..., description="The raw textual output from the model.")
    tokens_per_second: float = Field(..., description="Inference execution speed.")
    total_time_seconds: float = Field(..., description="Full roundtrip transaction latency.")
    model_used: str = Field(..., description="The definitive model that completed the request.")