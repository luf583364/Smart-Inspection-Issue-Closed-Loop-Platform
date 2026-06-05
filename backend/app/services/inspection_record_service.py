"""Read-side query for desktop pages: list + full detail of inspection records."""

from datetime import datetime
from typing import Iterable

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.attachment import Attachment
from app.models.equipment import Equipment
from app.models.inspection_check_item import InspectionCheckItem
from app.models.inspection_equipment_result import InspectionEquipmentResult
from app.models.inspection_item_result import InspectionItemResult
from app.models.inspection_record import InspectionRecord
from app.models.issue_process import IssueProcess
from app.models.room import Room
from app.models.user import User
from app.utils.enums import (
    EQUIPMENT_TYPE_LABEL,
    AttachmentCategory,
    EquipmentResultStatus,
    ProcessAction,
)
from app.utils.file_storage import url_for

_PROCESS_ACTION_LABEL = {
    ProcessAction.ASSIGN.value: "转发处理",
    ProcessAction.PROCESS.value: "提交处理结果",
    ProcessAction.SUBMIT_VERIFY.value: "提交核实",
    ProcessAction.VERIFY_PASS.value: "核实通过",
    ProcessAction.VERIFY_REJECT.value: "核实驳回",
}


def list_records(
    db: Session,
    *,
    room_id: int | None = None,
    inspector_id: int | None = None,
    status: str | None = None,
    has_issue: int | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    page: int = 1,
    size: int = 20,
) -> dict:
    filters = []
    if room_id is not None:
        filters.append(InspectionRecord.room_id == room_id)
    if inspector_id is not None:
        filters.append(InspectionRecord.inspector_id == inspector_id)
    if status:
        filters.append(InspectionRecord.status == status)
    if has_issue is not None:
        filters.append(InspectionRecord.has_issue == has_issue)
    if start:
        filters.append(InspectionRecord.inspection_time >= start)
    if end:
        filters.append(InspectionRecord.inspection_time <= end)

    count_stmt = select(func.count(InspectionRecord.id))
    base_stmt = (
        select(InspectionRecord, Room, User)
        .join(Room, Room.id == InspectionRecord.room_id)
        .join(User, User.id == InspectionRecord.inspector_id)
    )
    for f in filters:
        count_stmt = count_stmt.where(f)
        base_stmt = base_stmt.where(f)
    total = db.execute(count_stmt).scalar_one()

    rows = db.execute(
        base_stmt.order_by(InspectionRecord.inspection_time.desc())
        .offset((page - 1) * size).limit(size)
    ).all()

    record_ids = [r.id for r, _r, _u in rows]
    eq_total_map: dict[int, int] = {}
    eq_abn_map: dict[int, int] = {}
    if record_ids:
        for rid, n in db.execute(
            select(InspectionEquipmentResult.record_id, func.count(InspectionEquipmentResult.id))
            .where(InspectionEquipmentResult.record_id.in_(record_ids))
            .group_by(InspectionEquipmentResult.record_id)
        ).all():
            eq_total_map[rid] = n
        for rid, n in db.execute(
            select(InspectionEquipmentResult.record_id, func.count(InspectionEquipmentResult.id))
            .where(
                InspectionEquipmentResult.record_id.in_(record_ids),
                InspectionEquipmentResult.result == EquipmentResultStatus.ABNORMAL.value,
            )
            .group_by(InspectionEquipmentResult.record_id)
        ).all():
            eq_abn_map[rid] = n

    items = []
    for record, room, user in rows:
        items.append({
            "id": record.id,
            "record_no": record.record_no,
            "inspection_time": record.inspection_time,
            "submitted_at": record.submitted_at,
            "room_id": room.id,
            "room_name": room.name,
            "inspector_id": user.id,
            "inspector_name": user.name,
            "source": record.source,
            "has_issue": record.has_issue,
            "status": record.status,
            "equipment_total": eq_total_map.get(record.id, 0),
            "abnormal_equipment": eq_abn_map.get(record.id, 0),
        })
    return {"items": items, "total": total, "page": page, "size": size}


def get_record_detail(db: Session, record_id: int) -> dict:
    record = db.execute(select(InspectionRecord).where(InspectionRecord.id == record_id)).scalar_one_or_none()
    if not record:
        return None  # caller handles
    room = db.execute(select(Room).where(Room.id == record.room_id)).scalar_one()
    user = db.execute(select(User).where(User.id == record.inspector_id)).scalar_one()

    eq_results = list(db.execute(
        select(InspectionEquipmentResult, Equipment)
        .join(Equipment, Equipment.id == InspectionEquipmentResult.equipment_id)
        .where(InspectionEquipmentResult.record_id == record_id)
        .order_by(Equipment.id)
    ).all())

    item_rows = list(db.execute(
        select(InspectionItemResult, InspectionCheckItem)
        .join(InspectionCheckItem, InspectionCheckItem.id == InspectionItemResult.check_item_id)
        .where(InspectionItemResult.record_id == record_id)
        .order_by(InspectionItemResult.equipment_id, InspectionCheckItem.sort_order)
    ).all())
    items_by_eq: dict[int, list] = {}
    for ir, ci in item_rows:
        items_by_eq.setdefault(ir.equipment_id, []).append({
            "check_item_id": ci.id,
            "item_code": ci.item_code,
            "item_name": ci.item_name,
            "input_type": ci.input_type,
            "standard_value": ci.standard_value,
            "unit": ci.unit,
            "value": ir.value,
            "is_abnormal": ir.is_abnormal,
            "remark": ir.remark,
        })

    atts = list(db.execute(
        select(Attachment).where(
            Attachment.record_id == record_id,
        )
    ).scalars().all())
    atts_by_eq: dict[int, list] = {}
    issue_attachments: list[dict] = []
    _issue_cats = {AttachmentCategory.ISSUE_AFTER.value, AttachmentCategory.VERIFICATION.value}
    for a in atts:
        brief = {
            "id": a.id,
            "file_name": a.original_file_name or a.file_name,
            "url": url_for(a.file_path),
            "category": a.category,
        }
        eq_id = a.equipment_id or _parse_eq_from_name(a.file_name)
        # 整改 / 核实照片是记录级（无设备）→ 归入 issue_attachments
        if a.equipment_id is None and a.category in _issue_cats:
            issue_attachments.append(brief)
            continue
        if eq_id is None:
            continue
        atts_by_eq.setdefault(eq_id, []).append(brief)

    equipment_results = []
    for er, eq in eq_results:
        equipment_results.append({
            "equipment_id": eq.id,
            "equipment_code": eq.equipment_code,
            "equipment_name": eq.equipment_name,
            "equipment_type": eq.equipment_type,
            "equipment_type_label": EQUIPMENT_TYPE_LABEL.get(eq.equipment_type, eq.equipment_type),
            "location": eq.location,
            "result": er.result,
            "issue_description": er.issue_description,
            "completed_at": er.completed_at,
            "items": items_by_eq.get(eq.id, []),
            "attachments": atts_by_eq.get(eq.id, []),
        })

    timeline = []
    timeline.append({
        "at": record.created_at,
        "action": "created",
        "operator": user.name,
        "text": f"开始巡检（来源：{record.source}）",
    })
    if record.submitted_at:
        timeline.append({
            "at": record.submitted_at,
            "action": "submitted",
            "operator": user.name,
            "text": "提交本次巡检记录",
        })

    # 问题闭环流程（转发/处理/核实）追加到时间线，并算出当前处理人
    proc_rows = list(db.execute(
        select(IssueProcess).where(IssueProcess.record_id == record_id)
        .order_by(IssueProcess.created_at, IssueProcess.id)
    ).scalars().all())
    user_ids = {p.operator_id for p in proc_rows} | {p.assignee_id for p in proc_rows if p.assignee_id}
    name_map: dict[int, str] = {}
    if user_ids:
        for u in db.execute(select(User).where(User.id.in_(user_ids))).scalars().all():
            name_map[u.id] = u.name

    current_assignee = None
    for p in proc_rows:
        text = _PROCESS_ACTION_LABEL.get(p.action, p.action)
        if p.action == ProcessAction.ASSIGN.value and p.assignee_id:
            text = f"转发给「{name_map.get(p.assignee_id, p.assignee_id)}」处理"
            current_assignee = {"id": p.assignee_id, "name": name_map.get(p.assignee_id)}
        if p.content:
            text = f"{text}：{p.content}"
        timeline.append({
            "at": p.created_at,
            "action": p.action,
            "operator": name_map.get(p.operator_id),
            "text": text,
        })
    if record.status in ("completed", "rejected"):
        current_assignee = None

    return {
        "id": record.id,
        "record_no": record.record_no,
        "inspection_time": record.inspection_time,
        "submitted_at": record.submitted_at,
        "source": record.source,
        "status": record.status,
        "has_issue": record.has_issue,
        "remark": record.remark,
        "room": {"id": room.id, "code": room.code, "name": room.name, "area": room.area},
        "inspector": {"id": user.id, "name": user.name, "role": user.role},
        "current_assignee": current_assignee,
        "equipment_results": equipment_results,
        "issue_attachments": issue_attachments,
        "timeline": timeline,
    }


def _parse_eq_from_name(name: str) -> int | None:
    if not name.startswith("eq"):
        return None
    try:
        rest = name[2:]
        sep = rest.index("_")
        return int(rest[:sep])
    except (ValueError, IndexError):
        return None
