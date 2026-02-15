from pydantic import BaseModel
from typing import Optional, List

# --- Request Models ---

class ReviewRequest(BaseModel):
    content: str
    platform: Optional[str] = "unknown"

class ProductScoreRequest(BaseModel):
    product_url: str

class StatsResponse(BaseModel):
    overview: List[dict]
    trend: dict

# --- Response Models ---


class AnalysisResponse(BaseModel):
    is_fake: bool
    label: str
    confidence: float
    sentiment_score: Optional[float] = 0.0
    analysis: str
