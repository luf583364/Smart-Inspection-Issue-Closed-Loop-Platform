import axios, { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import { clearToken, getToken } from '@/utils/auth'

const request = axios.create({
  // 始终用相对地址：开发走 vite 代理、生产走 nginx，都转发到后端。
  // 不要用绝对地址(如 http://localhost:8000)，否则手机访问时 localhost 指向手机自身，
  // 会报 Network Error。后端地址由 vite.config 的 proxy / 部署的 nginx 决定。
  baseURL: '/',
  timeout: 20_000,
})

request.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

interface ApiBody<T = unknown> {
  code: number
  message: string
  data: T
}

request.interceptors.response.use(
  (response: AxiosResponse<ApiBody>) => {
    const body = response.data
    if (body && typeof body.code === 'number') {
      if (body.code === 0) return body as unknown as AxiosResponse
      ElMessage.error(body.message || '请求失败')
      return Promise.reject(body)
    }
    return response
  },
  (error: AxiosError<ApiBody>) => {
    const status = error.response?.status
    const msg = error.response?.data?.message || error.message || '网络异常'
    if (status === 401) {
      clearToken()
      ElMessage.error('登录已失效，请重新登录')
      if (location.hash && !location.hash.includes('/login')) {
        location.hash = '#/login'
      }
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  },
)

export const http = {
  get<T = any>(url: string, params?: Record<string, any>): Promise<T> {
    return request.get(url, { params }) as unknown as Promise<T>
  },
  post<T = any>(url: string, data?: any): Promise<T> {
    return request.post(url, data) as unknown as Promise<T>
  },
  put<T = any>(url: string, data?: any): Promise<T> {
    return request.put(url, data) as unknown as Promise<T>
  },
  delete<T = any>(url: string, params?: Record<string, any>): Promise<T> {
    return request.delete(url, { params }) as unknown as Promise<T>
  },
}

// 兼容直接拿 data 的便捷方法
export const api = {
  async get<T = any>(url: string, params?: Record<string, any>): Promise<T> {
    const res = await request.get(url, { params })
    return (res as unknown as ApiBody<T>).data
  },
  async post<T = any>(url: string, data?: any): Promise<T> {
    const res = await request.post(url, data)
    return (res as unknown as ApiBody<T>).data
  },
  async put<T = any>(url: string, data?: any): Promise<T> {
    const res = await request.put(url, data)
    return (res as unknown as ApiBody<T>).data
  },
  async delete<T = any>(url: string, params?: Record<string, any>): Promise<T> {
    const res = await request.delete(url, { params })
    return (res as unknown as ApiBody<T>).data
  },
}

export default request
