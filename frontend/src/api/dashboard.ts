import { api } from './request'

export interface SummaryData {
  today_inspection: number
  pending_handle: number
  pending_verify: number
  completed_total: number
  this_month_inspection: number
  room_count: number
}

export interface TrendsData {
  dates: string[]
  inspection_counts: number[]
  issue_counts: number[]
}

export interface IssueDistItem {
  status: string
  label: string
  value: number
}

export interface IssuesData {
  items: IssueDistItem[]
}

export interface RecentRecord {
  id: number
  record_no: string
  inspection_time: string
  room_name: string
  inspector_name: string
  has_issue: number
  status: string
}

export const apiDashboardSummary = () =>
  api.get<SummaryData>('/api/dashboard/summary')

export const apiDashboardTrends = (days = 7) =>
  api.get<TrendsData>('/api/dashboard/trends', { days })

export const apiDashboardIssues = () =>
  api.get<IssuesData>('/api/dashboard/issues')

export const apiDashboardRecent = (limit = 8) =>
  api.get<RecentRecord[]>('/api/dashboard/recent-records', { limit })
