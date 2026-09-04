from __future__ import annotations

from enum import StrEnum
from pydantic import BaseModel, Field


class AIAction(StrEnum):
    GENERATE = "GENERATE"
    REWRITE = "REWRITE"
    IMPROVE = "IMPROVE"
    SHORTEN = "SHORTEN"
    EXPAND = "EXPAND"
    CHANGE_TONE = "CHANGE_TONE"
    ADAPT_PLATFORM = "ADAPT_PLATFORM"
    IDEATE = "IDEATE"
    SUGGEST_REPLY = "SUGGEST_REPLY"


class AITone(StrEnum):
    FORMAL = "FORMAL"
    PROFESSIONAL = "PROFESSIONAL"
    CASUAL = "CASUAL"
    FRIENDLY = "FRIENDLY"
    TECHNICAL = "TECHNICAL"
    PROMOTIONAL = "PROMOTIONAL"


class AIPlatform(StrEnum):
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    LINKEDIN = "LINKEDIN"


class AIGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000, description="Topic, idea, or instructions")
    platform: AIPlatform | None = Field(default=None, description="Target social platform")
    tone: AITone = Field(default=AITone.PROFESSIONAL, description="Tone of voice")
    audience: str | None = Field(default=None, max_length=500, description="Target audience")
    objective: str | None = Field(default=None, max_length=500, description="Goal e.g. engagement, conversion")
    editorial_context: str | None = Field(default=None, max_length=1000, description="Brand editorial guidelines")


class AIRewriteRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="Text to rewrite")
    tone: AITone | None = Field(default=None, description="Target tone")
    platform: AIPlatform | None = Field(default=None, description="Target platform")
    editorial_context: str | None = Field(default=None, max_length=1000)


class AIImproveRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="Text to improve")
    platform: AIPlatform | None = Field(default=None, description="Target platform")
    editorial_context: str | None = Field(default=None, max_length=1000)


class AIShortenRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="Text to shorten")
    platform: AIPlatform | None = Field(default=None, description="Target platform")
    editorial_context: str | None = Field(default=None, max_length=1000)


class AIExpandRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="Text to expand")
    platform: AIPlatform | None = Field(default=None, description="Target platform")
    editorial_context: str | None = Field(default=None, max_length=1000)


class AIChangeToneRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="Text to transform")
    tone: AITone = Field(..., description="Desired tone")
    platform: AIPlatform | None = Field(default=None, description="Target platform")
    editorial_context: str | None = Field(default=None, max_length=1000)


class AIAdaptPlatformRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="Text to adapt")
    platform: AIPlatform = Field(..., description="Target platform: FACEBOOK, INSTAGRAM, LINKEDIN")
    tone: AITone | None = Field(default=None, description="Optional tone")
    editorial_context: str | None = Field(default=None, max_length=1000)


class AIIdeasRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=2000, description="Topic, theme or industry")
    platform: AIPlatform | None = Field(default=None, description="Target platform")
    tone: AITone | None = Field(default=None, description="Desired tone")
    target_audience: str | None = Field(default=None, max_length=500)
    editorial_context: str | None = Field(default=None, max_length=1000)


class AIUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class AIResponse(BaseModel):
    content: str
    action: AIAction
    usage: AIUsage | None = None
    ideas: list[str] | None = None
