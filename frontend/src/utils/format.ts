import dayjs from 'dayjs'

export const formatDateTime = (v: string | Date | null | undefined): string =>
  v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '-'

export const formatDate = (v: string | Date | null | undefined): string =>
  v ? dayjs(v).format('YYYY-MM-DD') : '-'

export const ROLE_LABEL: Record<string, string> = {
  admin: '管理员',
  inspector: '巡检员',
  handler: '处理员',
  verifier: '核实员',
}

export const STATUS_LABEL: Record<string, string> = {
  in_progress: '巡检中',
  completed: '已完成',
  pending_assign: '待转发',
  pending_handle: '待处理',
  handling: '处理中',
  pending_verify: '待核实',
  rejected: '已驳回',
}

export const LEVEL_LABEL: Record<string, string> = {
  normal: '一般',
  important: '重要',
  urgent: '紧急',
}

export const INSPECTION_TYPE_LABEL: Record<string, string> = {
  daily: '日常巡检',
  special: '专项巡检',
  temporary: '临时巡检',
}
