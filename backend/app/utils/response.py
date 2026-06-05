from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: T | None = None


def success(data: Any = None, message: str = "ok") -> dict:
    return {"code": 0, "message": message, "data": data}


def fail(code: int = 1, message: str = "fail", data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}


class BusinessError(Exception):
    """Raised by services for expected, user-facing failures."""

    def __init__(self, message: str, code: int = 1, http_status: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
