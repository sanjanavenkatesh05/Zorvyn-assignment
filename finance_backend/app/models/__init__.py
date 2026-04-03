# =============================================================================
# Models Package — MongoDB Document Definitions (Beanie ODM)
# =============================================================================
# Exports all document models and enums for convenient importing.
#
# Usage:
#   from app.models import User, Role, Record, RecordType
# =============================================================================

from app.models.user import User, Role
from app.models.record import Record, RecordType

# All document models that Beanie needs to initialize
ALL_DOCUMENT_MODELS = [User, Record]

__all__ = [
    "User",
    "Role",
    "Record",
    "RecordType",
    "ALL_DOCUMENT_MODELS",
]
