from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    def __init__(
        self,
        arg1: str = "BAD_REQUEST",
        arg2: Any = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
        code: Optional[str] = None,
        message: Optional[str] = None
    ):
        if code is not None and message is not None:
            self.code = code
            self.message = message
        elif isinstance(arg2, str):
            self.code = arg1
            self.message = arg2
        elif isinstance(arg2, int):
            self.code = "BAD_REQUEST"
            self.message = arg1
            status_code = arg2
        else:
            self.code = code or "BAD_REQUEST"
            self.message = message or arg1

        self.status_code = status_code
        self.detail = self.message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND", details: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(arg1=code, arg2=message, status_code=status.HTTP_404_NOT_FOUND, details=details, code=code, message=message)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", code: str = "UNAUTHORIZED", details: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(arg1=code, arg2=message, status_code=status.HTTP_401_UNAUTHORIZED, details=details, code=code, message=message)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Access forbidden", code: str = "FORBIDDEN", details: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(arg1=code, arg2=message, status_code=status.HTTP_403_FORBIDDEN, details=details, code=code, message=message)


class ConflictException(AppException):
    def __init__(self, message: str = "Conflict", code: str = "CONFLICT", details: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(arg1=code, arg2=message, status_code=status.HTTP_409_CONFLICT, details=details, code=code, message=message)


class ValidationException(AppException):
    def __init__(self, message: str = "Validation error", code: str = "VALIDATION_ERROR", details: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(arg1=code, arg2=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details, code=code, message=message)


# Aliases
AppError = AppException
NotFoundError = NotFoundException
UnauthorizedError = UnauthorizedException
ForbiddenError = ForbiddenException
ConflictError = ConflictException
ValidationError = ValidationException


async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, app_exception_handler)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        details = {}
        for err in exc.errors():
            loc = " -> ".join(str(l) for l in err.get("loc", []))
            details[loc] = err.get("msg", "Invalid value")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters",
                    "details": details
                }
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        code = "HTTP_ERROR"
        if exc.status_code == 401:
            code = "UNAUTHORIZED"
        elif exc.status_code == 403:
            code = "FORBIDDEN"
        elif exc.status_code == 404:
            code = "NOT_FOUND"
        elif exc.status_code == 409:
            code = "CONFLICT"
        elif exc.status_code == 422:
            code = "VALIDATION_ERROR"

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": str(exc.detail),
                    "details": {}
                }
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please contact system support.",
                    "details": {"error_type": exc.__class__.__name__}
                }
            }
        )

