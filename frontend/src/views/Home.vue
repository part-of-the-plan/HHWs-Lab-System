<template>
  <div v-if="isAdmin">
    <!-- 统计卡片 -->
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="6"><stat-card title="设备总数" :value="overview.total" color="#409eff" /></el-col>
      <el-col :span="6"><stat-card title="空闲设备" :value="overview.idle" color="#67c23a" /></el-col>
      <el-col :span="6"><stat-card title="借出中" :value="overview.borrowed" color="#e6a23c" /></el-col>
      <el-col :span="6"><stat-card title="逾期未还" :value="overview.overdue" color="#f56c6c" /></el-col>
    </el-row>

    <!-- 图表 -->
    <el-row :gutter="16">
      <el-col :span="14">
        <el-card>
          <h4 style="margin-bottom:12px">近30天借用趋势</h4>
          <div ref="trendChart" style="height:300px" />
        </el-card>
      </el-col>
      <el-col :span="10">
        <el-card>
          <h4 style="margin-bottom:12px">设备借用 TOP10</h4>
          <div ref="utilChart" style="height:300px" />
        </el-card>
      </el-col>
    </el-row>
  </div>

  <div v-else>
    <el-empty description="欢迎使用实验室设备管理系统">
      <el-button type="primary" @click="$router.push('/borrow/apply')">去申请借用</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { userStore } from '../stores/user'
import * as echarts from 'echarts'
import request from '../utils/request'

const isAdmin = computed(() =>
  userStore.hasPermission('stats:view') || userStore.hasPermission('borrow:approve'))

const overview = ref({ total: 0, idle: 0, borrowed: 0, overdue: 0 })
const trendChart = ref(null)
const utilChart = ref(null)

async function fetchOverview() {
  try {
    const res = await request.get('/stats/overview')
    const d = res.data
    const statuses = d.statuses || { labels: [], values: [] }
    const idx = (s) => statuses.labels.indexOf(s)
    const v = (s) => (idx(s) >= 0 ? statuses.values[idx(s)] : 0)
    overview.value = {
      total: statuses.values.reduce((a, b) => a + b, 0),
      idle: v('IDLE'),
      borrowed: v('BORROWED'),
      overdue: d.overdue_count || 0,
    }
  } catch { /* ignore */ }
}

async function initTrendChart() {
  try {
    const res = await request.get('/stats/trend')
    const d = res.data
    const chart = echarts.init(trendChart.value)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 10, bottom: 30 },
      xAxis: { type: 'category', data: d.labels, axisLabel: { rotate: 30, fontSize: 10 } },
      yAxis: { type: 'value', minInterval: 1 },
      series: [{ data: d.values, type: 'line', smooth: true, areaStyle: { opacity: 0.15 },
        itemStyle: { color: '#409eff' } }],
    })
  } catch { /* ignore */ }
}

async function initUtilChart() {
  try {
    const res = await request.get('/stats/utilization')
    const d = res.data
    const chart = echarts.init(utilChart.value)
    chart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 100, right: 20, top: 10, bottom: 10 },
      xAxis: { type: 'value', minInterval: 1 },
      yAxis: { type: 'category', data: d.labels.reverse(), inverse: true,
        axisLabel: { width: 90, overflow: 'truncate' } },
      series: [{ data: d.values.reverse(), type: 'bar',
        itemStyle: { color: '#67c23a', borderRadius: [0, 4, 4, 0] } }],
    })
  } catch { /* ignore */ }
}

onMounted(async () => {
  if (isAdmin.value) {
    await fetchOverview()
    await nextTick()
    initTrendChart()
    initUtilChart()
  }
})
</script>

<!-- ═══ 统计卡片组件 ═══ -->
<script>
import { h } from 'vue'
const card = {
  props: { title: String, value: [Number,String], color: String },
  render() {
    return h('div', {
      style: `background:${this.color};color:#fff;padding:20px;border-radius:8px;text-align:center`
    }, [
      h('div', { style: 'font-size:14px;opacity:0.9' }, this.title),
      h('div', { style: 'font-size:32px;font-weight:bold;margin-top:8px' }, String(this.value)),
    ])
  }
}
export default { components: { 'stat-card': card } }
</script>
