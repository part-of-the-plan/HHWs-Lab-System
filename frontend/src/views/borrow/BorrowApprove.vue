<template>
  <div>
    <el-card>
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <el-tab-pane label="待审批" name="PENDING" />
        <el-tab-pane label="待确认归还" name="RETURN_PENDING" />
      </el-tabs>

      <el-table :data="list" border stripe v-loading="loading">
        <el-table-column prop="username" label="申请人" width="100" />
        <el-table-column prop="device_name" label="设备" min-width="120" />
        <el-table-column prop="apply_time" label="申请时间" width="160" />
        <el-table-column prop="apply_reason" label="借用理由" min-width="140" />
        <el-table-column prop="expected_return_date" label="预计归还" width="120" />

        <!-- 待审批：通过/驳回 -->
        <el-table-column v-if="activeTab==='PENDING'" label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="success" @click="doApprove(row)">通过</el-button>
            <el-button size="small" type="danger" @click="openReject(row)">驳回</el-button>
          </template>
        </el-table-column>

        <!-- 待确认归还：确认归还 -->
        <el-table-column v-if="activeTab==='RETURN_PENDING'" label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click="doConfirmReturn(row)">确认归还</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pager.page"
        v-model:page-size="pager.per_page"
        :total="pager.total"
        :page-sizes="[10, 20]"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchList"
        @current-change="fetchList"
        style="margin-top:16px; justify-content:flex-end"
      />
    </el-card>

    <!-- 驳回弹窗 -->
    <el-dialog v-model="rejectDialog.visible" title="驳回借用申请" width="420px">
      <el-form>
        <el-form-item label="驳回理由">
          <el-input v-model="rejectDialog.reason" type="textarea" :rows="3" placeholder="请填写驳回理由" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialog.visible = false">取消</el-button>
        <el-button type="danger" :loading="rejectDialog.loading" @click="doReject">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '../../utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeTab = ref('PENDING')
const list = ref([])
const loading = ref(false)
const pager = reactive({ page: 1, per_page: 10, total: 0 })

const rejectDialog = reactive({ visible: false, loading: false, reason: '', currentId: null })

function onTabChange() {
  pager.page = 1
  fetchList()
}

async function fetchList() {
  loading.value = true
  try {
    const res = await request.get('/borrows', {
      params: { status: activeTab.value, page: pager.page, per_page: pager.per_page }
    })
    list.value = res.data.items
    pager.total = res.data.total
  } catch { /* ignore */ }
  finally { loading.value = false }
}

async function doApprove(row) {
  try {
    await ElMessageBox.confirm(`确认通过「${row.username}」对「${row.device_name}」的借用申请？`, '审批通过')
    await request.put(`/borrows/${row.id}/approve`)
    ElMessage.success('已通过，设备状态已更新')
    fetchList()
  } catch { /* ignore */ }
}

function openReject(row) {
  rejectDialog.currentId = row.id
  rejectDialog.reason = ''
  rejectDialog.visible = true
}

async function doReject() {
  if (!rejectDialog.reason.trim()) {
    ElMessage.warning('请填写驳回理由')
    return
  }
  rejectDialog.loading = true
  try {
    await request.put(`/borrows/${rejectDialog.currentId}/reject`, {
      reject_reason: rejectDialog.reason
    })
    ElMessage.success('已驳回')
    rejectDialog.visible = false
    fetchList()
  } catch { /* ignore */ }
  finally { rejectDialog.loading = false }
}

async function doConfirmReturn(row) {
  try {
    await ElMessageBox.confirm(`确认「${row.username}」已归还「${row.device_name}」？`, '确认归还')
    await request.put(`/borrows/${row.id}/confirm-return`)
    ElMessage.success('已确认归还，设备状态恢复为空闲')
    fetchList()
  } catch { /* ignore */ }
}

onMounted(fetchList)
</script>
