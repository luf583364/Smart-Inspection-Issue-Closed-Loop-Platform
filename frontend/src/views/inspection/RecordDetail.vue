<template>
  <div class="record-detail" v-loading="loading">
    <PageHeader :title="pageTitle" :subtitle="pageSub">
      <template #actions>
        <el-button :icon="ArrowLeft" @click="$router.push('/inspection/records')">返回列表</el-button>
        <el-button :icon="View" :loading="reportLoading.view" @click="onViewReport">查看报告</el-button>
        <el-button type="primary" :icon="Download" :loading="reportLoading.download" @click="onDownloadReport">
          下载报告
        </el-button>
      </template>
    </PageHeader>

    <div class="page-card meta-card" v-if="data">
      <div class="meta-grid">
        <div class="kv"><span class="k">记录编号</span><span class="v">{{ data.record_no }}</span></div>
        <div class="kv"><span class="k">机房</span><span class="v">{{ data.room.name }}<span class="hint">{{ data.room.code }}</span></span></div>
        <div class="kv"><span class="k">巡检人员</span><span class="v">{{ data.inspector.name }}</span></div>
        <div class="kv"><span class="k">来源</span><span class="v">
          <el-tag size="small" :type="data.source === 'qr' ? 'success' : 'info'" effect="light">
            {{ data.source === 'qr' ? '扫码' : '手动' }}
          </el-tag>
        </span></div>
        <div class="kv"><span class="k">巡检时间</span><span class="v">{{ formatDateTime(data.inspection_time) }}</span></div>
        <div class="kv"><span class="k">提交时间</span><span class="v">{{ formatDateTime(data.submitted_at) }}</span></div>
        <div class="kv"><span class="k">当前状态</span><span class="v"><StatusTag :status="data.status" /></span></div>
        <div class="kv"><span class="k">是否发现问题</span><span class="v">
          <el-tag v-if="data.has_issue" type="warning" size="small" effect="light">是</el-tag>
          <el-tag v-else type="success" size="small" effect="light">否</el-tag>
        </span></div>
        <div class="kv" v-if="data.current_assignee"><span class="k">当前处理人</span><span class="v">{{ data.current_assignee.name }}</span></div>
      </div>
      <div v-if="data.remark" class="remark">备注：{{ data.remark }}</div>
    </div>

    <div class="page-card" v-if="data">
      <div class="section-title">设备巡检结果（共 {{ data.equipment_results.length }} 台）</div>

      <div
        v-for="eq in data.equipment_results"
        :key="eq.equipment_id"
        class="eq-block"
        :class="{ abn: eq.result === 'abnormal' }"
      >
        <div class="eq-head">
          <div class="left">
            <span class="badge" :class="eq.result === 'abnormal' ? 'bad' : 'ok'">
              {{ eq.result === 'abnormal' ? '异常' : '正常' }}
            </span>
            <span class="name">{{ eq.equipment_name }}</span>
            <el-tag size="small" effect="light">{{ eq.equipment_type_label }}</el-tag>
            <span v-if="eq.location" class="loc">{{ eq.location }}</span>
          </div>
          <div class="right">
            <span>完成于 {{ formatDateTime(eq.completed_at) }}</span>
          </div>
        </div>

        <div v-if="eq.issue_description" class="issue">
          异常说明：{{ eq.issue_description }}
        </div>

        <el-table :data="eq.items" size="small" style="margin-top: 8px" border>
          <el-table-column prop="item_name" label="检查项" min-width="160" />
          <el-table-column label="标准值" width="120">
            <template #default="{ row }">
              {{ row.standard_value || '-' }}<span v-if="row.unit"> {{ row.unit }}</span>
            </template>
          </el-table-column>
          <el-table-column label="实测值" width="120">
            <template #default="{ row }">
              <span v-if="row.input_type === 'boolean'">
                {{ row.value === 'abnormal' ? '异常' : '正常' }}
              </span>
              <span v-else>{{ row.value || '-' }}</span>
              <span v-if="row.input_type === 'number' && row.unit" class="unit"> {{ row.unit }}</span>
            </template>
          </el-table-column>
          <el-table-column label="结果" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.is_abnormal" type="danger" size="small" effect="light">异常</el-tag>
              <el-tag v-else type="success" size="small" effect="light">正常</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" show-overflow-tooltip />
        </el-table>

        <div v-if="eq.attachments.length" class="atts">
          <div class="att-title">现场照片（{{ eq.attachments.length }}）</div>
          <div class="att-grid">
            <el-image
              v-for="att in eq.attachments"
              :key="att.id"
              :src="att.url"
              :preview-src-list="eq.attachments.map(a => a.url)"
              :initial-index="eq.attachments.indexOf(att)"
              fit="cover"
              class="att-thumb"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 问题闭环处理 -->
    <div class="page-card" v-if="data && data.has_issue">
      <div class="section-title">问题处理</div>

      <div class="issue-status-row">
        <StatusTag :status="data.status" />
        <span v-if="data.current_assignee" class="assignee">当前处理人：{{ data.current_assignee.name }}</span>
        <span v-if="data.status === 'completed'" class="done">问题已闭环</span>
      </div>

      <!-- 整改 / 核实照片 -->
      <div v-if="data.issue_attachments && data.issue_attachments.length" class="atts">
        <div class="att-title">整改 / 核实照片（{{ data.issue_attachments.length }}）</div>
        <div class="att-grid">
          <el-image
            v-for="att in data.issue_attachments"
            :key="att.id"
            :src="att.url"
            :preview-src-list="data.issue_attachments.map(a => a.url)"
            :initial-index="data.issue_attachments.indexOf(att)"
            fit="cover"
            class="att-thumb"
          />
        </div>
      </div>

      <!-- 操作按钮（按状态 + 角色） -->
      <div class="issue-actions">
        <el-button v-if="canAssign" type="primary" :icon="Promotion" @click="openAssign">转发给处理员</el-button>
        <el-button v-if="canHandle" type="primary" :icon="Tools" @click="openProcess">提交处理结果</el-button>
        <template v-if="canVerify">
          <el-button type="success" :icon="CircleCheck" @click="onVerifyPass">核实通过</el-button>
          <el-button type="danger" :icon="CircleClose" @click="onVerifyReject">驳回</el-button>
        </template>
        <span v-if="!canAssign && !canHandle && !canVerify && data.status !== 'completed'" class="muted-tip">
          当前状态由其他角色处理，你暂无可执行的操作
        </span>
      </div>
    </div>

    <div class="page-card" v-if="data">
      <div class="section-title">流程时间线</div>
      <el-timeline>
        <el-timeline-item
          v-for="(t, idx) in data.timeline"
          :key="idx"
          :timestamp="formatDateTime(t.at)"
          placement="top"
          :color="idx === data.timeline.length - 1 ? '#1E5EFF' : '#9CA3AF'"
        >
          <div class="tl-line">
            <span class="tl-action">{{ TL_LABEL[t.action] || t.action }}</span>
            <span v-if="t.operator" class="tl-op">· {{ t.operator }}</span>
          </div>
          <div v-if="t.text" class="tl-text">{{ t.text }}</div>
        </el-timeline-item>
      </el-timeline>
    </div>

    <!-- 转发对话框 -->
    <el-dialog v-model="assignVisible" title="转发给处理员" width="460px">
      <el-form label-width="84px">
        <el-form-item label="处理员" required>
          <el-select v-model="assignForm.assignee_id" placeholder="选择处理员" filterable style="width:100%">
            <el-option v-for="u in handlers" :key="u.id" :label="u.name" :value="u.id" />
          </el-select>
          <div v-if="!handlers.length" class="empty-tip">
            暂无「启用」的处理员。请到「系统管理 → 用户管理」把账号角色设为<b>处理员</b>且状态为<b>启用</b>。
          </div>
        </el-form-item>
        <el-form-item label="期望完成">
          <el-date-picker v-model="assignForm.expected_finish_time" type="datetime"
            placeholder="可选" value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="转发说明">
          <el-input v-model="assignForm.content" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitAssign">确定转发</el-button>
      </template>
    </el-dialog>

    <!-- 处理对话框 -->
    <el-dialog v-model="processVisible" title="提交处理结果" width="500px">
      <el-form label-width="84px">
        <el-form-item label="处理说明" required>
          <el-input v-model="processForm.content" type="textarea" :rows="4" placeholder="描述如何处理该问题" />
        </el-form-item>
        <el-form-item label="整改照片">
          <div class="photo-row">
            <el-image
              v-for="u in processForm.photos" :key="u" :src="u" fit="cover" class="att-thumb"
              :preview-src-list="processForm.photos"
            />
            <label class="upload-box">
              <input type="file" accept="image/*" class="hidden-input" @change="onIssuePhoto" />
              <el-icon><Plus /></el-icon>
            </label>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="processVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitProcess">提交核实</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  ArrowLeft, CircleCheck, CircleClose, Download, Plus, Promotion, Tools, View,
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader/index.vue'
import StatusTag from '@/components/StatusTag/index.vue'
import { formatDateTime } from '@/utils/format'
import { useUserStore } from '@/stores/user'
import {
  apiInspectionRecordDetail,
  apiInspectionReportBlob,
  type RecordDetail,
} from '@/api/inspectionRecord'
import { apiIssueAssign, apiIssueProcess, apiIssueVerify, apiUploadIssueImage } from '@/api/issue'
import { apiUserOptions } from '@/api/user'

const route = useRoute()
const userStore = useUserStore()
const recordId = computed(() => Number(route.params.recordId))

const loading = ref(false)
const data = ref<RecordDetail | null>(null)

const TL_LABEL: Record<string, string> = {
  created: '开始巡检',
  submitted: '提交记录',
  assign: '转发处理',
  process: '提交处理结果',
  submit_verify: '提交核实',
  verify_pass: '核实通过',
  verify_reject: '核实驳回',
}

/* ---------------- 问题闭环 ---------------- */
const role = computed(() => userStore.role)
const status = computed(() => data.value?.status ?? '')
const canAssign = computed(() => status.value === 'pending_assign' && role.value === 'admin')
const canHandle = computed(() => status.value === 'pending_handle' && ['admin', 'handler'].includes(role.value))
const canVerify = computed(() => status.value === 'pending_verify' && ['admin', 'verifier'].includes(role.value))

const submitting = ref(false)
const handlers = ref<Array<{ id: number; name: string; role: string }>>([])

const assignVisible = ref(false)
const assignForm = reactive<{ assignee_id?: number; content: string; expected_finish_time?: string }>({
  assignee_id: undefined, content: '', expected_finish_time: undefined,
})
async function openAssign() {
  assignForm.assignee_id = undefined
  assignForm.content = ''
  assignForm.expected_finish_time = undefined
  if (!handlers.value.length) {
    try { handlers.value = await apiUserOptions('handler') } catch { handlers.value = [] }
  }
  assignVisible.value = true
}
async function submitAssign() {
  if (!assignForm.assignee_id) { ElMessage.warning('请选择处理员'); return }
  submitting.value = true
  try {
    await apiIssueAssign(recordId.value, {
      assignee_id: assignForm.assignee_id,
      content: assignForm.content || undefined,
      expected_finish_time: assignForm.expected_finish_time || undefined,
    })
    ElMessage.success('已转发')
    assignVisible.value = false
    await load()
  } finally {
    submitting.value = false
  }
}

const processVisible = ref(false)
const processForm = reactive<{ content: string; photos: string[] }>({ content: '', photos: [] })
function openProcess() {
  processForm.content = ''
  processForm.photos = []
  processVisible.value = true
}
async function onIssuePhoto(e: Event) {
  const input = e.target as HTMLInputElement
  const f = input.files?.[0]
  input.value = ''
  if (!f) return
  if (f.size > 5 * 1024 * 1024) { ElMessage.error('单张照片不能超过 5MB'); return }
  try {
    const att = await apiUploadIssueImage(recordId.value, f, 'issue_after')
    processForm.photos.push(att.url)
    ElMessage.success('照片已上传')
  } catch {
    ElMessage.error('上传失败')
  }
}
async function submitProcess() {
  if (!processForm.content.trim()) { ElMessage.warning('请填写处理说明'); return }
  submitting.value = true
  try {
    await apiIssueProcess(recordId.value, processForm.content.trim())
    ElMessage.success('已提交核实')
    processVisible.value = false
    await load()
  } finally {
    submitting.value = false
  }
}

async function onVerifyPass() {
  try {
    await ElMessageBox.confirm('确认该问题已整改合格、核实通过？', '核实通过', {
      confirmButtonText: '通过', cancelButtonText: '取消', type: 'success',
    })
  } catch { return }
  await apiIssueVerify(recordId.value, true)
  ElMessage.success('已核实通过，问题闭环')
  await load()
}
async function onVerifyReject() {
  try {
    const { value } = await ElMessageBox.prompt('请填写驳回原因（将打回给处理员）', '驳回', {
      confirmButtonText: '驳回', cancelButtonText: '取消', inputType: 'textarea',
      inputValidator: (v) => (v && v.trim() ? true : '请填写原因'),
    })
    await apiIssueVerify(recordId.value, false, value.trim())
    ElMessage.success('已驳回，退回处理员')
    await load()
  } catch { /* canceled */ }
}

const pageTitle = computed(() => data.value ? `巡检详情 · ${data.value.record_no}` : '巡检详情')
const pageSub = computed(() => data.value ? `${data.value.room.name} · ${data.value.inspector.name}` : '')

async function load() {
  loading.value = true
  try {
    data.value = await apiInspectionRecordDetail(recordId.value)
  } finally {
    loading.value = false
  }
}

/* ---------------- report ---------------- */
const reportLoading = reactive({ view: false, download: false })

async function onViewReport() {
  reportLoading.view = true
  try {
    const blob = await apiInspectionReportBlob(recordId.value, false)
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
    // revoke a bit later so the new tab has time to load
    setTimeout(() => URL.revokeObjectURL(url), 60_000)
  } catch {
    ElMessage.error('报告生成失败')
  } finally {
    reportLoading.view = false
  }
}

async function onDownloadReport() {
  reportLoading.download = true
  try {
    const blob = await apiInspectionReportBlob(recordId.value, true)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${data.value?.record_no || 'inspection-report'}.html`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('报告下载失败')
  } finally {
    reportLoading.download = false
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
.record-detail {
  display: flex; flex-direction: column;
  gap: 12px;
}

.meta-card .meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;

  .kv {
    display: flex; flex-direction: column;
    .k { font-size: 12px; color: $text-tertiary; }
    .v { font-size: 14px; color: $text-primary; font-weight: 500; margin-top: 4px;
         display: flex; align-items: center; gap: 6px; }
    .hint { font-size: 11px; color: $text-tertiary; font-weight: 400; margin-left: 4px; }
  }
}
.remark {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed $border-light;
  font-size: 13px;
  color: $text-secondary;
}

.eq-block {
  padding: 14px 16px;
  background: #F8F9FC;
  border-radius: 8px;
  margin-bottom: 12px;
  border-left: 3px solid $status-completed;
  &.abn { border-left-color: $status-rejected; }
}
.eq-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;

  .left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .badge {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 10px;
    &.ok  { background: rgba(82,196,26,0.12); color: $status-completed; }
    &.bad { background: rgba(245,34,45,0.12); color: $status-rejected; }
  }
  .name { font-size: 15px; font-weight: 600; }
  .loc { font-size: 12px; color: $text-tertiary; }
  .right { font-size: 12px; color: $text-tertiary; }
}
.issue {
  margin-top: 8px;
  padding: 8px 10px;
  background: rgba(245,34,45,0.04);
  border-left: 3px solid rgba(245,34,45,0.4);
  border-radius: 4px;
  font-size: 13px;
  color: $status-rejected;
}
.atts {
  margin-top: 12px;
  .att-title { font-size: 12px; color: $text-tertiary; margin-bottom: 6px; }
  .att-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); gap: 6px; }
}
.att-thumb { width: 100%; aspect-ratio: 1; border-radius: 4px; border: 1px solid $border-light; }
.unit { color: $text-tertiary; font-size: 12px; }

.tl-line { font-size: 13px; color: $text-primary; }
.tl-op { color: $text-tertiary; margin-left: 4px; }
.tl-text { font-size: 12px; color: $text-secondary; margin-top: 2px; }

.issue-status-row {
  display: flex; align-items: center; gap: 14px; margin-bottom: 12px;
  .assignee { font-size: 13px; color: $text-secondary; }
  .done { font-size: 13px; color: $status-completed; font-weight: 600; }
}
.issue-actions {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 14px;
  .muted-tip { font-size: 13px; color: $text-tertiary; }
}
.photo-row { display: flex; flex-wrap: wrap; gap: 8px; }
.upload-box {
  width: 72px; height: 72px; border: 1px dashed $border-base; border-radius: 6px;
  display: flex; align-items: center; justify-content: center; cursor: pointer; color: $text-tertiary;
  &:hover { border-color: $brand-primary; color: $brand-primary; }
}
.hidden-input { display: none; }
.empty-tip { margin-top: 6px; font-size: 12px; color: $status-pending-assign; line-height: 1.5; }
</style>
