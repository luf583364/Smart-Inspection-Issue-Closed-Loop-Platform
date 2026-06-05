import request, { api } from './request'
import type { PageData } from './user'

export interface RecordListItem {
  id: number
  record_no: string
  inspection_time: string
  submitted_at?: string | null
  room_id: number
  room_name: string
  inspector_id: number
  inspector_name: string
  source: 'manual' | 'qr'
  has_issue: number
  status: string
  equipment_total: number
  abnormal_equipment: number
}

export interface RecordListQuery {
  room_id?: number
  inspector_id?: number
  status?: string
  has_issue?: number
  start?: string
  end?: string
  page?: number
  size?: number
}

export const apiInspectionRecordList = (params: RecordListQuery) =>
  api.get<PageData<RecordListItem>>('/api/inspection-records', params)

export interface ItemResultDetail {
  check_item_id: number
  item_code: string
  item_name: string
  input_type: string
  standard_value?: string | null
  unit?: string | null
  value: string | null
  is_abnormal: number
  remark: string | null
}

export interface EquipmentResultDetail {
  equipment_id: number
  equipment_code: string
  equipment_name: string
  equipment_type: string
  equipment_type_label: string
  location?: string | null
  result: 'normal' | 'abnormal' | null
  issue_description: string | null
  completed_at: string | null
  items: ItemResultDetail[]
  attachments: Array<{ id: number; file_name: string; url: string; category: string }>
}

export interface TimelineEntry {
  at: string
  action: string
  operator?: string | null
  text?: string | null
}

export interface RecordDetail {
  id: number
  record_no: string
  inspection_time: string
  submitted_at: string | null
  source: 'manual' | 'qr'
  status: string
  has_issue: number
  remark: string | null
  room: { id: number; code: string; name: string; area?: string | null }
  inspector: { id: number; name: string; role: string }
  current_assignee?: { id: number; name: string } | null
  equipment_results: EquipmentResultDetail[]
  issue_attachments?: Array<{ id: number; file_name: string; url: string; category: string }>
  timeline: TimelineEntry[]
}

export const apiInspectionRecordDetail = (id: number) =>
  api.get<RecordDetail>(`/api/inspection-records/${id}`)

/** Fetch the generated HTML report as a Blob (carries the Bearer auth header). */
export async function apiInspectionReportBlob(id: number, download = false): Promise<Blob> {
  const res = await request.get(`/api/inspection-records/${id}/report`, {
    params: { download: download ? 1 : 0 },
    responseType: 'blob',
  })
  return (res as unknown as { data: Blob }).data
}
