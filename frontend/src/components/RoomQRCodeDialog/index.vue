<template>
  <el-dialog
    v-model="visible"
    title="机房巡检二维码"
    width="680px"
    class="qr-dialog"
    :close-on-click-modal="false"
  >
    <div v-loading="loading" class="qr-body">
      <el-alert
        v-if="info?.warning"
        class="qr-warning"
        type="warning"
        show-icon
        :closable="false"
        :title="info.warning"
      />

      <div class="qr-layout">
        <div class="qr-preview">
          <img v-if="svgObjectUrl" :src="svgObjectUrl" alt="机房巡检二维码" />
          <div v-else class="qr-empty">二维码加载中</div>
        </div>

        <div class="qr-meta">
          <div class="meta-row">
            <span class="label">机房名称</span>
            <span class="value">{{ info?.room_name || room?.name || '-' }}</span>
          </div>
          <div class="meta-row">
            <span class="label">机房编号</span>
            <span class="value code">{{ info?.room_code || room?.code || '-' }}</span>
          </div>
          <div class="meta-row block">
            <span class="label">扫码地址</span>
            <el-input :model-value="info?.target_url || ''" readonly>
              <template #append>
                <el-button :icon="DocumentCopy" @click="copyUrl" />
              </template>
            </el-input>
          </div>
          <div class="scan-note">
            请使用手机扫码，登录后进入对应机房巡检页面。二维码不包含用户、密码或 Token。
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button :icon="Refresh" @click="loadQr" :loading="loading">刷新</el-button>
      <el-button :icon="Download" :disabled="!info?.printable" @click="download('svg')">
        下载 SVG
      </el-button>
      <el-button :icon="Download" :disabled="!info?.printable" @click="download('png')">
        下载 PNG
      </el-button>
      <el-button type="primary" :icon="Printer" :disabled="!info?.printable" @click="printQr">
        打印
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { DocumentCopy, Download, Printer, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { apiRoomQrBlob, apiRoomQrInfo, type RoomInfo, type RoomQrInfo } from '@/api/room'

type QrRoom = Pick<RoomInfo, 'id' | 'code' | 'name'> & Partial<RoomInfo>

const props = defineProps<{
  modelValue: boolean
  room: QrRoom | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})

const loading = ref(false)
const info = ref<RoomQrInfo | null>(null)
const svgObjectUrl = ref('')
const svgText = ref('')

function revokeSvgUrl() {
  if (svgObjectUrl.value) {
    URL.revokeObjectURL(svgObjectUrl.value)
    svgObjectUrl.value = ''
  }
}

async function loadQr() {
  if (!props.room) return
  loading.value = true
  try {
    info.value = await apiRoomQrInfo(props.room.id)
    const svg = await apiRoomQrBlob(props.room.id, 'svg')
    revokeSvgUrl()
    svgObjectUrl.value = URL.createObjectURL(svg)
    svgText.value = await svg.text()
  } finally {
    loading.value = false
  }
}

async function download(format: 'svg' | 'png') {
  if (!props.room || !info.value?.printable) return
  const blob = format === 'svg' && svgText.value
    ? new Blob([svgText.value], { type: 'image/svg+xml' })
    : await apiRoomQrBlob(props.room.id, format)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.room.code}-inspection-qr.${format}`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

async function copyUrl() {
  if (!info.value?.target_url) return
  await navigator.clipboard.writeText(info.value.target_url)
  ElMessage.success('扫码地址已复制')
}

function printQr() {
  if (!props.room || !info.value?.printable || !svgText.value) return
  const win = window.open('', '_blank', 'width=720,height=900')
  if (!win) {
    ElMessage.warning('浏览器阻止了打印窗口')
    return
  }
  const title = import.meta.env.VITE_APP_TITLE || '机房巡检系统'
  win.document.write(`<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(props.room.code)} 巡检二维码</title>
  <style>
    body { margin: 0; font-family: "Microsoft YaHei", sans-serif; color: #0f172a; }
    .sheet { width: 148mm; min-height: 210mm; padding: 18mm; box-sizing: border-box; }
    .title { font-size: 22px; font-weight: 700; margin-bottom: 6mm; }
    .meta { font-size: 14px; color: #475569; line-height: 1.8; }
    .qr { width: 82mm; height: 82mm; margin: 12mm 0; }
    .qr svg { width: 100%; height: 100%; }
    .note { margin-top: 8mm; font-size: 14px; color: #334155; }
    .url { margin-top: 5mm; font-size: 11px; color: #64748b; word-break: break-all; }
  </style>
</head>
<body>
  <main class="sheet">
    <div class="title">${escapeHtml(title)}</div>
    <div class="meta">机房名称：${escapeHtml(props.room.name)}</div>
    <div class="meta">机房编号：${escapeHtml(props.room.code)}</div>
    <div class="qr">${svgText.value}</div>
    <div class="note">请使用手机扫码登录后进行巡检</div>
    <div class="url">${escapeHtml(info.value.target_url)}</div>
  </main>
</body>
</html>`)
  win.document.close()
  win.focus()
  setTimeout(() => win.print(), 250)
}

function escapeHtml(value: string) {
  return value.replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[ch] || ch))
}

watch(() => props.modelValue, (open) => {
  if (open) loadQr()
})

onBeforeUnmount(revokeSvgUrl)
</script>

<style lang="scss" scoped>
.qr-body {
  min-height: 320px;
}

.qr-warning {
  margin-bottom: 14px;
}

.qr-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 20px;
  align-items: stretch;
}

.qr-preview {
  min-height: 240px;
  border: 1px solid $border-light;
  border-radius: 8px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;

  img {
    width: 204px;
    height: 204px;
  }
}

.qr-empty {
  color: $text-tertiary;
  font-size: 13px;
}

.qr-meta {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.meta-row {
  display: flex;
  flex-direction: column;
  gap: 4px;

  .label {
    font-size: 12px;
    color: $text-tertiary;
  }

  .value {
    color: $text-primary;
    font-size: 16px;
    font-weight: 600;
  }

  .code {
    font-family: Consolas, "Microsoft YaHei", monospace;
  }
}

.scan-note {
  padding: 10px 12px;
  border-radius: 8px;
  background: #F5F7FA;
  color: $text-secondary;
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 640px) {
  .qr-layout {
    grid-template-columns: 1fr;
  }

  .qr-preview {
    min-height: 220px;
  }
}
</style>
