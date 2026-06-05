from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_router
from app.core.config import settings
from app.core.logger import logger, setup_logger
from app.db.init_db import init_db
from app.middleware.exception_handler import register_exception_handlers
from app.middleware.request_logger import register_request_logger

setup_logger()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="机房智能巡检与问题闭环管理系统 API",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_request_logger(app)
    register_exception_handlers(app)
    app.include_router(api_router)

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount(settings.UPLOAD_BASE_URL, StaticFiles(directory=str(upload_dir)), name="uploads")

    @app.on_event("startup")
    def _startup():
        logger.info(f"{settings.APP_NAME} starting (env={settings.APP_ENV}) ...")
        init_db()

    @app.get("/health", tags=["系统"])
    def health():
        return {"code": 0, "message": "ok", "data": {"status": "up"}}

    return app


app = create_app()
