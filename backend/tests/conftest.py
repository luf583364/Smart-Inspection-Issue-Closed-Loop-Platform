import os
import shutil
import tempfile
from pathlib import Path

TEST_ROOT = Path(tempfile.mkdtemp(prefix="inspection-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(TEST_ROOT / 'inspection_test.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(TEST_ROOT / "uploads")
os.environ["JWT_SECRET"] = "test-secret"
os.environ["PUBLIC_WEB_BASE_URL"] = "http://localhost:5173"
os.environ["FRONTEND_ROUTER_MODE"] = "hash"

from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: F401, E402
from app.db.base import Base  # noqa: E402
from app.db.init_db import _seed  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


def _reset_uploads() -> None:
    upload_dir = Path(os.environ["UPLOAD_DIR"])
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        _seed(db)


def pytest_sessionfinish(session, exitstatus):  # noqa: ANN001
    shutil.rmtree(TEST_ROOT, ignore_errors=True)


import pytest  # noqa: E402


@pytest.fixture()
def client():
    _reset_uploads()
    _reset_db()
    with TestClient(app) as c:
        yield c
