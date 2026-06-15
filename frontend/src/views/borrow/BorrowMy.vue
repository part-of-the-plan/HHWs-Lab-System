<template>
  <div>
    <el-card>
      <el-table :data="list" border stripe v-loading="loading">
        <el-table-column prop="device_name" label="设备" min-width="120" />
        <el-table-column prop="apply_time" label="申请时间" width="160" />
        <el-table-column prop="expected_return_date" label="预计归还" width="120" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.effective_status || row.status)">
              {{ statusLabel(row.effective_status || row.status) }}
            </el-tag>
            <el-tag v-if="row.is_overdue" type="danger" size="small" style="margin-left:4px">逾期</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="apply_reason" label="借用理由" min-width="140" />
        <el-table-column prop="reject_reason" label="驳回原因" min-width="120" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button v-if="row.status==='BORROWED'"
              size="small" type="warning" @click="doReturnApply(row)">申请归还</el-button>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '../../utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const list = ref([])
const loading = ref(false)
const pager = reactive({ page: 1, per_page: 10, total: 0 })

const statusMap = {
  PENDING: '待审批', APPROVED: '已通过', REJECTED: '已驳回',
  BORROWED: '借出中', RETURN_PENDING: '待确认归还', RETURNED: '已归还', OVERDUE: '已逾期',
}
const statusTypeMap = {
  PENDING: 'info', APPROVED: 'success', REJECTED: 'danger',
  BORROWED: 'warning', RETURN_PENDING: '', RETURNED: 'success', OVERDUE: 'danger',
}
function statusLabel(s) { return statusMap[s] || s }
function statusType(s) { return statusTypeMap[s] || 'info' }

async function fetchList() {
  loading.value = true
  try {
    const res = await request.get('/borrows', { params: { page: pager.page, per_page: pager.per_page } })
    list.value = res.data.items
    pager.total = res.data.total
  } catch { /* ignore */ }
  finally { loading.value = false }
}

async function doReturnApply(row) {
  try {
    await ElMessageBox.confirm('确认申请归还该设备？', '提示', { type: 'info' })
    await request.put(`/borrows/${row.id}/return-apply`)
    ElMessage.success('归还申请已提交，等待管理员确认')
    fetchList()
  } catch { /* ignore */ }
}

onMounted(fetchList)
</script>
