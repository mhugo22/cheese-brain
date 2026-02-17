"""
Data models for Cheese Brain entities.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EntityCategory(str, Enum):
    """Supported entity categories."""

    PROJECT = "project"
    EMAIL = "email"
    API = "api"
    TOOL = "tool"
    DECISION = "decision"
    CODE_SNIPPET = "code_snippet"
    CONTACT = "contact"
    BOOKMARK = "bookmark"
    CONFIG_LOCATION = "config_location"
    FAILED_EXPERIMENT = "failed_experiment"
    PROBLEM = "problem"
    LEARNING_NOTE = "learning_note"
    WORKFLOW = "workflow"
    TROUBLESHOOTING = "troubleshooting"
    INFRASTRUCTURE = "infrastructure"
    MEETING_NOTE = "meeting_note"
    IDEA = "idea"
    HABIT = "habit"
    DEPENDENCY = "dependency"
    ENVIRONMENT_CONFIG = "environment_config"
    VENDOR_LICENSE = "vendor_license"
    METRIC = "metric"


class Entity(BaseModel):
    """Core entity model."""

    id: UUID = Field(default_factory=uuid4)
    category: EntityCategory
    title: str = Field(min_length=1, max_length=500)
    data: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }

    def mark_deleted(self) -> None:
        """Soft delete this entity."""
        self.deleted_at = datetime.utcnow()

    def is_deleted(self) -> bool:
        """Check if entity is soft-deleted."""
        return self.deleted_at is not None


class AuditLog(BaseModel):
    """Audit log entry for tracking changes."""

    id: int
    entity_id: UUID
    action: str  # 'create', 'update', 'delete'
    old_data: Optional[dict[str, Any]] = None
    new_data: dict[str, Any]
    changed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
