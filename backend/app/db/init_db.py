"""Seed demo data for the room inspection workflow.

Idempotent: skips seeding when any user already exists.
"""

from datetime import datetime, timedelta
import random

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logger import logger
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.equipment import Equipment
from app.models.inspection_check_item import InspectionCheckItem
from app.models.inspection_equipment_result import InspectionEquipmentResult
from app.models.inspection_item_result import InspectionItemResult
from app.models.inspection_record import InspectionRecord
from app.models.room import Room
from app.models.user import User
from app.utils.time_utils import now_local
from app.utils.enums import (
    CheckItemInputType,
    EquipmentResultStatus,
    EquipmentType,
    InspectionSource,
    RecordStatus,
    UserRole,
)


def _ensure_tables() -> None:
    """Verify the Alembic-managed schema exists before seeding demo data."""
    required = set(Base.metadata.tables.keys())
    existing = set(inspect(engine).get_table_names())
    missing = sorted(required - existing)
    if missing:
        raise RuntimeError(
            "Database schema is missing tables. Run `python -m alembic upgrade head` "
            f"before starting the app. Missing: {', '.join(missing)}"
        )


def _gen_record_no(seq: int, dt: datetime) -> str:
    return f"IR{dt.strftime('%Y%m%d')}{seq:04d}"


CHECK_ITEM_TEMPLATES: dict[str, list[tuple[str, str, str, str | None, str | None]]] = {
    EquipmentType.AIR_CONDITIONER.value: [
        ("ac_running", "空调运行状态", CheckItemInputType.BOOLEAN.value, "正常运行、无告警", None),
        ("ac_temperature", "机房温度", CheckItemInputType.NUMBER.value, "22-26", "℃"),
        ("ac_humidity", "机房湿度", CheckItemInputType.NUMBER.value, "40-60", "%"),
        ("ac_water_leak", "漏水/结露", CheckItemInputType.BOOLEAN.value, "无漏水、无结露", None),
        ("ac_filter", "回风/滤网状态", CheckItemInputType.BOOLEAN.value, "无堵塞、无明显积尘", None),
    ],
    EquipmentType.ACCESS_CONTROL.value: [
        ("access_controller", "门禁控制器状态", CheckItemInputType.BOOLEAN.value, "运行正常", None),
        ("access_open_close", "开关门/刷卡测试", CheckItemInputType.BOOLEAN.value, "可正常开启和关闭", None),
        ("access_alarm", "异常开门告警", CheckItemInputType.BOOLEAN.value, "无异常告警", None),
        ("access_log", "门禁记录", CheckItemInputType.BOOLEAN.value, "记录正常、时间准确", None),
    ],
    EquipmentType.VIDEO_MONITORING.value: [
        ("video_online", "摄像头在线状态", CheckItemInputType.BOOLEAN.value, "全部在线", None),
        ("video_image", "监控画面", CheckItemInputType.BOOLEAN.value, "清晰无遮挡", None),
        ("video_storage", "录像存储", CheckItemInputType.BOOLEAN.value, "正常保存", None),
        ("video_time", "视频时间同步", CheckItemInputType.BOOLEAN.value, "时间准确", None),
    ],
    EquipmentType.UPS.value: [
        ("ups_running", "UPS运行状态", CheckItemInputType.BOOLEAN.value, "运行正常、无告警", None),
        ("ups_load", "UPS负载率", CheckItemInputType.NUMBER.value, "<80", "%"),
        ("ups_battery", "电池状态", CheckItemInputType.BOOLEAN.value, "无鼓包、漏液、告警", None),
        ("ups_input_voltage", "输入电压", CheckItemInputType.NUMBER.value, "220", "V"),
        ("ups_output_voltage", "输出电压", CheckItemInputType.NUMBER.value, "220", "V"),
    ],
    EquipmentType.SMOKE_DETECTOR.value: [
        ("smoke_status", "烟雾探测器状态", CheckItemInputType.BOOLEAN.value, "运行正常", None),
        ("smoke_obstruction", "探测器遮挡/积尘", CheckItemInputType.BOOLEAN.value, "无遮挡、无明显积尘", None),
        ("smoke_alarm", "消防告警状态", CheckItemInputType.BOOLEAN.value, "无告警", None),
        ("smoke_self_test", "自检/联动状态", CheckItemInputType.BOOLEAN.value, "自检正常", None),
    ],
    EquipmentType.SERVER_ENV.value: [
        ("server_temp_alarm", "服务器温度告警", CheckItemInputType.BOOLEAN.value, "无过热告警", None),
        ("server_room_temp", "机柜/通道温度", CheckItemInputType.NUMBER.value, "<30", "℃"),
        ("server_fan_alarm", "风扇/硬件告警", CheckItemInputType.BOOLEAN.value, "无硬件告警", None),
        ("server_indicator", "服务器指示灯", CheckItemInputType.BOOLEAN.value, "无红灯/黄灯", None),
        ("server_cabling", "机柜卫生/线缆", CheckItemInputType.BOOLEAN.value, "整洁、线缆无松脱", None),
    ],
}


ROOM_EQUIPMENT_PLAN: dict[str, list[tuple[str, str, str, str]]] = {
    "JF-OFFICE": [
        ("EQ-OFFICE-AC-01", "空调运行状态", EquipmentType.AIR_CONDITIONER.value, "办公机房"),
        ("EQ-OFFICE-ACCESS-01", "门禁系统", EquipmentType.ACCESS_CONTROL.value, "办公机房入口"),
        ("EQ-OFFICE-VIDEO-01", "视频监控", EquipmentType.VIDEO_MONITORING.value, "办公机房"),
        ("EQ-OFFICE-UPS-01", "UPS状态", EquipmentType.UPS.value, "办公机房动力区"),
        ("EQ-OFFICE-SMOKE-01", "烟雾探测器", EquipmentType.SMOKE_DETECTOR.value, "办公机房天花"),
        ("EQ-OFFICE-SERVER-01", "服务器温度告警", EquipmentType.SERVER_ENV.value, "办公机房机柜区"),
    ],
    "JF-ECOM": [
        ("EQ-ECOM-AC-01", "空调运行状态", EquipmentType.AIR_CONDITIONER.value, "电商机房"),
        ("EQ-ECOM-ACCESS-01", "门禁系统", EquipmentType.ACCESS_CONTROL.value, "电商机房入口"),
        ("EQ-ECOM-VIDEO-01", "视频监控", EquipmentType.VIDEO_MONITORING.value, "电商机房"),
        ("EQ-ECOM-UPS-01", "UPS状态", EquipmentType.UPS.value, "电商机房动力区"),
        ("EQ-ECOM-SMOKE-01", "烟雾探测器", EquipmentType.SMOKE_DETECTOR.value, "电商机房天花"),
        ("EQ-ECOM-SERVER-01", "服务器温度告警", EquipmentType.SERVER_ENV.value, "电商机房机柜区"),
    ],
}


def _seed_users(db: Session) -> dict[str, User]:
    payload = [
        ("admin", "管理员", UserRole.ADMIN, "13800000000"),
        ("inspector01", "张巡检", UserRole.INSPECTOR, "13800000001"),
        ("inspector02", "李巡检", UserRole.INSPECTOR, "13800000002"),
        ("handler01", "王处理", UserRole.HANDLER, "13800000003"),
        ("handler02", "赵处理", UserRole.HANDLER, "13800000004"),
        ("verifier01", "孙核实", UserRole.VERIFIER, "13800000005"),
    ]
    users: dict[str, User] = {}
    for username, name, role, phone in payload:
        u = User(
            username=username,
            password_hash=hash_password("123456"),
            name=name,
            role=role.value,
            phone=phone,
            status=1,
        )
        db.add(u)
        users[username] = u
    db.commit()
    for u in users.values():
        db.refresh(u)
    return users


def _seed_rooms(db: Session, users: dict[str, User]) -> dict[str, Room]:
    payload = [
        ("JF-OFFICE", "办公机房", "办公区", users["inspector01"].id, "010-12340001"),
        ("JF-ECOM", "电商机房", "电商业务区", users["inspector02"].id, "010-12340002"),
    ]
    rooms: dict[str, Room] = {}
    for code, name, area, owner_id, phone in payload:
        r = Room(code=code, name=name, area=area, owner_id=owner_id, phone=phone, status=1)
        db.add(r)
        rooms[code] = r
    db.commit()
    for r in rooms.values():
        db.refresh(r)
    return rooms


def _seed_basic_rooms(db: Session) -> dict[str, Room]:
    payload = [
        ("JF-OFFICE", "办公机房", "办公区", None, "010-12340001"),
        ("JF-ECOM", "电商机房", "电商业务区", None, "010-12340002"),
    ]
    rooms: dict[str, Room] = {}
    for code, name, area, owner_id, phone in payload:
        room = Room(
            code=code,
            name=name,
            area=area,
            owner_id=owner_id,
            phone=phone,
            status=1,
        )
        db.add(room)
        rooms[code] = room
    db.commit()
    for room in rooms.values():
        db.refresh(room)
    return rooms


def _seed_check_items(db: Session) -> dict[str, list[InspectionCheckItem]]:
    by_type: dict[str, list[InspectionCheckItem]] = {}
    for eq_type, items in CHECK_ITEM_TEMPLATES.items():
        bucket: list[InspectionCheckItem] = []
        for idx, (code, name, input_type, std, unit) in enumerate(items, start=1):
            obj = InspectionCheckItem(
                equipment_type=eq_type,
                item_code=code,
                item_name=name,
                input_type=input_type,
                standard_value=std,
                unit=unit,
                required=1,
                sort_order=idx,
                status=1,
            )
            db.add(obj)
            bucket.append(obj)
        by_type[eq_type] = bucket
    db.commit()
    for items in by_type.values():
        for it in items:
            db.refresh(it)
    return by_type


def _seed_clean(db: Session) -> None:
    admin = User(
        username=settings.BOOTSTRAP_ADMIN_USERNAME,
        password_hash=hash_password(settings.BOOTSTRAP_ADMIN_PASSWORD),
        name=settings.BOOTSTRAP_ADMIN_NAME,
        role=UserRole.ADMIN.value,
        phone=settings.BOOTSTRAP_ADMIN_PHONE,
        status=1,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    rooms = _seed_basic_rooms(db)
    check_items = _seed_check_items(db)
    equipment = _seed_equipment(db, rooms)
    logger.info(
        "Seeded clean production data: "
        f"1 admin / {len(rooms)} rooms / "
        f"{sum(len(v) for v in check_items.values())} check_items / "
        f"{len(equipment)} equipment"
    )


def _seed_equipment(db: Session, rooms: dict[str, Room]) -> list[Equipment]:
    out: list[Equipment] = []
    for room_code, plan in ROOM_EQUIPMENT_PLAN.items():
        room = rooms.get(room_code)
        if not room:
            continue
        for code, name, eq_type, location in plan:
            eq = Equipment(
                equipment_code=code,
                equipment_name=name,
                equipment_type=eq_type,
                room_id=room.id,
                location=location,
                status=1,
                remark=None,
            )
            db.add(eq)
            out.append(eq)
    db.commit()
    for e in out:
        db.refresh(e)
    return out


def _seed_records(
    db: Session,
    users: dict[str, User],
    rooms: dict[str, Room],
    equipment: list[Equipment],
    check_items: dict[str, list[InspectionCheckItem]],
) -> None:
    """Create historical records covering all-normal and abnormal flows."""

    rng = random.Random(20260605)
    now = now_local()
    seq_by_day: dict[str, int] = {}

    def next_no(dt: datetime) -> str:
        key = dt.strftime("%Y%m%d")
        seq_by_day[key] = seq_by_day.get(key, 0) + 1
        return _gen_record_no(seq_by_day[key], dt)

    by_room: dict[int, list[Equipment]] = {}
    for eq in equipment:
        by_room.setdefault(eq.room_id, []).append(eq)

    # 演示记录全部落在「过去」（最近一条为昨天），避免与「一天一机房只能巡检一次」
    # 冲突：全新部署当天，演示巡检员仍可正常对机房做一次巡检，再次进入才会被拦截。
    plan = [
        (1, "JF-OFFICE", "inspector01", True),
        (1, "JF-ECOM", "inspector02", False),
        (2, "JF-OFFICE", "inspector01", True),
        (3, "JF-ECOM", "inspector02", False),
        (4, "JF-OFFICE", "inspector01", True),
        (5, "JF-ECOM", "inspector02", True),
        (6, "JF-OFFICE", "inspector01", False),
        (7, "JF-ECOM", "inspector02", True),
    ]

    for offset, room_code, inspector_username, all_normal in plan:
        dt = (now - timedelta(days=offset)).replace(
            hour=rng.randint(9, 18), minute=rng.choice([0, 15, 30, 45])
        )
        room = rooms[room_code]
        inspector = users[inspector_username]
        eqs = by_room.get(room.id, [])
        if not eqs:
            continue

        record = InspectionRecord(
            record_no=next_no(dt),
            inspector_id=inspector.id,
            room_id=room.id,
            inspection_time=dt,
            source=InspectionSource.MANUAL.value,
            status=RecordStatus.COMPLETED.value,
            has_issue=0,
            remark=None,
            submitted_at=dt + timedelta(minutes=rng.randint(15, 60)),
        )
        db.add(record)
        db.flush()

        record_has_issue = False
        forced_abnormal_eq_idx = offset % len(eqs) if not all_normal else -1
        for eq_idx, eq in enumerate(eqs):
            items = check_items.get(eq.equipment_type, [])
            eq_result = InspectionEquipmentResult(
                record_id=record.id,
                equipment_id=eq.id,
                result=EquipmentResultStatus.NORMAL.value,
                issue_description=None,
                completed_at=dt + timedelta(minutes=rng.randint(5, 30)),
            )
            db.add(eq_result)

            abnormal_idx: set[int] = set()
            if items and eq_idx == forced_abnormal_eq_idx:
                abnormal_idx.add(0)
            elif not all_normal and items and rng.random() < 0.2:
                abnormal_idx.add(rng.randrange(len(items)))

            for idx, ci in enumerate(items):
                is_abn = idx in abnormal_idx
                if ci.input_type == CheckItemInputType.BOOLEAN.value:
                    value = "abnormal" if is_abn else "normal"
                elif ci.input_type == CheckItemInputType.NUMBER.value:
                    value = str(rng.choice([31, 35, 88])) if is_abn else str(rng.choice([23, 24, 45]))
                else:
                    value = ""
                db.add(
                    InspectionItemResult(
                        record_id=record.id,
                        equipment_id=eq.id,
                        check_item_id=ci.id,
                        value=value,
                        is_abnormal=1 if is_abn else 0,
                        remark="现场检查发现异常，需排查" if is_abn else None,
                    )
                )

            if abnormal_idx:
                eq_result.result = EquipmentResultStatus.ABNORMAL.value
                eq_result.issue_description = f"{eq.equipment_name}发现异常，需排查"
                record_has_issue = True

        record.has_issue = 1 if record_has_issue else 0
        record.status = (
            RecordStatus.PENDING_ASSIGN.value if record_has_issue else RecordStatus.COMPLETED.value
        )

    db.commit()


def _seed(db: Session) -> None:
    users = _seed_users(db)
    rooms = _seed_rooms(db, users)
    check_items = _seed_check_items(db)
    equipment = _seed_equipment(db, rooms)
    _seed_records(db, users, rooms, equipment, check_items)

    record_total = db.execute(select(InspectionRecord)).scalars().all()
    logger.info(
        f"Seeded {len(users)} users / {len(rooms)} rooms / "
        f"{sum(len(v) for v in check_items.values())} check_items / "
        f"{len(equipment)} equipment / {len(record_total)} historical records"
    )


def init_db() -> None:
    _ensure_tables()
    with SessionLocal() as db:
        existing = db.execute(select(User).limit(1)).first()
        if existing:
            logger.info("DB already has data, skip seeding.")
            return
        if settings.SEED_DEMO_DATA:
            logger.info("Empty DB - seeding demo data ...")
            _seed(db)
        else:
            logger.info("Empty DB - seeding clean production data ...")
            _seed_clean(db)
