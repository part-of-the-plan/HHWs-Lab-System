/** Axios 全局封装：自动带 Token、统一处理 401/403 */
import axios from 'axios'
import { getToken, removeToken } from './auth'
import { ElMessage } from 'element-plus'

// baseURL 走环境变量：本地读 .env.development，上云读 .env.production
// 兜底 '/api'——同域部署时由 Nginx 反代到后端，前端无需关心后端地址
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
})

// 请求拦截：自动带 Token
request.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截：统一错误处理
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
  error => {
    if (error.response) {
      const status = error.response.status
      const data = error.response.data
      if (status === 401) {
        removeToken()
        ElMessage.error('登录已过期，请重新登录')
        // 跳转登录页，带上当前路径以便登录后跳回
        const from = window.location.hash
          ? window.location.hash.replace('#', '')
          : ''
        window.location.hash = '#/login' + (from ? `?redirect=${from}` : '')
      } else if (status === 403) {
        // 优先用后端返回的具体原因，否则兜底
        ElMessage.error(data?.message || '无此操作权限')
      } else if (status >= 500) {
        ElMessage.error('服务器异常，请稍后重试')
      } else {
        // 业务错误（含 400）：弹出后端返回的明确原因
        ElMessage.error(data?.message || '操作失败，请稍后重试')
      }
    } else {
      ElMessage.error('网络连接失败')
    }
    return Promise.reject(error)
  }
)

export default request
