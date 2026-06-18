<template>
  <div class="app-shell" :class="{ collapsed: isCollapse }">
    <!-- 侧边栏 -->
    <aside class="app-sidebar">
      <div class="sidebar-logo" @click="$router.push('/')">
        <span v-if="!isCollapse" class="logo-text">实验室设备管理</span>
        <span v-else class="logo-icon">🔬</span>
      </div>
      <el-menu
        :default-active="activePath"
        :collapse="isCollapse"
        router
        class="sidebar-menu"
        text-color="var(--sidebar-text)"
        active-text-color="var(--sidebar-active)"
        background-color="var(--sidebar-bg)"
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>

        <template v-for="(menu, key) in sideMenus" :key="key">
          <el-sub-menu v-if="menu.children" :index="key">
            <template #title>
              <el-icon><component :is="menu.icon" /></el-icon>
              <span>{{ menu.title }}</span>
            </template>
            <el-menu-item v-for="child in menu.children" :key="child.path"
              :index="child.path">
              {{ child.title }}
              <span v-if="badgeMap[child.path]" class="menu-badge">
                {{ badgeMap[child.path] > 99 ? '99+' : badgeMap[child.path] }}
              </span>
            </el-menu-item>
          </el-sub-menu>
        </template>
      </el-menu>
    </aside>

    <!-- 顶部栏 -->
    <header class="app-header">
      <div class="header-left">
        <button type="button" class="collapse-btn" @click="isCollapse = !isCollapse"
          :aria-label="isCollapse ? '展开侧边栏' : '收起侧边栏'">
          <el-icon :size="20"><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
        </button>
        <span class="header-greeting">{{ userStore.user?.real_name || '未登录' }}，欢迎</span>
      </div>
      <div class="header-right">
        <el-button text @click="showPwdDialog = true">修改密码</el-button>
        <el-button text @click="doLogout">退出登录</el-button>
      </div>
    </header>

    <!-- 面包屑导航 -->
    <nav v-if="breadcrumbs.length > 1" class="app-breadcrumb" aria-label="面包屑导航">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path"
          :to="item.path" style="cursor:pointer">
          {{ item.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </nav>

    <!-- 主内容 -->
    <main class="app-main">
      <router-view />
    </main>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="showPwdDialog" title="修改密码" width="420px" :close-on-click-modal="false">
      <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-width="80px">
        <el-form-item label="旧密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password
            autocomplete="current-password" placeholder="请输入旧密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password
            autocomplete="new-password" placeholder="8-20位，含大小写字母+数字+特殊字符" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="pwdForm.confirm_password" type="password" show-password
            autocomplete="new-password" placeholder="再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPwdDialog = false">取消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="doChangePassword">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, reactive, provide } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userStore } from '../stores/user'
import { menuMap } from '../router/index'
import { Fold, Expand, HomeFilled } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { initCsrfToken } from '../utils/request'
import request from '../utils/request'

const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)
const activePath = computed(() => route.path)

/** 面包屑：根据当前路径从 menuMap 解析层级 */
const PATH_MAP = (() => {
  const map = {}
  for (const [key, menu] of Object.entries(menuMap)) {
    if (menu.children) {
      for (const child of menu.children) {
        map[child.path] = { title: child.title, parent: menu.title }
      }
    }
  }
  return map
})()
const breadcrumbs = computed(() => {
  const path = route.path
  const crumbs = [{ title: '首页', path: '/' }]
  if (path === '/') return crumbs
  const entry = PATH_MAP[path]
  if (!entry) return crumbs
  crumbs.push({ title: entry.parent, path: '' })
  crumbs.push({ title: entry.title, path })
  return crumbs
})

/** 根据权限过滤菜单 */
const sideMenus = computed(() => {
  const perms = userStore.permissions
  const result = {}
  for (const [key, menu] of Object.entries(menuMap)) {
    if (menu.perm && !perms.includes(menu.perm)) continue
    if (menu.children) {
      const filtered = menu.children.filter(c => !c.perm || perms.includes(c.perm))
      if (filtered.length === 0) continue
      result[key] = { ...menu, children: filtered }
    } else {
      result[key] = menu
    }
  }
  return result
})

// ── 待办角标轮询 ──
const badgeMap = reactive({})     // path → count
let badgeTimer = null

async function fetchBadges() {
  try {
    const res = await request.get('/borrows/pending-count')
    const d = res.data
    const total = (d.pending || 0) + (d.return_pending || 0)
    badgeMap['/borrow/approve'] = total
    badgeMap['/borrow/my'] = d.my_overdue || 0
  } catch { /* 静默失败，不影响页面 */ }
}

// 提供给子组件（如 BorrowApprove）在审批操作后立即刷新角标
provide('refreshBadges', fetchBadges)

function doLogout() {
  ElMessageBox.confirm('确定退出登录？', '提示', { type: 'warning' })
    .then(() => {
      userStore.logout()
      router.push('/login')
    })
    .catch(() => {})
}

// ── 修改密码 ──
const showPwdDialog = ref(false)
const pwdLoading = ref(false)
const pwdFormRef = ref(null)
const pwdForm = reactive({ old_password: '', new_password: '', confirm_password: '' })

const validateConfirm = (_rule, value, callback) => {
  if (value !== pwdForm.new_password) {
    callback(new Error('两次输入的新密码不一致'))
  } else {
    callback()
  }
}
const pwdRules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, max: 20, message: '密码长度8-20位', trigger: 'blur' },
    { pattern: /[a-z]/, message: '需包含小写字母', trigger: 'blur' },
    { pattern: /[A-Z]/, message: '需包含大写字母', trigger: 'blur' },
    { pattern: /[0-9]/, message: '需包含数字', trigger: 'blur' },
    { pattern: /[^a-zA-Z0-9]/, message: '需包含特殊字符', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
}

async function doChangePassword() {
  const valid = await pwdFormRef.value.validate().catch(() => false)
  if (!valid) return
  pwdLoading.value = true
  try {
    await request.put('/auth/password', {
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    showPwdDialog.value = false
    pwdForm.old_password = ''
    pwdForm.new_password = ''
    pwdForm.confirm_password = ''
    userStore.logout()
    router.push('/login')
  } catch { /* request interceptor 已弹 message */ }
  finally { pwdLoading.value = false }
}

onMounted(() => {
  initCsrfToken()
  fetchBadges()
  badgeTimer = setInterval(fetchBadges, 30000)
})

onUnmounted(() => {
  if (badgeTimer) clearInterval(badgeTimer)
})
</script>

<style scoped>
/* ═══ 布局网格 ═══ */
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  grid-template-rows: var(--header-height) auto minmax(0, 1fr);
  min-height: 100vh;
  background: var(--app-bg);
  transition: grid-template-columns var(--duration-normal) var(--ease-out);
}

.app-shell.collapsed {
  grid-template-columns: var(--sidebar-collapsed-width) minmax(0, 1fr);
}

/* ── 侧边栏 ── */
.app-sidebar {
  grid-column: 1;
  grid-row: 1 / -1;
  background: var(--sidebar-bg);
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-logo {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-on-dark);
  font-weight: 600;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
  overflow: hidden;
}

.logo-text {
  font-size: 17px;
  white-space: nowrap;
}

.logo-icon {
  font-size: 22px;
}

.sidebar-menu {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  border-right: none !important;
}

.sidebar-menu:deep(.el-menu) {
  border-right: none;
}

/* ── 菜单项细调 ── */
.sidebar-menu :deep(.el-menu-item) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 20px !important;
  margin: 2px 8px;
  border-radius: var(--radius-sm);
  height: 44px;
  line-height: 44px;
  font-size: 14px;
  transition: color var(--duration-fast) var(--ease-standard),
              background var(--duration-fast) var(--ease-standard);
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.06);
}

/* 活跃项：浅蓝灰背景 + 白色文字，无左侧竖线 */
.sidebar-menu :deep(.el-menu-item.is-active) {
  color: #FFFFFF;
  background: rgba(229, 237, 250, 0.10);
  border-radius: 9px;
}

/* ── 子菜单标题细调 ── */
.sidebar-menu :deep(.el-sub-menu__title) {
  padding-left: 20px !important;
  margin: 2px 8px;
  border-radius: var(--radius-sm);
  height: 44px;
  line-height: 44px;
  font-size: 14px;
}

.sidebar-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.06);
}

/* 子菜单内的菜单项缩进 */
.sidebar-menu :deep(.el-menu--inline .el-menu-item) {
  padding-left: 48px !important;
}

/* ── 顶部栏 ── */
.app-header {
  grid-column: 2;
  grid-row: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--page-padding);
  background: var(--surface);
  border-bottom: 1px solid var(--border-light);
  min-width: 0;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0;
  transition: border-color var(--duration-fast) var(--ease-standard),
              color var(--duration-fast) var(--ease-standard),
              background var(--duration-fast) var(--ease-standard);
}

.collapse-btn:hover {
  border-color: var(--primary-300);
  color: var(--primary-600);
  background: var(--primary-50);
}

.collapse-btn:focus-visible {
  outline: 2px solid var(--primary-300);
  outline-offset: 2px;
}

.header-greeting {
  font-size: 15px;
  color: var(--text-primary);
}

/* ── 面包屑 ── */
.app-breadcrumb {
  grid-column: 2;
  grid-row: 2;
  padding: 12px var(--page-padding);
  background: var(--surface);
  border-bottom: 1px solid var(--border-light);
  min-width: 0;
}

/* ── 主内容 ── */
.app-main {
  grid-column: 2;
  grid-row: 3;
  padding: var(--page-padding);
  min-width: 0;
  overflow-x: hidden;
}

/* ── 菜单角标 ── */
.menu-badge {
  display: inline-block;
  background: var(--primary-600);
  color: var(--text-on-dark);
  font-size: 11px;
  font-weight: 600;
  border-radius: var(--el-border-radius-circle);
  padding: 0 6px;
  min-width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  margin-left: 6px;
}

/* ── 菜单滚动条隐藏 ── */
.sidebar-menu::-webkit-scrollbar {
  width: 4px;
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 4px;
}

@media (prefers-reduced-motion: reduce) {
  .app-shell {
    transition: none;
  }
}
</style>
