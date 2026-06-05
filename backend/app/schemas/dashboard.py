from datetime import datetime
from typing import List

from pydantic import BaseModel


class SummaryOut(BaseModel):
    today_inspection: int
    pending_handle: int
    pending_verify: int
    completed_total: int
    this_month_inspection: int
    room_count: int


class TrendsOut(BaseModel):
    dates: List[str]
    inspection_counts: List[int]
    issue_counts: List[int]


class IssueDistItem(BaseModel):
    status: str
    label: str
    value: int


class IssuesOut(BaseModel):
    items: List[IssueDistItem]


class RecentRecord(BaseModel):
    id: int
    record_no: str
    inspection_time: datetime
    room_name: str
    inspector_name: str
    has_issue: int
    status: str
