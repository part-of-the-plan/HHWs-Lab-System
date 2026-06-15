<template>
  <div class="login-bg">
    <el-card class="card">
      <h2 style="text-align:center;margin-bottom:16px">用户注册</h2>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" size="large">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="4-20位,字母数字下划线" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password
            placeholder="8位以上,大写+小写+数字+符号至少三种" autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="确认密码" prop="password2">
          <el-input v-model="form.password2" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="form.real_name" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" placeholder="选填" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="选填" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="doRegister" :loading="loading"
            style="width:100%">注 册</el-button>
        </el-form-item>
        <el-form-item>
          <div style="text-align:right;width:100%">
            已有账号？<el-link type="primary" @click="$router.push('/login')">去登录</el-link>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
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
.login-bg { display:flex; justify-content:center; align-items:center; min-height:100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.card { width:480px; }
</style>
