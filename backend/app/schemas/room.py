from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoomBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    area: str | None = None
    owner_id: int | None = None
    phone: str | None = None
    status: int = 1
    remark: str | None = None


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: str | None = None
    area: str | None = None
    owner_id: int | None = None
    phone: str | None = None
    remark: str | None = None


class RoomStatusUpdate(BaseModel):
    status: int = Field(..., ge=0, le=1)


class RoomOut(BaseModel):
    id: int
    code: str
    name: str
    area: str | None = None
    owner_id: int | None = None
    owner_name: str | None = None
    phone: str | None = None
    status: int
    remark: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoomOption(BaseModel):
    id: int
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class RoomQrInfo(BaseModel):
    room_id: int
    room_code: str
    room_name: str
    target_url: str
    printable: bool
    warning: str | None = None
