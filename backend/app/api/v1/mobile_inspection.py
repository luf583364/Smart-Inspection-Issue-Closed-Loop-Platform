from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.mobile_inspection import SaveEquipmentResultIn, StartIn
from app.services import mobile_inspection_service
from app.utils.file_storage import save_image
from app.utils.response import success

router = APIRouter()


@router.post("/rooms/{room_code}/start", summary="开始指定机房的巡检（移动端入口）")
def start_inspection(
    room_code: str,
    payload: StartIn | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    source = (payload.source if payload else None) or "manual"
    data = mobile_inspection_service.start_room_inspection(
        db, room_code=room_code, user=user, source=source
    )
    return success(data)


@router.get("/records/{record_id}/equipment/{equipment_id}", summary="单设备巡检状态/检查项")
def equipment_state(
    record_id: int,
    equipment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = mobile_inspection_service.get_equipment_inspection_state(
        db, record_id=record_id, equipment_id=equipment_id, user=user
    )
    return success(data)


@router.put("/records/{record_id}/equipment/{equipment_id}", summary="保存单台设备巡检结果")
def save_equipment_result(
    record_id: int,
    equipment_id: int,
    payload: SaveEquipmentResultIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = mobile_inspection_service.save_equipment_result(
        db,
        record_id=record_id,
        equipment_id=equipment_id,
        user=user,
        result=payload.result,
        issue_description=payload.issue_description,
        items=[i.model_dump() for i in payload.items],
    )
    return success(data)


@router.post("/records/{record_id}/equipment/{equipment_id}/attachments", summary="上传设备巡检照片")
async def upload_equipment_image(
    record_id: int,
    equipment_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    saved = await save_image(file)
    att = mobile_inspection_service.attach_image(
        db, record_id=record_id, equipment_id=equipment_id, user=user, saved=saved
    )
    return success(att)


@router.delete("/attachments/{attachment_id}", summary="删除巡检附件")
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = mobile_inspection_service.delete_attachment(db, attachment_id=attachment_id, user=user)
    return success(data)


class SubmitIn(BaseModel):
    remark: str | None = None


@router.post("/records/{record_id}/submit", summary="提交整次机房巡检")
def submit(
    record_id: int,
    payload: SubmitIn | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = mobile_inspection_service.submit_record(db, record_id=record_id, user=user)
    if payload and payload.remark:
        # remark is mostly cosmetic for now; persist it for transparency
        from app.models.inspection_record import InspectionRecord  # avoid circular at import time
        rec = db.get(InspectionRecord, record_id)
        if rec:
            rec.remark = payload.remark
            db.commit()
            data["remark"] = payload.remark
    return success(data)
