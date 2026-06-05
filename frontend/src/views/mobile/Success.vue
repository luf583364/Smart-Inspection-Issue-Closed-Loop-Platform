<template>
  <div class="m-page">
    <div class="hero">
      <div class="ring">
        <el-icon :size="44"><CircleCheckFilled /></el-icon>
      </div>
      <div class="title">提交成功</div>
      <div class="sub">本次机房巡检已记录归档</div>
    </div>

    <div class="card" v-if="summary">
      <div class="line"><span class="k">巡检编号</span><span class="v">{{ summary.record_no }}</span></div>
      <div class="line"><span class="k">当前状态</span><span class="v"><StatusTag :status="summary.status" /></span></div>
      <div class="line"><span class="k">设备总数</span><span class="v">{{ summary.summary.equipment_total }}</span></div>
      <div class="line"><span class="k">正常设备</span><span class="v ok">{{ summary.summary.normal_equipment }}</span></div>
      <div class="line"><span class="k">异常设备</span><span class="v bad">{{ summary.summary.abnormal_equipment }}</span></div>
      <div class="line"><span class="k">提交时间</span><span class="v">{{ formatDateTime(summary.submitted_at) }}</span></div>
    </div>

    <div v-else class="card">
      <div class="line"><span class="k">巡检编号</span><span class="v">{{ recordId }}</span></div>
    </div>

    <div class="actions">
      <el-button class="btn" size="large" @click="onLogout">退出登录</el-button>
      <el-button class="btn" type="primary" size="large" @click="goInspectAnother">再巡检一个机房</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CircleCheckFilled } from '@element-plus/icons-vue'
import StatusTag from '@/components/StatusTag/index.vue'
import { formatDateTime } from '@/utils/format'
import { useUserStore } from '@/stores/user'
import type { SubmitInspectionData } from '@/api/mobileInspection'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const recordId = computed(() => Number(route.params.recordId))
const summary = ref<SubmitInspectionData | null>(null)

onMounted(() => {
  const raw = sessionStorage.getItem(`record_${recordId.value}_summary`)
  if (raw) {
    try { summary.value = JSON.parse(raw) } catch {}
  }
})

function goInspectAnother() { router.replace('/mobile/inspection') }
function onLogout() {
  userStore.logout()
  router.replace('/login')
}
</script>

<style lang="scss" scoped>
.m-page {
  min-height: 100vh;
  background: #F4F6FA;
  display: flex; flex-direction: column;
  padding: 24px 16px;
}

.hero {
  text-align: center;
  padding: 36px 0 28px;
  .ring {
    width: 80px; height: 80px;
    border-radius: 50%;
    background: rgba(82,196,26,0.12);
    color: $status-completed;
    display: inline-flex; align-items: center; justify-content: center;
    margin-bottom: 16px;
  }
  .title { font-size: 22px; font-weight: 600; color: $text-primary; }
  .sub { font-size: 13px; color: $text-secondary; margin-top: 6px; }
}

.card {
  background: #fff;
  border-radius: 12px;
  padding: 16px 18px;
  box-shadow: 0 2px 8px rgba(15,37,71,0.05);
  .line {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 0;
    border-bottom: 1px dashed $border-light;
    &:last-child { border-bottom: none; }
    .k { font-size: 13px; color: $text-secondary; }
    .v { font-size: 13px; color: $text-primary; font-weight: 500; }
    .v.ok  { color: $status-completed; }
    .v.bad { color: $status-rejected; }
  }
}

.actions {
  margin-top: 28px;
  display: flex; gap: 10px;
  .btn { flex: 1; height: 46px; font-size: 14px; }
}
</style>
