<template>
  <div class="m-page" v-loading="loading">
    <!-- 顶部 -->
    <div class="m-header">
      <div class="bar">
        <el-button text :icon="ArrowLeft" @click="goBack">返回</el-button>
        <span class="hint">设备巡检</span>
      </div>
      <h2 class="title">{{ data?.equipment.equipment_name || '设备' }}</h2>
      <div class="sub">
        <span>{{ data?.equipment.equipment_type_label }}</span>
        <span v-if="data?.equipment.location">· {{ data.equipment.location }}</span>
      </div>
    </div>

    <!-- 整机结果 -->
    <div class="result-card">
      <div class="row-title">整机结果</div>
      <div class="big-btns">
        <button
          type="button"
          class="big-btn ok"
          :class="{ active: result === 'normal' }"
          @click="setResult('normal')"
        >
          正常
        </button>
        <button
          type="button"
          class="big-btn bad"
          :class="{ active: result === 'abnormal' }"
          @click="setResult('abnormal')"
        >
          异常
        </button>
      </div>
    </div>

    <!-- 检查项 -->
    <div class="items">
      <div
        v-for="(it, idx) in items"
        :key="it.check_item_id"
        class="item-card"
        :class="{ abn: it.is_abnormal }"
      >
        <div class="row1">
          <span class="num">{{ idx + 1 }}</span>
          <span class="name">{{ it.item_name }}</span>
        </div>
        <div v-if="it.standard_value" class="std">
          标准：{{ it.standard_value }}{{ it.unit ? ' ' + it.unit : '' }}
        </div>

        <!-- boolean -->
        <div v-if="it.input_type === 'boolean'" class="two-btns">
          <button
            type="button"
            class="bk ok"
            :class="{ active: it.value === 'normal' && !it.is_abnormal }"
            @click="setBool(it, false)"
          >正常</button>
          <button
            type="button"
            class="bk bad"
            :class="{ active: it.is_abnormal }"
            @click="setBool(it, true)"
          >异常</button>
        </div>

        <!-- number -->
        <div v-else-if="it.input_type === 'number'" class="numinput">
          <el-input
            v-model="it.value"
            type="text"
            inputmode="decimal"
            :placeholder="`填写读数${it.unit ? '（' + it.unit + '）' : ''}`"
            @change="onNumberChange(it)"
          >
            <template v-if="it.unit" #append>{{ it.unit }}</template>
          </el-input>
          <el-switch
            v-model="it.is_abnormal"
            inline-prompt
            active-text="异常"
            inactive-text="正常"
            style="margin-left:8px"
          />
        </div>

        <!-- text/photo -->
        <div v-else class="numinput">
          <el-input v-model="it.value" placeholder="填写描述（选填）" />
          <el-switch
            v-model="it.is_abnormal"
            inline-prompt
            active-text="异常"
            inactive-text="正常"
            style="margin-left:8px"
          />
        </div>

        <el-input
          v-if="it.is_abnormal"
          v-model="it.remark"
          type="textarea"
          :rows="2"
          class="remark"
          placeholder="描述具体异常情况（选填）"
        />
      </div>
    </div>

    <!-- 异常说明 + 照片 -->
    <div v-if="result === 'abnormal'" class="result-card">
      <div class="row-title">异常说明</div>
      <el-input
        v-model="issueDescription"
        type="textarea"
        :rows="3"
        placeholder="请描述本台设备整体的异常情况"
      />

      <div class="row-title" style="margin-top:14px">现场照片</div>
      <div class="photo-grid">
        <div
          v-for="att in attachments"
          :key="att.id"
          class="photo"
          :style="{ backgroundImage: `url(${att.url})` }"
        >
          <el-icon class="del" @click.stop="removeAttachment(att.id)"><Close /></el-icon>
        </div>
        <label class="photo add" v-if="attachments.length < 6">
          <input
            type="file"
            accept="image/jpeg,image/jpg,image/png,image/webp"
            capture="environment"
            class="hidden-input"
            @change="onFileChosen"
          />
          <el-icon :size="22"><Plus /></el-icon>
          <div class="hint">拍照 / 选图</div>
        </label>
      </div>
      <div class="phototip">支持 JPG / PNG / WebP，单张不超过 5MB</div>
    </div>

    <div class="m-footer">
      <el-button class="btn save" size="large" @click="onSaveBack" :loading="saving">保存并返回</el-button>
      <el-button class="btn next" type="primary" size="large" @click="onSaveNext" :loading="saving">保存并下一项</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { ArrowLeft, Close, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  apiDeleteAttachment,
  apiGetEquipmentInspection,
  apiSaveEquipmentResult,
  apiUploadEquipmentImage,
  type AttachmentBrief,
  type EquipmentInspectionDetail,
  type EquipmentItemValue,
  type SaveEquipmentResultResp,
} from '@/api/mobileInspection'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const saving = ref(false)
const data = ref<EquipmentInspectionDetail | null>(null)

const items = ref<EquipmentItemValue[]>([])
const attachments = ref<AttachmentBrief[]>([])
const result = ref<'normal' | 'abnormal' | null>(null)
const issueDescription = ref('')
const dirty = ref(false)

const recordId = computed(() => Number(route.params.recordId))
const equipmentId = computed(() => Number(route.params.equipmentId))

function markDirty() { dirty.value = true }

function setResult(r: 'normal' | 'abnormal') {
  result.value = r
  if (r === 'normal') {
    items.value.forEach(i => {
      i.is_abnormal = false
      if (i.input_type === 'boolean') i.value = 'normal'
    })
    issueDescription.value = ''
  }
  markDirty()
}

function setBool(it: EquipmentItemValue, abnormal: boolean) {
  it.is_abnormal = abnormal
  it.value = abnormal ? 'abnormal' : 'normal'
  if (abnormal) result.value = 'abnormal'
  recomputeResult()
  markDirty()
}

function onNumberChange(it: EquipmentItemValue) {
  if (it.is_abnormal) result.value = 'abnormal'
  markDirty()
}

function recomputeResult() {
  const anyAbn = items.value.some(i => i.is_abnormal)
  if (anyAbn) {
    result.value = 'abnormal'
  } else if (result.value !== 'normal') {
    // 用户没主动按"正常"时不强行覆盖
  }
}

async function load() {
  loading.value = true
  try {
    data.value = await apiGetEquipmentInspection(recordId.value, equipmentId.value)
    items.value = data.value.items.map(i => ({ ...i }))
    attachments.value = [...data.value.attachments]
    result.value = data.value.result
    issueDescription.value = data.value.issue_description ?? ''
    dirty.value = false
  } finally {
    loading.value = false
  }
}

function validate(): { ok: boolean; msg?: string } {
  if (!result.value) return { ok: false, msg: '请选择整机结果（正常 / 异常）' }
  // 必填项校验：boolean 必须有 value；number 必须填值或 is_abnormal 已勾选
  for (const it of items.value) {
    if (it.input_type === 'boolean' && !it.value) {
      return { ok: false, msg: `「${it.item_name}」未选择正常/异常` }
    }
    if (it.input_type === 'number' && (it.value === null || it.value === '' || it.value === undefined) && !it.is_abnormal) {
      return { ok: false, msg: `「${it.item_name}」未填写数值，如确实无法测量请标记异常并说明` }
    }
  }
  if (result.value === 'abnormal') {
    const anyMark = items.value.some(i => i.is_abnormal)
    if (!anyMark && !issueDescription.value.trim()) {
      return { ok: false, msg: '已选择异常，请至少标记一项异常或填写异常描述' }
    }
  }
  return { ok: true }
}

async function save(): Promise<SaveEquipmentResultResp | null> {
  const v = validate()
  if (!v.ok) { ElMessage.warning(v.msg!); return null }
  saving.value = true
  try {
    const saved = await apiSaveEquipmentResult(recordId.value, equipmentId.value, {
      result: result.value!,
      issue_description: result.value === 'abnormal' ? issueDescription.value.trim() || null : null,
      items: items.value.map(i => ({
        check_item_id: i.check_item_id,
        value: i.value,
        is_abnormal: !!i.is_abnormal,
        remark: i.remark || null,
      })),
    })
    dirty.value = false
    return saved
  } catch {
    return null
  } finally {
    saving.value = false
  }
}

async function onSaveBack() {
  if (await save()) {
    ElMessage.success('已保存')
    router.back()
  }
}

async function onSaveNext() {
  const saved = await save()
  if (!saved) return
  ElMessage.success('已保存')
  if (saved.next_equipment_id && saved.next_equipment_id !== equipmentId.value) {
    router.replace({
      name: 'MobileEquipmentInspect',
      params: { recordId: String(recordId.value), equipmentId: String(saved.next_equipment_id) },
    })
    return
  }
  router.replace({ name: 'MobileConfirm', params: { recordId: String(recordId.value) } })
}

function onFileChosen(e: Event) {
  const target = e.target as HTMLInputElement
  const f = target.files?.[0]
  target.value = ''
  if (!f) return
  if (!/^image\/(jpeg|jpg|png|webp)$/.test(f.type)) {
    ElMessage.error('仅支持 JPG / PNG / WebP')
    return
  }
  if (f.size > 5 * 1024 * 1024) {
    ElMessage.error('单张照片不能超过 5MB')
    return
  }
  uploadFile(f)
}

async function uploadFile(file: File) {
  saving.value = true
  try {
    const att = await apiUploadEquipmentImage(recordId.value, equipmentId.value, file)
    attachments.value.push(att)
    markDirty()
    ElMessage.success('上传成功')
  } finally {
    saving.value = false
  }
}

async function removeAttachment(id: number) {
  try {
    await ElMessageBox.confirm('确定删除这张现场照片？', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch { return }
  saving.value = true
  try {
    await apiDeleteAttachment(id)
    attachments.value = attachments.value.filter(a => a.id !== id)
    ElMessage.success('照片已删除')
  } finally {
    saving.value = false
  }
}

function goBack() {
  if (dirty.value) {
    ElMessageBox.confirm('当前修改尚未保存，确定离开?', '提示', {
      confirmButtonText: '离开',
      cancelButtonText: '继续编辑',
      type: 'warning',
    }).then(() => router.back()).catch(() => {})
  } else {
    router.back()
  }
}

// Track unsaved changes when navigating away
onBeforeRouteLeave((_to, _from, next) => {
  if (!dirty.value) { next(); return }
  ElMessageBox.confirm('当前修改尚未保存，确定离开?', '提示', {
    confirmButtonText: '离开',
    cancelButtonText: '继续编辑',
    type: 'warning',
  }).then(() => next()).catch(() => next(false))
})

function onBeforeUnload(e: BeforeUnloadEvent) {
  if (dirty.value) {
    e.preventDefault()
    e.returnValue = ''
  }
}

onMounted(() => {
  window.addEventListener('beforeunload', onBeforeUnload)
  load()
})
onBeforeUnmount(() => window.removeEventListener('beforeunload', onBeforeUnload))
</script>

<style lang="scss" scoped>
.m-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding-bottom: 96px;
  background: linear-gradient(180deg, #0F2547 0%, #0F2547 130px, #F4F6FA 130px, #F4F6FA 100%);
}

.m-header {
  color: #fff;
  padding: 12px 16px 20px;
  .bar { display: flex; align-items: center; justify-content: space-between; }
  .bar .el-button { color: rgba(255,255,255,0.85); }
  .hint { font-size: 12px; color: rgba(255,255,255,0.55); }
  .title { margin: 8px 0 4px; font-size: 20px; font-weight: 600; }
  .sub { font-size: 12px; color: rgba(255,255,255,0.65); }
}

.result-card, .items {
  margin: 0 12px 12px;
}
.result-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 2px 8px rgba(15,37,71,0.05);
}
.row-title {
  font-size: 13px;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 10px;
}
.big-btns {
  display: flex;
  gap: 10px;
}
.big-btn {
  flex: 1;
  height: 56px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px;
  border: 1.5px solid #E5E7EB;
  background: #F8F9FC;
  color: $text-secondary;
  letter-spacing: 4px;
  cursor: pointer;
  transition: all 0.15s;
  &.ok.active { background: rgba(82,196,26,0.12); color: $status-completed; border-color: $status-completed; }
  &.bad.active { background: rgba(245,34,45,0.10); color: $status-rejected; border-color: $status-rejected; }
}

.items {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.item-card {
  background: #fff;
  padding: 12px 14px;
  border-radius: 10px;
  box-shadow: 0 2px 6px rgba(15,37,71,0.04);
  border-left: 3px solid transparent;
  &.abn { border-left-color: $status-rejected; }

  .row1 {
    display: flex; align-items: center; gap: 8px;
    .num {
      width: 20px; height: 20px; border-radius: 50%;
      background: $brand-light; color: $brand-primary;
      font-size: 11px; display: flex; align-items: center; justify-content: center;
    }
    .name { font-size: 14px; font-weight: 500; }
  }
  .std { font-size: 11px; color: $text-tertiary; margin: 4px 0 8px 28px; }

  .two-btns {
    display: flex; gap: 8px; margin-top: 8px;
    .bk {
      flex: 1; height: 44px; font-size: 14px;
      border-radius: 8px; border: 1px solid #E5E7EB; background: #F8F9FC;
      color: $text-secondary; cursor: pointer;
      &.ok.active { background: rgba(82,196,26,0.12); color: $status-completed; border-color: $status-completed; }
      &.bad.active { background: rgba(245,34,45,0.10); color: $status-rejected; border-color: $status-rejected; }
    }
  }
  .numinput {
    display: flex; align-items: center; gap: 8px; margin-top: 8px;
    :deep(.el-input) { flex: 1; }
  }
  .remark { margin-top: 8px; }
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.photo {
  position: relative;
  aspect-ratio: 1;
  background-size: cover;
  background-position: center;
  background-color: #F8F9FC;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid $border-light;

  .del {
    position: absolute;
    top: 4px;
    right: 4px;
    background: rgba(0,0,0,0.6);
    color: #fff;
    border-radius: 50%;
    width: 22px; height: 22px;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
  }

  &.add {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    color: $text-tertiary;
    cursor: pointer;
    border: 1.5px dashed $border-base;
    .hint { font-size: 11px; margin-top: 4px; }
  }
}
.phototip { margin-top: 8px; font-size: 11px; color: $text-tertiary; }
.hidden-input { display: none; }

.m-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  max-width: 480px;
  margin: 0 auto;
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
  background: #fff;
  border-top: 1px solid $border-light;
  display: flex;
  gap: 10px;

  .btn { flex: 1; height: 48px; font-size: 15px; }
  .btn.save { background: #F5F7FA; color: $text-primary; border: 1px solid $border-base; }
}
</style>
