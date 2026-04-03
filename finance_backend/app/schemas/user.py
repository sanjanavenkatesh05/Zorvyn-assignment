# =============================================================================
# Zorvyn Finance Backend — User Schemas (Request/Response Validation)
# =============================================================================
# Pydantic models that validate incoming request data and shape outgoing
# responses for user-related endpoints.
#
# Separation of Concerns:
#   - Models (app/models/user.py)  → MongoDB document structure
#   - Schemas (this file)          → API request/response validation
#
# This ensures the API never exposes internal fields like hashed_password
# and validates user input before it reaches the database layer.
# =============================================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import Role


# ---------------------------------------------------------------------------
# Request Schemas — Validate incoming data
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    """
    Schema for user registration (POST /auth/register).

    Validates:
    - Email format (valid email address)
    - Password length (minimum 8 characters)
    - Full name is not empty

    Note: The password is hashed before storage — never saved as plaintext.
    """

    email: EmailStr = Field(
        ...,
        description="Valid email address. Must be unique in the system.",
        json_schema_extra={"example": "sanjana@zorvyn.com"},
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (minimum 8 characters). Will be hashed before storage.",
        json_schema_extra={"example": "SecurePass123!"},
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full name of the user.",
        json_schema_extra={"example": "Sanjana Venkatesh"},
    )


class UserUpdate(BaseModel):
    """
    Schema for updating user profile (PATCH /users/me).

    All fields are optional — only provided fields will be updated.
    """

    full_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated full name.",
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="Updated email address.",
    )


class RoleUpdate(BaseModel):
    """
    Schema for changing a user's role (PATCH /users/{id}/role).

    Admin-only operation. Validates that the role is a valid enum value.
    """

    role: Role = Field(
        ...,
        description="New role to assign: 'viewer', 'analyst', or 'admin'.",
        json_schema_extra={"example": "analyst"},
    )


class StatusUpdate(BaseModel):
    """
    Schema for activating/deactivating a user (PATCH /users/{id}/status).

    Admin-only operation. Inactive users cannot log in or access any endpoint.
    """

    is_active: bool = Field(
        ...,
        description="Set to false to deactivate the user account.",
        json_schema_extra={"example": True},
    )


# ---------------------------------------------------------------------------
# Response Schemas — Shape outgoing data
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    """
    Schema for user data in API responses.

    Excludes sensitive fields like hashed_password.
    The 'id' field is serialized from MongoDB's ObjectId to a string.
    """

    id: str = Field(
        ...,
        description="Unique user identifier (MongoDB ObjectId as string).",
        json_schema_extra={"example": "660f1a2b3c4d5e6f7a8b9c0d"},
    )
    email: EmailStr = Field(
        ...,
        description="User's email address.",
    )
    full_name: str = Field(
        ...,
        description="User's full display name.",
    )
    role: Role = Field(
        ...,
        description="User's current role (viewer, analyst, or admin).",
    )
    is_active: bool = Field(
        ...,
        description="Whether the user account is active.",
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp (UTC).",
    )

    # Allow creating this schema from ORM/ODM model attributes
    model_config = ConfigDict(from_attributes=True)
