<template>
  <aside class="sider" :class="{ collapsed: appStore.sideCollapsed }">
    <div class="brand">
      <div class="brand-logo">
        <el-icon :size="20"><Cpu /></el-icon>
      </div>
      <transition name="fade">
        <div v-show="!appStore.sideCollapsed" class="brand-text">
          <div class="brand-title">智能巡检</div>
          <div class="brand-sub">机房运维管理</div>
        </div>
      </transition>
    </div>

    <el-scrollbar class="menu-scroll">
      <el-menu
        :default-active="activePath"
        :collapse="appStore.sideCollapsed"
        :collapse-transition="false"
        background-color="transparent"
        text-color="rgba(255,255,255,0.75)"
        active-text-color="#FFFFFF"
        unique-opened
        router
        class="nav-menu"
      >
        <template v-for="item in visibleMenu" :key="item.title">
          <!-- 分组 -->
          <el-sub-menu
            v-if="item.children?.length"
            :index="`group-${item.title}`"
            :disabled="item.disabled"
          >
            <template #title>
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
              <el-tag
                v-if="item.badge"
                size="small"
                effect="dark"
                round
                class="badge"
              >{{ item.badge }}</el-tag>
            </template>
            <el-menu-item
              v-for="c in item.children!.filter(c => !c.roles || c.roles.includes(userStore.role))"
              :key="c.title"
              :index="c.path || `disabled-${c.title}`"
              :disabled="c.disabled || !c.path"
            >
              <el-icon><component :is="c.icon" /></el-icon>
              <template #title>{{ c.title }}</template>
            </el-menu-item>
          </el-sub-menu>

          <!-- 单项 -->
          <el-menu-item
            v-else
            :index="item.path || `disabled-${item.title}`"
            :disabled="item.disabled || !item.path"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <template #title>{{ item.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-scrollbar>

    <div class="footer">
      <div v-show="!appStore.sideCollapsed" class="footer-text">
        v0.1.0 · 演示版本
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Cpu } from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useUserStore } from '@/stores/user'
import { menu } from '@/router/routes'

const route = useRoute()
const appStore = useAppStore()
const userStore = useUserStore()

const activePath = computed(() => route.path)

const visibleMenu = computed(() =>
  menu.filter(m => !m.roles || m.roles.includes(userStore.role)),
)
</script>

<style lang="scss" scoped>
.sider {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  width: $sider-width;
  background: linear-gradient(180deg, #0F2547 0%, #0B1A36 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width 0.25s ease;
  box-shadow: 2px 0 12px rgba(15, 37, 71, 0.1);

  &.collapsed {
    width: $sider-collapsed;
  }
}

.brand {
  height: $header-height;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;

  .brand-logo {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: linear-gradient(135deg, $brand-primary 0%, #4D7DFF 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    flex-shrink: 0;
    box-shadow: 0 4px 10px rgba(30, 94, 255, 0.35);
  }
  .brand-text {
    overflow: hidden;
    white-space: nowrap;
  }
  .brand-title {
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 0.5px;
    line-height: 1.2;
  }
  .brand-sub {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.45);
    margin-top: 2px;
    letter-spacing: 1px;
  }
}

.menu-scroll {
  flex: 1;
  margin-top: 6px;
}

.nav-menu {
  border-right: none;
  background: transparent !important;

  :deep(.el-menu-item),
  :deep(.el-sub-menu__title) {
    border-radius: 6px;
    margin: 2px 10px;
    height: 42px;
    line-height: 42px;
    padding-left: 14px !important;

    &:hover {
      background: rgba(255, 255, 255, 0.06) !important;
    }
  }

  :deep(.el-menu-item.is-active) {
    background: linear-gradient(90deg, rgba(30, 94, 255, 0.35) 0%, rgba(30, 94, 255, 0.12) 100%) !important;
    color: #fff !important;
    position: relative;
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 8px;
      bottom: 8px;
      width: 3px;
      background: #4D7DFF;
      border-radius: 0 2px 2px 0;
    }
  }

  :deep(.el-menu-item.is-disabled),
  :deep(.el-sub-menu.is-disabled .el-sub-menu__title) {
    opacity: 0.45 !important;
    cursor: not-allowed !important;
  }

  :deep(.el-sub-menu .el-menu-item) {
    margin-left: 20px;
    margin-right: 10px;
  }
}

.badge {
  margin-left: auto;
  margin-right: 8px;
  background: rgba(250, 140, 22, 0.18);
  color: #FA8C16;
  border: none;
  font-size: 11px;
  height: 18px;
  line-height: 18px;
  padding: 0 6px;
}

.footer {
  padding: 12px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
  text-align: center;
  letter-spacing: 0.5px;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
