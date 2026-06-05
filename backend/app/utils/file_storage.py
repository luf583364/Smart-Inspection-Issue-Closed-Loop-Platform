import re
import secrets
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from loguru import logger

from app.core.config import settings
from app.utils.response import BusinessError

ALLOWED_MIME = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}

# 5 MB cap per image
MAX_BYTES = 5 * 1024 * 1024


_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]")


def _safe_stem(name: str) -> str:
    stem = Path(name).stem[:40] or "file"
    return _SAFE_NAME_RE.sub("_", stem)


async def save_image(file: UploadFile) -> dict:
    """Persist an uploaded image under uploads/YYYY/MM/.

    Returns: { file_name, file_path (relative), file_size, mime_type, url }
    Raises BusinessError on invalid input.
    """
    if not file or not file.filename:
        raise BusinessError("未接收到文件", code=4101)

    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_MIME:
        raise BusinessError(
            "仅支持 JPG / PNG / WebP 图片",
            code=4102,
        )

    ext = ALLOWED_MIME[content_type]

    data = await file.read()
    size = len(data)
    if size == 0:
        raise BusinessError("文件为空", code=4103)
    if size > MAX_BYTES:
        raise BusinessError(f"文件大小不能超过 {MAX_BYTES // (1024 * 1024)} MB", code=4104)

    # double-check magic bytes for the common formats
    if not _looks_like_image(data):
        raise BusinessError("文件内容不是有效的图片", code=4105)

    now = datetime.now()
    sub_dir = Path(settings.UPLOAD_DIR) / f"{now.year:04d}" / f"{now.month:02d}"
    sub_dir.mkdir(parents=True, exist_ok=True)

    stem = _safe_stem(file.filename)
    rand = secrets.token_hex(6)
    final_name = f"{now.strftime('%Y%m%d%H%M%S')}_{rand}_{stem}{ext}"
    final_path = sub_dir / final_name
    final_path.write_bytes(data)

    relative = str(final_path.relative_to(Path(settings.UPLOAD_DIR))).replace("\\", "/")
    url = f"{settings.UPLOAD_BASE_URL}/{relative}"

    return {
        "file_name": file.filename,
        "file_path": relative,
        "file_size": size,
        "mime_type": content_type,
        "url": url,
    }


def url_for(path: str | None) -> str:
    if not path:
        return ""
    return f"{settings.UPLOAD_BASE_URL}/{path}"


def delete_saved_file(path: str | None) -> bool:
    if not path:
        return False
    upload_root = Path(settings.UPLOAD_DIR).resolve()
    target = (upload_root / path).resolve()
    try:
        target.relative_to(upload_root)
    except ValueError:
        raise BusinessError("非法附件路径", code=4106)
    if not target.exists():
        logger.warning(f"Attachment file already missing: {target}")
        return False
    target.unlink()
    return True


def _looks_like_image(data: bytes) -> bool:
    if len(data) < 12:
        return False
    if data[:3] == b"\xff\xd8\xff":  # JPEG
        return True
    if data[:8] == b"\x89PNG\r\n\x1a\n":  # PNG
        return True
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":  # WebP
        return True
    return False
