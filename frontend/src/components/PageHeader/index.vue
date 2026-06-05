<template>
  <div class="page-header">
    <div class="left">
      <div class="title">{{ title }}</div>
      <div v-if="subtitle" class="subtitle">{{ subtitle }}</div>
    </div>
    <div class="right">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
}>()
</script>

<style lang="scss" scoped>
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;

  .title {
    font-size: 20px;
    font-weight: 600;
    color: $text-primary;
    line-height: 1.3;
  }
  .subtitle {
    margin-top: 4px;
    font-size: 13px;
    color: $text-secondary;
  }
}
</style>
