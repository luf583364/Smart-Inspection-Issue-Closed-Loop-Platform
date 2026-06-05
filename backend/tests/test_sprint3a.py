from pathlib import Path
from datetime import timedelta

from app.db.session import SessionLocal
from app.models.attachment import Attachment
from app.models.equipment import Equipment
from app.models.inspection_record import InspectionRecord
from app.models.operation_log import OperationLog
from app.utils.enums import AttachmentCategory


def api_data(resp):
    body = resp.json()
    assert body["code"] == 0, body
    return body["data"]


def auth_headers(client, username="admin", password="123456"):
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    data = api_data(resp)
    return {"Authorization": f"Bearer {data['token']}"}


def items_for_state(state, abnormal_count=0):
    out = []
    for idx, item in enumerate(state["items"]):
        abnormal = idx < abnormal_count
        if item["input_type"] == "boolean":
            value = "abnormal" if abnormal else "normal"
        elif item["input_type"] == "number":
            value = "35" if abnormal else "23"
        else:
            value = "abnormal" if abnormal else ""
        out.append({
            "check_item_id": item["check_item_id"],
            "value": value,
            "is_abnormal": abnormal,
            "remark": "abnormal in test" if abnormal else None,
        })
    return out


def save_equipment(client, headers, record_id, equipment_id, abnormal_count=0):
    state = api_data(
        client.get(
            f"/api/mobile/inspection/records/{record_id}/equipment/{equipment_id}",
            headers=headers,
        )
    )
    result = "abnormal" if abnormal_count else "normal"
    return api_data(
        client.put(
            f"/api/mobile/inspection/records/{record_id}/equipment/{equipment_id}",
            headers=headers,
            json={
                "result": result,
                "issue_description": "test abnormal" if abnormal_count else None,
                "items": items_for_state(state, abnormal_count),
            },
        )
    )


def png_bytes():
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
        b"\x90wS\xde"
    )


def test_login_success_and_failure(client):
    ok = client.post("/api/auth/login", json={"username": "admin", "password": "123456"})
    assert ok.status_code == 200
    assert ok.json()["code"] == 0

    bad = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert bad.status_code == 401
    assert bad.json()["code"] == 1001


def test_start_save_next_navigation_and_all_normal_submit(client):
    headers = auth_headers(client, "inspector01")
    started = api_data(
        client.post(
            "/api/mobile/inspection/rooms/JF-OFFICE/start",
            headers=headers,
            json={"source": "manual"},
        )
    )
    assert started["equipment_list"]
    assert started["next_pending_equipment_id"] == started["equipment_list"][0]["id"]

    record_id = started["record_id"]
    equipment = started["equipment_list"]
    first_save = save_equipment(client, headers, record_id, equipment[0]["id"])
    assert first_save["completed_count"] == 1
    assert first_save["next_equipment_id"] == equipment[1]["id"]
    assert first_save["all_completed"] is False

    for eq in equipment[1:]:
        save_equipment(client, headers, record_id, eq["id"])

    final_state = api_data(
        client.get(
            f"/api/mobile/inspection/records/{record_id}/equipment/{equipment[-1]['id']}",
            headers=headers,
        )
    )
    assert final_state["all_completed"] is True
    assert final_state["next_pending_equipment_id"] is None

    submitted = api_data(
        client.post(f"/api/mobile/inspection/records/{record_id}/submit", headers=headers, json={})
    )
    assert submitted["status"] == "completed"
    assert submitted["has_issue"] == 0


def test_submit_ignores_equipment_enabled_after_record_started(client):
    headers = auth_headers(client, "inspector01")
    started = api_data(
        client.post(
            "/api/mobile/inspection/rooms/JF-OFFICE/start",
            headers=headers,
            json={"source": "manual"},
        )
    )
    record_id = started["record_id"]
    equipment = started["equipment_list"]
    for eq in equipment:
        save_equipment(client, headers, record_id, eq["id"])

    with SessionLocal() as db:
        record = db.get(InspectionRecord, record_id)
        assert record is not None
        late_at = record.created_at + timedelta(seconds=1)
        db.add(Equipment(
            equipment_code="EQ-LATE-AC-01",
            equipment_name="临时启用空调",
            equipment_type="AIR_CONDITIONER",
            room_id=record.room_id,
            location="临时测试",
            status=1,
            created_at=late_at,
            updated_at=late_at,
        ))
        db.commit()

    submitted = api_data(
        client.post(f"/api/mobile/inspection/records/{record_id}/submit", headers=headers, json={})
    )
    assert submitted["status"] == "completed"
    assert submitted["summary"]["equipment_total"] == len(equipment)


def test_attachment_upload_delete_submit_lock_and_detail_category(client):
    headers = auth_headers(client, "inspector02")
    started = api_data(
        client.post(
            "/api/mobile/inspection/rooms/JF-ECOM/start",
            headers=headers,
            json={"source": "manual"},
        )
    )
    record_id = started["record_id"]
    equipment = started["equipment_list"]
    first_equipment_id = equipment[0]["id"]

    bad_upload = client.post(
        f"/api/mobile/inspection/records/{record_id}/equipment/{first_equipment_id}/attachments",
        headers=headers,
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )
    assert bad_upload.status_code == 400
    assert bad_upload.json()["code"] == 4102

    uploaded = api_data(
        client.post(
            f"/api/mobile/inspection/records/{record_id}/equipment/{first_equipment_id}/attachments",
            headers=headers,
            files={"file": ("scene.png", png_bytes(), "image/png")},
        )
    )
    attachment_id = uploaded["id"]
    with SessionLocal() as db:
        att = db.get(Attachment, attachment_id)
        assert att is not None
        file_path = Path(att.file_path)
        assert att.record_id == record_id
        assert att.equipment_id == first_equipment_id
        assert att.original_file_name == "scene.png"
        assert att.category == AttachmentCategory.INSPECTION_ABNORMAL.value

    deleted = api_data(
        client.delete(f"/api/mobile/inspection/attachments/{attachment_id}", headers=headers)
    )
    assert deleted["deleted"] is True
    with SessionLocal() as db:
        assert db.get(Attachment, attachment_id) is None
        assert db.query(OperationLog).filter(OperationLog.action == "attachment.delete").count() == 1
    upload_root = Path(__import__("os").environ["UPLOAD_DIR"])
    assert not (upload_root / file_path).exists()

    locked = api_data(
        client.post(
            f"/api/mobile/inspection/records/{record_id}/equipment/{first_equipment_id}/attachments",
            headers=headers,
            files={"file": ("locked.png", png_bytes(), "image/png")},
        )
    )
    locked_id = locked["id"]

    save_equipment(client, headers, record_id, first_equipment_id, abnormal_count=1)
    for eq in equipment[1:]:
        save_equipment(client, headers, record_id, eq["id"])

    submitted = api_data(
        client.post(f"/api/mobile/inspection/records/{record_id}/submit", headers=headers, json={})
    )
    assert submitted["status"] == "pending_assign"
    assert submitted["has_issue"] == 1

    denied = client.delete(f"/api/mobile/inspection/attachments/{locked_id}", headers=headers)
    assert denied.status_code == 403
    assert denied.json()["code"] == 4233

    detail = api_data(client.get(f"/api/inspection-records/{record_id}", headers=headers))
    first_detail = next(x for x in detail["equipment_results"] if x["equipment_id"] == first_equipment_id)
    assert first_detail["attachments"][0]["category"] == AttachmentCategory.INSPECTION_ABNORMAL.value


def test_qrcode_info_images_and_disabled_room(client):
    headers = auth_headers(client, "admin")
    info = api_data(client.get("/api/rooms/1/qr-info", headers=headers))
    assert "/#/mobile/inspection/rooms/JF-OFFICE/start?source=qr" in info["target_url"]
    assert "token" not in info["target_url"].lower()
    assert "123456" not in info["target_url"]
    assert info["printable"] is False
    assert info["warning"]

    svg = client.get("/api/rooms/1/qrcode?format=svg", headers=headers)
    assert svg.status_code == 200
    assert svg.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in svg.content

    png = client.get("/api/rooms/1/qrcode?format=png", headers=headers)
    assert png.status_code == 200
    assert png.headers["content-type"] == "image/png"
    assert png.content.startswith(b"\x89PNG")

    api_data(client.put("/api/rooms/1/status", headers=headers, json={"status": 0}))
    disabled = client.get("/api/rooms/1/qr-info", headers=headers)
    assert disabled.status_code == 400
    assert disabled.json()["code"] == 3003
