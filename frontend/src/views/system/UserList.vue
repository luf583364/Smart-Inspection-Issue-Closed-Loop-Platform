<template>
  <div class="user-list">
    <PageHeader title="用户管理" subtitle="维护系统账号、角色与启用状态" />

    <div class="page-card">
      <!-- 工具栏 -->
      <div class="toolbar">
        <el-form :inline="true" class="filter-form">
          <el-form-item>
            <el-input
              v-model="query.keyword"
              placeholder="账号 / 姓名"
              clearable
              style="width: 200px"
              @clear="onSearch"
              @keyup.enter="onSearch"
            />
          </el-form-item>
          <el-form-item>
            <el-select v-model="query.role" placeholder="角色" clearable style="width: 140px">
              <el-option label="管理员" value="admin" />
              <el-option label="巡检员" value="inspector" />
              <el-option label="处理员" value="handler" />
              <el-option label="核实员" value="verifier" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-select v-model="query.status" placeholder="状态" clearable style="width: 120px">
              <el-option label="启用" :value="1" />
              <el-option label="停用" :value="0" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :icon="Search" @click="onSearch">查询</el-button>
            <el-button :icon="Refresh" @click="onReset">重置</el-button>
          </el-form-item>
        </el-form>
        <el-button type="primary" :icon="Plus" @click="onCreate">新增用户</el-button>
      </div>

      <!-- 表格 -->
      <el-table :data="list" v-loading="loading" stripe table-layout="auto">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="账号" min-width="140" />
        <el-table-column prop="name" label="姓名" min-width="120" />
        <el-table-column label="角色" width="110">
          <template #default="{ row }">
            <el-tag :type="ROLE_TAG[row.role]" effect="light" size="small">
              {{ ROLE_LABEL[row.role] || row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="联系方式" min-width="150" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.status === 1" type="success" effect="light" size="small">启用</el-tag>
            <el-tag v-else type="info" effect="light" size="small">停用</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260" align="left">
          <template #default="scope">
            <el-button type="primary" link :icon="Edit" @click="onEdit(scope.row as UserInfo)">编辑</el-button>
            <el-button
              :type="(scope.row as UserInfo).status === 1 ? 'danger' : 'success'"
              link
              :icon="(scope.row as UserInfo).status === 1 ? CircleClose : CircleCheck"
              @click="onToggleStatus(scope.row as UserInfo)"
            >
              {{ (scope.row as UserInfo).status === 1 ? '停用' : '启用' }}
            </el-button>
            <el-button
              type="danger"
              link
              :icon="Delete"
              @click="onDelete(scope.row as UserInfo)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="query.page"
          v-model:page-size="query.size"
          :page-sizes="[10, 20, 50]"
          :total="total"
          background
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchList"
          @current-change="fetchList"
        />
      </div>
    </div>

    <!-- 新增 / 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑用户' : '新增用户'"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="90px"
        size="default"
      >
        <el-form-item label="账号" prop="username">
          <el-input
            v-model="form.username"
            :disabled="!!editingId"
            placeholder="登录账号，4-50 字符"
          />
        </el-form-item>
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" placeholder="选择角色">
            <el-option label="管理员" value="admin" />
            <el-option label="巡检员" value="inspector" />
            <el-option label="处理员" value="handler" />
            <el-option label="核实员" value="verifier" />
          </el-select>
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input v-model="form.phone" placeholder="选填" />
        </el-form-item>
        <el-form-item label="密码" :prop="editingId ? '' : 'password'">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="editingId ? '留空则不修改' : '至少 4 位'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import {
  CircleCheck,
  CircleClose,
  Delete,
  Edit,
  Plus,
  Refresh,
  Search,
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader/index.vue'
import { ROLE_LABEL, formatDateTime } from '@/utils/format'
import type { UserInfo } from '@/api/auth'
import {
  apiUserCreate,
  apiUserDelete,
  apiUserList,
  apiUserSetStatus,
  apiUserUpdate,
} from '@/api/user'

const ROLE_TAG: Record<string, 'primary' | 'success' | 'warning' | 'info'> = {
  admin: 'primary',
  inspector: 'success',
  handler: 'warning',
  verifier: 'info',
}

interface Query {
  keyword: string
  role: string
  status: number | null
  page: number
  size: number
}

const query = reactive<Query>({
  keyword: '',
  role: '',
  status: null,
  page: 1,
  size: 20,
})

const list = ref<UserInfo[]>([])
const total = ref(0)
const loading = ref(false)

async function fetchList() {
  loading.value = true
  try {
    const data = await apiUserList({
      keyword: query.keyword || undefined,
      role: query.role || undefined,
      status: query.status ?? undefined,
      page: query.page,
      size: query.size,
    })
    list.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  query.page = 1
  fetchList()
}
function onReset() {
  query.keyword = ''
  query.role = ''
  query.status = null
  query.page = 1
  fetchList()
}

/* ------------- 弹窗 ------------- */
const dialogVisible = ref(false)
const submitting = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const form = reactive({
  username: '',
  name: '',
  role: 'inspector',
  phone: '',
  password: '',
})
const rules: FormRules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 4, message: '至少 4 位', trigger: 'blur' }],
}

function resetForm() {
  form.username = ''
  form.name = ''
  form.role = 'inspector'
  form.phone = ''
  form.password = ''
  formRef.value?.clearValidate()
}

function onCreate() {
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function onEdit(row: UserInfo) {
  editingId.value = row.id
  resetForm()
  form.username = row.username
  form.name = row.name
  form.role = row.role
  form.phone = row.phone || ''
  dialogVisible.value = true
}

async function onSubmit() {
  if (!formRef.value) return
  try {
    if (editingId.value) {
      // 编辑时密码可空
      await formRef.value.validateField(['name', 'role'])
    } else {
      await formRef.value.validate()
    }
  } catch {
    return
  }
  submitting.value = true
  try {
    if (editingId.value) {
      const payload: Record<string, unknown> = {
        name: form.name,
        role: form.role,
        phone: form.phone || undefined,
      }
      if (form.password) payload.password = form.password
      await apiUserUpdate(editingId.value, payload)
      ElMessage.success('已保存')
    } else {
      await apiUserCreate({
        username: form.username,
        password: form.password,
        name: form.name,
        role: form.role,
        phone: form.phone || undefined,
      })
      ElMessage.success('已新增')
    }
    dialogVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

async function onToggleStatus(row: UserInfo) {
  const target = row.status === 1 ? 0 : 1
  const text = target === 0 ? '停用' : '启用'
  try {
    await ElMessageBox.confirm(`确定${text}用户「${row.name}」?`, '提示', {
      confirmButtonText: text,
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch { return }
  await apiUserSetStatus(row.id, target)
  ElMessage.success(`已${text}`)
  fetchList()
}

async function onDelete(row: UserInfo) {
  try {
    await ElMessageBox.confirm(
      `确定删除用户「${row.name}」? 删除后不可恢复；已有巡检记录或仍是机房负责人的用户不能删除。`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )
  } catch { return }
  await apiUserDelete(row.id)
  ElMessage.success('已删除')
  if (list.value.length === 1 && query.page > 1) query.page -= 1
  fetchList()
}

onMounted(fetchList)
</script>

<style lang="scss" scoped>
.user-list {
  display: flex;
  flex-direction: column;
}
.filter-form {
  flex: 1;
  :deep(.el-form-item) { margin-bottom: 0; }
}
.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
