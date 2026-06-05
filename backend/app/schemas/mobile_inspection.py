from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class StartIn(BaseModel):
    source: str | None = Field(default="manual", pattern="^(manual|qr)$")


class AttachmentBrief(BaseModel):
    id: int
    file_name: str
    url: str
    file_size: int | None = None
    category: str | None = None


class ItemResultIn(BaseModel):
    check_item_id: int
    value: str | None = None
    is_abnormal: bool = False
    remark: str | None = None


class SaveEquipmentResultIn(BaseModel):
    result: str = Field(..., pattern="^(normal|abnormal)$")
    issue_description: str | None = None
    items: List[ItemResultIn] = Field(default_factory=list)


class CheckItemBrief(BaseModel):
    id: int
    item_code: str
    item_name: str
    input_type: str
    standard_value: str | None = None
    unit: str | None = None


class EquipmentItemValue(BaseModel):
    check_item_id: int
    item_code: str
    item_name: str
    input_type: str
    standard_value: str | None = None
    unit: str | None = None
    value: str | None = None
    is_abnormal: bool = False
    remark: str | None = None


class EquipmentBriefForInspect(BaseModel):
    id: int
    equipment_code: str
    equipment_name: str
    equipment_type: str
    equipment_type_label: str
    location: str | None = None
    result: str | None = None  # null / normal / abnormal
    completed_at: datetime | None = None
    issue_description: str | None = None
    item_count: int
    abnormal_item_count: int


class StartOut(BaseModel):
    record_id: int
    record_no: str
    status: str
    source: str
    inspection_time: datetime
    room: dict
    inspector: dict
    equipment_list: List[EquipmentBriefForInspect]
    progress: dict  # { total, completed, normal, abnormal }
    completed_count: int
    total_count: int
    remaining_count: int
    next_pending_equipment_id: int | None = None
    all_completed: bool


class EquipmentDetailOut(BaseModel):
    record_id: int
    current_record: dict | None = None
    equipment: dict
    items: List[EquipmentItemValue]
    attachments: List[AttachmentBrief]
    result: str | None = None
    issue_description: str | None = None
    completed_at: datetime | None = None
    equipment_list: List[EquipmentBriefForInspect] = Field(default_factory=list)
    progress: dict | None = None
    completed_count: int | None = None
    total_count: int | None = None
    remaining_count: int | None = None
    next_pending_equipment_id: int | None = None
    all_completed: bool | None = None


class ProgressOut(BaseModel):
    total: int
    completed: int
    normal: int
    abnormal: int


class SaveEquipmentResultOut(BaseModel):
    record_id: int
    completed_count: int
    total_count: int
    remaining_count: int
    next_equipment_id: int | None = None
    next_pending_equipment_id: int | None = None
    all_completed: bool
    progress: ProgressOut


class SubmitOut(BaseModel):
    record_id: int
    record_no: str
    status: str
    has_issue: int
    submitted_at: datetime
    summary: dict  # equipment counts
