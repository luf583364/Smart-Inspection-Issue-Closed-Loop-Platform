from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=1, max_length=50)
    role: str = Field(..., pattern="^(admin|inspector|handler|verifier)$")
    phone: str | None = None
    status: int = 1


class UserCreate(UserBase):
    password: str = Field(..., min_length=4, max_length=100)


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = Field(None, pattern="^(admin|inspector|handler|verifier)$")
    phone: str | None = None
    password: str | None = Field(None, min_length=4, max_length=100)


class UserStatusUpdate(BaseModel):
    status: int = Field(..., ge=0, le=1)


class UserOut(BaseModel):
    id: int
    username: str
    name: str
    role: str
    phone: str | None = None
    status: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserOption(BaseModel):
    id: int
    name: str
    role: str

    model_config = ConfigDict(from_attributes=True)
