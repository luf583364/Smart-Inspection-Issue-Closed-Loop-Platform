<template>
  <div class="m-page" v-loading="loading">
    <!-- 顶部 -->
    <div class="m-header">
      <div class="bar">
        <el-button text :icon="ArrowLeft" @click="goBack">返回</el-button>
        <span class="src-tag" :class="data?.source">{{ sourceLabel }}</span>
      </div>
      <h2 class="title">
        {{ data?.room.name || '机房巡检' }}
      </h2>
      <div class="sub">
        <span class="code">编号 {{ data?.room.code || '--' }}</span>
        <span v-if="data?.room.area" class="area">{{ data.room.area }}</span>
      </div>
      <div class="meta">
        <span>巡检人员：{{ data?.inspector.name || '--' }}</span>
        <span>记录编号：{{ data?.record_no || '--' }}</span>
      </div>
    </div>

    <!-- 进度 -->
    <div class="progress-card">
      <div class="bar">
        <div class="fill" :style="{ width: progressPercent + '%' }" />
      </div>
      <div class="nums">
        <div class="n">
          <div class="v">{{ progress.completed }}/{{ progress.total }}</div>
          <div class="l">已巡检</div>
        </div>
        <div class="n ok">
          <div class="v">{{ progress.normal }}</div>
          <div class="l">正常</div>
        </div>
        <div class="n bad">
          <div class="v">{{ progress.abnormal }}</div>
          <div class="l">异常</div>
        </div>
      </div>
    </div>

    <!-- 设备列表 -->
    <div class="eq-list">
      <div
        v-for="eq in equipmentList"
        :key="eq.id"
        class="eq-card"
        :class="stateClass(eq)"
        @click="goEquipment(eq)"
      >
        <div class="row1">
          <span class="name">{{ eq.equipment_name }}</span>
          <span class="state-tag">{{ stateLabel(eq) }}</span>
        </div>
        <div class="row2">
          <span class="type">{{ eq.equipment_type_label }}</span>
          <span v-if="eq.location" class="loc">{{ eq.location }}</span>
        </div>
        <div class="row3">
          <span>{{ eq.item_count }} 项检查</span>
          <span v-if="eq.abnormal_item_count > 0" class="abn">{{ eq.abnormal_item_count }} 项异常</span>
          <el-icon class="arrow"><ArrowRight /></el-icon>
        </div>
      </div>
      <div v-if="!loading && equipmentList.length === 0" class="empty">
        当前机房暂无可巡检设备
      </div>
    </div>

    <!-- 底部固定按钮 -->
    <div class="m-footer">
      <el-button
        type="primary"
        size="large"
        class="submit-btn"
        :disabled="!canSubmit"
        @click="goConfirm"
      >
        {{ submitText }}
      </el-button>
      <div v-if="!canSubmit && equipmentList.length > 0" class="tip">
        请完成全部 {{ progress.total }} 台设备的巡检后提交
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  apiStartRoomInspection,
  type InspectionEquipmentBrief,
  type InspectionProgress,
  type StartInspectionData,
} from '@/api/mobileInspection'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const data = ref<StartInspectionData | null>(null)

const equipmentList = computed<InspectionEquipmentBrief[]>(() => data.value?.equipment_list ?? [])
const progress = computed<InspectionProgress>(() => data.value?.progress ?? { total: 0, completed: 0, normal: 0, abnormal: 0 })
const progressPercent = computed(() => (progress.value.total ? Math.round((progress.value.completed / progress.value.total) * 100) : 0))
const canSubmit = computed(() => progress.value.total > 0 && progress.value.completed >= progress.value.total)

const sourceLabel = computed(() => (data.value?.source === 'qr' ? '扫码进入' : '手动开始'))
const submitText = computed(() => (canSubmit.value ? '前往提交本次巡检' : `还剩 ${progress.value.total - progress.value.completed} 台未完成`))

function stateClass(eq: InspectionEquipmentBrief) {
  if (eq.result === 'abnormal') return 'state-bad'
  if (eq.result === 'normal') return 'state-ok'
  return 'state-pending'
}
function stateLabel(eq: InspectionEquipmentBrief) {
  if (eq.result === 'abnormal') return '异常'
  if (eq.result === 'normal') return '已完成'
  return '待巡检'
}

async function load() {
  const roomCode = String(route.params.roomCode || '')
  const source = (route.query.source === 'qr' ? 'qr' : 'manual') as 'manual' | 'qr'
  if (!roomCode) {
    ElMessage.error('缺少机房编号')
    return
  }
  loading.value = true
  try {
    data.value = await apiStartRoomInspection(roomCode, source)
  } catch (e: any) {
    // request interceptor already toasts
  } finally {
    loading.value = false
  }
}

function goBack() {
  // 桌面端登录后用户从机房页面跳过来；移动端扫码用户没历史可退，则回首页
  if (window.history.length > 1) {
    router.back()
  } else {
    router.replace('/dashboard')
  }
}

function goEquipment(eq: InspectionEquipmentBrief) {
  if (!data.value) return
  router.push({
    name: 'MobileEquipmentInspect',
    params: { recordId: String(data.value.record_id), equipmentId: String(eq.id) },
  })
}

function goConfirm() {
  if (!data.value) return
  if (!canSubmit.value) {
    ElMessage.warning('还有设备未完成，请先逐台巡检')
    return
  }
  router.push({ name: 'MobileConfirm', params: { recordId: String(data.value.record_id) } })
}

onMounted(load)
</script>

<style lang="scss" scoped>
.m-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding-bottom: 110px;
  background: linear-gradient(180deg, #0F2547 0%, #0F2547 160px, #F4F6FA 160px, #F4F6FA 100%);
}

.m-header {
  color: #fff;
  padding: 12px 16px 18px;

  .bar { display: flex; align-items: center; justify-content: space-between; }
  .bar .el-button { color: rgba(255,255,255,0.8); }
  .src-tag {
    font-size: 11px;
    background: rgba(255,255,255,0.15);
    padding: 2px 8px;
    border-radius: 10px;
    &.qr { background: rgba(82,196,26,0.25); }
  }
  .title { margin: 8px 0 4px; font-size: 22px; font-weight: 600; }
  .sub { font-size: 12px; color: rgba(255,255,255,0.65); display: flex; gap: 12px; }
  .sub .area::before { content: '·'; margin-right: 8px; }
  .meta {
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
    font-size: 12px;
    color: rgba(255,255,255,0.55);
  }
}

.progress-card {
  background: #fff;
  margin: 0 12px 12px;
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 6px 18px rgba(15,37,71,0.08);

  .bar {
    height: 6px;
    border-radius: 3px;
    background: #EEF0F4;
    overflow: hidden;
    .fill {
      height: 100%;
      background: linear-gradient(90deg, #1E5EFF 0%, #4D7DFF 100%);
      transition: width 0.25s ease;
    }
  }
  .nums {
    display: flex;
    margin-top: 12px;
    .n {
      flex: 1;
      text-align: center;
      .v { font-size: 18px; font-weight: 600; color: $text-primary; }
      .l { font-size: 11px; color: $text-tertiary; margin-top: 2px; }
      &.ok .v { color: $status-completed; }
      &.bad .v { color: $status-rejected; }
    }
  }
}

.eq-list {
  padding: 0 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.eq-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 2px 8px rgba(15,37,71,0.04);
  position: relative;
  border-left: 3px solid transparent;

  &.state-pending { border-left-color: #FAAD14; }
  &.state-ok      { border-left-color: $status-completed; }
  &.state-bad     { border-left-color: $status-rejected; }

  .row1 {
    display: flex;
    justify-content: space-between;
    align-items: center;
    .name { font-size: 15px; font-weight: 600; color: $text-primary; }
    .state-tag {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 10px;
      background: #F5F7FA;
      color: $text-secondary;
    }
  }
  &.state-ok .state-tag { background: rgba(82,196,26,0.12); color: $status-completed; }
  &.state-bad .state-tag { background: rgba(245,34,45,0.12); color: $status-rejected; }
  &.state-pending .state-tag { background: rgba(250,173,20,0.16); color: #B47300; }

  .row2 { display: flex; gap: 12px; font-size: 12px; color: $text-secondary; margin-top: 6px; }
  .row3 {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 10px;
    font-size: 12px;
    color: $text-tertiary;
    .abn { color: $status-rejected; }
    .arrow { margin-left: auto; }
  }
}

.empty {
  padding: 40px 16px;
  text-align: center;
  color: $text-tertiary;
  font-size: 13px;
}

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

  .submit-btn { width: 100%; height: 48px; font-size: 15px; letter-spacing: 1px; }
  .tip { text-align: center; font-size: 12px; color: $text-tertiary; margin-top: 6px; }
}
</style>
