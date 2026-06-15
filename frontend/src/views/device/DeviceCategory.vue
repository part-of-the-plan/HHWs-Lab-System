<template>
  <div>
    <el-card>
      <div style="margin-bottom:12px">
        <el-button v-if="userStore.hasPermission('category:manage')" type="primary" @click="openAdd">
          + 添加分类
        </el-button>
      </div>

      <el-table :data="list" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="分类名称" min-width="160" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column label="操作" width="160" v-if="userStore.hasPermission('category:manage')">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" link @click="doDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑分类' : '添加分类'"
      width="420px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.loading" @click="doSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '../../utils/request'
import { userStore } from '../../stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const list = ref([])
const loading = ref(false)

const dialog = reactive({ visible: false, isEdit: false, loading: false })
const formRef = ref(null)
const form = reactive({ id: null, name: '', description: '' })
const rules = { name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }] }

async function fetchList() {
  loading.value = true
  try {
    const res = await request.get('/categories')
    list.value = res.data || []
  } catch { /* ignore */ }
  finally { loading.value = false }
}

function openAdd() {
  dialog.isEdit = false
  resetForm()
  dialog.visible = true
}

function openEdit(row) {
  dialog.isEdit = true
  form.id = row.id
  form.name = row.name
  form.description = row.description || ''
  dialog.visible = true
}

function resetForm() {
  form.id = null; form.name = ''; form.description = ''
  formRef.value?.resetFields()
}

async function doSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  dialog.loading = true
  try {
    const data = { name: form.name, description: form.description }
    if (dialog.isEdit) {
      await request.put(`/categories/${form.id}`, data)
      ElMessage.success('已更新')
    } else {
      await request.post('/categories', data)
      ElMessage.success('分类添加成功')
    }
    dialog.visible = false
    fetchList()
  } catch { /* ignore */ }
  finally { dialog.loading = false }
}

async function doDelete(row) {
  // 1. 二次确认（取消则静默返回）
  try {
    await ElMessageBox.confirm(
      `确认删除分类「${row.name}」？`, '删除确认',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
    )
  } catch {
    return // 用户主动取消
  }

  // 2. 执行删除（失败原因由拦截器统一弹出，如"分类下还有设备"）
  try {
    await request.delete(`/categories/${row.id}`)
    ElMessage.success('分类已删除')
    fetchList()
  } catch { /* 拦截器已弹出错误原因 */ }
}

onMounted(fetchList)
</script>
