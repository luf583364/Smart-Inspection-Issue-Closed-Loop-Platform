from datetime import datetime

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services import inspection_record_service, issue_service, report_service
from app.utils.enums import AttachmentCategory
from app.utils.file_storage import save_image
from app.utils.response import BusinessError, success

router = APIRouter()


@router.get("", summary="后台巡检记录列表")
def list_records(
    room_id: int | None = None,
    inspector_id: int | None = None,
    status: str | None = None,
    has_issue: int | None = Query(None, ge=0, le=1),
    start: datetime | None = None,
    end: datetime | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    data = inspection_record_service.list_records(
        db,
        room_id=room_id,
        inspector_id=inspector_id,
        status=status,
        has_issue=has_issue,
        start=start,
        end=end,
        page=page,
        size=size,
    )
    return success(data)


@router.get("/{record_id}", summary="巡检详情")
def detail(record_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    data = inspection_record_service.get_record_detail(db, record_id)
    if data is None:
        raise BusinessError("巡检记录不存在", code=4401, http_status=404)
    return success(data)


@router.get("/{record_id}/report", summary="查看 / 下载巡检报告(HTML)")
def get_report(
    record_id: int,
    download: int = Query(0, ge=0, le=1, description="1=下载附件, 0=浏览器内查看"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    res = report_service.ensure_report(db, record_id)
    if res is None:
        raise BusinessError("巡检记录不存在", code=4401, http_status=404)
    path, record_no = res
    html_text = path.read_text(encoding="utf-8")
    disposition = "attachment" if download else "inline"
    headers = {
        "Content-Disposition": f'{disposition}; filename="{record_no}.html"',
    }
    return Response(content=html_text, media_type="text/html; charset=utf-8", headers=headers)


@router.post("/{record_id}/report/generate", summary="重新生成巡检报告")
def regenerate_report(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    path = report_service.generate_report(db, record_id)
    if path is None:
        raise BusinessError("巡检记录不存在", code=4401, http_status=404)
    return success({"record_id": record_id, "file_name": path.name})


# ----------------- 问题闭环（转发 / 处理 / 核实） -----------------


class AssignIn(BaseModel):
    assignee_id: int
    content: str | None = None
    expected_finish_time: datetime | None = None


class ProcessIn(BaseModel):
    content: str


class VerifyIn(BaseModel):
    passed: bool
    content: str | None = None


@router.post("/{record_id}/assign", summary="转发问题给处理员（管理员）")
def assign_issue(
    record_id: int,
    payload: AssignIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return success(issue_service.assign(
        db, record_id=record_id, user=user,
        assignee_id=payload.assignee_id, content=payload.content,
        expected_finish_time=payload.expected_finish_time,
    ))


@router.post("/{record_id}/process", summary="提交处理结果（处理员）")
def process_issue(
    record_id: int,
    payload: ProcessIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return success(issue_service.process(db, record_id=record_id, user=user, content=payload.content))


@router.post("/{record_id}/verify", summary="核实通过 / 驳回（核实员）")
def verify_issue(
    record_id: int,
    payload: VerifyIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return success(issue_service.verify(
        db, record_id=record_id, user=user, passed=payload.passed, content=payload.content,
    ))


@router.post("/{record_id}/issue-attachments", summary="上传整改 / 核实照片")
async def upload_issue_image(
    record_id: int,
    category: str = Query(AttachmentCategory.ISSUE_AFTER.value, description="issue_after / verification"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if category not in (AttachmentCategory.ISSUE_AFTER.value, AttachmentCategory.VERIFICATION.value):
        category = AttachmentCategory.ISSUE_AFTER.value
    saved = await save_image(file)
    att = issue_service.attach_issue_image(
        db, record_id=record_id, user=user, saved=saved, category=category,
    )
    return success(att)
