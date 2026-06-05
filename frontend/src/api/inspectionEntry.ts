import request, { api } from './request'

export interface InspectionQrInfo {
  target_url: string
  printable: boolean
  warning?: string | null
}

/** Fixed system inspection-entry QR (points at the mobile room picker). */
export const apiInspectionQrInfo = () =>
  api.get<InspectionQrInfo>('/api/inspection/qr-info', { _t: Date.now() })

export async function apiInspectionQrBlob(format: 'svg' | 'png'): Promise<Blob> {
  const res = await request.get('/api/inspection/qrcode', {
    params: { format, _t: Date.now() },
    responseType: 'blob',
  })
  return (res as unknown as { data: Blob }).data
}
