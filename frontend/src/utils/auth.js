/** Token 与权限本地存储 */
const TOKEN_KEY = 'lab_device_token'
const USER_KEY = 'lab_device_user'
const PERMS_KEY = 'lab_device_perms'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}
export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}
export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export function getUser() {
  const raw = localStorage.getItem(USER_KEY)
  return raw ? JSON.parse(raw) : null
}
export function setUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}
export function removeUser() {
  localStorage.removeItem(USER_KEY)
}

export function getPermissions() {
  const raw = localStorage.getItem(PERMS_KEY)
  return raw ? JSON.parse(raw) : []
}
export function setPermissions(perms) {
  localStorage.setItem(PERMS_KEY, JSON.stringify(perms))
}
export function removePermissions() {
  localStorage.removeItem(PERMS_KEY)
}

/** 是否有某权限 */
export function hasPermission(code) {
  return getPermissions().includes(code)
}

/** 退出登录：清除所有本地数据 */
export function logout() {
  removeToken()
  removeUser()
  removePermissions()
  clearCsrfToken()
}

// ==================== CSRF Token（仅内存，不持久化） ====================

let _csrfToken = null

export function setCsrfToken(token) {
  _csrfToken = token
}

export function getCsrfToken() {
  return _csrfToken
}

export function clearCsrfToken() {
  _csrfToken = null
}
