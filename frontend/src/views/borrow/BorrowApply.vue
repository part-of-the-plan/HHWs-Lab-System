<template>
  <div>
    <el-card>
      <h3 style="margin-bottom:16px">申请借用</h3>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" style="max-width:520px">
        <el-form-item label="选择设备" prop="device_id">
          <el-select v-model="form.device_id" placeholder="请选择设备" filterable style="width:100%">
            <el-option v-for="d in devices" :key="d.id" :label="`${d.name} (${d.device_no})`" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="借用理由" prop="apply_reason">
          <el-input v-model="form.apply_reason" type="textarea" :rows="3" placeholder="请说明借用用途" />
        </el-form-item>
        <el-form-item label="预计归还日期" prop="expected_return_date">
          <el-date-picker v-model="form.expected_return_date" type="date"
            placeholder="选择日期" value-format="YYYY-MM-DD"
            :disabled-date="disabledDate" style="width:100%" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="doSubmit">提交申请</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import request from '../../utils/request'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const refreshBadges = inject('refreshBadges', () => {})

const devices = ref([])
const loading = ref(false)
const formRef = ref(null)

const form = reactive({
  device_id: null,
  apply_reason: '',
  expected_return_date: '',
})

const rules = {
  device_id: [{ required: true, message: '请选择设备', trigger: 'change' }],
  apply_reason: [{ required: true, message: '请填写借用理由', trigger: 'blur' }],
  expected_return_date: [{ required: true, message: '请选择归还日期', trigger: 'change' }],
}

function disabledDate(time) {
  return time.getTime() < Date.now() - 86400000 // 不能选过去
}

async function fetchDevices() {
  try {
    // 只拉空闲设备
    const res = await request.get('/devices', { params: { status: 'IDLE', per_page: 999 } })
    devices.value = res.data.items || []
    // 如果从设备列表跳转过来，自动选中
    if (route.query.device_id) {
      form.device_id = Number(route.query.device_id)
    }
  } catch { /* ignore */ }
}

async function doSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await request.post('/borrows', {
      device_id: form.device_id,
      apply_reason: form.apply_reason,
      expected_return_date: form.expected_return_date,
    })
    ElMessage.success('申请已提交')
    refreshBadges()
    router.push('/borrow/my')
  } catch { /* ignore */ }
  finally { loading.value = false }
}

onMounted(fetchDevices)
</script>
