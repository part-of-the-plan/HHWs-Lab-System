<template>
  <div v-if="isAdmin" class="dashboard">
    <!-- ═══ 统计卡片 ═══ -->
    <div class="stat-cards">
      <div class="stat-card reveal" style="--i:0" @click="$router.push('/device/list')"
        @keydown.enter="$router.push('/device/list')"
        tabindex="0" role="link" :aria-label="`设备总数：${overview.total}`">
        <div class="stat-card-head">
          <span class="stat-dot info"></span>
          <span class="stat-label">设备总数</span>
        </div>
        <div class="stat-value">{{ display.total }}</div>
      </div>

      <div class="stat-card reveal" style="--i:1" @click="$router.push('/device/list?status=IDLE')"
        @keydown.enter="$router.push('/device/list?status=IDLE')"
        tabindex="0" role="link" :aria-label="`空闲设备：${overview.idle}`">
        <div class="stat-card-head">
          <span class="stat-dot success"></span>
          <span class="stat-label">空闲设备</span>
        </div>
        <div class="stat-value">{{ display.idle }}</div>
      </div>

      <div class="stat-card reveal" style="--i:2" @click="$router.push('/device/list?status=BORROWED')"
        @keydown.enter="$router.push('/device/list?status=BORROWED')"
        tabindex="0" role="link" :aria-label="`借出中：${overview.borrowed}`">
        <div class="stat-card-head">
          <span class="stat-dot warning"></span>
          <span class="stat-label">借出中</span>
        </div>
        <div class="stat-value">{{ display.borrowed }}</div>
      </div>

      <div class="stat-card reveal" style="--i:3" @click="$router.push('/borrow/approve?tab=OVERDUE')"
        @keydown.enter="$router.push('/borrow/approve?tab=OVERDUE')"
        tabindex="0" role="link" :aria-label="`逾期未还：${overview.overdue}`">
        <div class="stat-card-head">
          <span class="stat-dot danger" :class="{ 'is-alert': overview.overdue > 0 }"></span>
          <span class="stat-label">逾期未还</span>
        </div>
        <div class="stat-value">{{ display.overdue }}</div>
      </div>
    </div>

    <!-- ═══ 图表区域 ═══ -->
    <div class="chart-grid">
      <div class="chart-card chart-reveal" style="--i:4">
        <h3 class="chart-title">近30天借用趋势</h3>
        <div ref="trendChart" class="chart-body"></div>
      </div>
      <div class="chart-card chart-reveal" style="--i:5">
        <h3 class="chart-title">设备借用 TOP10</h3>
        <div ref="utilChart" class="chart-body"></div>
      </div>
    </div>
  </div>

  <div v-else class="dashboard-empty">
    <el-empty description="欢迎使用实验室设备管理系统">
      <el-button type="primary" @click="$router.push('/borrow/apply')">去申请借用</el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { userStore } from '../stores/user'
import * as echarts from 'echarts'
import request from '../utils/request'

const isAdmin = computed(() =>
  userStore.hasPermission('stats:view') || userStore.hasPermission('borrow:approve'))

const overview = ref({ total: 0, idle: 0, borrowed: 0, overdue: 0 })
/* 用于数字滚动显示的值（与真实值分离，最终必须等于真实值） */
const display = reactive({ total: 0, idle: 0, borrowed: 0, overdue: 0 })

const trendChart = ref(null)
const utilChart = ref(null)

let trendInstance = null
let utilInstance = null
let resizeObserver = null
const tweenFrames = {}   // key → rAF id，用于卸载时取消

/* ── 减少动态媒体查询 ── */
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

/* ── 图表配色 ── */
const CHART = {
  line: '#7087BB',
  area: 'rgba(187, 208, 237, 0.28)',
  grid: '#E4EAF2',
  axisLabel: '#6B7488',   // 4.6:1 on white，满足 WCAG AA
  tooltipBg: 'rgba(255,255,255,0.96)',
  tooltipBorder: '#D3DCE8',
}

/* ── 数字缓动：从当前显示值平滑增长到目标值（不循环，终值精确） ── */
function tweenNumber(key, target) {
  const safeTarget = Number.isFinite(target) ? target : 0

  /* 减少动态模式：直接显示终值 */
  if (prefersReducedMotion) {
    display[key] = safeTarget
    return
  }

  if (tweenFrames[key]) cancelAnimationFrame(tweenFrames[key])

  const start = display[key] || 0
  const diff = safeTarget - start
  if (diff === 0) { display[key] = safeTarget; return }

  const duration = 900
  let startTime = 0

  const step = (now) => {
    if (!startTime) startTime = now
    const p = Math.min((now - startTime) / duration, 1)
    /* cubicOut 缓动 */
    const eased = 1 - Math.pow(1 - p, 3)
    display[key] = Math.round(start + diff * eased)
    if (p < 1) {
      tweenFrames[key] = requestAnimationFrame(step)
    } else {
      display[key] = safeTarget   // 锁定精确终值
      tweenFrames[key] = 0
    }
  }
  tweenFrames[key] = requestAnimationFrame(step)
}

/* ── 设备状态总览（统计卡片） ── */
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
    /* 真实数据到位后播放一次数字滚动 */
    tweenNumber('total', overview.value.total)
    tweenNumber('idle', overview.value.idle)
    tweenNumber('borrowed', overview.value.borrowed)
    tweenNumber('overdue', overview.value.overdue)
  } catch { /* ignore */ }
}

async function initTrendChart() {
  if (!trendChart.value) return
  try {
    const res = await request.get('/stats/trend')
    const d = res.data

    if (trendInstance) {
      trendInstance.dispose()
      trendInstance = null
    }

    trendInstance = echarts.init(trendChart.value)

    trendInstance.setOption({
      animation: !prefersReducedMotion,
      animationDuration: 800,
      animationEasing: 'cubicOut',
      animationDurationUpdate: 500,
      animationEasingUpdate: 'cubicOut',

      tooltip: {
        trigger: 'axis',
        backgroundColor: CHART.tooltipBg,
        borderColor: CHART.tooltipBorder,
        borderWidth: 1,
        textStyle: { color: '#263248', fontSize: 13 },
        axisPointer: {
          type: 'line',
          lineStyle: { color: CHART.grid, type: 'dashed' },
        },
      },
      grid: { left: 44, right: 24, top: 16, bottom: 32 },
      xAxis: {
        type: 'category',
        data: d.labels,
        axisLine: { lineStyle: { color: CHART.grid } },
        axisTick: { show: false },
        axisLabel: { rotate: 30, fontSize: 11, color: CHART.axisLabel },
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        splitLine: { lineStyle: { color: CHART.grid, type: 'dashed' } },
        axisLabel: { fontSize: 11, color: CHART.axisLabel },
      },
      series: [{
        id: 'borrow-trend',
        type: 'line',
        data: d.values,
        smooth: 0.28,
        showSymbol: false,
        symbol: 'circle',
        symbolSize: 6,
        connectNulls: false,
        lineStyle: {
          width: 2.4,
          color: CHART.line,
          cap: 'round',
        },
        itemStyle: {
          color: CHART.line,
          borderColor: '#FFFFFF',
          borderWidth: 2,
        },
        areaStyle: {
          color: CHART.area,
        },
        emphasis: {
          focus: 'series',
        },
      }],
    })
  } catch { /* ignore */ }
}

async function initUtilChart() {
  if (!utilChart.value) return
  try {
    const res = await request.get('/stats/utilization')
    const d = res.data

    if (utilInstance) {
      utilInstance.dispose()
      utilInstance = null
    }

    utilInstance = echarts.init(utilChart.value)

    utilInstance.setOption({
      animation: !prefersReducedMotion,
      animationDuration: 700,
      animationEasing: 'cubicOut',
      animationDurationUpdate: 400,
      animationEasingUpdate: 'cubicOut',
      /* 柱形从上到下错峰展开 */
      animationDelay: (idx) => idx * 50,

      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: CHART.tooltipBg,
        borderColor: CHART.tooltipBorder,
        borderWidth: 1,
        textStyle: { color: '#263248', fontSize: 13 },
      },
      grid: { left: 104, right: 24, top: 8, bottom: 8 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        splitLine: { lineStyle: { color: CHART.grid, type: 'dashed' } },
        axisLabel: { fontSize: 11, color: CHART.axisLabel },
      },
      yAxis: {
        type: 'category',
        data: d.labels,
        inverse: true,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          width: 90,
          overflow: 'truncate',
          fontSize: 12,
          color: '#263248',
        },
      },
      series: [{
        id: 'util-top10',
        type: 'bar',
        data: d.values,
        barWidth: 18,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#879DCC' },
            { offset: 1, color: '#A2B7E4' },
          ]),
          borderRadius: [0, 6, 6, 0],
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#7087BB' },
              { offset: 1, color: '#879DCC' },
            ]),
          },
        },
      }],
    })
  } catch { /* ignore */ }
}

/* ── ResizeObserver：仅在实际尺寸变化时 resize ── */
function setupResizeObserver() {
  const sizes = { trendW: 0, trendH: 0, utilW: 0, utilH: 0 }
  let pendingFrame = 0

  resizeObserver = new ResizeObserver((entries) => {
    let trendChanged = false
    let utilChanged = false

    for (const entry of entries) {
      const w = Math.round(entry.contentRect.width)
      const h = Math.round(entry.contentRect.height)

      if (w === 0 || h === 0) continue

      if (entry.target === trendChart.value) {
        if (w !== sizes.trendW || h !== sizes.trendH) {
          sizes.trendW = w
          sizes.trendH = h
          trendChanged = true
        }
      } else if (entry.target === utilChart.value) {
        if (w !== sizes.utilW || h !== sizes.utilH) {
          sizes.utilW = w
          sizes.utilH = h
          utilChanged = true
        }
      }
    }

    if (!trendChanged && !utilChanged) return

    cancelAnimationFrame(pendingFrame)
    pendingFrame = requestAnimationFrame(() => {
      if (trendChanged) trendInstance?.resize()
      if (utilChanged) utilInstance?.resize()
    })
  })

  if (trendChart.value) resizeObserver.observe(trendChart.value)
  if (utilChart.value) resizeObserver.observe(utilChart.value)
}

onMounted(async () => {
  if (isAdmin.value) {
    await fetchOverview()
    await nextTick()
    await initTrendChart()
    await initUtilChart()
    setupResizeObserver()
  }
})

onUnmounted(() => {
  /* 取消未完成的数字缓动 */
  for (const key in tweenFrames) {
    if (tweenFrames[key]) cancelAnimationFrame(tweenFrames[key])
  }
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (trendInstance) {
    trendInstance.dispose()
    trendInstance = null
  }
  if (utilInstance) {
    utilInstance.dispose()
    utilInstance = null
  }
})
</script>

<style scoped>
/* ═══ 仪表盘容器 ═══ */
.dashboard {
  display: flex;
  flex-direction: column;
  gap: var(--content-gap);
}

/* ═══ 统计卡片网格 ═══ */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--content-gap);
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 24px;
  background: var(--surface);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-xs);
  cursor: pointer;
  transition: transform var(--duration-fast) var(--ease-out),
              box-shadow var(--duration-fast) var(--ease-out),
              border-color var(--duration-fast) var(--ease-out);
  user-select: none;
}

/* Card Hover Lift：仅上移 2px + 轻微边框/阴影 */
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
  border-color: var(--border-light);
}

.stat-card:focus-visible {
  outline: 2px solid var(--primary-300);
  outline-offset: 2px;
}

.stat-card:active {
  transform: translateY(0);
}

.stat-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ── 彩色圆点指示器 ── */
.stat-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--neutral-status);
}

.stat-dot.info    { background: var(--info); }
.stat-dot.success { background: var(--success); }
.stat-dot.warning { background: var(--warning); }
.stat-dot.danger  { background: var(--danger); }

/* 逾期 > 0 时低强度脉冲，提示真正的异常 */
.stat-dot.danger.is-alert {
  animation: status-pulse 2s var(--ease-standard) infinite;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
  letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums;
}

/* ═══ 图表网格 ═══ */
.chart-grid {
  display: grid;
  grid-template-columns: 7fr 5fr;
  gap: var(--content-gap);
}

.chart-card {
  background: var(--surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-xs);
  padding: 20px 24px;
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 12px;
}

.chart-body {
  height: 300px;
}

/* ═══ 入场动效：错峰浮现 ═══ */
.reveal {
  opacity: 0;
  animation: card-reveal 460ms var(--ease-out) forwards;
  animation-delay: calc(var(--i, 0) * 60ms);
}

/* 图表卡片：仅 opacity + translateY，不使用 scale，避免容器尺寸变化触发 resize */
.chart-reveal {
  opacity: 0;
  animation: fade-up 480ms var(--ease-out) forwards;
  animation-delay: calc(var(--i, 0) * 60ms);
}

/* ═══ 非管理员空态 ═══ */
.dashboard-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

/* ═══ 响应式 ═══ */
@media (max-width: 1024px) {
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .chart-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .stat-cards {
    grid-template-columns: 1fr;
  }

  .stat-card {
    padding: 16px 20px;
  }

  .stat-value {
    font-size: 26px;
  }

  .chart-card {
    padding: 16px;
  }

  .chart-body {
    height: 240px;
  }
}

/* ═══ 减少动态：禁止位移/滚动/脉冲，保留即时反馈 ═══ */
@media (prefers-reduced-motion: reduce) {
  .stat-card {
    transition: none;
  }
  .reveal,
  .chart-reveal {
    opacity: 1;
    animation: none;
  }
  .stat-dot.danger.is-alert {
    animation: none;
  }
}
</style>
