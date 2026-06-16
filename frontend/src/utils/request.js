/** Axios 全局封装：自动带 Token、CSRF Token、统一处理 401/403 */
import axios from 'axios'
import { getToken, removeToken, getCsrfToken, setCsrfToken, clearCsrfToken } from './auth'
import { ElMessage } from 'element-plus'

// baseURL 走环境变量：本地读 .env.development，上云读 .env.production
// 兜底 '/api'——同域部署时由 Nginx 反代到后端，前端无需关心后端地址
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
})

// ── 请求拦截：自动带 Token + CSRF Token ──
request.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // 写请求必须带 CSRF Token（登录/验证码等白名单接口后端不校验，前端也无需带）
    const method = (config.method || '').toLowerCase()
    if (['post', 'put', 'delete', 'patch'].includes(method)) {
      const csrf = getCsrfToken()
      if (csrf) {
        config.headers['X-CSRF-Token'] = csrf
      }
    }
    return config
  },
  error => Promise.reject(error)
)

// ── CSRF Token 刷新（自动重试一次）──
let _csrfRefreshing = null  // 防并发：多个请求同时 403 时只刷新一次

async function refreshCsrfToken() {
  if (_csrfRefreshing) return _csrfRefreshing
  _csrfRefreshing = request.get('/auth/csrf-token').then(res => {
    if (res.code === 0 && res.data?.csrf_token) {
      setCsrfToken(res.data.csrf_token)
    }
  }).finally(() => {
    _csrfRefreshing = null
  })
  return _csrfRefreshing
}

// ── 响应拦截：统一错误处理 ──
request.interceptors.response.use(
  response => {
    const data = response.data
    // 后端返回的 code != 0 视为业务错误
    if (data.code !== 0) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  async error => {
    if (error.response) {
      const status = error.response.status
      const data = error.response.data
      if (status === 401) {
        removeToken()
        clearCsrfToken()
        ElMessage.error('登录已过期，请重新登录')
        const from = window.location.hash
          ? window.location.hash.replace('#', '')
          : ''
        window.location.hash = '#/login' + (from ? `?redirect=${from}` : '')
      } else if (status === 403) {
        const msg = data?.message || ''
        // CSRF Token 过期/缺失 → 自动刷新 token 并重试一次
        if (msg.includes('CSRF') && !error.config._csrfRetried) {
          error.config._csrfRetried = true
          try {
            await refreshCsrfToken()
            // 重试时带上新的 CSRF Token
            const newCsrf = getCsrfToken()
            if (newCsrf) {
              error.config.headers['X-CSRF-Token'] = newCsrf
            }
            return request(error.config)
          } catch {
            // 刷新失败（可能是登录也过期了），让 403 提示正常展示
          }
        }
        ElMessage.error(data?.message || '无此操作权限')
      } else if (status >= 500) {
        ElMessage.error('服务器异常，请稍后重试')
      } else {
        ElMessage.error(data?.message || '操作失败，请稍后重试')
      }
    } else {
      ElMessage.error('网络连接失败')
    }
    return Promise.reject(error)
  }
)

/** 登录成功后调用：获取 CSRF Token 并存入内存 */
export async function initCsrfToken() {
  try {
    const res = await request.get('/auth/csrf-token')
    if (res.code === 0 && res.data?.csrf_token) {
      setCsrfToken(res.data.csrf_token)
    }
  } catch {
    // 静默失败，后续写请求会触发 403 → 自动刷新
  }
}

export default request
