import time

from fastapi import FastAPI, Request

from app.core.logger import logger


def register_request_logger(app: FastAPI) -> None:
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        cost_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} "
            f"({cost_ms:.1f}ms) from {request.client.host if request.client else '-'}"
        )
        return response
