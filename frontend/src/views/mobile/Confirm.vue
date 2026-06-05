<template>
  <div class="m-page" v-loading="loading">
    <div class="m-header">
      <div class="bar">
        <el-button text :icon="ArrowLeft" @click="$router.back()">返回</el-button>
        <span class="hint">提交确认</span>
      </div>
      <h2 class="title">即将提交本次巡检</h2>
      <div class="sub" v-if="detail">{{ detail.room.name }} · {{ detail.record_no }}</div>
    </div>

    <div class="sum-card" v-if="detail">
      <div class="row">
        <div class="cell">
          <div class="v">{{ stat.total }}</div>
          <div class="l">设备总数</div>
        </div>
        <div class="cell ok">
          <div class="v">{{ stat.normal }}</div>
          <div class="l">正常</div>
        </div>
        <div class="cell bad">
          <div class="v">{{ stat.abnormal }}</div>
          <div class="l">异常</div>
        </div>
      </div>
    </div>

    <div v-if="abnormalEquipments.length" class="list-card">
      <div class="row-title">异常设备摘要</div>
      <div v-for="eq in abnormalEquipments" :key="eq.equipment_id" class="abn-item">
        <div class="row1">
          <span class="dot" />
          <span class="name">{{ eq.equipment_name }}</span>
          <span class="type">{{ eq.equipment_type_label }}</span>
        </div>
        <div v-if="eq.issue_description" class="desc">{{ eq.issue_description }}</div>
        <div class="cnt" v-if="abnormalItemsCount(eq) > 0">{{ abnormalItemsCount(eq) }} 项检查项异常</div>
      </div>
    </div>

    <div class="list-card">
      <div class="row-title">备注（可选）</div>
      <el-input
        v-model="remark"
        type="textarea"
        :rows="3"
        placeholder="本次巡检整体补充说明"
        maxlength="500"
        show-word-limit
      />
    </div>

    <div class="m-footer">
      <el-button class="btn cancel" size="large" @click="$router.back()">返回继续巡检</el-button>
      <el-button
        class="btn confirm"
        type="primary"
        size="large"
        :loading="submitting"
        @click="onSubmit"
      >
        确认提交
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiSubmitInspection } from '@/api/mobileInspection'
import {
  apiInspectionRecordDetail,
  type EquipmentResultDetail,
  type RecordDetail,
} from '@/api/inspectionRecord'

const route = useRoute()
const router = useRouter()
const recordId = computed(() => Number(route.params.recordId))

const loading = ref(false)
const submitting = ref(false)
const detail = ref<RecordDetail | null>(null)
const remark = ref('')

const stat = computed(() => {
  const list = detail.value?.equipment_results ?? []
  return {
    total: list.length,
    normal: list.filter(e => e.result === 'normal').length,
    abnormal: list.filter(e => e.result === 'abnormal').length,
  }
})

const abnormalEquipments = computed<EquipmentResultDetail[]>(() =>
  detail.value?.equipment_results.filter(e => e.result === 'abnormal') ?? [],
)

function abnormalItemsCount(eq: EquipmentResultDetail) {
  return eq.items.filter(i => i.is_abnormal === 1).length
}

async function load() {
  loading.value = true
  try {
    detail.value = await apiInspectionRecordDetail(recordId.value)
  } finally {
    loading.value = false
  }
}

async function onSubmit() {
  submitting.value = true
  try {
    const r = await apiSubmitInspection(recordId.value, remark.value || undefined)
    ElMessage.success('提交成功')
    sessionStorage.setItem(`record_${recordId.value}_summary`, JSON.stringify(r))
    router.replace({ name: 'MobileSuccess', params: { recordId: String(recordId.value) } })
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<style lang="scss" scoped>
.m-page {
  display: flex; flex-direction: column;
  min-height: 100vh;
  padding-bottom: 100px;
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

.sum-card, .list-card {
  background: #fff;
  margin: 0 12px 12px;
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 2px 8px rgba(15,37,71,0.05);
}

.sum-card .row {
  display: flex;
  .cell {
    flex: 1; text-align: center;
    .v { font-size: 24px; font-weight: 700; color: $text-primary; }
    .l { font-size: 12px; color: $text-tertiary; margin-top: 4px; }
    &.ok .v { color: $status-completed; }
    &.bad .v { color: $status-rejected; }
  }
}

.row-title { font-size: 13px; font-weight: 600; color: $text-primary; margin-bottom: 10px; }

.abn-item {
  padding: 10px 0;
  border-bottom: 1px dashed $border-light;
  &:last-child { border-bottom: none; }
  .row1 {
    display: flex; align-items: center; gap: 8px;
    .dot { width: 6px; height: 6px; border-radius: 50%; background: $status-rejected; }
    .name { font-size: 14px; font-weight: 500; color: $text-primary; }
    .type { font-size: 11px; color: $text-tertiary; margin-left: 4px; }
  }
  .desc { font-size: 12px; color: $text-secondary; margin: 6px 0 0 14px; line-height: 1.5; }
  .cnt { font-size: 11px; color: $status-rejected; margin: 4px 0 0 14px; }
}

.m-footer {
  position: fixed; bottom: 0; left: 0; right: 0;
  max-width: 480px;
  margin: 0 auto;
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
  background: #fff;
  border-top: 1px solid $border-light;
  display: flex; gap: 10px;
  .btn { flex: 1; height: 48px; font-size: 15px; }
  .btn.cancel { background: #F5F7FA; color: $text-primary; border: 1px solid $border-base; }
}
</style>
