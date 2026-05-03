from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ExecutionStatus = Literal["success", "failed", "timeout", "partial"]
Environment = Literal["dev", "staging", "production"]
RiskLevel = Literal["low", "medium", "high", "critical"]


class ExecutionCreate(BaseModel):
    automation_name: str = Field(..., min_length=1, max_length=120)
    status: ExecutionStatus
    duration_seconds: float = Field(..., ge=0)
    retry_count: int = Field(..., ge=0)
    error_type: str | None = Field(default=None, max_length=80)
    error_message: str | None = None
    started_at: datetime | None = None
    environment: Environment


class PredictionResponse(BaseModel):
    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    probable_causes: list[str]
    recommended_actions: list[str]
    explanation: str


class ExecutionResponse(ExecutionCreate, PredictionResponse):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MetricsResponse(BaseModel):
    total_executions: int
    counts_by_status: dict[str, int]
    counts_by_risk_level: dict[str, int]
    average_risk_score: float
