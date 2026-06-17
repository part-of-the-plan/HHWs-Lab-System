<template>
  <el-container style="min-height:100vh">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse?'64px':'240px'" class="aside">
      <div class="logo" @click="$router.push('/')">
        <span v-if="!isCollapse">实验室设备管理</span>
        <span v-else>🔬</span>
      </div>
      <el-menu
        :default-active="activePath"
        :collapse="isCollapse"
        :collapse-transition="false"
        router
        text-color="#bfcbd9"
        active-text-color="#409eff"
        background-color="#304156"
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
              <span v-if="badgeMap[child.path]" class="menu-badge">{{ badgeMap[child.path] > 99 ? '99+' : badgeMap[child.path] }}</span>
            </el-menu-item>
          </el-sub-menu>
        </template>
      </el-menu>
    </el-aside>

    <!-- 右侧 -->
    <el-container>
      <el-header class="header">
        <div style="display:flex;align-items:center;gap:12px">
          <el-icon style="cursor:pointer;font-size:20px" @click="isCollapse=!isCollapse">
            <Fold v-if="!isCollapse" /><Expand v-else />
          </el-icon>
          <span style="font-size:16px">{{ userStore.user?.real_name || '未登录' }}，欢迎</span>
        </div>
        <div style="display:flex;align-items:center;gap:12px">
          <el-button text @click="showPwdDialog = true">修改密码</el-button>
          <el-button text @click="doLogout">退出登录</el-button>
        </div>
      </el-header>
      <!-- 面包屑导航 -->
      <div v-if="breadcrumbs.length > 1" class="breadcrumb-bar">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path"
            :to="item.path" style="cursor:pointer">
            {{ item.title }}
          </el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      <el-main>
        <router-view />
      </el-main>
    </el-container>

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
  </el-container>
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
    // 审批管理页：pending + return_pending 合计
    const total = (d.pending || 0) + (d.return_pending || 0)
    badgeMap['/borrow/approve'] = total
    // 我的记录：自己逾期未还的数量
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
    // 退出登录
    userStore.logout()
    router.push('/login')
  } catch { /* request interceptor 已弹 message */ }
  finally { pwdLoading.value = false }
}

// 页面刷新后重新获取 CSRF Token（JWT 在 localStorage 但 CSRF Token 在内存已丢失）
onMounted(() => {
  initCsrfToken()
  fetchBadges()
  badgeTimer = setInterval(fetchBadges, 30000)   // 每30s刷新角标
})

onUnmounted(() => {
  if (badgeTimer) clearInterval(badgeTimer)
})
</script>

<style scoped>
.aside { background:#304156; }
.logo { height:60px; display:flex; align-items:center; justify-content:center;
  color:#fff; font-size:18px; font-weight:bold; cursor:pointer;
  border-bottom:1px solid rgba(255,255,255,0.1); }
.header { display:flex; align-items:center; justify-content:space-between;
  background:#fff; border-bottom:1px solid #e6e6e6; height:60px; }
.breadcrumb-bar { padding:12px 20px; background:#fff; border-bottom:1px solid #eee; }
.menu-badge { display:inline-block; background:#f56c6c; color:#fff; font-size:11px;
  border-radius:10px; padding:0 6px; min-width:18px; height:18px; line-height:18px;
  text-align:center; margin-left:6px; }
</style>
