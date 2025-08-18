from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class PromptName(str, Enum):
    """Enum for server-stored prompt templates."""
    COMPANY_ANALYSIS = "company_analysis"
    TEXT_SUMMARY = "text_summary"
    CODE_REVIEW = "code_review"
    GENERAL_QUESTION = "general_question"


class LLMRequest(BaseModel):
    """Request model for the /ask-llm endpoint."""
    prompt_name: Optional[PromptName] = Field(None, description="Reference to a server-stored prompt template")
    prompt_text: Optional[str] = Field(None, description="Direct prompt text (used if prompt_name not provided)")
    data: Optional[Dict[str, Any]] = Field(default={}, description="Dictionary for variable substitution in prompts")
    model: Optional[str] = Field(None, description="Specific model to use for the request")


class LLMResponse(BaseModel):
    """Response model for the /ask-llm endpoint."""
    success: bool = Field(..., description="Whether the request was successful")
    response: Optional[str] = Field(None, description="LLM response text")
    model_used: str = Field(..., description="Model that was used for the response")
    tokens_used: Optional[Dict[str, int]] = Field(None, description="Token usage information")
    request_id: str = Field(..., description="Unique request identifier for tracing")
    error: Optional[str] = Field(None, description="Error message if request failed")


class TokenUsage(BaseModel):
    """Token usage information from OpenRouter."""
    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total number of tokens used")


class OpenRouterResponse(BaseModel):
    """OpenRouter API response model."""
    id: str = Field(..., description="Response ID")
    choices: List[Dict[str, Any]] = Field(..., description="Model choices")
    usage: TokenUsage = Field(..., description="Token usage information")
    model: str = Field(..., description="Model used")


class AccessToken(BaseModel):
    """Access token model for authentication."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Token data for JWT payload."""
    user_id: str = Field(..., description="User identifier")
    exp: Optional[int] = Field(None, description="Expiration timestamp")
