<template>
  <div class="m-page" v-loading="loading">
    <!-- 顶部 -->
    <div class="m-header">
      <div class="bar">
        <span class="hi">{{ greeting }}</span>
        <el-button text class="right-btn" @click="onLogout">退出</el-button>
      </div>
      <h2 class="title">选择要巡检的机房</h2>
      <div class="sub">点击机房卡片开始巡检 · 当前账号 {{ userStore.user?.name || '' }}</div>
    </div>

    <!-- 搜索 -->
    <div class="search">
      <el-input
        v-model="keyword"
        placeholder="搜索机房编号 / 名称 / 区域"
        clearable
        :prefix-icon="Search"
      />
    </div>

    <!-- 机房列表 -->
    <div class="room-list">
      <div
        v-for="r in filteredRooms"
        :key="r.id"
        class="room-card"
        :class="{ done: r.inspected_today }"
        @click="goRoom(r)"
      >
        <div class="row1">
          <span class="name">{{ r.name }}</span>
          <span v-if="r.inspected_today" class="done-tag">已巡检</span>
          <span class="code">{{ r.code }}</span>
        </div>
        <div class="row2">
          <span v-if="r.area" class="tag area">{{ r.area }}</span>
          <span class="eqs">{{ r.equipment_count }} 台设备</span>
          <span v-if="r.owner_name" class="owner">负责人：{{ r.owner_name }}</span>
        </div>
        <el-icon class="arrow">
          <CircleCheck v-if="r.inspected_today" />
          <ArrowRight v-else />
        </el-icon>
      </div>

      <div v-if="!loading && filteredRooms.length === 0" class="empty">
        {{ rooms.length === 0 ? '当前没有启用的机房，请先在后台「机房管理」中添加' : '没有匹配的机房' }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, CircleCheck, Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { apiInspectableRooms, type InspectableRoom } from '@/api/mobileInspection'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 经固定二维码进入时 query.source=qr，选机房后沿用该来源
const entrySource = computed(() => (route.query.source === 'qr' ? 'qr' : 'manual'))

const loading = ref(false)
const rooms = ref<InspectableRoom[]>([])
const keyword = ref('')

const greeting = computed(() => {
  const h = new Date().getHours()
  const g = h < 6 ? '夜深了' : h < 11 ? '早上好' : h < 14 ? '中午好' : h < 18 ? '下午好' : '晚上好'
  return `${g}，开始今天的巡检吧`
})

const filteredRooms = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return rooms.value
  return rooms.value.filter(r =>
    [r.code, r.name, r.area].some(v => (v || '').toLowerCase().includes(kw)),
  )
})

async function load() {
  loading.value = true
  try {
    rooms.value = await apiInspectableRooms()
  } finally {
    loading.value = false
  }
}

function goRoom(r: InspectableRoom) {
  if (r.inspected_today) {
    ElMessage.info('今天已巡检过该机房，每个机房每天仅可巡检一次')
    return
  }
  router.push({
    name: 'MobileInspectionStart',
    params: { roomCode: r.code },
    query: { source: entrySource.value },
  })
}

function onLogout() {
  userStore.logout()
  ElMessage.success('已退出')
  router.replace('/login')
}

onMounted(load)
</script>

<style lang="scss" scoped>
.m-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding-bottom: 24px;
  background: linear-gradient(180deg, #0F2547 0%, #0F2547 150px, #F4F6FA 150px, #F4F6FA 100%);
}

.m-header {
  color: #fff;
  padding: 14px 16px 18px;

  .bar { display: flex; align-items: center; justify-content: space-between; }
  .hi { font-size: 13px; color: rgba(255,255,255,0.7); }
  .right-btn { color: rgba(255,255,255,0.85); }
  .title { margin: 10px 0 4px; font-size: 22px; font-weight: 600; }
  .sub { font-size: 12px; color: rgba(255,255,255,0.6); }
}

.search {
  margin: 0 12px 12px;
}
.search :deep(.el-input__wrapper) {
  border-radius: 10px;
}

.room-list {
  padding: 0 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.room-card {
  background: #fff;
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 0 2px 8px rgba(15,37,71,0.05);
  position: relative;
  cursor: pointer;
  transition: box-shadow .15s, transform .15s;
  border-left: 3px solid $brand-primary;

  &:active { transform: scale(0.99); }
  &:hover { box-shadow: 0 6px 16px rgba(15,37,71,0.1); }

  &.done {
    border-left-color: $status-completed;
    background: #FAFCF7;
    .name { color: $text-secondary; }
    .arrow { color: $status-completed; }
  }

  .row1 {
    display: flex; align-items: baseline; gap: 8px;
    .name { font-size: 16px; font-weight: 600; color: $text-primary; }
    .code { font-size: 12px; color: $text-tertiary; }
    .done-tag {
      font-size: 11px; padding: 1px 8px; border-radius: 8px; font-weight: 500;
      background: rgba(82,196,26,0.14); color: $status-completed;
    }
  }
  .row2 {
    display: flex; align-items: center; gap: 10px; margin-top: 8px;
    .tag {
      font-size: 11px; padding: 1px 8px; border-radius: 8px;
      background: $brand-light; color: $brand-primary;
    }
    .eqs { font-size: 12px; color: $text-tertiary; }
    .owner { font-size: 12px; color: $text-secondary; }
  }
  .arrow {
    position: absolute; right: 14px; top: 50%; transform: translateY(-50%);
    color: $text-tertiary;
  }
}

.empty {
  padding: 48px 16px;
  text-align: center;
  color: $text-tertiary;
  font-size: 13px;
}
</style>
