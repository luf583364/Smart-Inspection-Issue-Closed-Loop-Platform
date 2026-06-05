from fastapi import APIRouter

from app.api.v1 import (
    auth,
    dashboard,
    equipment,
    inspection_qr,
    inspection_records,
    mobile_inspection,
    rooms,
    users,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["首页看板"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["机房管理"])
api_router.include_router(equipment.router, prefix="/equipment", tags=["设备管理"])
api_router.include_router(inspection_records.router, prefix="/inspection-records", tags=["巡检记录"])
api_router.include_router(inspection_qr.router, prefix="/inspection", tags=["巡检入口二维码"])
api_router.include_router(mobile_inspection.router, prefix="/mobile/inspection", tags=["移动端巡检"])
