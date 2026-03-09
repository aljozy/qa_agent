"""Core data models for the QA Agent system."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class RequirementType(str, Enum):
    """Types of requirements that can be parsed."""

    USER_STORY = "user_story"
    API_ENDPOINT = "api_endpoint"
    FUNCTIONAL = "functional"
    SCHEMA = "schema"


class TestType(str, Enum):
    """Types of test artifacts that can be generated."""

    MANUAL = "manual"
    AUTOMATION = "automation"
    API = "api"
    UI = "ui"
    DATABASE = "database"


class Requirement(BaseModel):
    """Represents a parsed requirement from any source."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique requirement ID")
    type: RequirementType = Field(..., description="Type of requirement")
    content: str = Field(..., description="Full text content of the requirement")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the requirement"
    )
    source: str = Field(..., description="Source document or file path")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the requirement was parsed"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class TestArtifact(BaseModel):
    """Represents a generated test artifact."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique test artifact ID")
    type: TestType = Field(..., description="Type of test artifact")
    content: str = Field(..., description="Full content of the test artifact")
    requirement_ids: List[str] = Field(
        default_factory=list, description="IDs of requirements this artifact tests"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about the artifact"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the artifact was generated"
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class ValidationResult(BaseModel):
    """Result of validating input data before parsing."""

    is_valid: bool = Field(..., description="Whether the input is valid")
    errors: List[str] = Field(
        default_factory=list, description="List of validation error messages"
    )
    warnings: List[str] = Field(
        default_factory=list, description="List of validation warnings"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional validation metadata"
    )
