<template>
  <div class="room-equipment">
    <PageHeader :title="pageTitle" :subtitle="pageSub">
      <template #actions>
        <el-button :icon="ArrowLeft" @click="$router.push('/basic/rooms')">返回机房列表</el-button>
      </template>
    </PageHeader>

    <div class="page-card">
      <div class="info-grid" v-if="roomData">
        <div class="kv"><span class="k">机房编号</span><span class="v">{{ roomData.code }}</span></div>
        <div class="kv"><span class="k">所属区域</span><span class="v">{{ roomData.area || '-' }}</span></div>
        <div class="kv"><span class="k">设备数量</span><span class="v">{{ total }} 台</span></div>
      </div>

      <div class="toolbar">
        <div class="section-title">设备清单</div>
        <el-button v-if="canEdit" type="primary" :icon="Plus" @click="onCreate">新增设备</el-button>
      </div>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="equipment_code" label="设备编号" width="160" />
        <el-table-column prop="equipment_name" label="设备名称" min-width="160" />
        <el-table-column label="设备类型" width="130">
          <template #default="{ row }">
            <el-tag size="small" effect="light">{{ row.equipment_type_label }}</el-tag>
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
        <el-table-column prop="remark" label="备注" show-overflow-tooltip />
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
          <el-input v-model="form.equipment_name" placeholder="设备名称" />
        </el-form-item>
        <el-form-item label="设备类型" prop="equipment_type">
          <el-select v-model="form.equipment_type" placeholder="选择类型" filterable>
            <el-option v-for="t in equipmentTypes" :key="t.code" :label="t.label" :value="t.code" />
          </el-select>
        </el-form-item>
        <el-form-item label="安装位置">
          <el-input v-model="form.location" placeholder="例如 A 区动力间" />
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
import { useRoute } from 'vue-router'
import {
  ArrowLeft,
  CircleCheck,
  CircleClose,
  Edit,
  Plus,
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageHeader from '@/components/PageHeader/index.vue'
import { useUserStore } from '@/stores/user'
import {
  apiEquipmentCreate,
  apiEquipmentSetStatus,
  apiEquipmentTypes,
  apiEquipmentUpdate,
  apiRoomEquipment,
  type EquipmentInfo,
} from '@/api/equipment'

const route = useRoute()
const userStore = useUserStore()
const canEdit = computed(() => userStore.isAdmin)

const roomId = computed(() => Number(route.params.roomId))
const roomData = ref<{ id: number; code: string; name: string; area?: string; status?: number } | null>(null)
const list = ref<EquipmentInfo[]>([])
const total = ref(0)
const loading = ref(false)

const pageTitle = computed(() => roomData.value ? `${roomData.value.name} · 设备清单` : '机房设备')
const pageSub = computed(() => roomData.value ? `查看与管理「${roomData.value.name}」中的设备` : '')

const equipmentTypes = ref<Array<{ code: string; label: string }>>([])

async function fetchTypes() {
  equipmentTypes.value = await apiEquipmentTypes()
}

async function fetchList() {
  loading.value = true
  try {
    const data = await apiRoomEquipment(roomId.value)
    roomData.value = data.room
    list.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
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
  location: '',
  remark: '',
})
const rules: FormRules = {
  equipment_code: [{ required: true, message: '请输入设备编号', trigger: 'blur' }],
  equipment_name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  equipment_type: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
}

function resetForm() {
  form.equipment_code = ''
  form.equipment_name = ''
  form.equipment_type = ''
  form.location = ''
  form.remark = ''
  formRef.value?.clearValidate()
}

function onCreate() {
  editingId.value = null
  resetForm()
  if (!equipmentTypes.value.length) fetchTypes()
  dialogVisible.value = true
}

function onEdit(row: EquipmentInfo) {
  editingId.value = row.id
  resetForm()
  form.equipment_code = row.equipment_code
  form.equipment_name = row.equipment_name
  form.equipment_type = row.equipment_type
  form.location = row.location || ''
  form.remark = row.remark || ''
  if (!equipmentTypes.value.length) fetchTypes()
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
        location: form.location || undefined,
        remark: form.remark || undefined,
      })
      ElMessage.success('已保存')
    } else {
      await apiEquipmentCreate({
        equipment_code: form.equipment_code,
        equipment_name: form.equipment_name,
        equipment_type: form.equipment_type,
        room_id: roomId.value,
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

onMounted(() => {
  fetchList()
  fetchTypes()
})
</script>

<style lang="scss" scoped>
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
  padding: 4px 0 16px;
  border-bottom: 1px dashed $border-light;
  margin-bottom: 16px;

  .kv {
    display: flex; flex-direction: column;
    .k { font-size: 12px; color: $text-tertiary; }
    .v { font-size: 14px; color: $text-primary; font-weight: 500; margin-top: 4px; }
  }
}
.section-title { margin: 0; }
</style>
