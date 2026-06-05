"""Mobile inspection orchestration.

Owns the lifecycle of one room-level inspection record:
  start → save per-equipment results → upload images → submit.

Status transitions are managed here so the API layer stays thin.
"""

from datetime import datetime
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.attachment import Attachment
from app.models.equipment import Equipment
from app.models.inspection_check_item import InspectionCheckItem
from app.models.inspection_equipment_result import InspectionEquipmentResult
from app.models.inspection_item_result import InspectionItemResult
from app.models.inspection_record import InspectionRecord
from app.models.operation_log import OperationLog
from app.models.room import Room
from app.models.user import User
from app.utils.enums import (
    AttachmentCategory,
    AttachmentTarget,
    EquipmentResultStatus,
    EQUIPMENT_TYPE_LABEL,
    InspectionSource,
    RecordStatus,
    UserRole,
)
from app.utils.file_storage import delete_saved_file, url_for
from app.utils.response import BusinessError


def _gen_record_no(db: Session, dt: datetime) -> str:
    day = dt.strftime("%Y%m%d")
    prefix = f"IR{day}"
    rows = db.execute(
        select(InspectionRecord.record_no).where(InspectionRecord.record_no.like(f"{prefix}%"))
    ).scalars().all()
    used = {int(no[len(prefix):]) for no in rows if no[len(prefix):].isdigit()}
    seq = 1
    while seq in used:
        seq += 1
    return f"{prefix}{seq:04d}"


def _can_inspect(user: User) -> bool:
    return user.role in (UserRole.ADMIN.value, UserRole.INSPECTOR.value)


def _load_equipment_for_room(db: Session, room_id: int) -> list[Equipment]:
    return list(
        db.execute(
            select(Equipment)
            .where(Equipment.room_id == room_id, Equipment.status == 1)
            .order_by(Equipment.id)
        ).scalars().all()
    )


def _load_equipment_for_record(db: Session, record: InspectionRecord) -> list[Equipment]:
    equipment = _load_equipment_for_room(db, record.room_id)
    done_ids = set(
        db.execute(
            select(InspectionEquipmentResult.equipment_id).where(
                InspectionEquipmentResult.record_id == record.id
            )
        ).scalars().all()
    )
    started_at = record.created_at or record.inspection_time
    return [
        eq
        for eq in equipment
        if eq.id in done_ids
        or not (
            started_at
            and (
                (eq.created_at and eq.created_at > started_at)
                or (eq.updated_at and eq.updated_at > started_at)
            )
        )
    ]


def _check_items_for_types(db: Session, types: Iterable[str]) -> dict[str, list[InspectionCheckItem]]:
    types = list(set(types))
    if not types:
        return {}
    rows = db.execute(
        select(InspectionCheckItem)
        .where(InspectionCheckItem.equipment_type.in_(types), InspectionCheckItem.status == 1)
        .order_by(InspectionCheckItem.equipment_type, InspectionCheckItem.sort_order)
    ).scalars().all()
    by_type: dict[str, list[InspectionCheckItem]] = {}
    for ci in rows:
        by_type.setdefault(ci.equipment_type, []).append(ci)
    return by_type


def _progress(db: Session, record_id: int, total: int) -> dict:
    rows = db.execute(
        select(InspectionEquipmentResult.result)
        .where(InspectionEquipmentResult.record_id == record_id)
    ).scalars().all()
    completed = len(rows)
    normal = sum(1 for r in rows if r == EquipmentResultStatus.NORMAL.value)
    abnormal = sum(1 for r in rows if r == EquipmentResultStatus.ABNORMAL.value)
    return {"total": total, "completed": completed, "normal": normal, "abnormal": abnormal}


def _inspection_nav(
    db: Session,
    record: InspectionRecord,
    *,
    current_equipment_id: int | None = None,
) -> dict:
    equipment_list = _load_equipment_for_record(db, record)
    total = len(equipment_list)
    progress = _progress(db, record.id, total)
    done_ids = set(
        db.execute(
            select(InspectionEquipmentResult.equipment_id).where(
                InspectionEquipmentResult.record_id == record.id
            )
        ).scalars().all()
    )

    ordered_ids = [e.id for e in equipment_list]
    if current_equipment_id in ordered_ids:
        idx = ordered_ids.index(current_equipment_id)
        candidates = ordered_ids[idx + 1:] + ordered_ids[:idx + 1]
    else:
        candidates = ordered_ids

    next_equipment_id = next((eid for eid in candidates if eid not in done_ids), None)
    remaining = max(total - progress["completed"], 0)
    return {
        "record_id": record.id,
        "completed_count": progress["completed"],
        "total_count": total,
        "remaining_count": remaining,
        "next_equipment_id": next_equipment_id,
        "next_pending_equipment_id": next_equipment_id,
        "all_completed": remaining == 0,
        "progress": progress,
    }


def _equipment_briefs_for_record(
    db: Session,
    record: InspectionRecord,
    equipment_list: list[Equipment],
) -> list[dict]:
    existing_results = db.execute(
        select(InspectionEquipmentResult).where(InspectionEquipmentResult.record_id == record.id)
    ).scalars().all()
    result_by_eq = {r.equipment_id: r for r in existing_results}

    abnormal_item_counts = {}
    for eq in equipment_list:
        cnt = db.execute(
            select(InspectionItemResult)
            .where(
                InspectionItemResult.record_id == record.id,
                InspectionItemResult.equipment_id == eq.id,
                InspectionItemResult.is_abnormal == 1,
            )
        ).scalars().all()
        abnormal_item_counts[eq.id] = len(cnt)

    check_items_by_type = _check_items_for_types(db, [e.equipment_type for e in equipment_list])

    equipment_briefs = []
    for eq in equipment_list:
        items = check_items_by_type.get(eq.equipment_type, [])
        r = result_by_eq.get(eq.id)
        equipment_briefs.append({
            "id": eq.id,
            "equipment_code": eq.equipment_code,
            "equipment_name": eq.equipment_name,
            "equipment_type": eq.equipment_type,
            "equipment_type_label": EQUIPMENT_TYPE_LABEL.get(eq.equipment_type, eq.equipment_type),
            "location": eq.location,
            "result": r.result if r else None,
            "completed_at": r.completed_at if r else None,
            "issue_description": r.issue_description if r else None,
            "item_count": len(items),
            "abnormal_item_count": abnormal_item_counts.get(eq.id, 0),
        })
    return equipment_briefs


# ----------------- public service API -----------------


def start_room_inspection(
    db: Session,
    *,
    room_code: str,
    user: User,
    source: str = "manual",
) -> dict:
    if not _can_inspect(user):
        raise BusinessError("当前账号无巡检权限", code=4201, http_status=403)

    room = db.execute(select(Room).where(Room.code == room_code)).scalar_one_or_none()
    if not room:
        raise BusinessError("机房不存在", code=4202, http_status=404)
    if room.status != 1:
        raise BusinessError("该机房当前已停用", code=4203)

    equipment_list = _load_equipment_for_room(db, room.id)
    if not equipment_list:
        raise BusinessError("该机房暂无可巡检设备，请先在「设备管理」中添加", code=4204)

    if source not in (InspectionSource.MANUAL.value, InspectionSource.QR.value):
        source = InspectionSource.MANUAL.value

    # try to reuse an in-progress record for this user/room
    record = db.execute(
        select(InspectionRecord)
        .where(
            InspectionRecord.room_id == room.id,
            InspectionRecord.inspector_id == user.id,
            InspectionRecord.status == RecordStatus.IN_PROGRESS.value,
        )
        .order_by(InspectionRecord.created_at.desc())
    ).scalar_one_or_none()

    if not record:
        now = datetime.now().replace(microsecond=0)
        record = InspectionRecord(
            record_no=_gen_record_no(db, now),
            inspector_id=user.id,
            room_id=room.id,
            inspection_time=now,
            source=source,
            status=RecordStatus.IN_PROGRESS.value,
            has_issue=0,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

    equipment_list = _load_equipment_for_record(db, record)
    equipment_briefs = _equipment_briefs_for_record(db, record, equipment_list)
    nav = _inspection_nav(db, record)

    return {
        "record_id": record.id,
        "record_no": record.record_no,
        "status": record.status,
        "source": record.source,
        "inspection_time": record.inspection_time,
        "room": {
            "id": room.id,
            "code": room.code,
            "name": room.name,
            "area": room.area,
        },
        "inspector": {"id": user.id, "name": user.name, "role": user.role},
        "equipment_list": equipment_briefs,
        "progress": nav["progress"],
        "completed_count": nav["completed_count"],
        "total_count": nav["total_count"],
        "remaining_count": nav["remaining_count"],
        "next_pending_equipment_id": nav["next_pending_equipment_id"],
        "all_completed": nav["all_completed"],
    }


def get_equipment_inspection_state(
    db: Session, *, record_id: int, equipment_id: int, user: User
) -> dict:
    record = _require_my_active_record(db, record_id, user)
    equipment = db.execute(select(Equipment).where(Equipment.id == equipment_id)).scalar_one_or_none()
    if not equipment or equipment.room_id != record.room_id:
        raise BusinessError("设备不属于本次巡检机房", code=4210, http_status=404)

    items = db.execute(
        select(InspectionCheckItem)
        .where(
            InspectionCheckItem.equipment_type == equipment.equipment_type,
            InspectionCheckItem.status == 1,
        )
        .order_by(InspectionCheckItem.sort_order)
    ).scalars().all()

    saved = db.execute(
        select(InspectionItemResult).where(
            InspectionItemResult.record_id == record_id,
            InspectionItemResult.equipment_id == equipment_id,
        )
    ).scalars().all()
    saved_by_id = {s.check_item_id: s for s in saved}

    item_values = []
    for it in items:
        s = saved_by_id.get(it.id)
        item_values.append({
            "check_item_id": it.id,
            "item_code": it.item_code,
            "item_name": it.item_name,
            "input_type": it.input_type,
            "standard_value": it.standard_value,
            "unit": it.unit,
            "value": s.value if s else None,
            "is_abnormal": bool(s.is_abnormal) if s else False,
            "remark": s.remark if s else None,
        })

    eq_result = db.execute(
        select(InspectionEquipmentResult).where(
            InspectionEquipmentResult.record_id == record_id,
            InspectionEquipmentResult.equipment_id == equipment_id,
        )
    ).scalar_one_or_none()

    atts = db.execute(
        select(Attachment).where(
            Attachment.record_id == record_id,
            Attachment.equipment_id == equipment_id,
            Attachment.category.in_([
                AttachmentCategory.INSPECTION_ABNORMAL.value,
                AttachmentCategory.ISSUE_BEFORE.value,
            ]),
        )
    ).scalars().all()
    eq_attachments = [
        {
            "id": a.id,
            "file_name": a.original_file_name or a.file_name,
            "url": url_for(a.file_path),
            "file_size": a.file_size,
            "category": a.category,
        }
        for a in atts
    ]

    equipment_list = _load_equipment_for_record(db, record)
    nav = _inspection_nav(db, record, current_equipment_id=equipment_id)

    return {
        "record_id": record_id,
        "current_record": {
            "id": record.id,
            "record_no": record.record_no,
            "status": record.status,
            "room_id": record.room_id,
        },
        "equipment": {
            "id": equipment.id,
            "equipment_code": equipment.equipment_code,
            "equipment_name": equipment.equipment_name,
            "equipment_type": equipment.equipment_type,
            "equipment_type_label": EQUIPMENT_TYPE_LABEL.get(equipment.equipment_type, equipment.equipment_type),
            "location": equipment.location,
        },
        "items": item_values,
        "attachments": eq_attachments,
        "result": eq_result.result if eq_result else None,
        "issue_description": eq_result.issue_description if eq_result else None,
        "completed_at": eq_result.completed_at if eq_result else None,
        "equipment_list": _equipment_briefs_for_record(db, record, equipment_list),
        "progress": nav["progress"],
        "completed_count": nav["completed_count"],
        "total_count": nav["total_count"],
        "remaining_count": nav["remaining_count"],
        "next_pending_equipment_id": nav["next_pending_equipment_id"],
        "all_completed": nav["all_completed"],
    }


def save_equipment_result(
    db: Session,
    *,
    record_id: int,
    equipment_id: int,
    user: User,
    result: str,
    issue_description: str | None,
    items: list[dict],
) -> dict:
    record = _require_my_active_record(db, record_id, user)
    equipment = db.execute(select(Equipment).where(Equipment.id == equipment_id)).scalar_one_or_none()
    if not equipment or equipment.room_id != record.room_id:
        raise BusinessError("设备不属于本次巡检机房", code=4210, http_status=404)

    # validate items belong to equipment_type
    valid_items = db.execute(
        select(InspectionCheckItem).where(
            InspectionCheckItem.equipment_type == equipment.equipment_type,
            InspectionCheckItem.status == 1,
        )
    ).scalars().all()
    valid_ids = {it.id for it in valid_items}
    required_ids = {it.id for it in valid_items if it.required == 1}

    incoming_ids = {x["check_item_id"] for x in items}
    bad = incoming_ids - valid_ids
    if bad:
        raise BusinessError(f"包含不属于该设备类型的检查项: {sorted(bad)}", code=4211)
    if not required_ids.issubset(incoming_ids):
        missing = required_ids - incoming_ids
        raise BusinessError(f"以下必填项未提交: {sorted(missing)}", code=4212)

    # upsert item results
    db.execute(
        InspectionItemResult.__table__.delete().where(
            InspectionItemResult.record_id == record_id,
            InspectionItemResult.equipment_id == equipment_id,
        )
    )
    for x in items:
        db.add(InspectionItemResult(
            record_id=record_id,
            equipment_id=equipment_id,
            check_item_id=x["check_item_id"],
            value=x.get("value"),
            is_abnormal=1 if x.get("is_abnormal") else 0,
            remark=x.get("remark"),
        ))

    # check: result=abnormal must have at least one is_abnormal=1 OR issue_description
    if result == EquipmentResultStatus.ABNORMAL.value and not any(x.get("is_abnormal") for x in items) and not issue_description:
        raise BusinessError("已选择「异常」，请至少标记一项异常或填写异常描述", code=4213)

    # upsert equipment result
    eq_result = db.execute(
        select(InspectionEquipmentResult).where(
            InspectionEquipmentResult.record_id == record_id,
            InspectionEquipmentResult.equipment_id == equipment_id,
        )
    ).scalar_one_or_none()
    if eq_result:
        eq_result.result = result
        eq_result.issue_description = issue_description if result == EquipmentResultStatus.ABNORMAL.value else None
        eq_result.completed_at = datetime.now().replace(microsecond=0)
    else:
        db.add(InspectionEquipmentResult(
            record_id=record_id,
            equipment_id=equipment_id,
            result=result,
            issue_description=issue_description if result == EquipmentResultStatus.ABNORMAL.value else None,
            completed_at=datetime.now().replace(microsecond=0),
        ))

    db.commit()

    return _inspection_nav(db, record, current_equipment_id=equipment_id)


def attach_image(
    db: Session,
    *,
    record_id: int,
    equipment_id: int,
    user: User,
    saved: dict,
) -> dict:
    """Persist an Attachment row that points at a file already saved by file_storage.

    File name is rewritten to encode the equipment_id so we can scope it later.
    """
    record = _require_my_active_record(db, record_id, user)
    equipment = db.execute(select(Equipment).where(Equipment.id == equipment_id)).scalar_one_or_none()
    if not equipment or equipment.room_id != record.room_id:
        raise BusinessError("设备不属于本次巡检机房", code=4210, http_status=404)

    scoped_name = f"eq{equipment_id}_{saved['file_name']}"
    att = Attachment(
        target_type=AttachmentTarget.RECORD.value,
        target_id=record_id,
        record_id=record_id,
        equipment_id=equipment_id,
        category=AttachmentCategory.INSPECTION_ABNORMAL.value,
        original_file_name=saved["file_name"],
        file_name=scoped_name,
        file_path=saved["file_path"],
        file_size=saved["file_size"],
        mime_type=saved["mime_type"],
        uploader_id=user.id,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return {
        "id": att.id,
        "file_name": att.original_file_name or att.file_name,
        "url": url_for(att.file_path),
        "file_size": att.file_size,
        "category": att.category,
    }


def delete_attachment(db: Session, *, attachment_id: int, user: User) -> dict:
    att = db.execute(select(Attachment).where(Attachment.id == attachment_id)).scalar_one_or_none()
    if not att:
        raise BusinessError("附件不存在", code=4230, http_status=404)
    if att.record_id is None:
        raise BusinessError("历史附件缺少巡检记录关联，无法在移动端删除", code=4231)

    record = db.execute(
        select(InspectionRecord).where(InspectionRecord.id == att.record_id)
    ).scalar_one_or_none()
    if not record:
        raise BusinessError("附件关联的巡检记录不存在", code=4232, http_status=404)
    if record.status != RecordStatus.IN_PROGRESS.value:
        raise BusinessError("巡检记录已提交，附件不可删除", code=4233, http_status=403)
    if user.role != UserRole.ADMIN.value and record.inspector_id != user.id:
        raise BusinessError("只能删除自己当前巡检记录中的附件", code=4234, http_status=403)

    deleted_file = delete_saved_file(att.file_path)
    db.delete(att)
    db.add(OperationLog(
        user_id=user.id,
        action="attachment.delete",
        target_type="attachment",
        target_id=attachment_id,
        detail={
            "record_id": record.id,
            "equipment_id": att.equipment_id,
            "file_path": att.file_path,
            "file_deleted": deleted_file,
        },
    ))
    db.commit()
    return {"id": attachment_id, "deleted": True, "file_deleted": deleted_file}


def submit_record(db: Session, *, record_id: int, user: User) -> dict:
    record = _require_my_active_record(db, record_id, user)

    equipment = _load_equipment_for_record(db, record)
    eq_ids = {e.id for e in equipment}

    results = db.execute(
        select(InspectionEquipmentResult).where(InspectionEquipmentResult.record_id == record_id)
    ).scalars().all()
    done_ids = {r.equipment_id for r in results}

    missing = eq_ids - done_ids
    if missing:
        raise BusinessError(
            f"还有 {len(missing)} 台设备未巡检，请完成后再提交",
            code=4220,
        )

    has_abnormal = any(r.result == EquipmentResultStatus.ABNORMAL.value for r in results)
    from_status = record.status
    record.has_issue = 1 if has_abnormal else 0
    record.status = (
        RecordStatus.PENDING_ASSIGN.value if has_abnormal else RecordStatus.COMPLETED.value
    )
    record.submitted_at = datetime.now().replace(microsecond=0)

    normal_n = sum(1 for r in results if r.result == EquipmentResultStatus.NORMAL.value)
    abnormal_n = sum(1 for r in results if r.result == EquipmentResultStatus.ABNORMAL.value)

    db.add(OperationLog(
        user_id=user.id,
        action="inspection.submit",
        target_type="inspection_record",
        target_id=record.id,
        detail={
            "record_no": record.record_no,
            "room_id": record.room_id,
            "from_status": from_status,
            "to_status": record.status,
            "equipment_total": len(equipment),
            "normal_equipment": normal_n,
            "abnormal_equipment": abnormal_n,
        },
    ))
    db.commit()
    db.refresh(record)

    # Generate the persisted HTML report right after a successful submit so the
    # file shows up in REPORTS_DIR immediately. Imported lazily to avoid an
    # import cycle (report_service -> inspection_record_service).
    from app.services import report_service
    report_service.safe_generate(db, record.id)

    return {
        "record_id": record.id,
        "record_no": record.record_no,
        "status": record.status,
        "has_issue": record.has_issue,
        "submitted_at": record.submitted_at,
        "summary": {
            "equipment_total": len(equipment),
            "normal_equipment": normal_n,
            "abnormal_equipment": abnormal_n,
        },
    }


def _require_my_active_record(db: Session, record_id: int, user: User) -> InspectionRecord:
    record = db.execute(select(InspectionRecord).where(InspectionRecord.id == record_id)).scalar_one_or_none()
    if not record:
        raise BusinessError("巡检记录不存在", code=4205, http_status=404)
    if record.status != RecordStatus.IN_PROGRESS.value:
        raise BusinessError("当前记录已提交，不可继续修改", code=4206)
    if user.role != UserRole.ADMIN.value and record.inspector_id != user.id:
        raise BusinessError("只能操作自己创建的巡检记录", code=4207, http_status=403)
    return record
