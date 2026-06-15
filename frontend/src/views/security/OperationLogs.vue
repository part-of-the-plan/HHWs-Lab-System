<template>
  <div>
    <!-- 筛选栏 -->
    <el-card style="margin-bottom:16px">
      <el-form :inline="true" :model="filter">
        <el-form-item label="操作类型">
          <el-input v-model="filter.action" placeholder="如 LOGIN_SUCCESS" clearable style="width:180px" />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="filter.username" placeholder="搜索用户名" clearable style="width:160px" />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker v-model="filter.dateRange" type="daterange"
            range-separator="至" start-placeholder="开始日期" end-placeholder="结束日期"
            value-format="YYYY-MM-DD" style="width:260px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="doSearch">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card>
      <el-table :data="list" border stripe v-loading="loading" max-height="600">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="操作者" width="100" />
        <el-table-column prop="action" label="操作类型" width="180">
          <template #default="{ row }">
            <el-tag :type="actionType(row.action)" size="small">{{ row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target" label="操作目标" width="140" />
        <el-table-column prop="detail" label="详情" min-width="160" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="130" />
        <el-table-column prop="created_at" label="时间" width="160" />
      </el-table>

      <el-pagination
        v-model:current-page="pager.page" v-model:page-size="pager.per_page"
        :total="pager.total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
        @size-change="fetchList" @current-change="fetchList"
        style="margin-top:16px; justify-content:flex-end" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '../../utils/request'

const list = ref([])
const loading = ref(false)
const filter = reactive({ action: '', username: '', dateRange: null })
const pager = reactive({ page: 1, per_page: 10, total: 0 })

// 根据操作类型给 tag 颜色
function actionType(action) {
  if (!action) return 'info'
  if (action.startsWith('LOGIN')) return ''
  if (action.startsWith('DEVICE')) return 'success'
  if (action.startsWith('CATEGORY')) return 'warning'
  if (action.startsWith('BORROW')) return 'primary'
  if (action.startsWith('USER')) return 'danger'
  return 'info'
}

async function fetchList() {
  loading.value = true
  try {
    const params = { page: pager.page, per_page: pager.per_page }
    if (filter.action) params.action = filter.action
    if (filter.username) params.username = filter.username
    if (filter.dateRange && filter.dateRange.length === 2) {
      params.date_from = filter.dateRange[0]
      params.date_to = filter.dateRange[1]
    }
    const res = await request.get('/logs', { params })
    list.value = res.data.items
    pager.total = res.data.total
  } catch { /* ignore */ }
  finally { loading.value = false }
}

function doSearch() { pager.page = 1; fetchList() }

function resetFilter() {
  filter.action = ''
  filter.username = ''
  filter.dateRange = null
  doSearch()
}

onMounted(fetchList)
</script>
