<template>
  <div class="room-list">
    <PageHeader title="机房管理" subtitle="维护机房基础信息和负责人" />

    <div class="page-card">
      <div class="toolbar">
        <el-form :inline="true" class="filter-form">
          <el-form-item>
            <el-input
              v-model="query.keyword"
              placeholder="编号 / 名称 / 区域"
              clearable
              style="width: 240px"
              @clear="onSearch"
              @keyup.enter="onSearch"
            />
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
        <el-button v-if="canEdit" type="primary" :icon="Plus" @click="onCreate">新增机房</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe table-layout="auto">
        <el-table-column prop="code" label="机房编号" width="120" />
        <el-table-column prop="name" label="机房名称" min-width="160" />
        <el-table-column prop="area" label="区域" width="100" />
        <el-table-column prop="owner_name" label="负责人" width="120">
          <template #default="{ row }">
            {{ row.owner_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="联系电话" width="150" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status === 1" type="success" effect="light" size="small">启用</el-tag>
            <el-tag v-else type="info" effect="light" size="small">停用</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" show-overflow-tooltip />
        <el-table-column label="操作" width="330" align="left">
          <template #default="scope">
            <el-button type="primary" link :icon="Cpu" @click="onViewEquipment(scope.row as RoomInfo)">
              查看设备
            </el-button>
            <template v-if="canEdit">
              <el-button type="primary" link :icon="Edit" @click="onEdit(scope.row as RoomInfo)">编辑</el-button>
              <el-button
                :type="(scope.row as RoomInfo).status === 1 ? 'danger' : 'success'"
                link
                :icon="(scope.row as RoomInfo).status === 1 ? CircleClose : CircleCheck"
                @click="onToggleStatus(scope.row as RoomInfo)"
              >
                {{ (scope.row as RoomInfo).status === 1 ? '停用' : '启用' }}
              </el-button>
              <el-button
                type="danger"
                link
                :icon="Delete"
                @click="onDelete(scope.row as RoomInfo)"
              >
                删除
              </el-button>
            </template>
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

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑机房' : '新增机房'"
      width="560px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="机房编号" prop="code">
          <el-input v-model="form.code" :disabled="!!editingId" placeholder="如 JF-OFFICE" />
        </el-form-item>
        <el-form-item label="机房名称" prop="name">
          <el-input v-model="form.name" placeholder="机房中文名" />
        </el-form-item>
        <el-form-item label="所属区域">
          <el-input v-model="form.area" placeholder="如 A 区" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-select v-model="form.owner_id" placeholder="选择负责人" clearable filterable>
            <el-option
              v-for="u in inspectorOptions"
              :key="u.id"
              :label="u.name"
              :value="u.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.phone" placeholder="选填" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="选填" />
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
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  CircleCheck,
  CircleClose,
  Cpu,
  Delete,
  Edit,
  Plus,
  Refresh,
  Search,
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader/index.vue'
import { useUserStore } from '@/stores/user'
import {
  apiRoomCreate,
  apiRoomDelete,
  apiRoomList,
  apiRoomSetStatus,
  apiRoomUpdate,
  type RoomInfo,
} from '@/api/room'
import { apiUserOptions } from '@/api/user'

const userStore = useUserStore()
const router = useRouter()
const canEdit = computed(() => userStore.isAdmin)

function onViewEquipment(row: RoomInfo) {
  router.push(`/rooms/${row.id}/equipment`)
}

interface Query {
  keyword: string
  status: number | null
  page: number
  size: number
}
const query = reactive<Query>({
  keyword: '',
  status: 1,
  page: 1,
  size: 20,
})

const list = ref<RoomInfo[]>([])
const total = ref(0)
const loading = ref(false)

async function fetchList() {
  loading.value = true
  try {
    const data = await apiRoomList({
      keyword: query.keyword || undefined,
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
function onSearch() { query.page = 1; fetchList() }
function onReset() {
  query.keyword = ''
  query.status = 1
  query.page = 1
  fetchList()
}

/* 负责人下拉 */
const inspectorOptions = ref<Array<{ id: number; name: string; role: string }>>([])
async function loadOwnerOptions() {
  try {
    inspectorOptions.value = await apiUserOptions('inspector')
  } catch {
    inspectorOptions.value = []
  }
}

/* 弹窗 */
const dialogVisible = ref(false)
const submitting = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const form = reactive({
  code: '',
  name: '',
  area: '',
  owner_id: undefined as number | undefined,
  phone: '',
  remark: '',
})
const rules: FormRules = {
  code: [{ required: true, message: '请输入机房编号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入机房名称', trigger: 'blur' }],
}

function resetForm() {
  form.code = ''
  form.name = ''
  form.area = ''
  form.owner_id = undefined
  form.phone = ''
  form.remark = ''
  formRef.value?.clearValidate()
}

function onCreate() {
  editingId.value = null
  resetForm()
  if (!inspectorOptions.value.length) loadOwnerOptions()
  dialogVisible.value = true
}

function onEdit(row: RoomInfo) {
  editingId.value = row.id
  resetForm()
  form.code = row.code
  form.name = row.name
  form.area = row.area || ''
  form.owner_id = row.owner_id ?? undefined
  form.phone = row.phone || ''
  form.remark = row.remark || ''
  if (!inspectorOptions.value.length) loadOwnerOptions()
  dialogVisible.value = true
}

async function onSubmit() {
  if (!formRef.value) return
  try { await formRef.value.validate() } catch { return }
  submitting.value = true
  try {
    if (editingId.value) {
      await apiRoomUpdate(editingId.value, {
        name: form.name,
        area: form.area || undefined,
        owner_id: form.owner_id,
        phone: form.phone || undefined,
        remark: form.remark || undefined,
      })
      ElMessage.success('已保存')
    } else {
      await apiRoomCreate({
        code: form.code,
        name: form.name,
        area: form.area || undefined,
        owner_id: form.owner_id,
        phone: form.phone || undefined,
        remark: form.remark || undefined,
      })
      ElMessage.success('已新增')
    }
    dialogVisible.value = false
    fetchList()
  } finally {
    submitting.value = false
  }
}

async function onToggleStatus(row: RoomInfo) {
  const target = row.status === 1 ? 0 : 1
  const text = target === 0 ? '停用' : '启用'
  try {
    await ElMessageBox.confirm(`确定${text}机房「${row.name}」?`, '提示', {
      confirmButtonText: text,
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch { return }
  await apiRoomSetStatus(row.id, target)
  ElMessage.success(`已${text}`)
  fetchList()
}

async function onDelete(row: RoomInfo) {
  try {
    await ElMessageBox.confirm(
      `确定删除机房「${row.name}」? 删除后不可恢复；已有设备或巡检记录的机房不能删除。`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )
  } catch { return }
  await apiRoomDelete(row.id)
  ElMessage.success('已删除')
  if (list.value.length === 1 && query.page > 1) query.page -= 1
  fetchList()
}

onMounted(() => {
  fetchList()
})
</script>

<style lang="scss" scoped>
.room-list { display: flex; flex-direction: column; }
.filter-form { flex: 1; :deep(.el-form-item) { margin-bottom: 0; } }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
