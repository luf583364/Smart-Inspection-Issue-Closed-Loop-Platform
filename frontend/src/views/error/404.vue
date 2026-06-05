<template>
  <div class="not-found">
    <div class="content">
      <div class="code">404</div>
      <div class="text">您访问的页面不存在或已被移除</div>
      <el-button type="primary" @click="$router.replace('/')">返回首页</el-button>
    </div>
  </div>
</template>

<script setup lang="ts"></script>

<style lang="scss" scoped>
.not-found {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg-layout;
}
.content { text-align: center; }
.code {
  font-size: 120px;
  font-weight: 800;
  color: $brand-primary;
  letter-spacing: 4px;
  line-height: 1;
  background: linear-gradient(180deg, $brand-primary 0%, $brand-dark 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.text {
  margin: 16px 0 28px;
  color: $text-secondary;
  font-size: 14px;
}
</style>
