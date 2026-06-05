import request, { api } from './request'
import { getToken } from '@/utils/auth'

/** 问题闭环：转发 / 处理 / 核实 + 整改照片上传 */

export interface AssignPayload {
  assignee_id: number
  content?: string
  expected_finish_time?: string
}

export const apiIssueAssign = (recordId: number, payload: AssignPayload) =>
  api.post(`/api/inspection-records/${recordId}/assign`, payload)

export const apiIssueProcess = (recordId: number, content: string) =>
  api.post(`/api/inspection-records/${recordId}/process`, { content })

export const apiIssueVerify = (recordId: number, passed: boolean, content?: string) =>
  api.post(`/api/inspection-records/${recordId}/verify`, { passed, content })

/** 上传整改 / 核实照片（multipart） */
export async function apiUploadIssueImage(
  recordId: number,
  file: File,
  category: 'issue_after' | 'verification' = 'issue_after',
): Promise<{ id: number; url: string; category: string }> {
  const fd = new FormData()
  fd.append('file', file)
  const res = await request.post(
    `/api/inspection-records/${recordId}/issue-attachments`,
    fd,
    {
      params: { category },
      headers: {
        Authorization: `Bearer ${getToken()}`,
        'Content-Type': 'multipart/form-data',
      },
    },
  )
  return (res as unknown as { data: { id: number; url: string; category: string } }).data
}
