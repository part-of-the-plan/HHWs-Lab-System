<template>
  <div class="reg-shell">
    <!-- 左侧品牌面板（与登录页共用） -->
    <section class="reg-brand">
      <div class="brand-grid" aria-hidden="true" />
      <div class="brand-content">
        <svg class="brand-illustration" viewBox="0 0 200 160" fill="none"
          xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <circle cx="100" cy="72" r="58" stroke="#A2B7E4" stroke-width="1.2" opacity="0.6" />
          <circle cx="100" cy="72" r="48" stroke="#BBD0ED" stroke-width="1" opacity="0.5" />
          <circle cx="100" cy="72" r="26" stroke="#7087BB" stroke-width="2" opacity="0.55" />
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
          <line x1="100" y1="62" x2="100" y2="82" stroke="#7087BB" stroke-width="1.2" opacity="0.45" />
          <line x1="90" y1="72" x2="110" y2="72" stroke="#7087BB" stroke-width="1.2" opacity="0.45" />
          <line x1="100" y1="72" x2="68" y2="43" stroke="#495589" stroke-width="2.5" stroke-linecap="round" opacity="0.7" />
          <circle cx="100" cy="72" r="4" fill="#495589" opacity="0.65" />
          <rect x="44" y="134" width="12" height="18" rx="3" stroke="#879DCC" stroke-width="1.2" opacity="0.45" />
          <rect x="62" y="127" width="12" height="25" rx="3" stroke="#7087BB" stroke-width="1.2" opacity="0.55" />
          <rect x="80" y="130" width="12" height="22" rx="3" stroke="#879DCC" stroke-width="1.2" opacity="0.5" />
          <rect x="98" y="122" width="12" height="30" rx="3" stroke="#7087BB" stroke-width="1.4" opacity="0.6" />
          <rect x="116" y="129" width="12" height="23" rx="3" stroke="#879DCC" stroke-width="1.2" opacity="0.5" />
          <rect x="134" y="133" width="12" height="19" rx="3" stroke="#879DCC" stroke-width="1.2" opacity="0.45" />
          <line x1="44" y1="138" x2="146" y2="138" stroke="#BBD0ED" stroke-width="0.8" opacity="0.4" />
        </svg>

        <h1 class="brand-title">实验室设备管理系统</h1>
        <p class="brand-desc">高校实验室设备全生命周期管理平台</p>

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

    <!-- 右侧注册面板 -->
    <section class="reg-panel">
      <div class="reg-card-wrapper">
        <el-card class="reg-card" shadow="never">
          <h2 class="reg-title stagger" style="--s:0">用户注册</h2>
          <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" size="large">
            <el-form-item label="用户名" prop="username" class="stagger" style="--s:1">
              <el-input v-model="form.username" placeholder="4-20位,字母数字下划线" />
            </el-form-item>
            <el-form-item label="密码" prop="password" class="stagger" style="--s:2">
              <el-input v-model="form.password" type="password" show-password
                placeholder="8位以上,大写+小写+数字+符号至少三种" autocomplete="new-password" />
            </el-form-item>
            <el-form-item label="确认密码" prop="password2" class="stagger" style="--s:3">
              <el-input v-model="form.password2" type="password" show-password autocomplete="new-password" />
            </el-form-item>
            <el-form-item label="真实姓名" prop="real_name" class="stagger" style="--s:4">
              <el-input v-model="form.real_name" />
            </el-form-item>
            <el-form-item label="手机号" prop="phone" class="stagger" style="--s:5">
              <el-input v-model="form.phone" placeholder="选填" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email" class="stagger" style="--s:6">
              <el-input v-model="form.email" placeholder="选填" />
            </el-form-item>
            <el-form-item class="stagger" style="--s:7">
              <el-button type="primary" @click="doRegister" :loading="loading"
                class="reg-btn">注 册</el-button>
            </el-form-item>
            <el-form-item class="stagger" style="--s:8">
              <div class="auth-switch">
                已有账号？<el-link type="primary" @click="$router.push('/login')">去登录</el-link>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import request from '../utils/request'
import { ElMessage } from 'element-plus'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  password2: '',
  real_name: '',
  phone: '',
  email: '',
})

const validatePass2 = (rule, value, cb) => {
  if (value !== form.password) cb(new Error('两次密码不一致'))
  else cb()
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 4, max: 20, message: '4-20位', trigger: 'blur' },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  password2: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validatePass2, trigger: 'blur' },
  ],
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
}

async function doRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await request.post('/auth/register', {
      username: form.username,
      password: form.password,
      real_name: form.real_name,
      phone: form.phone,
      email: form.email,
    })
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch { /* handled */ }
  finally { loading.value = false }
}
</script>

<style scoped>
/* ═══ 布局：分栏 ═══ */
.reg-shell {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100vh;
  background: var(--app-bg);
}

/* ── 左侧品牌面板 ── */
.reg-brand {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: var(--primary-100);
  overflow: hidden;
}

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

/* ── 右侧注册面板 ── */
.reg-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: var(--app-bg);
  overflow-y: auto;
}

.reg-card-wrapper {
  width: 100%;
  max-width: 460px;
}

.reg-card {
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
  animation-delay: calc(120ms + var(--s, 0) * 60ms);
}

@media (prefers-reduced-transparency: reduce) {
  .reg-card {
    background: var(--surface);
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
  }
}

:deep(.reg-card .el-card__body) {
  padding: 32px 28px 20px;
}

.reg-title {
  text-align: center;
  margin: 0 0 20px;
  color: var(--text-heading);
  font-size: 22px;
  font-weight: 600;
}

/* ── 输入框聚焦光晕（低强度灰蓝）── */
.reg-card :deep(.el-input__wrapper) {
  transition: box-shadow var(--duration-fast) var(--ease-standard);
}

.reg-card :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 3px rgba(112, 135, 187, 0.16),
              0 0 0 1px var(--primary-500) inset;
}

/* ── 注册按钮 ── */
.reg-btn {
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

.reg-btn:not(.is-loading):hover {
  box-shadow: 0 4px 14px rgba(46, 62, 109, 0.18);
}

.reg-btn:not(.is-loading):active {
  transform: translateY(1px);
}

.reg-btn.is-loading {
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
  .reg-shell {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }

  .reg-brand {
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

  .reg-panel {
    padding: 16px 20px 40px;
    align-items: flex-start;
  }

  .reg-card-wrapper {
    max-width: none;
  }

  :deep(.reg-card .el-card__body) {
    padding: 24px 20px 20px;
  }
}

/* ═══ 减少动态：确保起始态不残留 ═══ */
@media (prefers-reduced-motion: reduce) {
  .reg-card,
  .stagger {
    opacity: 1;
    animation: none;
  }
}
</style>
