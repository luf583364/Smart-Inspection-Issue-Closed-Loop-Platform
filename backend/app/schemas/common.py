from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Pagination(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=200)


class PageResult(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int


class IdResp(BaseModel):
    id: int
