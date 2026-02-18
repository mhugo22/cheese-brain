"""
Data models for Cheese Brain entities.
"""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_serializer, field_validator


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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

    @field_validator('data')
    @classmethod
    def validate_data_size_and_depth(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate data field size and nesting depth.
        
        Limits:
        - Max 1MB serialized size
        - Max 10 levels of nesting
        
        Raises:
            ValueError: If validation fails
        """
        # Check serialized size
        serialized = json.dumps(v, default=str)
        size_bytes = len(serialized.encode('utf-8'))
        max_bytes = 1 * 1024 * 1024  # 1MB
        
        if size_bytes > max_bytes:
            raise ValueError(
                f"Data field too large: {size_bytes / 1024:.1f}KB "
                f"(max {max_bytes / 1024:.0f}KB)"
            )
        
        # Check nesting depth
        def get_depth(obj: Any, current_depth: int = 0) -> int:
            if current_depth > 10:
                raise ValueError("Data field nesting too deep (max 10 levels)")
            
            if isinstance(obj, dict):
                return max(
                    (get_depth(val, current_depth + 1) for val in obj.values()),
                    default=current_depth
                )
            elif isinstance(obj, list):
                return max(
                    (get_depth(item, current_depth + 1) for item in obj),
                    default=current_depth
                )
            return current_depth
        
        get_depth(v)
        return v

    @field_serializer('id', 'created_at', 'updated_at', 'deleted_at')
    def serialize_special_types(self, value):
        """Serialize UUID and datetime fields to string."""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        return value

    def mark_deleted(self) -> None:
        """Soft delete this entity."""
        self.deleted_at = datetime.now(timezone.utc)

    def is_deleted(self) -> bool:
        """Check if entity is soft-deleted."""
        return self.deleted_at is not None


class RelationshipType(str, Enum):
    """Supported relationship types."""

    USES = "uses"  # Workflow uses Tool, Project uses Email Account
    BELONGS_TO = "belongs_to"  # Email belongs to Project, Tool belongs to Workflow
    REQUIRES = "requires"  # Project requires Tool, Workflow requires API
    RELATED_TO = "related_to"  # Generic bidirectional relationship
    DEPENDS_ON = "depends_on"  # Project depends on Infrastructure
    DOCUMENTS = "documents"  # Bookmark documents Project, Note documents Decision
    IMPLEMENTS = "implements"  # Tool implements Workflow, Code implements Design


class Relationship(BaseModel):
    """Relationship between two entities."""

    id: UUID = Field(default_factory=uuid4)
    from_id: UUID
    to_id: UUID
    relationship_type: RelationshipType
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_serializer('id', 'from_id', 'to_id', 'created_at')
    def serialize_special_types(self, value):
        """Serialize UUID and datetime fields to string."""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        return value


class AuditLog(BaseModel):
    """Audit log entry for tracking changes."""

    id: int
    entity_id: UUID
    action: str  # 'create', 'update', 'delete'
    old_data: Optional[dict[str, Any]] = None
    new_data: dict[str, Any]
    changed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_serializer('entity_id', 'changed_at')
    def serialize_special_types(self, value):
        """Serialize UUID and datetime fields to string."""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        return value
