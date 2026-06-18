<template>
  <div class="login-shell">
    <!-- 左侧品牌面板 -->
    <section class="login-brand">
      <div class="brand-grid" aria-hidden="true" />
      <div class="brand-content">
        <!-- 抽象设备线稿 -->
        <svg class="brand-illustration" viewBox="0 0 200 160" fill="none"
          xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <!-- 外环：精密仪器刻度盘 -->
          <circle cx="100" cy="72" r="58" stroke="#A2B7E4" stroke-width="1.2" opacity="0.6" />
          <circle cx="100" cy="72" r="48" stroke="#BBD0ED" stroke-width="1" opacity="0.5" />
          <circle cx="100" cy="72" r="26" stroke="#7087BB" stroke-width="2" opacity="0.55" />
          <!-- 刻度线 -->
          <g stroke="#A2B7E4" stroke-width="1.5" opacity="0.5">
            <line x1="100" y1="20" x2="100" y2="28" />
            <line x1="100" y1="116" x2="100" y2="124" />
            <line x1="48" y1="72" x2="56" y2="72" />
            <line x1="144" y1="72" x2="152" y2="72" />
            <line x1="63" y1="35" x2="69" y2="41" />
            <line x1="131" y1="103" x2="137" y2="109" />
            <line x1="137" y1="35" x2="131" y2="41" />
            <line x1="69" y1="103" x2="63" y2="109" />
          </g>
          <!-- 中心十字 -->
          <line x1="100" y1="62" x2="100" y2="82" stroke="#7087BB" stroke-width="1.2" opacity="0.45" />
          <line x1="90" y1="72" x2="110" y2="72" stroke="#7087BB" stroke-width="1.2" opacity="0.45" />
          <!-- 指针 -->
          <line x1="100" y1="72" x2="68" y2="43" stroke="#495589" stroke-width="2.5" stroke-linecap="round" opacity="0.7" />
          <circle cx="100" cy="72" r="4" fill="#495589" opacity="0.65" />
          <!-- 底部柱形：设备抽象 -->
          <rect x="44" y="134" width="12" height="18" rx="3" stroke="#879DCC" stroke-width="1.2" opacity="0.45" />
          <rect x="62" y="127" width="12" height="25" rx="3" stroke="#7087BB" stroke-width="1.2" opacity="0.55" />
          <rect x="80" y="130" width="12" height="22" rx="3" stroke="#879DCC" stroke-width="1.2" opacity="0.5" />
          <rect x="98" y="122" width="12" height="30" rx="3" stroke="#7087BB" stroke-width="1.4" opacity="0.6" />
          <rect x="116" y="129" width="12" height="23" rx="3" stroke="#879DCC" stroke-width="1.2" opacity="0.5" />
          <rect x="134" y="133" width="12" height="19" rx="3" stroke="#879DCC" stroke-width="1.2" opacity="0.45" />
          <!-- 连接线 -->
          <line x1="44" y1="138" x2="146" y2="138" stroke="#BBD0ED" stroke-width="0.8" opacity="0.4" />
        </svg>

        <h1 class="brand-title">实验室设备管理系统</h1>
        <p class="brand-desc">高校实验室设备全生命周期管理平台</p>

        <!-- 轻量安全提示 -->
        <div class="brand-hint">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="#7087BB" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          <span>所有数据传输均经过加密保护</span>
        </div>
      </div>
    </section>

    <!-- 右侧登录面板 -->
    <section class="login-panel">
      <div class="login-card-wrapper">
        <el-card class="login-card" shadow="never">
          <h2 class="login-title stagger" style="--s:0">登录</h2>
          <el-form ref="formRef" :model="form" :rules="rules" label-width="0" size="large">
            <el-form-item prop="username" class="stagger" style="--s:1">
              <el-input v-model="form.username" placeholder="用户名" prefix-icon="User"
                autocomplete="username" />
            </el-form-item>
            <el-form-item prop="password" class="stagger" style="--s:2">
              <el-input v-model="form.password" type="password" placeholder="密码"
                prefix-icon="Lock" show-password autocomplete="new-password" />
            </el-form-item>
            <el-form-item class="stagger" style="--s:3">
              <div class="captcha-row">
                <el-input v-model="form.captcha_code" placeholder="验证码" />
                <div class="captcha-img-box" @click="refreshCaptcha" title="点击刷新验证码">
                  <img :src="captchaImg" class="captcha-img" :class="{ refreshing: captchaRefreshing }"
                    alt="验证码" />
                </div>
                <button type="button" class="captcha-refresh-btn" @click="refreshCaptcha"
                  title="刷新验证码" aria-label="刷新验证码">
                  <el-icon :class="{ spinning: captchaRefreshing }"><Refresh /></el-icon>
                </button>
              </div>
            </el-form-item>
            <el-form-item class="stagger" style="--s:4">
              <el-button type="primary" @click="doLogin" :loading="loading"
                class="login-btn">登 录</el-button>
            </el-form-item>
            <el-form-item class="stagger" style="--s:5">
              <div class="auth-switch">
                还没有账号？<el-link type="primary" @click="$router.push('/register')">去注册</el-link>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import request, { initCsrfToken } from '../utils/request'
import { setToken, setUser, setPermissions } from '../utils/auth'
import { userStore } from '../stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  captcha_code: '',
})
const captchaImg = ref('')
const captchaRefreshing = ref(false)
let captchaId = ''

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function refreshCaptcha() {
  if (captchaRefreshing.value) return   // 动画期间防止重复请求
  captchaRefreshing.value = true
  try {
    const res = await request.get('/auth/captcha')
    captchaImg.value = res.data.captcha_img
    captchaId = res.data.captcha_id
  } catch { /* 拦截器已处理 */ }
  finally {
    /* 让刷新动画播完一个轻量周期再复位（不阻塞接口逻辑） */
    setTimeout(() => { captchaRefreshing.value = false }, 220)
  }
}

async function doLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  if (!form.captcha_code) {
    ElMessage.warning('请输入验证码')
    return
  }
  loading.value = true
  try {
    const res = await request.post('/auth/login', {
      username: form.username,
      password: form.password,
      captcha_id: captchaId,
      captcha_code: form.captcha_code,
    })
    setToken(res.data.access_token)
    setUser(res.data.user)
    setPermissions(res.data.permissions)
    userStore.loginSuccess(res.data)
    await initCsrfToken()
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch { /* request interceptor 已弹 message */ }
  finally { loading.value = false }
}

onMounted(refreshCaptcha)
</script>

<style scoped>
/* ═══ 布局：分栏 ═══ */
.login-shell {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100vh;
  background: var(--app-bg);
}

/* ── 左侧品牌面板 ── */
.login-brand {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: var(--primary-100);
  overflow: hidden;
}

/* 工程网格 */
.brand-grid {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(162, 183, 228, 0.12) 1px, transparent 1px),
    linear-gradient(90deg, rgba(162, 183, 228, 0.12) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: radial-gradient(ellipse 70% 60% at 50% 40%, black 30%, transparent 70%);
  -webkit-mask-image: radial-gradient(ellipse 70% 60% at 50% 40%, black 30%, transparent 70%);
}

.brand-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  max-width: 360px;
}

/* 设备线稿 */
.brand-illustration {
  width: 200px;
  height: 160px;
  margin-bottom: 32px;
  opacity: 0.85;
}

.brand-title {
  font-size: 22px;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 12px;
  text-wrap: balance;
}

.brand-desc {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
  margin: 0 0 28px;
  text-wrap: balance;
}

.brand-hint {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-tertiary);
}

/* ── 右侧登录面板 ── */
.login-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: var(--app-bg);
}

.login-card-wrapper {
  width: 100%;
  max-width: 400px;
}

/* 卡片 */
.login-card {
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  opacity: 0;
  animation: card-reveal 520ms var(--ease-out) forwards;
}

/* 表单元素错峰浮现 */
.stagger {
  opacity: 0;
  animation: fade-up 440ms var(--ease-out) forwards;
  animation-delay: calc(120ms + var(--s, 0) * 70ms);
}

@media (prefers-reduced-transparency: reduce) {
  .login-card {
    background: var(--surface);
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
  }
}

:deep(.login-card .el-card__body) {
  padding: 36px 32px 24px;
}

.login-title {
  text-align: center;
  margin: 0 0 28px;
  color: var(--text-heading);
  font-size: 22px;
  font-weight: 600;
}

/* ── 验证码网格 ── */
.captcha-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 124px 36px;
  align-items: stretch;
  gap: 10px;
  width: 100%;
}

.captcha-row :deep(.el-input) {
  height: 100%;
}

.captcha-img-box {
  width: 124px;
  height: 44px;
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-sm);
  overflow: hidden;
  cursor: pointer;
  box-sizing: border-box;
  background: var(--surface);
  transition: border-color var(--duration-fast) var(--ease-standard);
}

.captcha-img-box:hover {
  border-color: var(--border-focus);
}

.captcha-img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 验证码刷新：轻微 opacity + blur，容器尺寸不变 */
.captcha-img.refreshing {
  animation: captcha-flip 220ms var(--ease-standard);
}

@keyframes captcha-flip {
  0%   { opacity: 1; filter: blur(0); }
  50%  { opacity: 0.4; filter: blur(2px); }
  100% { opacity: 1; filter: blur(0); }
}

/* 刷新按钮图标旋转 */
.captcha-refresh-btn .spinning {
  animation: icon-spin 360ms var(--ease-out);
}

@keyframes icon-spin {
  from { transform: rotate(0); }
  to   { transform: rotate(180deg); }
}

.captcha-refresh-btn {
  width: 36px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  font-size: 16px;
  box-sizing: border-box;
  transition: border-color var(--duration-fast) var(--ease-standard),
              color var(--duration-fast) var(--ease-standard),
              background var(--duration-fast) var(--ease-standard);
}

.captcha-refresh-btn:hover {
  border-color: var(--primary-600);
  color: var(--primary-600);
  background: var(--primary-50);
}

.captcha-refresh-btn:focus-visible {
  outline: 2px solid var(--primary-300);
  outline-offset: 2px;
}

/* ── 输入框聚焦光晕（低强度灰蓝，非霓虹）── */
.login-card :deep(.el-input__wrapper) {
  transition: box-shadow var(--duration-fast) var(--ease-standard);
}

.login-card :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 3px rgba(112, 135, 187, 0.16),
              0 0 0 1px var(--primary-500) inset;
}

/* ── 登录按钮 ── */
.login-btn {
  width: 100%;
  --el-button-bg-color: var(--primary-600);
  --el-button-border-color: var(--primary-600);
  --el-button-hover-bg-color: var(--primary-700);
  --el-button-hover-border-color: var(--primary-700);
  --el-button-active-bg-color: var(--primary-800);
  --el-button-active-border-color: var(--primary-800);
  --el-button-focus-box-shadow-color: rgba(162, 183, 228, 0.4);
  transition: transform var(--duration-fast) var(--ease-standard),
              box-shadow var(--duration-fast) var(--ease-standard);
}

/* hover：轻微上浮 + 阴影 */
.login-btn:not(.is-loading):hover {
  box-shadow: 0 4px 14px rgba(46, 62, 109, 0.18);
}

/* pressed */
.login-btn:not(.is-loading):active {
  transform: translateY(1px);
}

/* loading 时尺寸锁定，防止抖动 */
.login-btn.is-loading {
  transform: none;
}

/* ── 底部切换文字 ── */
.auth-switch {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 14px;
  line-height: 20px;
  white-space: nowrap;
  color: var(--text-secondary);
}

/* ═══ 响应式 ═══ */
@media (max-width: 767px) {
  .login-shell {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }

  .login-brand {
    padding: 32px 24px 16px;
  }

  .brand-illustration {
    width: 120px;
    height: 96px;
    margin-bottom: 16px;
  }

  .brand-title {
    font-size: 18px;
    margin-bottom: 6px;
  }

  .brand-desc {
    font-size: 13px;
    margin-bottom: 12px;
  }

  .brand-hint {
    display: none;
  }

  .login-panel {
    padding: 16px 20px 40px;
    align-items: flex-start;
  }

  .login-card-wrapper {
    max-width: none;
  }

  :deep(.login-card .el-card__body) {
    padding: 24px 20px 20px;
  }
}

/* ═══ 减少动态：确保起始态不残留 ═══ */
@media (prefers-reduced-motion: reduce) {
  .login-card,
  .stagger {
    opacity: 1;
    animation: none;
  }
  .captcha-img.refreshing,
  .captcha-refresh-btn .spinning {
    animation: none;
  }
}
</style>
