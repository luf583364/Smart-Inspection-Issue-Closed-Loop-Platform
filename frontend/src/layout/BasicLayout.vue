<template>
  <div class="layout">
    <SideMenu />
    <div class="layout-main" :class="{ collapsed: appStore.sideCollapsed }">
      <HeaderBar />
      <main class="layout-content">
        <router-view v-slot="{ Component, route }">
          <component :is="Component" :key="route.path" />
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import SideMenu from './SideMenu.vue'
import HeaderBar from './HeaderBar.vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()
</script>

<style lang="scss" scoped>
.layout {
  display: flex;
  height: 100vh;
  background: $bg-layout;
}

.layout-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: $sider-width;
  transition: margin-left 0.25s ease;
  min-width: 0;

  &.collapsed {
    margin-left: $sider-collapsed;
  }
}

.layout-content {
  flex: 1;
  padding: $content-padding;
  overflow: auto;
}
</style>

<!-- Transition classes are applied to the slotted child component's root,
     which has different data-v-* attributes; keep these rules global. -->
<style lang="scss">
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-slide-enter-from { opacity: 0; transform: translateY(8px); }
.fade-slide-leave-to   { opacity: 0; transform: translateY(-8px); }
</style>
