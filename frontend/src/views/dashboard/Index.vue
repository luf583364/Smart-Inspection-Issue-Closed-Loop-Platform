<template>
  <div class="dashboard">
    <PageHeader title="工作台" :subtitle="welcomeText" />

    <!-- KPI 卡片 -->
    <el-row :gutter="16" class="kpi-row" v-loading="loading.summary">
      <el-col :xs="12" :sm="12" :md="8" :lg="4" v-for="card in kpiCards" :key="card.key">
        <div class="kpi-card" :style="{ '--accent': card.color }">
          <div class="kpi-meta">
            <div class="kpi-label">{{ card.label }}</div>
            <div class="kpi-value">{{ summary?.[card.key] ?? '--' }}</div>
            <div class="kpi-sub">{{ card.sub }}</div>
          </div>
          <div class="kpi-icon">
            <el-icon :size="22"><component :is="card.icon" /></el-icon>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区 -->
    <el-row :gutter="16" class="charts-row">
      <el-col :xs="24" :lg="16">
        <div class="chart-card">
          <div class="chart-head">
            <div class="chart-title">最近 7 天巡检趋势</div>
            <div class="chart-sub">每日巡检总数 vs 发现问题数</div>
          </div>
          <div ref="trendsRef" class="chart" v-loading="loading.trends" />
        </div>
      </el-col>

      <el-col :xs="24" :lg="8">
        <div class="chart-card">
          <div class="chart-head">
            <div class="chart-title">问题状态分布</div>
            <div class="chart-sub">按记录当前状态聚合</div>
          </div>
          <div ref="issuesRef" class="chart" v-loading="loading.issues" />
        </div>
      </el-col>
    </el-row>

    <!-- 最近巡检 -->
    <div class="chart-card recent">
      <div class="chart-head">
        <div class="chart-title">最近巡检记录</div>
        <div class="chart-sub">最新提交的 {{ recent.length }} 条</div>
      </div>
      <el-table
        :data="recent"
        v-loading="loading.recent"
        size="default"
        stripe
        :empty-text="loading.recent ? '加载中...' : '暂无巡检数据'"
      >
        <el-table-column prop="record_no" label="记录编号" width="170" />
        <el-table-column label="巡检时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.inspection_time) }}</template>
        </el-table-column>
        <el-table-column prop="room_name" label="机房" />
        <el-table-column prop="inspector_name" label="巡检人员" width="120" />
        <el-table-column label="是否发现问题" width="130" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.has_issue" type="warning" size="small" effect="light">是</el-tag>
            <el-tag v-else type="success" size="small" effect="light">否</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="当前状态" width="120">
          <template #default="{ row }"><StatusTag :status="row.status" /></template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import * as echarts from 'echarts'
import {
  AlarmClock,
  Calendar,
  CircleCheck,
  Clock,
  OfficeBuilding,
  Tickets,
} from '@element-plus/icons-vue'
import PageHeader from '@/components/PageHeader/index.vue'
import StatusTag from '@/components/StatusTag/index.vue'
import { useUserStore } from '@/stores/user'
import { formatDateTime } from '@/utils/format'
import {
  apiDashboardIssues,
  apiDashboardRecent,
  apiDashboardSummary,
  apiDashboardTrends,
  type IssuesData,
  type RecentRecord,
  type SummaryData,
  type TrendsData,
} from '@/api/dashboard'

const userStore = useUserStore()

const summary = ref<SummaryData | null>(null)
const trends = ref<TrendsData | null>(null)
const issues = ref<IssuesData | null>(null)
const recent = ref<RecentRecord[]>([])

const loading = reactive({
  summary: false,
  trends: false,
  issues: false,
  recent: false,
})

const welcomeText = computed(() => {
  const h = new Date().getHours()
  const greet = h < 6 ? '夜深了' : h < 11 ? '早上好' : h < 14 ? '中午好' : h < 18 ? '下午好' : '晚上好'
  return `${greet}，${userStore.user?.name || ''}。这里是机房巡检与问题处理的全局概览`
})

type KpiKey = keyof SummaryData
const kpiCards: Array<{
  key: KpiKey
  label: string
  sub: string
  color: string
  icon: any
}> = [
  { key: 'today_inspection',      label: '今日巡检', sub: '今日新增', color: '#1E5EFF', icon: Calendar },
  { key: 'pending_handle',        label: '待处理',   sub: '需要尽快响应', color: '#FAAD14', icon: AlarmClock },
  { key: 'pending_verify',        label: '待核实',   sub: '等待核实结论', color: '#722ED1', icon: Clock },
  { key: 'completed_total',       label: '已完成',   sub: '累计完成', color: '#52C41A', icon: CircleCheck },
  { key: 'this_month_inspection', label: '本月巡检', sub: '本月累计', color: '#13C2C2', icon: Tickets },
  { key: 'room_count',            label: '在管机房', sub: '当前启用', color: '#0F2547', icon: OfficeBuilding },
]

/* ---------------- charts ---------------- */
const trendsRef = ref<HTMLDivElement>()
const issuesRef = ref<HTMLDivElement>()
let trendsChart: echarts.ECharts | null = null
let issuesChart: echarts.ECharts | null = null

function renderTrends() {
  if (!trendsRef.value || !trends.value) return
  trendsChart = trendsChart ?? echarts.init(trendsRef.value)
  trendsChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { right: 0, top: 0, icon: 'roundRect', itemWidth: 10, itemHeight: 10 },
    grid: { left: 36, right: 16, top: 36, bottom: 28 },
    xAxis: {
      type: 'category',
      data: trends.value.dates,
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisLabel: { color: '#9CA3AF' },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#F1F2F5' } },
      axisLabel: { color: '#9CA3AF' },
    },
    series: [
      {
        name: '巡检数',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2.5, color: '#1E5EFF' },
        itemStyle: { color: '#1E5EFF' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(30,94,255,0.30)' },
            { offset: 1, color: 'rgba(30,94,255,0.02)' },
          ]),
        },
        data: trends.value.inspection_counts,
      },
      {
        name: '问题数',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2.5, color: '#FA8C16' },
        itemStyle: { color: '#FA8C16' },
        data: trends.value.issue_counts,
      },
    ],
  })
}

const ISSUE_COLOR: Record<string, string> = {
  pending_assign: '#FA8C16',
  pending_handle: '#FAAD14',
  handling: '#1890FF',
  pending_verify: '#722ED1',
  rejected: '#F5222D',
  completed: '#52C41A',
}

function renderIssues() {
  if (!issuesRef.value || !issues.value) return
  issuesChart = issuesChart ?? echarts.init(issuesRef.value)
  const data = issues.value.items
    .filter(i => i.value > 0)
    .map(i => ({ name: i.label, value: i.value, itemStyle: { color: ISSUE_COLOR[i.status] } }))
  issuesChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, icon: 'circle', itemWidth: 8, itemHeight: 8 },
    series: [
      {
        type: 'pie',
        radius: ['52%', '74%'],
        avoidLabelOverlap: true,
        label: { show: false },
        labelLine: { show: false },
        data,
      },
    ],
  })
}

function onResize() {
  trendsChart?.resize()
  issuesChart?.resize()
}

/* ---------------- fetch ---------------- */
async function loadAll() {
  loading.summary = true
  loading.trends = true
  loading.issues = true
  loading.recent = true
  try {
    const [s, t, i, r] = await Promise.all([
      apiDashboardSummary(),
      apiDashboardTrends(7),
      apiDashboardIssues(),
      apiDashboardRecent(8),
    ])
    summary.value = s
    trends.value = t
    issues.value = i
    recent.value = r
  } finally {
    loading.summary = false
    loading.trends = false
    loading.issues = false
    loading.recent = false
  }
}

watch(trends, () => renderTrends(), { flush: 'post' })
watch(issues, () => renderIssues(), { flush: 'post' })

onMounted(() => {
  loadAll()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  trendsChart?.dispose()
  issuesChart?.dispose()
})
</script>

<style lang="scss" scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.kpi-row { margin: 0 -8px; }
.kpi-row :deep(.el-col) { padding: 8px !important; }

.kpi-card {
  --accent: #{$brand-primary};
  background: $bg-card;
  border-radius: $radius-md;
  box-shadow: $shadow-card;
  padding: 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  overflow: hidden;
  min-height: 96px;
  transition: box-shadow 0.2s, transform 0.2s;

  &::before {
    content: '';
    position: absolute;
    left: 0; top: 14px; bottom: 14px;
    width: 3px;
    border-radius: 0 2px 2px 0;
    background: var(--accent);
  }
  &:hover {
    box-shadow: $shadow-hover;
    transform: translateY(-1px);
  }

  .kpi-label {
    font-size: 13px;
    color: $text-secondary;
  }
  .kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: $text-primary;
    line-height: 1.1;
    margin: 6px 0 2px;
    font-variant-numeric: tabular-nums;
  }
  .kpi-sub {
    font-size: 11px;
    color: $text-tertiary;
  }
  .kpi-icon {
    width: 40px; height: 40px;
    border-radius: 10px;
    background: color-mix(in srgb, var(--accent) 15%, transparent);
    color: var(--accent);
    display: flex; align-items: center; justify-content: center;
  }
}

.charts-row { margin: 0 -8px; }
.charts-row :deep(.el-col) { padding: 8px !important; }

.chart-card {
  background: $bg-card;
  border-radius: $radius-md;
  box-shadow: $shadow-card;
  padding: 20px;
  display: flex;
  flex-direction: column;
}
.chart-head {
  margin-bottom: 16px;
  .chart-title {
    font-size: 15px;
    font-weight: 600;
    color: $text-primary;
  }
  .chart-sub {
    margin-top: 4px;
    font-size: 12px;
    color: $text-tertiary;
  }
}
.chart {
  width: 100%;
  height: 280px;
}
.recent {
  margin-top: 0;
}
</style>
