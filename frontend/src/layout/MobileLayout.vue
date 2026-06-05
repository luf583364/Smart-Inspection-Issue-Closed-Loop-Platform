<template>
  <div class="mobile-shell">
    <div class="mobile-frame">
      <router-view v-slot="{ Component, route }">
        <component :is="Component" :key="route.path" />
      </router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style lang="scss" scoped>
.mobile-shell {
  min-height: 100vh;
  background: #F4F6FA;
  display: flex;
  justify-content: center;
}

.mobile-frame {
  width: 100%;
  max-width: 480px;
  min-height: 100vh;
  background: $bg-card;
  box-shadow: 0 0 24px rgba(15, 37, 71, 0.06);
  display: flex;
  flex-direction: column;
  position: relative;
}

@media (max-width: 540px) {
  .mobile-frame { box-shadow: none; }
}

.m-fade-enter-active, .m-fade-leave-active { transition: opacity 0.18s; }
.m-fade-enter-from, .m-fade-leave-to { opacity: 0; }
</style>
