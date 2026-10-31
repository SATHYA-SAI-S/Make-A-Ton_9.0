from typing import Any
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class AppException(Exception):
    def __init__(self, arg1: str, arg2: Any = None, status_code: int = 400, details: dict = None):
        if isinstance(arg2, str):
            self.code = arg1
            self.message = arg2
            self.status_code = status_code
        elif isinstance(arg2, int):
            self.code = "BAD_REQUEST"
            self.message = arg1
            self.status_code = arg2
        else:
            self.code = "BAD_REQUEST"
            self.message = arg1
            self.status_code = status_code
        self.detail = self.message
        self.details = details or {}
        super().__init__(self.message)

class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", details: dict = None):
        super().__init__(arg1="NOT_FOUND", arg2=message, status_code=404, details=details)

def app_exception_handler(request: Request, exc: AppException):
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
