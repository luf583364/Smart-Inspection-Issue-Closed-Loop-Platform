from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class RecordListItem(BaseModel):
    id: int
    record_no: str
    inspection_time: datetime
    submitted_at: datetime | None = None
    room_id: int
    room_name: str
    inspector_id: int
    inspector_name: str
    source: str
    has_issue: int
    status: str
    equipment_total: int
    abnormal_equipment: int


class ItemResultDetail(BaseModel):
    check_item_id: int
    item_code: str
    item_name: str
    input_type: str
    standard_value: str | None = None
    unit: str | None = None
    value: str | None = None
    is_abnormal: int
    remark: str | None = None


class EquipmentResultDetail(BaseModel):
    equipment_id: int
    equipment_code: str
    equipment_name: str
    equipment_type: str
    equipment_type_label: str
    location: str | None = None
    result: str | None = None
    issue_description: str | None = None
    completed_at: datetime | None = None
    items: List[ItemResultDetail] = []
    attachments: List[dict] = []  # [{id, file_name, url, category}]


class TimelineEntry(BaseModel):
    at: datetime
    action: str
    operator: str | None = None
    text: str | None = None


class RecordDetail(BaseModel):
    id: int
    record_no: str
    inspection_time: datetime
    submitted_at: datetime | None = None
    source: str
    status: str
    has_issue: int
    remark: str | None = None

    room: dict  # {id, code, name, area}
    inspector: dict  # {id, name}

    equipment_results: List[EquipmentResultDetail] = []
    timeline: List[TimelineEntry] = []
