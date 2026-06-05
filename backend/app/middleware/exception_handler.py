from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logger import logger
from app.utils.response import BusinessError, fail


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessError)
    async def business_error_handler(_: Request, exc: BusinessError):
        return JSONResponse(
            status_code=exc.http_status,
            content=fail(code=exc.code, message=exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError):
        details = exc.errors()
        first = details[0] if details else {}
        loc = ".".join(str(x) for x in first.get("loc", []) if x != "body")
        msg = f"{loc}: {first.get('msg', 'invalid input')}" if loc else first.get("msg", "invalid input")
        return JSONResponse(status_code=422, content=fail(code=4001, message=msg, data=details))

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=fail(code=exc.status_code, message=str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def unknown_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
        return JSONResponse(
            status_code=500,
            content=fail(code=5000, message="服务器内部错误"),
        )
