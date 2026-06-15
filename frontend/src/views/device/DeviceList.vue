<template>
  <div>
    <!-- 搜索栏 -->
    <el-card style="margin-bottom:16px">
      <el-form :inline="true" :model="filter" size="default">
        <el-form-item label="设备名称">
          <el-input v-model="filter.keyword" placeholder="输入名称搜索" clearable />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="filter.category_id" placeholder="全部分类" clearable style="width:160px">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filter.status" placeholder="全部状态" clearable style="width:140px">
            <el-option label="空闲" value="IDLE" />
            <el-option label="借出" value="BORROWED" />
            <el-option label="维修中" value="REPAIRING" />
            <el-option label="已报废" value="SCRAPPED" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="doSearch">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card>
      <div style="margin-bottom:12px">
        <el-button v-if="userStore.hasPermission('device:create')" type="primary" @click="openAdd">
          + 添加设备
        </el-button>
      </div>

      <el-table :data="list" border stripe v-loading="loading">
        <el-table-column prop="device_no" label="设备编号" width="160" />
        <el-table-column prop="name" label="设备名称" min-width="140" />
        <el-table-column prop="model" label="型号" width="120" />
        <el-table-column prop="category_name" label="分类" width="120" />
        <el-table-column prop="location" label="位置" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button v-if="userStore.hasPermission('device:update')"
              size="small" type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button v-if="userStore.hasPermission('device:delete')"
              size="small" type="danger" link @click="doDelete(row)">删除</el-button>
            <el-button v-if="userStore.hasPermission('borrow:apply') && row.status==='IDLE'"
              size="small" type="success" link @click="goBorrow(row)">借用</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pager.page"
        v-model:page-size="pager.per_page"
        :total="pager.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchList"
        @current-change="fetchList"
        style="margin-top:16px; justify-content:flex-end"
      />
    </el-card>

    <!-- 添加/编辑弹窗 -->
    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑设备' : '添加设备'"
      width="520px" @close="resetForm">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="型号">
          <el-input v-model="form.model" />
        </el-form-item>
        <el-form-item label="分类" prop="category_id">
          <el-select v-model="form.category_id" placeholder="请选择分类" style="width:100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="位置">
          <el-input v-model="form.location" />
        </el-form-item>
        <el-form-item label="状态" v-if="dialog.isEdit">
          <el-select v-model="form.status" style="width:100%">
            <el-option label="空闲" value="IDLE" />
            <el-option label="借出" value="BORROWED" />
            <el-option label="维修中" value="REPAIRING" />
            <el-option label="已报废" value="SCRAPPED" />
          </el-select>
        </el-form-item>
        <el-form-item label="购买日期">
          <el-date-picker v-model="form.purchase_date" type="date" placeholder="选择日期"
            value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="资产价值">
          <el-input-number v-model="form.asset_value" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="图片URL">
          <el-input v-model="form.image_url" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
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
import { useRouter } from 'vue-router'
import request from '../../utils/request'
import { userStore } from '../../stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

// 分类列表
const categories = ref([])

// 筛选
const filter = reactive({ keyword: '', category_id: null, status: '' })

// 分页
const pager = reactive({ page: 1, per_page: 10, total: 0 })

// 列表
const list = ref([])
const loading = ref(false)

// 弹窗
const dialog = reactive({ visible: false, isEdit: false, loading: false })
const formRef = ref(null)
const form = reactive({
  id: null, name: '', model: '', category_id: null,
  location: '', status: 'IDLE', purchase_date: '',
  asset_value: null, image_url: '', remark: '',
})
const rules = {
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
}

// 状态映射
const statusMap = { IDLE: '空闲', BORROWED: '借出', REPAIRING: '维修中', SCRAPPED: '已报废' }
const statusTypeMap = { IDLE: 'success', BORROWED: 'warning', REPAIRING: 'danger', SCRAPPED: 'info' }
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }

// 获取分类
async function fetchCategories() {
  try {
    const res = await request.get('/categories')
    categories.value = res.data.items || res.data || []
  } catch { /* ignore */ }
}

// 获取列表
async function fetchList() {
  loading.value = true
  try {
    const params = { page: pager.page, per_page: pager.per_page }
    if (filter.keyword) params.keyword = filter.keyword
    if (filter.category_id) params.category_id = filter.category_id
    if (filter.status) params.status = filter.status
    const res = await request.get('/devices', { params })
    list.value = res.data.items
    pager.total = res.data.total
  } catch { /* ignore */ }
  finally { loading.value = false }
}

function doSearch() {
  pager.page = 1
  fetchList()
}

function resetFilter() {
  filter.keyword = ''
  filter.category_id = null
  filter.status = ''
  doSearch()
}

// 添加
function openAdd() {
  dialog.isEdit = false
  resetForm()
  dialog.visible = true
}

// 编辑
function openEdit(row) {
  dialog.isEdit = true
  form.id = row.id
  form.name = row.name
  form.model = row.model || ''
  form.category_id = row.category_id
  form.location = row.location || ''
  form.status = row.status
  form.purchase_date = row.purchase_date || ''
  form.asset_value = row.asset_value
  form.image_url = row.image_url || ''
  form.remark = row.remark || ''
  dialog.visible = true
}

function resetForm() {
  form.id = null
  form.name = ''
  form.model = ''
  form.category_id = null
  form.location = ''
  form.status = 'IDLE'
  form.purchase_date = ''
  form.asset_value = null
  form.image_url = ''
  form.remark = ''
  formRef.value?.resetFields()
}

// 提交
async function doSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  dialog.loading = true
  try {
    const data = {
      name: form.name, model: form.model, category_id: form.category_id,
      location: form.location, purchase_date: form.purchase_date,
      asset_value: form.asset_value, image_url: form.image_url, remark: form.remark,
    }
    if (dialog.isEdit) {
      data.status = form.status
      await request.put(`/devices/${form.id}`, data)
      ElMessage.success('设备已更新')
    } else {
      data.status = 'IDLE'
      await request.post('/devices', data)
      ElMessage.success('设备添加成功')
    }
    dialog.visible = false
    fetchList()
  } catch { /* ignore */ }
  finally { dialog.loading = false }
}

// 删除
async function doDelete(row) {
  // 1. 二次确认（取消则静默返回）
  try {
    await ElMessageBox.confirm(
      `确认删除设备「${row.name}」？删除后不可恢复。`, '删除确认',
      { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
    )
  } catch {
    return // 用户主动取消
  }

  // 2. 执行删除（失败原因由拦截器统一弹出，如"有未完结借用记录"）
  try {
    await request.delete(`/devices/${row.id}`)
    ElMessage.success('设备已删除')
    fetchList()
  } catch { /* 拦截器已弹出错误原因 */ }
}

// 跳转借用
function goBorrow(row) {
  router.push({ path: '/borrow/apply', query: { device_id: row.id } })
}

onMounted(() => {
  fetchCategories()
  fetchList()
})
</script>
