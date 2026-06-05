import { api } from './request'

export interface UserInfo {
  id: number
  username: string
  name: string
  role: 'admin' | 'inspector' | 'handler' | 'verifier'
  phone?: string | null
  status: number
  created_at?: string
}

export interface LoginResp {
  token: string
  user: UserInfo
}

export const apiLogin = (username: string, password: string) =>
  api.post<LoginResp>('/api/auth/login', { username, password })

export const apiMe = () => api.get<UserInfo>('/api/auth/me')
