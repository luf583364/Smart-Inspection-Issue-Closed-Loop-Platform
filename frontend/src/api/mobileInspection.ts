import request, { api } from './request'
import { getToken } from '@/utils/auth'

export interface InspectorBrief {
  id: number
  name: string
  role: string
}

export interface InspectionRoomBrief {
  id: number
  code: string
  name: string
  area?: string | null
}

export interface InspectionEquipmentBrief {
  id: number
  equipment_code: string
  equipment_name: string
  equipment_type: string
  equipment_type_label: string
  location?: string | null
  result: 'normal' | 'abnormal' | null
  completed_at?: string | null
  issue_description?: string | null
  item_count: number
  abnormal_item_count: number
}

export interface InspectionProgress {
  total: number
  completed: number
  normal: number
  abnormal: number
}

export interface StartInspectionData {
  record_id: number
  record_no: string
  status: string
  source: 'manual' | 'qr'
  inspection_time: string
  room: InspectionRoomBrief
  inspector: InspectorBrief
  equipment_list: InspectionEquipmentBrief[]
  progress: InspectionProgress
  completed_count: number
  total_count: number
  remaining_count: number
  next_pending_equipment_id: number | null
  all_completed: boolean
}

/** One enabled room in the mobile picker, with whether the current account already inspected it today. */
export interface InspectableRoom {
  id: number
  code: string
  name: string
  area?: string | null
  owner_id?: number | null
  owner_name?: string | null
  status: number
  equipment_count: number
  inspected_today: boolean
}

export const apiInspectableRooms = () =>
  api.get<InspectableRoom[]>('/api/mobile/inspection/rooms')

export const apiStartRoomInspection = (roomCode: string, source: 'manual' | 'qr' = 'manual') =>
  api.post<StartInspectionData>(`/api/mobile/inspection/rooms/${encodeURIComponent(roomCode)}/start`, { source })

export interface AttachmentBrief {
  id: number
  file_name: string
  url: string
  file_size?: number
  category?: string | null
}

export interface EquipmentItemValue {
  check_item_id: number
  item_code: string
  item_name: string
  input_type: 'boolean' | 'number' | 'text' | 'photo'
  standard_value?: string | null
  unit?: string | null
  value: string | null
  is_abnormal: boolean
  remark: string | null
}

export interface EquipmentInspectionDetail {
  record_id: number
  current_record?: {
    id: number
    record_no: string
    status: string
    room_id: number
  }
  equipment: {
    id: number
    equipment_code: string
    equipment_name: string
    equipment_type: string
    equipment_type_label: string
    location?: string | null
  }
  items: EquipmentItemValue[]
  attachments: AttachmentBrief[]
  result: 'normal' | 'abnormal' | null
  issue_description: string | null
  completed_at: string | null
  equipment_list?: InspectionEquipmentBrief[]
  progress?: InspectionProgress
  completed_count?: number
  total_count?: number
  remaining_count?: number
  next_pending_equipment_id?: number | null
  all_completed?: boolean
}

export const apiGetEquipmentInspection = (recordId: number, equipmentId: number) =>
  api.get<EquipmentInspectionDetail>(`/api/mobile/inspection/records/${recordId}/equipment/${equipmentId}`)

export interface ItemResultPayload {
  check_item_id: number
  value: string | null
  is_abnormal: boolean
  remark?: string | null
}

export interface SaveEquipmentResultPayload {
  result: 'normal' | 'abnormal'
  issue_description?: string | null
  items: ItemResultPayload[]
}

export interface SaveEquipmentResultResp {
  record_id: number
  completed_count: number
  total_count: number
  remaining_count: number
  next_equipment_id: number | null
  next_pending_equipment_id: number | null
  all_completed: boolean
  progress: InspectionProgress
}

export const apiSaveEquipmentResult = (
  recordId: number,
  equipmentId: number,
  payload: SaveEquipmentResultPayload,
) =>
  api.put<SaveEquipmentResultResp>(
    `/api/mobile/inspection/records/${recordId}/equipment/${equipmentId}`,
    payload,
  )

/** Uploads an image via multipart/form-data. Returns the persisted AttachmentBrief. */
export async function apiUploadEquipmentImage(
  recordId: number,
  equipmentId: number,
  file: File,
): Promise<AttachmentBrief> {
  const fd = new FormData()
  fd.append('file', file)
  const res = await request.post(
    `/api/mobile/inspection/records/${recordId}/equipment/${equipmentId}/attachments`,
    fd,
    {
      headers: {
        Authorization: `Bearer ${getToken()}`,
        'Content-Type': 'multipart/form-data',
      },
    },
  )
  return (res as unknown as { data: AttachmentBrief }).data
}

export const apiDeleteAttachment = (attachmentId: number) =>
  api.delete<{ id: number; deleted: boolean; file_deleted: boolean }>(
    `/api/mobile/inspection/attachments/${attachmentId}`,
  )

export interface SubmitInspectionData {
  record_id: number
  record_no: string
  status: string
  has_issue: number
  submitted_at: string
  summary: {
    equipment_total: number
    normal_equipment: number
    abnormal_equipment: number
  }
  remark?: string | null
}

export const apiSubmitInspection = (recordId: number, remark?: string) =>
  api.post<SubmitInspectionData>(
    `/api/mobile/inspection/records/${recordId}/submit`,
    remark ? { remark } : {},
  )
