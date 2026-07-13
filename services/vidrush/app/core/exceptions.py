from fastapi import Request
from fastapi.responses import JSONResponse

class JarvisAPIException(Exception):
    """Base exception for all Jarvis API Custom Errors"""
    def __init__(self, status_code: int, user_message: str, internal_code: str):
        self.status_code = status_code
        self.user_message = user_message
        self.internal_code = internal_code

class SchemaValidationFailure(JarvisAPIException):
    """Thrown when LLM or User input severely violates the MasterNarrativeSchema."""
    def __init__(self, message="The script contradicts the character's established personality. Please review the Director's notes.", data_payload=None):
        super().__init__(
            status_code=400,
            user_message=message,
            internal_code="ERR_SCHEMA_VALIDATION_FAILURE"
        )
        self.data_payload = data_payload

class ConflictResolutionError(SchemaValidationFailure):
    """Thrown when contradictory user edits create an impossible narrative paradox."""
    def __init__(self, message="Conflict detected: Upbeat visual style contradicts existential dread character bias.", data_payload=None):
        super().__init__(
            message=message,
            data_payload=data_payload
        )
        self.internal_code = "ERR_CONFLICT_RESOLUTION_PARADOX"

class AssetUnavailableError(JarvisAPIException):
    """Thrown when an external rendering API goes down."""
    def __init__(self, message="Luma API is down; falling back to local procedural generation."):
        super().__init__(
            status_code=503,
            user_message=message,
            internal_code="ERR_ASSET_UNAVAILABLE"
        )

class TemporalConflictError(JarvisAPIException):
    """Thrown when Sandbox edits create overlapping or invalid timecodes."""
    def __init__(self, message="The requested fade overlaps with an existing sound cue, please shift the edit point by 50ms."):
        super().__init__(
            status_code=409,
            user_message=message,
            internal_code="ERR_TEMPORAL_CONFLICT"
        )

# FastAPI Exception Handlers
async def jarvis_exception_handler(request: Request, exc: JarvisAPIException):
    """Maps custom Jarvis exceptions to standardized JSON responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": exc.internal_code,
            "message": exc.user_message,
            "resolution_hint": "Check the API documentation for valid constraints."
        }
    )

def setup_exception_handlers(app):
    app.add_exception_handler(JarvisAPIException, jarvis_exception_handler)
