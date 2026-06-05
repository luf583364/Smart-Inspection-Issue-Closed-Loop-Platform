<template>
  <header class="header-bar">
    <div class="left">
      <el-button
        :icon="appStore.sideCollapsed ? Expand : Fold"
        text
        circle
        class="toggle-btn"
        @click="appStore.toggleSide"
      />
      <el-breadcrumb separator="/" class="bread">
        <el-breadcrumb-item v-if="parentTitle">{{ parentTitle }}</el-breadcrumb-item>
        <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div class="right">
      <el-tooltip content="刷新页面" placement="bottom">
        <el-button :icon="Refresh" text circle @click="reload" />
      </el-tooltip>

      <el-dropdown trigger="click" @command="onCommand">
        <div class="user-pane">
          <el-avatar :size="32" class="avatar">
            {{ shortName }}
          </el-avatar>
          <div class="user-meta">
            <div class="name">{{ userStore.user?.name || '--' }}</div>
            <div class="role">{{ roleLabel }}</div>
          </div>
          <el-icon :size="12" class="caret"><CaretBottom /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item disabled>
              <el-icon><UserFilled /></el-icon>
              {{ userStore.user?.username }}
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  CaretBottom,
  Expand,
  Fold,
  Refresh,
  SwitchButton,
  UserFilled,
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { ROLE_LABEL } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()

const parentTitle = computed(() => (route.meta.parentTitle as string) || '')
const currentTitle = computed(() => (route.meta.title as string) || '')
const roleLabel = computed(() => ROLE_LABEL[userStore.role] || userStore.role || '')
const shortName = computed(() => {
  const n = userStore.user?.name || ''
  return n ? n.slice(-1) : 'U'
})

function reload() {
  location.reload()
}

async function onCommand(cmd: string) {
  if (cmd === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '退出',
        cancelButtonText: '取消',
        type: 'warning',
      })
      userStore.logout()
      router.push('/login')
    } catch {
      // canceled
    }
  }
}
</script>

<style lang="scss" scoped>
.header-bar {
  height: $header-height;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px 0 4px;
  border-bottom: 1px solid $border-light;
  position: sticky;
  top: 0;
  z-index: 50;

  .left {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .right {
    display: flex;
    align-items: center;
    gap: 12px;
  }
}

.toggle-btn {
  font-size: 18px;
  color: $text-secondary;
}

.bread {
  :deep(.el-breadcrumb__item) {
    .el-breadcrumb__inner {
      font-weight: 400;
      color: $text-secondary;
    }
    &:last-child .el-breadcrumb__inner {
      color: $text-primary;
      font-weight: 500;
    }
  }
}

.user-pane {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 10px 4px 4px;
  border-radius: 20px;
  cursor: pointer;
  transition: background 0.2s;
  &:hover { background: $bg-hover; }

  .avatar {
    background: linear-gradient(135deg, $brand-primary 0%, #4D7DFF 100%);
    color: #fff;
    font-weight: 600;
    font-size: 13px;
  }
  .user-meta {
    line-height: 1.25;
    .name {
      font-size: 13px;
      color: $text-primary;
      font-weight: 500;
    }
    .role {
      font-size: 11px;
      color: $text-tertiary;
    }
  }
  .caret { color: $text-tertiary; }
}
</style>
