"""System-wide fixed inspection entry QR.

One permanent QR for the whole system: scan -> login -> room picker -> inspect.
Unlike the per-room QR, this encodes the inspection home (no room), so a single
printed code works for every room.
"""

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_roles
from app.api.v1.rooms import _local_warning, _qr_response
from app.core.config import settings
from app.models.user import User
from app.utils.response import success

router = APIRouter()


def _entry_url() -> str:
    base = settings.PUBLIC_WEB_BASE_URL.rstrip("/")
    path = "/mobile/inspection?source=qr"
    if settings.FRONTEND_ROUTER_MODE.lower() == "hash":
        return f"{base}/#{path}"
    return f"{base}{path}"


@router.get("/qr-info", summary="巡检入口二维码信息（固定）")
def qr_info(_: User = Depends(require_roles("admin"))):
    url = _entry_url()
    warning = _local_warning(url)
    return success({
        "target_url": url,
        "printable": warning is None,
        "warning": warning,
    })


@router.get("/qrcode", summary="巡检入口二维码图片（固定）")
def qrcode(
    format: str = Query("svg", pattern="^(svg|png)$"),
    _: User = Depends(require_roles("admin")),
):
    resp = _qr_response(_entry_url(), format)
    resp.headers["Content-Disposition"] = f'inline; filename="inspection-entry-qr.{format}"'
    return resp
