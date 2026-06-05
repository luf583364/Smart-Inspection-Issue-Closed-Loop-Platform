<template>
  <span class="status-tag" :class="`status-${status}`">
    <span class="dot" />
    <span class="text">{{ STATUS_LABEL[status] ?? status }}</span>
  </span>
</template>

<script setup lang="ts">
import { STATUS_LABEL } from '@/utils/format'

defineProps<{ status: string }>()
</script>

<style lang="scss" scoped>
.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  line-height: 1.6;
  font-weight: 500;

  .dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: currentColor;
  }
}

.status-completed       { color: $status-completed;      background: rgba(82, 196, 26, 0.12); }
.status-in_progress     { color: $text-secondary;        background: rgba(96, 98, 102, 0.10); }
.status-pending_assign  { color: $status-pending-assign; background: rgba(250, 140, 22, 0.12); }
.status-pending_handle  { color: $status-pending-handle; background: rgba(250, 173, 20, 0.14); }
.status-handling        { color: $status-handling;       background: rgba(24, 144, 255, 0.12); }
.status-pending_verify  { color: $status-pending-verify; background: rgba(114, 46, 209, 0.12); }
.status-rejected        { color: $status-rejected;       background: rgba(245, 34, 45, 0.12); }
</style>
