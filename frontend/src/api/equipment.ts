import { api } from './request'
import type { PageData } from './user'

export interface EquipmentInfo {
  id: number
  equipment_code: string
  equipment_name: string
  equipment_type: string
  equipment_type_label?: string | null
  room_id: number
  room_name?: string | null
  room_code?: string | null
  location?: string | null
  status: number
  remark?: string | null
  created_at?: string
}

export interface EquipmentListQuery {
  room_id?: number
  equipment_type?: string
  status?: number
  keyword?: string
  page?: number
  size?: number
}

export const apiEquipmentList = (params: EquipmentListQuery) =>
  api.get<PageData<EquipmentInfo>>('/api/equipment', params)

export const apiEquipmentTypes = () =>
  api.get<Array<{ code: string; label: string }>>('/api/equipment/types')

export const apiRoomEquipment = (roomId: number) =>
  api.get<{
    room: { id: number; code: string; name: string; area?: string; status?: number }
    items: EquipmentInfo[]
    total: number
  }>(`/api/rooms/${roomId}/equipment`)

export interface EquipmentCreatePayload {
  equipment_code: string
  equipment_name: string
  equipment_type: string
  room_id: number
  location?: string
  remark?: string
  status?: number
}

export interface EquipmentUpdatePayload {
  equipment_name?: string
  equipment_type?: string
  room_id?: number
  location?: string
  remark?: string
}

export const apiEquipmentCreate = (payload: EquipmentCreatePayload) =>
  api.post<EquipmentInfo>('/api/equipment', payload)

export const apiEquipmentUpdate = (id: number, payload: EquipmentUpdatePayload) =>
  api.put<EquipmentInfo>(`/api/equipment/${id}`, payload)

export const apiEquipmentSetStatus = (id: number, status: number) =>
  api.put<EquipmentInfo>(`/api/equipment/${id}/status`, { status })

export interface CheckItem {
  id: number
  equipment_type: string
  item_code: string
  item_name: string
  input_type: 'boolean' | 'number' | 'text' | 'photo'
  standard_value?: string | null
  unit?: string | null
  required: number
  sort_order: number
}

export const apiEquipmentCheckItems = (equipmentId: number) =>
  api.get<CheckItem[]>(`/api/equipment/${equipmentId}/check-items`)
