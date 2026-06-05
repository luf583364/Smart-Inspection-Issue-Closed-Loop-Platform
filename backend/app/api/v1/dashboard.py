from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services import dashboard_service
from app.utils.response import success

router = APIRouter()


@router.get("/summary", summary="首页 KPI 卡片")
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return success(dashboard_service.get_summary(db))


@router.get("/trends", summary="最近 N 天巡检趋势")
def trends(
    days: int = Query(7, ge=2, le=30),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return success(dashboard_service.get_trends(db, days=days))


@router.get("/issues", summary="问题状态分布")
def issues(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return success(dashboard_service.get_issue_distribution(db))


@router.get("/recent-records", summary="最近巡检记录")
def recent_records(
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return success(dashboard_service.get_recent_records(db, limit=limit))
