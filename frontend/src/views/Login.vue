<template>
  <div class="login-bg">
    <el-card class="login-card">
      <h2 style="text-align:center;margin-bottom:24px">实验室设备管理系统</h2>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="0" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User"
            autocomplete="username" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码"
            prefix-icon="Lock" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item>
          <div style="display:flex;gap:8px;align-items:center">
            <el-input v-model="form.captcha_code" placeholder="验证码" style="flex:1" />
            <img :src="captchaImg" @click="refreshCaptcha"
              style="height:40px;cursor:pointer;border:1px solid #dcdfe6;border-radius:4px"
              title="点击刷新" />
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="doLogin" :loading="loading"
            style="width:100%">登 录</el-button>
        </el-form-item>
        <el-form-item>
          <div style="text-align:right;width:100%">
            还没有账号？<el-link type="primary" @click="$router.push('/register')">去注册</el-link>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
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
let captchaId = ''

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function refreshCaptcha() {
  const res = await request.get('/auth/captcha')
  captchaImg.value = res.data.captcha_img
  captchaId = res.data.captcha_id
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
    // 获取 CSRF Token（写操作必须携带）
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
.login-bg { display:flex; justify-content:center; align-items:center; min-height:100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.login-card { width:420px; }
</style>
