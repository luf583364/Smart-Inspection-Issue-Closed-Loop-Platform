<template>
  <div class="record-list">
    <PageHeader title="巡检记录" subtitle="查询历史巡检的提交结果和异常情况" />

    <div class="page-card">
      <div class="toolbar">
        <el-form :inline="true" class="filter-form">
          <el-form-item>
            <el-select v-model="query.room_id" placeholder="机房" clearable filterable style="width: 180px">
              <el-option
                v-for="r in roomOptions"
                :key="r.id"
                :label="`${r.code} · ${r.name}`"
                :value="r.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-select v-model="query.inspector_id" placeholder="巡检人员" clearable filterable style="width: 160px">
              <el-option
                v-for="u in inspectorOptions"
                :key="u.id"
                :label="u.name"
                :value="u.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-select v-model="query.status" placeholder="状态" clearable style="width: 140px">
              <el-option v-for="s in STATUS_OPTIONS" :key="s.value" :label="s.label" :value="s.value" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-select v-model="query.has_issue" placeholder="是否有问题" clearable style="width: 140px">
              <el-option label="有异常" :value="1" />
              <el-option label="全部正常" :value="0" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="width: 240px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="onSearch">查询</el-button>
            <el-button :icon="Refresh" @click="onReset">重置</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="record_no" label="记录编号" width="170" />
        <el-table-column label="巡检时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.inspection_time) }}</template>
        </el-table-column>
        <el-table-column prop="room_name" label="机房" min-width="140" />
        <el-table-column prop="inspector_name" label="巡检人员" width="120" />
        <el-table-column label="来源" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.source === 'qr' ? 'success' : 'info'" effect="light">
              {{ row.source === 'qr' ? '扫码' : '手动' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="设备进度" width="130">
          <template #default="{ row }">
            <span>{{ row.equipment_total }}</span>
            <span v-if="row.abnormal_equipment > 0" class="warn">（异常 {{ row.abnormal_equipment }}）</span>
          </template>
        </el-table-column>
        <el-table-column label="是否发现问题" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.has_issue" type="warning" size="small" effect="light">是</el-tag>
            <el-tag v-else type="success" size="small" effect="light">否</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }"><StatusTag :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="提交时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.submitted_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="180">
          <template #default="scope">
            <el-button type="primary" link @click="goDetail(scope.row.id)">详情</el-button>
            <el-button type="primary" link :icon="View" @click="onViewReport(scope.row as RecordListItem)">报告</el-button>
            <el-button type="primary" link :icon="Download" @click="onDownloadReport(scope.row as RecordListItem)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.size"
          :page-sizes="[10, 20, 50]"
          :total="total"
          background
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchList"
          @current-change="fetchList"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Download, Refresh, Search, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/PageHeader/index.vue'
import StatusTag from '@/components/StatusTag/index.vue'
import { formatDateTime } from '@/utils/format'
import { apiRoomOptions } from '@/api/room'
import { apiUserOptions } from '@/api/user'
import {
  apiInspectionRecordList,
  apiInspectionReportBlob,
  type RecordListItem,
} from '@/api/inspectionRecord'

const router = useRouter()

const STATUS_OPTIONS = [
  { value: 'completed', label: '已完成' },
  { value: 'pending_assign', label: '待转发' },
  { value: 'pending_handle', label: '待处理' },
  { value: 'handling', label: '处理中' },
  { value: 'pending_verify', label: '待核实' },
  { value: 'rejected', label: '已驳回' },
  { value: 'in_progress', label: '巡检中' },
]

interface Query {
  room_id: number | null
  inspector_id: number | null
  status: string
  has_issue: number | null
  page: number
  size: number
}
const query = reactive<Query>({
  room_id: null,
  inspector_id: null,
  status: '',
  has_issue: null,
  page: 1,
  size: 20,
})
const dateRange = ref<[string, string] | null>(null)

const list = ref<RecordListItem[]>([])
const total = ref(0)
const loading = ref(false)

const roomOptions = ref<Array<{ id: number; code: string; name: string }>>([])
const inspectorOptions = ref<Array<{ id: number; name: string; role: string }>>([])

async function fetchList() {
  loading.value = true
  try {
    const data = await apiInspectionRecordList({
      room_id: query.room_id ?? undefined,
      inspector_id: query.inspector_id ?? undefined,
      status: query.status || undefined,
      has_issue: query.has_issue ?? undefined,
      start: dateRange.value?.[0] ? `${dateRange.value[0]}T00:00:00` : undefined,
      end: dateRange.value?.[1] ? `${dateRange.value[1]}T23:59:59` : undefined,
      page: query.page,
      size: query.size,
    })
    list.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function onSearch() { query.page = 1; fetchList() }
function onReset() {
  query.room_id = null
  query.inspector_id = null
  query.status = ''
  query.has_issue = null
  dateRange.value = null
  query.page = 1
  fetchList()
}

function goDetail(id: number) { router.push(`/inspection/records/${id}`) }

async function onViewReport(row: RecordListItem) {
  try {
    const blob = await apiInspectionReportBlob(row.id, false)
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
    setTimeout(() => URL.revokeObjectURL(url), 60_000)
  } catch {
    ElMessage.error('报告生成失败')
  }
}

async function onDownloadReport(row: RecordListItem) {
  try {
    const blob = await apiInspectionReportBlob(row.id, true)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${row.record_no}.html`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('报告下载失败')
  }
}

onMounted(async () => {
  ;[roomOptions.value, inspectorOptions.value] = await Promise.all([
    apiRoomOptions(),
    apiUserOptions('inspector'),
  ])
  fetchList()
})
</script>

<style lang="scss" scoped>
.record-list { display: flex; flex-direction: column; }
.filter-form { flex: 1; :deep(.el-form-item) { margin-bottom: 0; } }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
.warn { color: $status-rejected; margin-left: 4px; font-size: 12px; }
</style>
