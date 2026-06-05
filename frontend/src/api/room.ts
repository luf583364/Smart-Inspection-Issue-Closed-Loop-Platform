import request, { api } from './request'
import type { PageData } from './user'

export interface RoomInfo {
  id: number
  code: string
  name: string
  area?: string | null
  owner_id?: number | null
  owner_name?: string | null
  phone?: string | null
  status: number
  remark?: string | null
  created_at?: string
}

export interface RoomListQuery {
  keyword?: string
  status?: number
  page?: number
  size?: number
}

export const apiRoomList = (params: RoomListQuery) =>
  api.get<PageData<RoomInfo>>('/api/rooms', params)

export const apiRoomOptions = () =>
  api.get<Array<{ id: number; code: string; name: string }>>('/api/rooms/options')

export const apiRoomDetail = (id: number) =>
  api.get<RoomInfo>(`/api/rooms/${id}`)

export interface RoomCreatePayload {
  code: string
  name: string
  area?: string
  owner_id?: number
  phone?: string
  status?: number
  remark?: string
}

export const apiRoomCreate = (payload: RoomCreatePayload) =>
  api.post<RoomInfo>('/api/rooms', payload)

export const apiRoomUpdate = (id: number, payload: Partial<RoomCreatePayload>) =>
  api.put<RoomInfo>(`/api/rooms/${id}`, payload)

export const apiRoomSetStatus = (id: number, status: number) =>
  api.put<RoomInfo>(`/api/rooms/${id}/status`, { status })

export const apiRoomDelete = (id: number) =>
  api.delete<{ id: number; deleted: boolean }>(`/api/rooms/${id}`)

export interface RoomQrInfo {
  room_id: number
  room_code: string
  room_name: string
  target_url: string
  printable: boolean
  warning?: string | null
}

export const apiRoomQrInfo = (id: number) =>
  api.get<RoomQrInfo>(`/api/rooms/${id}/qr-info`, { _t: Date.now() })

export async function apiRoomQrBlob(id: number, format: 'svg' | 'png'): Promise<Blob> {
  const res = await request.get(`/api/rooms/${id}/qrcode`, {
    params: { format, _t: Date.now() },
    responseType: 'blob',
  })
  return (res as unknown as { data: Blob }).data
}
