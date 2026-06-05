"""Issue closed-loop state machine.

Flow for a submitted inspection that contains abnormalities:

    pending_assign --assign(admin)-->        pending_handle
    pending_handle --process(handler)-->     pending_verify
    pending_verify --verify_pass(verifier)-->  completed
    pending_verify --verify_reject(verifier)-> pending_handle   (打回重处理)

Each transition writes an issue_processes row (audit trail) and an operation log.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attachment import Attachment
from app.models.issue_process import IssueProcess
from app.models.inspection_record import InspectionRecord
from app.models.operation_log import OperationLog
from app.models.user import User
from app.utils.enums import (
    AttachmentCategory,
    AttachmentTarget,
    ProcessAction,
    RecordStatus,
    UserRole,
)
from app.utils.file_storage import url_for
from app.utils.response import BusinessError


def _require_record(db: Session, record_id: int) -> InspectionRecord:
    record = db.execute(
        select(InspectionRecord).where(InspectionRecord.id == record_id)
    ).scalar_one_or_none()
    if not record:
        raise BusinessError("巡检记录不存在", code=4401, http_status=404)
    return record


def _require_role(user: User, *roles: str) -> None:
    if user.role not in roles:
        raise BusinessError("当前账号无权执行该操作", code=4410, http_status=403)


def current_assignee_id(db: Session, record_id: int) -> int | None:
    """The handler the issue is currently assigned to (latest assign action)."""
    row = db.execute(
        select(IssueProcess.assignee_id)
        .where(
            IssueProcess.record_id == record_id,
            IssueProcess.action == ProcessAction.ASSIGN.value,
        )
        .order_by(IssueProcess.created_at.desc(), IssueProcess.id.desc())
    ).first()
    return row[0] if row else None


def _log(db: Session, user: User, action: str, record: InspectionRecord, detail: dict) -> None:
    db.add(OperationLog(
        user_id=user.id,
        action=action,
        target_type="inspection_record",
        target_id=record.id,
        detail={"record_no": record.record_no, **detail},
    ))


# ----------------- transitions -----------------


def assign(
    db: Session,
    *,
    record_id: int,
    user: User,
    assignee_id: int,
    content: str | None = None,
    expected_finish_time: datetime | None = None,
) -> dict:
    _require_role(user, UserRole.ADMIN.value)
    record = _require_record(db, record_id)
    if record.status not in (RecordStatus.PENDING_ASSIGN.value, RecordStatus.PENDING_HANDLE.value):
        raise BusinessError("当前状态不可转发", code=4411)

    assignee = db.get(User, assignee_id)
    if not assignee or assignee.status != 1:
        raise BusinessError("处理人不存在或已停用", code=4412, http_status=404)
    if assignee.role not in (UserRole.HANDLER.value, UserRole.ADMIN.value):
        raise BusinessError("只能转发给处理员", code=4413)

    from_status = record.status
    record.status = RecordStatus.PENDING_HANDLE.value
    db.add(IssueProcess(
        record_id=record.id,
        action=ProcessAction.ASSIGN.value,
        operator_id=user.id,
        assignee_id=assignee_id,
        content=content,
        expected_finish_time=expected_finish_time,
        from_status=from_status,
        to_status=record.status,
    ))
    _log(db, user, "issue.assign", record, {"assignee_id": assignee_id, "to": record.status})
    db.commit()
    return {"record_id": record.id, "status": record.status, "assignee_id": assignee_id}


def process(db: Session, *, record_id: int, user: User, content: str) -> dict:
    _require_role(user, UserRole.HANDLER.value, UserRole.ADMIN.value)
    record = _require_record(db, record_id)
    if record.status not in (RecordStatus.PENDING_HANDLE.value, RecordStatus.HANDLING.value):
        raise BusinessError("当前状态不可提交处理结果", code=4414)
    if not content or not content.strip():
        raise BusinessError("请填写处理说明", code=4415)

    from_status = record.status
    record.status = RecordStatus.PENDING_VERIFY.value
    db.add(IssueProcess(
        record_id=record.id,
        action=ProcessAction.PROCESS.value,
        operator_id=user.id,
        content=content.strip(),
        from_status=from_status,
        to_status=record.status,
    ))
    _log(db, user, "issue.process", record, {"to": record.status})
    db.commit()
    return {"record_id": record.id, "status": record.status}


def verify(db: Session, *, record_id: int, user: User, passed: bool, content: str | None = None) -> dict:
    _require_role(user, UserRole.VERIFIER.value, UserRole.ADMIN.value)
    record = _require_record(db, record_id)
    if record.status != RecordStatus.PENDING_VERIFY.value:
        raise BusinessError("当前状态不可核实", code=4416)
    if not passed and not (content and content.strip()):
        raise BusinessError("驳回时请填写原因", code=4417)

    from_status = record.status
    if passed:
        record.status = RecordStatus.COMPLETED.value
        action = ProcessAction.VERIFY_PASS.value
    else:
        record.status = RecordStatus.PENDING_HANDLE.value
        action = ProcessAction.VERIFY_REJECT.value

    db.add(IssueProcess(
        record_id=record.id,
        action=action,
        operator_id=user.id,
        content=content.strip() if content else None,
        from_status=from_status,
        to_status=record.status,
    ))
    _log(db, user, "issue.verify", record, {"passed": passed, "to": record.status})
    db.commit()
    return {"record_id": record.id, "status": record.status, "passed": passed}


def attach_issue_image(
    db: Session,
    *,
    record_id: int,
    user: User,
    saved: dict,
    category: str = AttachmentCategory.ISSUE_AFTER.value,
) -> dict:
    """Record-level (not device-level) photo for handling/verification."""
    _require_role(user, UserRole.HANDLER.value, UserRole.VERIFIER.value, UserRole.ADMIN.value)
    record = _require_record(db, record_id)
    att = Attachment(
        target_type=AttachmentTarget.RECORD.value,
        target_id=record.id,
        record_id=record.id,
        equipment_id=None,
        category=category,
        original_file_name=saved["file_name"],
        file_name=saved["file_name"],
        file_path=saved["file_path"],
        file_size=saved["file_size"],
        mime_type=saved["mime_type"],
        uploader_id=user.id,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return {"id": att.id, "url": url_for(att.file_path), "category": att.category}
