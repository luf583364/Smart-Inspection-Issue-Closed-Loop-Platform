from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    INSPECTOR = "inspector"
    HANDLER = "handler"
    VERIFIER = "verifier"


class CommonStatus(int, Enum):
    DISABLED = 0
    ENABLED = 1


class IssueLevel(str, Enum):
    NORMAL = "normal"
    IMPORTANT = "important"
    URGENT = "urgent"


class InspectionSource(str, Enum):
    MANUAL = "manual"
    QR = "qr"


class EquipmentType(str, Enum):
    AIR_CONDITIONER = "AIR_CONDITIONER"
    ACCESS_CONTROL = "ACCESS_CONTROL"
    VIDEO_MONITORING = "VIDEO_MONITORING"
    UPS = "UPS"
    SMOKE_DETECTOR = "SMOKE_DETECTOR"
    SERVER_ENV = "SERVER_ENV"


EQUIPMENT_TYPE_LABEL = {
    "AIR_CONDITIONER": "空调系统",
    "ACCESS_CONTROL": "门禁系统",
    "VIDEO_MONITORING": "视频监控",
    "UPS": "UPS状态",
    "SMOKE_DETECTOR": "烟雾探测器",
    "SERVER_ENV": "服务器温度告警",
    # Legacy demo equipment types kept for historical rows.
    "POWER_CABINET": "配电柜",
    "FIRE_CONTROL": "消防设备",
    "NETWORK": "网络设备",
    "CABINET": "机柜",
    "SENSOR": "传感器",
}


class CheckItemInputType(str, Enum):
    BOOLEAN = "boolean"
    NUMBER = "number"
    TEXT = "text"
    PHOTO = "photo"


class EquipmentResultStatus(str, Enum):
    NORMAL = "normal"
    ABNORMAL = "abnormal"


class RecordStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PENDING_ASSIGN = "pending_assign"
    PENDING_HANDLE = "pending_handle"
    HANDLING = "handling"
    PENDING_VERIFY = "pending_verify"
    REJECTED = "rejected"


class ProcessAction(str, Enum):
    ASSIGN = "assign"
    PROCESS = "process"
    SUBMIT_VERIFY = "submit_verify"
    VERIFY_PASS = "verify_pass"
    VERIFY_REJECT = "verify_reject"


class AttachmentTarget(str, Enum):
    RECORD = "record"
    PROCESS = "process"


class AttachmentCategory(str, Enum):
    INSPECTION_SCENE = "inspection_scene"
    INSPECTION_ABNORMAL = "inspection_abnormal"
    ISSUE_BEFORE = "issue_before"
    ISSUE_AFTER = "issue_after"
    VERIFICATION = "verification"
