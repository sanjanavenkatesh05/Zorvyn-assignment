# =============================================================================
# Zorvyn Finance Backend — User Document Model
# =============================================================================
# Defines the MongoDB document schema for users in the system.
#
# Key Design Decisions:
#   - Role is an enum (viewer, analyst, admin) for type safety.
#   - Email has a unique index to prevent duplicates at the DB level.
#   - is_active flag supports soft user deactivation without deletion.
#   - Timestamps (created_at, updated_at) are auto-set for audit trails.
#
# Usage:
#   from app.models.user import User, Role
#   admin_users = await User.find(User.role == Role.admin).to_list()
# =============================================================================

from datetime import datetime, timezone
from enum import Enum

from beanie import Document, Indexed
from pydantic import EmailStr, Field


class Role(str, Enum):
    """
    User roles that define access levels throughout the system.

    - viewer:  Can only view dashboard data and records (read-only).
    - analyst: Can view records and access analytics/insights.
    - admin:   Full access — create, update, delete records and manage users.

    The role hierarchy is enforced via the RoleChecker dependency (see
    app/api/dependencies.py), NOT by checking roles inside endpoint functions.
    """

    viewer = "viewer"
    analyst = "analyst"
    admin = "admin"


class User(Document):
    """
    MongoDB document representing a user in the finance system.

    Fields:
        email:           Unique email address (indexed for fast lookups).
        hashed_password: Bcrypt-hashed password (never store plaintext!).
        full_name:       Display name of the user.
        role:            Access level — defaults to 'viewer' for new users.
        is_active:       Whether the account is active. Inactive users
                         cannot authenticate or access any endpoint.
        created_at:      Timestamp of account creation (UTC).
        updated_at:      Timestamp of last profile update (UTC).

    MongoDB Collection: "users"
    """

    # ── Core Fields ──────────────────────────────────────────────────────
    email: Indexed(EmailStr, unique=True) = Field(
        ...,
        description="Unique email address used for login.",
        json_schema_extra={"example": "admin@zorvyn.com"},
    )
    hashed_password: str = Field(
        ...,
        description="Bcrypt-hashed password. Never returned in API responses.",
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Full display name of the user.",
        json_schema_extra={"example": "Sanjana Venkatesh"},
    )

    # ── Role & Status ────────────────────────────────────────────────────
    role: Role = Field(
        default=Role.viewer,
        description="User role determining access permissions.",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the user account is active. Inactive users cannot log in.",
    )

    # ── Timestamps ───────────────────────────────────────────────────────
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the user account was created (UTC).",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the user profile was last updated (UTC).",
    )

    class Settings:
        """Beanie ODM settings for this document."""

        # MongoDB collection name
        name = "users"

    def __repr__(self) -> str:
        return f"<User email={self.email} role={self.role.value}>"
