<template>
  <div class="issue-list">
    <PageHeader :title="title" :subtitle="subtitle" />

    <div class="page-card">
      <el-table :data="list" v-loading="loading" stripe :empty-text="loading ? '加载中...' : '暂无数据'">
        <el-table-column prop="record_no" label="记录编号" width="170" />
        <el-table-column prop="room_name" label="机房" min-width="140" />
        <el-table-column prop="inspector_name" label="巡检人员" width="110" />
        <el-table-column label="设备(异常)" width="120">
          <template #default="{ row }">
            <span>{{ row.equipment_total }}</span>
            <span v-if="row.abnormal_equipment > 0" class="warn">（异常 {{ row.abnormal_equipment }}）</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }"><StatusTag :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="提交时间" width="160">
          <template #default="{ row }">{{ formatDateTime(row.submitted_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="120">
          <template #default="{ row }">
            <el-button type="primary" link @click="goDetail(row.id)">{{ actionText }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
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
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '@/components/PageHeader/index.vue'
import StatusTag from '@/components/StatusTag/index.vue'
import { formatDateTime } from '@/utils/format'
import { apiInspectionRecordList, type RecordListItem } from '@/api/inspectionRecord'

const route = useRoute()
const router = useRouter()

const STATUS_META: Record<string, { title: string; sub: string; action: string }> = {
  pending_assign: { title: '待转发', sub: '巡检发现异常、等待转发给处理员的问题', action: '转发处理' },
  pending_handle: { title: '待处理', sub: '已转发、等待处理员处理的问题', action: '去处理' },
  pending_verify: { title: '待核实', sub: '处理员已提交、等待核实的问题', action: '去核实' },
  completed: { title: '已完成', sub: '已闭环归档的问题', action: '查看详情' },
  rejected: { title: '已驳回', sub: '核实驳回的问题', action: '查看详情' },
}

const status = computed(() => String(route.params.status || 'pending_handle'))
const meta = computed(() => STATUS_META[status.value] || STATUS_META.pending_handle)
const title = computed(() => `问题闭环 · ${meta.value.title}`)
const subtitle = computed(() => meta.value.sub)
const actionText = computed(() => meta.value.action)

const list = ref<RecordListItem[]>([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = ref(20)

async function fetchList() {
  loading.value = true
  try {
    const data = await apiInspectionRecordList({
      status: status.value,
      has_issue: status.value === 'completed' ? 1 : undefined,
      page: page.value,
      size: size.value,
    })
    list.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function goDetail(id: number) {
  router.push(`/inspection/records/${id}`)
}

onMounted(fetchList)
</script>

<style lang="scss" scoped>
.issue-list { display: flex; flex-direction: column; }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
.warn { color: $status-rejected; font-size: 12px; margin-left: 4px; }
</style>
