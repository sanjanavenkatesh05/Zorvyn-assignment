# =============================================================================
# Zorvyn Finance Backend — Token Response Schema
# =============================================================================
# Pydantic model for the JWT authentication response returned by POST /login.
#
# Usage:
#   from app.schemas.token import TokenResponse
# =============================================================================

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """
    Response schema for the login endpoint.

    Returned when a user successfully authenticates with valid credentials.
    The client should store the access_token and include it in subsequent
    requests via the Authorization header:
        Authorization: Bearer <access_token>

    Attributes:
        access_token: The JWT token string.
        token_type:   Always "bearer" (OAuth2 standard).
    """

    access_token: str = Field(
        ...,
        description="JWT access token to include in Authorization header.",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."},
    )
    token_type: str = Field(
        default="bearer",
        description="Token type. Always 'bearer' per OAuth2 spec.",
        json_schema_extra={"example": "bearer"},
    )
