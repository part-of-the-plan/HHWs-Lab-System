/** 用户状态（Vue3 reactive 全局共享，免 Pinia 依赖更轻） */
import { reactive } from 'vue'
import {
  getUser as getStorageUser,
  setUser as setStorageUser,
  getPermissions as getStoragePerms,
  setPermissions as setStoragePerms,
  logout as clearAll,
  hasPermission as checkPerm,
} from '../utils/auth'

export const userStore = reactive({
  user: getStorageUser(),
  permissions: getStoragePerms(),
  token: localStorage.getItem('lab_device_token'),

  get loggedIn() {
    return !!this.token && !!this.user
  },

  hasPermission(code) {
    return this.permissions.includes(code)
  },

  loginSuccess(data) {
    this.token = data.access_token
    this.user = data.user
    this.permissions = data.permissions || []
    setStorageUser(data.user)
    setStoragePerms(data.permissions)
  },

  logout() {
    this.token = null
    this.user = null
    this.permissions = []
    clearAll()
  },
})
