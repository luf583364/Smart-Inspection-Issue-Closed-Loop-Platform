"""Dashboard aggregations — pure read queries against existing tables."""

from datetime import date, datetime, time, timedelta
from typing import List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.inspection_record import InspectionRecord
from app.models.room import Room
from app.models.user import User
from app.utils.enums import RecordStatus

STATUS_LABEL_ZH = {
    RecordStatus.COMPLETED.value: "已完成",
    RecordStatus.PENDING_ASSIGN.value: "待转发",
    RecordStatus.PENDING_HANDLE.value: "待处理",
    RecordStatus.HANDLING.value: "处理中",
    RecordStatus.PENDING_VERIFY.value: "待核实",
    RecordStatus.REJECTED.value: "已驳回",
}

ISSUE_ORDER = [
    RecordStatus.PENDING_ASSIGN.value,
    RecordStatus.PENDING_HANDLE.value,
    RecordStatus.HANDLING.value,
    RecordStatus.PENDING_VERIFY.value,
    RecordStatus.REJECTED.value,
    RecordStatus.COMPLETED.value,
]


def _day_range(d: date) -> tuple[datetime, datetime]:
    start = datetime.combine(d, time.min)
    end = datetime.combine(d, time.max)
    return start, end


def get_summary(db: Session) -> dict:
    today = date.today()
    today_start, today_end = _day_range(today)
    month_start = datetime(today.year, today.month, 1)

    def count(*where):
        stmt = select(func.count(InspectionRecord.id))
        for w in where:
            stmt = stmt.where(w)
        return db.execute(stmt).scalar_one()

    return {
        "today_inspection": count(
            InspectionRecord.inspection_time >= today_start,
            InspectionRecord.inspection_time <= today_end,
        ),
        "pending_handle": count(
            InspectionRecord.status == RecordStatus.PENDING_HANDLE.value
        ),
        "pending_verify": count(
            InspectionRecord.status == RecordStatus.PENDING_VERIFY.value
        ),
        "completed_total": count(
            InspectionRecord.status == RecordStatus.COMPLETED.value
        ),
        "this_month_inspection": count(
            InspectionRecord.inspection_time >= month_start,
        ),
        "room_count": db.execute(
            select(func.count(Room.id)).where(Room.status == 1)
        ).scalar_one(),
    }


def get_trends(db: Session, days: int = 7) -> dict:
    today = date.today()
    start_date = today - timedelta(days=days - 1)

    inspection_rows = db.execute(
        select(
            func.date(InspectionRecord.inspection_time).label("d"),
            func.count(InspectionRecord.id).label("n"),
        )
        .where(InspectionRecord.inspection_time >= datetime.combine(start_date, time.min))
        .group_by(func.date(InspectionRecord.inspection_time))
    ).all()
    issue_rows = db.execute(
        select(
            func.date(InspectionRecord.inspection_time).label("d"),
            func.count(InspectionRecord.id).label("n"),
        )
        .where(
            InspectionRecord.inspection_time >= datetime.combine(start_date, time.min),
            InspectionRecord.has_issue == 1,
        )
        .group_by(func.date(InspectionRecord.inspection_time))
    ).all()

    insp_map = {str(r.d): int(r.n) for r in inspection_rows}
    iss_map = {str(r.d): int(r.n) for r in issue_rows}

    dates: List[str] = []
    insp: List[int] = []
    iss: List[int] = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        key = d.isoformat()
        dates.append(d.strftime("%m-%d"))
        insp.append(insp_map.get(key, 0))
        iss.append(iss_map.get(key, 0))

    return {"dates": dates, "inspection_counts": insp, "issue_counts": iss}


def get_issue_distribution(db: Session) -> dict:
    rows = db.execute(
        select(InspectionRecord.status, func.count(InspectionRecord.id))
        .group_by(InspectionRecord.status)
    ).all()
    raw = {status: int(n) for status, n in rows}
    items = [
        {
            "status": s,
            "label": STATUS_LABEL_ZH.get(s, s),
            "value": raw.get(s, 0),
        }
        for s in ISSUE_ORDER
    ]
    return {"items": items}


def get_recent_records(db: Session, limit: int = 8) -> list[dict]:
    rows = db.execute(
        select(InspectionRecord, Room.name, User.name)
        .join(Room, Room.id == InspectionRecord.room_id)
        .join(User, User.id == InspectionRecord.inspector_id)
        .order_by(InspectionRecord.inspection_time.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": rec.id,
            "record_no": rec.record_no,
            "inspection_time": rec.inspection_time,
            "room_name": room_name,
            "inspector_name": inspector_name,
            "has_issue": rec.has_issue,
            "status": rec.status,
        }
        for rec, room_name, inspector_name in rows
    ]
