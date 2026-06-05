from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EquipmentBase(BaseModel):
    equipment_code: str = Field(..., min_length=1, max_length=50)
    equipment_name: str = Field(..., min_length=1, max_length=100)
    equipment_type: str = Field(..., min_length=1, max_length=32)
    room_id: int
    location: str | None = None
    status: int = 1
    remark: str | None = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    equipment_name: str | None = None
    equipment_type: str | None = None
    room_id: int | None = None
    location: str | None = None
    remark: str | None = None


class EquipmentStatusUpdate(BaseModel):
    status: int = Field(..., ge=0, le=1)


class EquipmentOut(BaseModel):
    id: int
    equipment_code: str
    equipment_name: str
    equipment_type: str
    equipment_type_label: str | None = None
    room_id: int
    room_name: str | None = None
    room_code: str | None = None
    location: str | None = None
    status: int
    remark: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
