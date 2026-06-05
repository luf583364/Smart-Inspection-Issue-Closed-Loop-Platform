"""two room inspection templates

Revision ID: b7c2d4e9f1a0
Revises: a3f5c9d8e2b1
Create Date: 2026-06-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c2d4e9f1a0"
down_revision: Union[str, None] = "a3f5c9d8e2b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CURRENT_TYPES = [
    "AIR_CONDITIONER",
    "ACCESS_CONTROL",
    "VIDEO_MONITORING",
    "UPS",
    "SMOKE_DETECTOR",
    "SERVER_ENV",
]

LEGACY_ROOM_CODES = ["JF-A01", "JF-A02", "JF-B01", "JF-B02", "JF-C01"]

ROOMS = [
    ("JF-OFFICE", "JF-A01", "办公机房", "办公区", "inspector01", "010-12340001"),
    ("JF-ECOM", "JF-A02", "电商机房", "电商业务区", "inspector02", "010-12340002"),
]

CHECK_ITEM_TEMPLATES = {
    "AIR_CONDITIONER": [
        ("ac_running", "空调运行状态", "boolean", "正常运行、无告警", None, 1),
        ("ac_temperature", "机房温度", "number", "22-26", "℃", 2),
        ("ac_humidity", "机房湿度", "number", "40-60", "%", 3),
        ("ac_water_leak", "漏水/结露", "boolean", "无漏水、无结露", None, 4),
        ("ac_filter", "回风/滤网状态", "boolean", "无堵塞、无明显积尘", None, 5),
    ],
    "ACCESS_CONTROL": [
        ("access_controller", "门禁控制器状态", "boolean", "运行正常", None, 1),
        ("access_open_close", "开关门/刷卡测试", "boolean", "可正常开启和关闭", None, 2),
        ("access_alarm", "异常开门告警", "boolean", "无异常告警", None, 3),
        ("access_log", "门禁记录", "boolean", "记录正常、时间准确", None, 4),
    ],
    "VIDEO_MONITORING": [
        ("video_online", "摄像头在线状态", "boolean", "全部在线", None, 1),
        ("video_image", "监控画面", "boolean", "清晰无遮挡", None, 2),
        ("video_storage", "录像存储", "boolean", "正常保存", None, 3),
        ("video_time", "视频时间同步", "boolean", "时间准确", None, 4),
    ],
    "UPS": [
        ("ups_running", "UPS运行状态", "boolean", "运行正常、无告警", None, 1),
        ("ups_load", "UPS负载率", "number", "<80", "%", 2),
        ("ups_battery", "电池状态", "boolean", "无鼓包、漏液、告警", None, 3),
        ("ups_input_voltage", "输入电压", "number", "220", "V", 4),
        ("ups_output_voltage", "输出电压", "number", "220", "V", 5),
    ],
    "SMOKE_DETECTOR": [
        ("smoke_status", "烟雾探测器状态", "boolean", "运行正常", None, 1),
        ("smoke_obstruction", "探测器遮挡/积尘", "boolean", "无遮挡、无明显积尘", None, 2),
        ("smoke_alarm", "消防告警状态", "boolean", "无告警", None, 3),
        ("smoke_self_test", "自检/联动状态", "boolean", "自检正常", None, 4),
    ],
    "SERVER_ENV": [
        ("server_temp_alarm", "服务器温度告警", "boolean", "无过热告警", None, 1),
        ("server_room_temp", "机柜/通道温度", "number", "<30", "℃", 2),
        ("server_fan_alarm", "风扇/硬件告警", "boolean", "无硬件告警", None, 3),
        ("server_indicator", "服务器指示灯", "boolean", "无红灯/黄灯", None, 4),
        ("server_cabling", "机柜卫生/线缆", "boolean", "整洁、线缆无松脱", None, 5),
    ],
}

EQUIPMENT_PLAN = {
    "JF-OFFICE": [
        ("EQ-OFFICE-AC-01", "空调运行状态", "AIR_CONDITIONER", "办公机房"),
        ("EQ-OFFICE-ACCESS-01", "门禁系统", "ACCESS_CONTROL", "办公机房入口"),
        ("EQ-OFFICE-VIDEO-01", "视频监控", "VIDEO_MONITORING", "办公机房"),
        ("EQ-OFFICE-UPS-01", "UPS状态", "UPS", "办公机房动力区"),
        ("EQ-OFFICE-SMOKE-01", "烟雾探测器", "SMOKE_DETECTOR", "办公机房天花"),
        ("EQ-OFFICE-SERVER-01", "服务器温度告警", "SERVER_ENV", "办公机房机柜区"),
    ],
    "JF-ECOM": [
        ("EQ-ECOM-AC-01", "空调运行状态", "AIR_CONDITIONER", "电商机房"),
        ("EQ-ECOM-ACCESS-01", "门禁系统", "ACCESS_CONTROL", "电商机房入口"),
        ("EQ-ECOM-VIDEO-01", "视频监控", "VIDEO_MONITORING", "电商机房"),
        ("EQ-ECOM-UPS-01", "UPS状态", "UPS", "电商机房动力区"),
        ("EQ-ECOM-SMOKE-01", "烟雾探测器", "SMOKE_DETECTOR", "电商机房天花"),
        ("EQ-ECOM-SERVER-01", "服务器温度告警", "SERVER_ENV", "电商机房机柜区"),
    ],
}


def _scalar(bind, sql: str, params: dict | None = None):
    return bind.execute(sa.text(sql), params or {}).scalar()


def _owner_id(bind, username: str):
    return _scalar(bind, "SELECT id FROM users WHERE username = :username", {"username": username})


def _upsert_room(bind, code: str, legacy_code: str, name: str, area: str, username: str, phone: str) -> int:
    owner_id = _owner_id(bind, username)
    room_id = _scalar(bind, "SELECT id FROM rooms WHERE code = :code", {"code": code})
    if room_id is None:
        room_id = _scalar(bind, "SELECT id FROM rooms WHERE code = :code", {"code": legacy_code})

    params = {
        "id": room_id,
        "code": code,
        "name": name,
        "area": area,
        "owner_id": owner_id,
        "phone": phone,
    }
    if room_id is None:
        bind.execute(
            sa.text(
                """
                INSERT INTO rooms
                    (code, name, area, owner_id, phone, status, remark, created_at, updated_at)
                VALUES
                    (:code, :name, :area, :owner_id, :phone, 1, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            params,
        )
        room_id = _scalar(bind, "SELECT id FROM rooms WHERE code = :code", {"code": code})
    else:
        bind.execute(
            sa.text(
                """
                UPDATE rooms
                SET code = :code,
                    name = :name,
                    area = :area,
                    owner_id = :owner_id,
                    phone = :phone,
                    status = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            params,
        )
    return int(room_id)


def _upsert_check_item(
    bind,
    equipment_type: str,
    item_code: str,
    item_name: str,
    input_type: str,
    standard_value: str | None,
    unit: str | None,
    sort_order: int,
) -> None:
    row_id = _scalar(
        bind,
        """
        SELECT id FROM inspection_check_items
        WHERE equipment_type = :equipment_type AND item_code = :item_code
        """,
        {"equipment_type": equipment_type, "item_code": item_code},
    )
    params = {
        "id": row_id,
        "equipment_type": equipment_type,
        "item_code": item_code,
        "item_name": item_name,
        "input_type": input_type,
        "standard_value": standard_value,
        "unit": unit,
        "sort_order": sort_order,
    }
    if row_id is None:
        bind.execute(
            sa.text(
                """
                INSERT INTO inspection_check_items
                    (equipment_type, item_code, item_name, input_type, standard_value,
                     unit, required, sort_order, status, created_at, updated_at)
                VALUES
                    (:equipment_type, :item_code, :item_name, :input_type, :standard_value,
                     :unit, 1, :sort_order, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            params,
        )
    else:
        bind.execute(
            sa.text(
                """
                UPDATE inspection_check_items
                SET item_name = :item_name,
                    input_type = :input_type,
                    standard_value = :standard_value,
                    unit = :unit,
                    required = 1,
                    sort_order = :sort_order,
                    status = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            params,
        )


def _upsert_equipment(bind, room_id: int, code: str, name: str, equipment_type: str, location: str) -> None:
    eq_id = _scalar(bind, "SELECT id FROM equipment WHERE equipment_code = :code", {"code": code})
    params = {
        "id": eq_id,
        "equipment_code": code,
        "equipment_name": name,
        "equipment_type": equipment_type,
        "room_id": room_id,
        "location": location,
    }
    if eq_id is None:
        bind.execute(
            sa.text(
                """
                INSERT INTO equipment
                    (equipment_code, equipment_name, equipment_type, room_id, location,
                     status, remark, created_at, updated_at)
                VALUES
                    (:equipment_code, :equipment_name, :equipment_type, :room_id, :location,
                     1, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            params,
        )
    else:
        bind.execute(
            sa.text(
                """
                UPDATE equipment
                SET equipment_name = :equipment_name,
                    equipment_type = :equipment_type,
                    room_id = :room_id,
                    location = :location,
                    status = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            params,
        )


def upgrade() -> None:
    bind = op.get_bind()

    room_ids: dict[str, int] = {}
    for code, legacy_code, name, area, username, phone in ROOMS:
        room_ids[code] = _upsert_room(bind, code, legacy_code, name, area, username, phone)

    bind.execute(
        sa.text(
            """
            UPDATE rooms
            SET status = 0, updated_at = CURRENT_TIMESTAMP
            WHERE code IN :legacy_codes
            """
        ).bindparams(sa.bindparam("legacy_codes", expanding=True)),
        {"legacy_codes": LEGACY_ROOM_CODES},
    )

    bind.execute(
        sa.text(
            """
            UPDATE inspection_check_items
            SET status = 0, updated_at = CURRENT_TIMESTAMP
            WHERE equipment_type IN :types
            """
        ).bindparams(sa.bindparam("types", expanding=True)),
        {"types": CURRENT_TYPES + ["POWER_CABINET", "FIRE_CONTROL", "NETWORK", "CABINET", "SENSOR"]},
    )
    for equipment_type, items in CHECK_ITEM_TEMPLATES.items():
        for item in items:
            _upsert_check_item(bind, equipment_type, *item)

    new_equipment_codes = [item[0] for plan in EQUIPMENT_PLAN.values() for item in plan]
    active_room_ids = list(room_ids.values())
    bind.execute(
        sa.text(
            """
            UPDATE equipment
            SET status = 0, updated_at = CURRENT_TIMESTAMP
            WHERE room_id IN :room_ids AND equipment_code NOT IN :equipment_codes
            """
        ).bindparams(
            sa.bindparam("room_ids", expanding=True),
            sa.bindparam("equipment_codes", expanding=True),
        ),
        {"room_ids": active_room_ids, "equipment_codes": new_equipment_codes},
    )

    for room_code, plan in EQUIPMENT_PLAN.items():
        for code, name, equipment_type, location in plan:
            _upsert_equipment(bind, room_ids[room_code], code, name, equipment_type, location)


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE equipment
            SET status = 0, updated_at = CURRENT_TIMESTAMP
            WHERE equipment_code IN :equipment_codes
            """
        ).bindparams(sa.bindparam("equipment_codes", expanding=True)),
        {"equipment_codes": [item[0] for plan in EQUIPMENT_PLAN.values() for item in plan]},
    )
    bind.execute(
        sa.text(
            """
            UPDATE rooms
            SET status = 0, updated_at = CURRENT_TIMESTAMP
            WHERE code IN ('JF-OFFICE', 'JF-ECOM')
            """
        )
    )
