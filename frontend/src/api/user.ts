import { api } from './request'
import type { UserInfo } from './auth'

export interface UserListQuery {
  keyword?: string
  role?: string
  status?: number
  page?: number
  size?: number
}

export interface PageData<T> {
  items: T[]
  total: number
  page: number
  size: number
}

export const apiUserList = (params: UserListQuery) =>
  api.get<PageData<UserInfo>>('/api/users', params)

export const apiUserOptions = (role?: string) =>
  api.get<Array<{ id: number; name: string; role: string }>>('/api/users/options', { role })

export interface UserCreatePayload {
  username: string
  password: string
  name: string
  role: string
  phone?: string
  status?: number
}

export interface UserUpdatePayload {
  name?: string
  role?: string
  phone?: string
  password?: string
}

export const apiUserCreate = (payload: UserCreatePayload) =>
  api.post<UserInfo>('/api/users', payload)

export const apiUserUpdate = (id: number, payload: UserUpdatePayload) =>
  api.put<UserInfo>(`/api/users/${id}`, payload)

export const apiUserSetStatus = (id: number, status: number) =>
  api.put<UserInfo>(`/api/users/${id}/status`, { status })

export const apiUserDelete = (id: number) =>
  api.delete<{ id: number; deleted: boolean }>(`/api/users/${id}`)
