<template>
  <div class="inspection-qr">
    <PageHeader title="巡检入口二维码" subtitle="一张固定二维码，贴在机房现场。巡检员扫码 → 登录 → 选择机房巡检" />

    <div class="page-card" v-loading="loading">
      <el-alert
        v-if="info?.warning"
        class="warn"
        type="warning"
        show-icon
        :closable="false"
        :title="info.warning"
      />

      <div class="layout">
        <div class="preview">
          <img v-if="svgObjectUrl" :src="svgObjectUrl" alt="巡检入口二维码" />
          <div v-else class="empty">二维码加载中…</div>
        </div>

        <div class="meta">
          <div class="steps">
            <div class="step"><span class="n">1</span> 打印这张二维码，贴在机房入口/巡检点</div>
            <div class="step"><span class="n">2</span> 巡检员用手机扫码，自动打开登录页</div>
            <div class="step"><span class="n">3</span> 登录后选择当前机房，逐台设备巡检并提交</div>
            <div class="step"><span class="n">4</span> 提交后，管理员即可在「巡检记录」中查看数据与报告</div>
          </div>

          <div class="url-row">
            <span class="label">扫码地址</span>
            <el-input :model-value="info?.target_url || ''" readonly>
              <template #append>
                <el-button :icon="DocumentCopy" @click="copyUrl" />
              </template>
            </el-input>
          </div>

          <div class="note">二维码为固定地址，不含账号、密码或 Token；更换服务器地址后会自动更新。</div>

          <div class="actions">
            <el-button :icon="Refresh" @click="load" :loading="loading">刷新</el-button>
            <el-button :icon="Download" :disabled="!info?.printable" @click="download('svg')">下载 SVG</el-button>
            <el-button :icon="Download" :disabled="!info?.printable" @click="download('png')">下载 PNG</el-button>
            <el-button type="primary" :icon="Printer" :disabled="!info?.printable" @click="printQr">打印</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { DocumentCopy, Download, Printer, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/PageHeader/index.vue'
import { apiInspectionQrBlob, apiInspectionQrInfo, type InspectionQrInfo } from '@/api/inspectionEntry'

const loading = ref(false)
const info = ref<InspectionQrInfo | null>(null)
const svgObjectUrl = ref('')
const svgText = ref('')

function revoke() {
  if (svgObjectUrl.value) {
    URL.revokeObjectURL(svgObjectUrl.value)
    svgObjectUrl.value = ''
  }
}

async function load() {
  loading.value = true
  try {
    info.value = await apiInspectionQrInfo()
    const svg = await apiInspectionQrBlob('svg')
    revoke()
    svgObjectUrl.value = URL.createObjectURL(svg)
    svgText.value = await svg.text()
  } finally {
    loading.value = false
  }
}

async function download(format: 'svg' | 'png') {
  if (!info.value?.printable) return
  const blob = format === 'svg' && svgText.value
    ? new Blob([svgText.value], { type: 'image/svg+xml' })
    : await apiInspectionQrBlob(format)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `inspection-entry-qr.${format}`
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
  if (!info.value?.printable || !svgText.value) return
  const win = window.open('', '_blank', 'width=720,height=900')
  if (!win) {
    ElMessage.warning('浏览器阻止了打印窗口')
    return
  }
  const title = import.meta.env.VITE_APP_TITLE || '机房巡检系统'
  win.document.write(`<!doctype html>
<html><head><meta charset="utf-8" /><title>巡检入口二维码</title>
<style>
  body { margin:0; font-family:"Microsoft YaHei",sans-serif; color:#0f172a; }
  .sheet { width:148mm; min-height:210mm; padding:18mm; box-sizing:border-box; text-align:center; }
  .title { font-size:24px; font-weight:700; margin-bottom:4mm; }
  .sub { font-size:14px; color:#475569; margin-bottom:12mm; }
  .qr { width:96mm; height:96mm; margin:0 auto; }
  .qr svg { width:100%; height:100%; }
  .tip { margin-top:10mm; font-size:15px; color:#334155; }
  .url { margin-top:6mm; font-size:11px; color:#94a3b8; word-break:break-all; }
</style></head>
<body><main class="sheet">
  <div class="title">${escapeHtml(title)}</div>
  <div class="sub">扫码进行机房巡检</div>
  <div class="qr">${svgText.value}</div>
  <div class="tip">请使用手机扫码，登录后选择机房进行巡检</div>
  <div class="url">${escapeHtml(info.value.target_url)}</div>
</main></body></html>`)
  win.document.close()
  win.focus()
  setTimeout(() => win.print(), 250)
}

function escapeHtml(v: string) {
  return v.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] || c))
}

onMounted(load)
onBeforeUnmount(revoke)
</script>

<style lang="scss" scoped>
.warn { margin-bottom: 16px; }

.layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 28px;
  align-items: start;
}

.preview {
  width: 280px;
  height: 280px;
  border: 1px solid $border-light;
  border-radius: 10px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;

  img { width: 248px; height: 248px; }
  .empty { color: $text-tertiary; font-size: 13px; }
}

.meta { display: flex; flex-direction: column; gap: 16px; }

.steps {
  display: flex;
  flex-direction: column;
  gap: 10px;

  .step {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
    color: $text-secondary;
    .n {
      flex-shrink: 0;
      width: 22px; height: 22px;
      border-radius: 50%;
      background: $brand-light;
      color: $brand-primary;
      display: flex; align-items: center; justify-content: center;
      font-size: 12px; font-weight: 600;
    }
  }
}

.url-row {
  .label { display: block; font-size: 12px; color: $text-tertiary; margin-bottom: 6px; }
}

.note {
  font-size: 12px;
  color: $text-tertiary;
  background: $bg-hover;
  padding: 10px 12px;
  border-radius: 8px;
}

.actions { display: flex; gap: 10px; flex-wrap: wrap; }

@media (max-width: 720px) {
  .layout { grid-template-columns: 1fr; }
  .preview { width: 100%; }
}
</style>
