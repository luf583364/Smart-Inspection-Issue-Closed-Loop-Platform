<template>
  <div class="equipment-list">
    <PageHeader title="设备管理" subtitle="维护机房中的可巡检设备" />

    <div class="page-card">
      <div class="toolbar">
        <el-form :inline="true" class="filter-form">
          <el-form-item>
            <el-input
              v-model="query.keyword"
              placeholder="编号 / 名称 / 位置"
              clearable
              style="width: 220px"
              @clear="onSearch"
              @keyup.enter="onSearch"
            />
          </el-form-item>
          <el-form-item>
            <el-select v-model="query.room_id" placeholder="所属机房" clearable filterable style="width: 180px">
              <el-option
                v-for="r in roomOptions"
                :key="r.id"
                :label="`${r.code} · ${r.name}`"
                :value="r.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-select v-model="query.equipment_type" placeholder="设备类型" clearable style="width: 160px">
              <el-option v-for="t in equipmentTypes" :key="t.code" :label="t.label" :value="t.code" />
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
        <el-button v-if="canEdit" type="primary" :icon="Plus" @click="onCreate">新增设备</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="equipment_code" label="设备编号" width="170" />
        <el-table-column prop="equipment_name" label="设备名称" min-width="160" />
        <el-table-column label="设备类型" width="130">
          <template #default="{ row }">
            <el-tag size="small" effect="light">{{ row.equipment_type_label || row.equipment_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="所属机房" min-width="160">
          <template #default="{ row }">
            <span v-if="row.room_name">
              <el-link type="primary" @click="goRoomEquipment(row.room_id)">{{ row.room_name }}</el-link>
              <span class="code">{{ row.room_code }}</span>
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="安装位置" min-width="140">
          <template #default="{ row }">{{ row.location || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status === 1" type="success" effect="light" size="small">启用</el-tag>
            <el-tag v-else type="info" effect="light" size="small">停用</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="200" v-if="canEdit">
          <template #default="scope">
            <el-button type="primary" link :icon="Edit" @click="onEdit(scope.row as EquipmentInfo)">编辑</el-button>
            <el-button
              :type="(scope.row as EquipmentInfo).status === 1 ? 'danger' : 'success'"
              link
              :icon="(scope.row as EquipmentInfo).status === 1 ? CircleClose : CircleCheck"
              @click="onToggleStatus(scope.row as EquipmentInfo)"
            >
              {{ (scope.row as EquipmentInfo).status === 1 ? '停用' : '启用' }}
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

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑设备' : '新增设备'"
      width="560px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="设备编号" prop="equipment_code">
          <el-input v-model="form.equipment_code" :disabled="!!editingId" placeholder="如 EQ-A01-UPS-01" />
        </el-form-item>
        <el-form-item label="设备名称" prop="equipment_name">
          <el-input v-model="form.equipment_name" />
        </el-form-item>
        <el-form-item label="设备类型" prop="equipment_type">
          <el-select v-model="form.equipment_type" placeholder="选择类型" filterable>
            <el-option v-for="t in equipmentTypes" :key="t.code" :label="t.label" :value="t.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属机房" prop="room_id">
          <el-select v-model="form.room_id" placeholder="选择机房" filterable>
            <el-option
              v-for="r in roomOptions"
              :key="r.id"
              :label="`${r.code} · ${r.name}`"
              :value="r.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="安装位置">
          <el-input v-model="form.location" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" />
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
  apiEquipmentCreate,
  apiEquipmentList,
  apiEquipmentSetStatus,
  apiEquipmentTypes,
  apiEquipmentUpdate,
  type EquipmentInfo,
} from '@/api/equipment'
import { apiRoomOptions } from '@/api/room'

const router = useRouter()
const userStore = useUserStore()
const canEdit = computed(() => userStore.isAdmin)

interface Query {
  keyword: string
  room_id: number | null
  equipment_type: string
  status: number | null
  page: number
  size: number
}
const query = reactive<Query>({
  keyword: '',
  room_id: null,
  equipment_type: '',
  status: null,
  page: 1,
  size: 20,
})

const list = ref<EquipmentInfo[]>([])
const total = ref(0)
const loading = ref(false)

const equipmentTypes = ref<Array<{ code: string; label: string }>>([])
const roomOptions = ref<Array<{ id: number; code: string; name: string }>>([])

async function fetchList() {
  loading.value = true
  try {
    const data = await apiEquipmentList({
      keyword: query.keyword || undefined,
      room_id: query.room_id ?? undefined,
      equipment_type: query.equipment_type || undefined,
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
  query.room_id = null
  query.equipment_type = ''
  query.status = null
  query.page = 1
  fetchList()
}

function goRoomEquipment(roomId: number) {
  router.push(`/rooms/${roomId}/equipment`)
}

/* ----------- dialog ----------- */
const dialogVisible = ref(false)
const submitting = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const form = reactive({
  equipment_code: '',
  equipment_name: '',
  equipment_type: '',
  room_id: undefined as number | undefined,
  location: '',
  remark: '',
})
const rules: FormRules = {
  equipment_code: [{ required: true, message: '请输入设备编号', trigger: 'blur' }],
  equipment_name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  equipment_type: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
  room_id: [{ required: true, message: '请选择所属机房', trigger: 'change' }],
}

function resetForm() {
  form.equipment_code = ''
  form.equipment_name = ''
  form.equipment_type = ''
  form.room_id = undefined
  form.location = ''
  form.remark = ''
  formRef.value?.clearValidate()
}

function onCreate() {
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function onEdit(row: EquipmentInfo) {
  editingId.value = row.id
  resetForm()
  form.equipment_code = row.equipment_code
  form.equipment_name = row.equipment_name
  form.equipment_type = row.equipment_type
  form.room_id = row.room_id
  form.location = row.location || ''
  form.remark = row.remark || ''
  dialogVisible.value = true
}

async function onSubmit() {
  if (!formRef.value) return
  try { await formRef.value.validate() } catch { return }
  submitting.value = true
  try {
    if (editingId.value) {
      await apiEquipmentUpdate(editingId.value, {
        equipment_name: form.equipment_name,
        equipment_type: form.equipment_type,
        room_id: form.room_id,
        location: form.location || undefined,
        remark: form.remark || undefined,
      })
      ElMessage.success('已保存')
    } else {
      await apiEquipmentCreate({
        equipment_code: form.equipment_code,
        equipment_name: form.equipment_name,
        equipment_type: form.equipment_type,
        room_id: form.room_id!,
        location: form.location || undefined,
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

async function onToggleStatus(row: EquipmentInfo) {
  const target = row.status === 1 ? 0 : 1
  const text = target === 0 ? '停用' : '启用'
  try {
    await ElMessageBox.confirm(`确定${text}设备「${row.equipment_name}」?`, '提示', {
      confirmButtonText: text,
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch { return }
  await apiEquipmentSetStatus(row.id, target)
  ElMessage.success(`已${text}`)
  fetchList()
}

onMounted(async () => {
  ;[equipmentTypes.value, roomOptions.value] = await Promise.all([
    apiEquipmentTypes(),
    apiRoomOptions(),
  ])
  fetchList()
})
</script>

<style lang="scss" scoped>
.equipment-list { display: flex; flex-direction: column; }
.filter-form { flex: 1; :deep(.el-form-item) { margin-bottom: 0; } }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
.code { font-size: 11px; color: $text-tertiary; margin-left: 6px; }
</style>
