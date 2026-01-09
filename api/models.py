"""Data models for Claude Pulse API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ModelLimit(BaseModel):
    """Rate limit for a specific model."""
    model_name: str = Field(..., description="Model name (e.g., 'sonnet', 'opus', 'all')")
    usage_percent: float = Field(..., ge=0, le=100, description="Current usage percentage")
    reset_timestamp: Optional[datetime] = Field(None, description="When the limit resets")
    reset_seconds: Optional[int] = Field(None, description="Seconds until reset")


class UsageData(BaseModel):
    """Usage data received from the Chrome extension."""
    session_usage_percent: float = Field(..., ge=0, le=100, description="Session usage percentage")
    session_reset_seconds: Optional[int] = Field(None, description="Seconds until session reset")
    weekly_usage_percent: Optional[float] = Field(None, ge=0, le=100, description="Weekly usage percentage")
    weekly_reset_time: Optional[datetime] = Field(None, description="When weekly limit resets (ISO timestamp)")
    model_limits: Optional[list[ModelLimit]] = Field(default=None, description="Model-specific limits")
    timestamp: datetime = Field(default_factory=datetime.now, description="When data was scraped")
    page_load_time: Optional[datetime] = Field(None, description="When the Claude.ai page was loaded/refreshed")


class UsageResponse(BaseModel):
    """Response containing current usage data and calculated metrics."""
    session_usage_percent: float
    session_reset_seconds: Optional[int] = None
    session_reset_formatted: Optional[str] = None
    weekly_usage_percent: Optional[float] = None
    weekly_reset_time: Optional[datetime] = None
    week_elapsed_percent: float
    pacing_ratio: Optional[float] = None
    budget_status: str = "unknown"  # "under", "over", "unknown"
    model_limits: Optional[list[ModelLimit]] = None
    last_updated: Optional[datetime] = None
    page_load_time: Optional[datetime] = None  # When Claude.ai page was last refreshed


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "1.0.0"
