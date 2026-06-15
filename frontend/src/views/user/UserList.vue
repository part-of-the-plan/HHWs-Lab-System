<template>
  <div>
    <!-- 搜索 -->
    <el-card style="margin-bottom:16px">
      <el-form :inline="true" :model="filter">
        <el-form-item label="搜索">
          <el-input v-model="filter.keyword" placeholder="用户名/真实姓名" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="doSearch">搜索</el-button>
          <el-button @click="filter.keyword=''; doSearch()">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card>
      <el-table :data="list" border stripe v-loading="loading">
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="真实姓名" width="100" />
        <el-table-column prop="phone" label="手机号" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="160" />
        <el-table-column label="角色" min-width="140">
          <template #default="{ row }">
            <el-tag v-for="r in row.role_names" :key="r" size="small" style="margin-right:4px">{{ r }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status===1 ? 'success' : 'danger'">{{ row.status===1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button v-if="userStore.hasPermission('user:update')" size="small" type="primary" link @click="openEdit(row)">编辑</el-button>

            <!-- 自操作保护：超管不能改自己的角色 -->
            <el-tooltip v-if="userStore.hasPermission('user:assign') && isSelf(row)"
              content="不能修改自己的角色，防止误操作锁死账号" placement="top">
              <span style="margin-left:12px">
                <el-button size="small" type="warning" link disabled>角色</el-button>
              </span>
            </el-tooltip>
            <el-button v-else-if="userStore.hasPermission('user:assign')"
              size="small" type="warning" link @click="openRole(row)">角色</el-button>

            <!-- 自操作保护：超管不能禁用自己 -->
            <el-tooltip v-if="userStore.hasPermission('user:status') && isSelf(row)"
              content="不能禁用自己的账号" placement="top">
              <span style="margin-left:12px">
                <el-button size="small" type="danger" link disabled>禁用</el-button>
              </span>
            </el-tooltip>
            <el-button v-else-if="userStore.hasPermission('user:status')" size="small"
              :type="row.status===1 ? 'danger' : 'success'" link @click="doToggleStatus(row)">
              {{ row.status===1 ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pager.page" v-model:page-size="pager.per_page"
        :total="pager.total" :page-sizes="[10, 20]" layout="total, sizes, prev, pager, next"
        @size-change="fetchList" @current-change="fetchList"
        style="margin-top:16px; justify-content:flex-end" />
    </el-card>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editDialog.visible" title="编辑用户" width="420px">
      <el-form ref="editFormRef" :model="editForm" label-width="80px">
        <el-form-item label="真实姓名">
          <el-input v-model="editForm.real_name" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="editForm.phone" placeholder="留空不修改" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="editDialog.loading" @click="doEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 角色分配弹窗 -->
    <el-dialog v-model="roleDialog.visible" title="分配角色" width="420px">
      <el-checkbox-group v-model="roleDialog.checked">
        <el-checkbox v-for="r in allRoles" :key="r.id" :label="r.id" style="display:block;margin-bottom:8px">
          {{ r.role_name }} <span style="color:#909399;font-size:12px">{{ r.description }}</span>
        </el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="roleDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="roleDialog.loading" @click="doAssignRole">保存</el-button>
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
const filter = reactive({ keyword: '' })
const pager = reactive({ page: 1, per_page: 10, total: 0 })
const allRoles = ref([])

// 判断是否当前登录用户本人（自操作保护）
function isSelf(row) {
  return userStore.user && row.id === userStore.user.id
}

// 编辑
const editDialog = reactive({ visible: false, loading: false })
const editFormRef = ref(null)
const editForm = reactive({ id: null, real_name: '', email: '', phone: '' })

// 角色
const roleDialog = reactive({ visible: false, loading: false, checked: [], userId: null })

async function fetchList() {
  loading.value = true
  try {
    const params = { page: pager.page, per_page: pager.per_page }
    if (filter.keyword) params.keyword = filter.keyword
    const res = await request.get('/users', { params })
    list.value = res.data.items
    pager.total = res.data.total
  } catch { /* ignore */ }
  finally { loading.value = false }
}

function doSearch() { pager.page = 1; fetchList() }

async function fetchRoles() {
  try {
    const res = await request.get('/roles')
    allRoles.value = res.data || []
  } catch { /* ignore */ }
}

// ── 编辑 ──
function openEdit(row) {
  editForm.id = row.id
  editForm.real_name = row.real_name
  editForm.email = row.email || ''
  editForm.phone = ''
  editDialog.visible = true
}

async function doEdit() {
  editDialog.loading = true
  try {
    const data = { real_name: editForm.real_name, email: editForm.email }
    if (editForm.phone) data.phone = editForm.phone
    await request.put(`/users/${editForm.id}`, data)
    ElMessage.success('已更新')
    editDialog.visible = false
    fetchList()
  } catch { /* ignore */ }
  finally { editDialog.loading = false }
}

// ── 角色 ──
function openRole(row) {
  roleDialog.userId = row.id
  roleDialog.checked = row.role_ids ? [...row.role_ids] : []
  roleDialog.visible = true
}

async function doAssignRole() {
  roleDialog.loading = true
  try {
    await request.put(`/users/${roleDialog.userId}/roles`, { role_ids: roleDialog.checked })
    ElMessage.success('角色已更新')
    roleDialog.visible = false
    fetchList()
  } catch { /* ignore */ }
  finally { roleDialog.loading = false }
}

// ── 启停 ──
async function doToggleStatus(row) {
  const newStatus = row.status === 1 ? 0 : 1
  const label = newStatus === 0 ? '禁用' : '启用'

  // 1. 二次确认（用户取消则静默返回）
  try {
    await ElMessageBox.confirm(
      newStatus === 0
        ? `确认禁用用户「${row.username}」？禁用后该用户将无法登录系统。`
        : `确认启用用户「${row.username}」？`,
      '操作确认',
      { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' }
    )
  } catch {
    return // 用户主动取消，无需提示
  }

  // 2. 执行操作（失败原因由拦截器统一弹出）
  try {
    await request.put(`/users/${row.id}/status`, { status: newStatus })
    ElMessage.success(`已${label}用户「${row.username}」`)
    fetchList()
  } catch { /* 拦截器已弹出错误原因 */ }
}

onMounted(() => { fetchRoles(); fetchList() })
</script>
