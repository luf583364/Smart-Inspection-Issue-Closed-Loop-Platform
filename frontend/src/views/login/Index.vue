<template>
  <div class="login-page">
    <!-- 左侧 -->
    <section class="hero">
      <div class="grid-bg" />
      <div class="hero-content">
        <div class="hero-logo">
          <el-icon :size="22"><Cpu /></el-icon>
        </div>
        <h1 class="hero-title">机房智能巡检<br />与问题闭环管理系统</h1>
        <p class="hero-sub">Smart Inspection & Issue Closed-Loop Platform</p>

        <ul class="features">
          <li>
            <el-icon class="ic"><CircleCheck /></el-icon>
            <div>
              <div class="f-title">全流程闭环</div>
              <div class="f-desc">巡检 · 转发 · 处理 · 核实 · 归档</div>
            </div>
          </li>
          <li>
            <el-icon class="ic"><DataLine /></el-icon>
            <div>
              <div class="f-title">可视化看板</div>
              <div class="f-desc">实时掌握巡检与问题处理态势</div>
            </div>
          </li>
          <li>
            <el-icon class="ic"><LocationFilled /></el-icon>
            <div>
              <div class="f-title">多机房统一管理</div>
              <div class="f-desc">按区域、机房、责任人一目了然</div>
            </div>
          </li>
        </ul>
      </div>
      <div class="hero-foot">© 2026 Smart Inspection System</div>
    </section>

    <!-- 右侧 -->
    <section class="form-side">
      <div class="card">
        <div class="card-head">
          <div class="card-title">欢迎登录</div>
          <div class="card-sub">请使用您的账号登录后台</div>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          size="large"
          @keyup.enter.prevent="onSubmit"
          @submit.prevent
        >
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入账号"
              :prefix-icon="UserFilled"
              clearable
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>

          <el-button
            type="primary"
            native-type="button"
            class="submit-btn"
            :loading="loading"
            @click="onSubmit"
          >
            登&nbsp;&nbsp;录
          </el-button>
        </el-form>

      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  CircleCheck,
  Cpu,
  DataLine,
  LocationFilled,
  Lock,
  UserFilled,
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { isMobileDevice, sanitizeRedirect } from '@/router/guards'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const form = reactive({ username: '', password: '' })
const loading = ref(false)

const rules: FormRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function onSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  loading.value = true
  try {
    await userStore.login(form.username, form.password)
    ElMessage.success(`欢迎回来，${userStore.user?.name || ''}`)
    const safe = sanitizeRedirect(route.query.redirect)
    const canInspect = ['admin', 'inspector'].includes(userStore.role)
    // 手机端可巡检角色：登录后直接进巡检首页（不进后台），除非本就是要去某个 /mobile 页面
    if (isMobileDevice() && canInspect && (!safe || !safe.startsWith('/mobile'))) {
      router.replace('/mobile/inspection')
    } else {
      router.replace(safe ?? '/dashboard')
    }
  } catch {
    // 拦截器已 toast
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  display: flex;
  min-height: 100vh;
  background: $bg-card;
}

/* ---------------- 左侧 hero ---------------- */
.hero {
  flex: 1.1;
  position: relative;
  background:
    radial-gradient(circle at 80% 20%, rgba(77, 125, 255, 0.35) 0%, transparent 40%),
    radial-gradient(circle at 20% 80%, rgba(30, 94, 255, 0.25) 0%, transparent 40%),
    linear-gradient(135deg, #0F2547 0%, #0B1A36 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 48px 64px;
  overflow: hidden;

  .grid-bg {
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
    background-size: 48px 48px;
    pointer-events: none;
    mask-image: radial-gradient(ellipse at center, #000 30%, transparent 80%);
  }
}
.hero-content { position: relative; }
.hero-logo {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: linear-gradient(135deg, $brand-primary 0%, #4D7DFF 100%);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 8px 28px rgba(30, 94, 255, 0.35);
}
.hero-title {
  margin: 24px 0 8px;
  font-size: 34px;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: 1px;
}
.hero-sub {
  margin: 0 0 36px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 2px;
}

.features {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;

  li {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 16px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    backdrop-filter: blur(8px);
  }
  .ic {
    width: 36px; height: 36px;
    border-radius: 8px;
    background: rgba(77, 125, 255, 0.18);
    color: #6FA0FF;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
  }
  .f-title { font-size: 14px; font-weight: 500; }
  .f-desc  { font-size: 12px; color: rgba(255, 255, 255, 0.5); margin-top: 2px; }
}

.hero-foot {
  position: relative;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  letter-spacing: 1px;
}

/* ---------------- 右侧表单 ---------------- */
.form-side {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
}
.card {
  width: 100%;
  max-width: 380px;
}
.card-head {
  margin-bottom: 28px;
  .card-title {
    font-size: 24px;
    font-weight: 600;
    color: $text-primary;
  }
  .card-sub {
    margin-top: 6px;
    font-size: 13px;
    color: $text-secondary;
  }
}
.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  letter-spacing: 4px;
  background: linear-gradient(90deg, $brand-primary 0%, #4D7DFF 100%);
  border: none;
  margin-top: 8px;
  box-shadow: 0 6px 16px rgba(30, 94, 255, 0.25);
}

/* 小屏隐藏 hero */
@media (max-width: 960px) {
  .hero { display: none; }
}
</style>
