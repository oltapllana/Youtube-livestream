"""
Request and Response models for API validation using Pydantic
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class TimePreference(BaseModel):
    """Time preference constraints"""
    start: int = Field(..., description="Start time in minutes from midnight")
    end: int = Field(..., description="End time in minutes from midnight")
    preferred_genre: str = Field(..., description="Preferred content genre")
    bonus: int = Field(default=0, description="Bonus points for preference")


class YouTubeStream(BaseModel):
    """YouTube stream information"""
    url: str = Field(..., description="YouTube video URL")
    title: str = Field(..., description="Stream title")
    genre: str = Field(..., description="Content genre/category")
    channel_id: Optional[int] = Field(None, description="Mapped channel ID")


class ScheduleRequest(BaseModel):
    """Input request for scheduling"""
    opening_time: int = Field(default=480, description="Opening time in minutes from midnight (default 8 AM)")
    closing_time: int = Field(default=1380, description="Closing time in minutes from midnight (default 11 PM)")
    min_duration: int = Field(default=30, description="Minimum program duration")
    min_duration_pct: Optional[int] = Field(
        default=None,
        description="Min duration as % of shortest program (70/80/90/100)",
    )
    channels_count: int = Field(default=10, description="Number of channels (max 12)")
    max_consecutive_genre: int = Field(default=2, description="Max consecutive programs of same genre")
    switch_penalty: int = Field(default=10, description="Penalty for channel switches")
    switch_penalty_pct: Optional[int] = Field(
        default=None,
        description="Switch penalty as % of average score (3/5/7/10)",
    )
    termination_penalty: int = Field(default=20, description="Penalty for unused time")
    time_preferences: List[TimePreference] = Field(default_factory=list, description="Time-based preferences")
    bonus_pct: Optional[int] = Field(
        default=None,
        description="Time preference bonus as % of average score (3/5/7/10)",
    )
    youtube_streams: Optional[List[YouTubeStream]] = Field(default=None, description="YouTube streams (optional — backend has 12 hardcoded streams)")

    # NEW: allow category and explicit channel selection from frontend
    category_filter: Optional[List[str]] = Field(default=None, description="Filter streams by category keys")
    selected_channel_ids: Optional[List[int]] = Field(default=None, description="Specific channel IDs to restrict selection")


class Program(BaseModel):
    """Scheduled program"""
    program_id: str
    start: int
    end: int
    genre: str
    score: int
    url: Optional[str] = None


class Channel(BaseModel):
    """Channel with programs"""
    channel_id: int
    programs: List[Program]


class ScheduleResponse(BaseModel):
    """Output response with generated schedule"""
    request_id: str
    status: str  # "success", "error", "processing"
    channels: Optional[List[Channel]] = None
    total_score: Optional[float] = None
    execution_time: Optional[float] = None
    error_message: Optional[str] = None


class ScheduleStatus(BaseModel):
    """Status check response"""
    request_id: str
    status: str
    progress: Optional[int] = None  # 0-100
    message: str