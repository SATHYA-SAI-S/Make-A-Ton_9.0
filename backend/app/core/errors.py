"""
SubscriptIQ Standardized Error Handling.
All API errors return { "error": { "code": "...", "message": "...", "details": {} } }.
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

class SubscriptIQError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }

    def to_response(self) -> JSONResponse:
        return JSONResponse(status_code=self.status_code, content=self.to_dict())

class NotFoundError(SubscriptIQError):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=f"{resource} with id '{resource_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "id": resource_id}
        )

class PermissionDeniedError(SubscriptIQError):
    def __init__(self, message: str = "Access denied."):
        super().__init__(
            code="PERMISSION_DENIED",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )

class ValidationError(SubscriptIQError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )
