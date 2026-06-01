from pydantic import BaseModel, Field
from typing import List

# A much more practical, general-purpose schema for structured knowledge extraction
class GeneralInsight(BaseModel):
    core_phenomenon: str = Field(..., description="The main subject or feeling being discussed.")
    contributing_factors: List[str] = Field(..., description="Environmental, biological, or physical reasons for this state.")
    actionable_advice: List[str] = Field(..., description="Practical steps the user can take right now to improve their situation.")
    scientific_context: str = Field(..., description="A short biological or psychological explanation of why this happens.")

class StructuredAnalysisRequest(BaseModel):
    text_to_analyze: str
    model: str = "llama3.2"
    temperature: float = Field(default=0.4, ge=0.0, le=1.0, description="Sampling temperature for creativity control.")
    max_retries: int = 3