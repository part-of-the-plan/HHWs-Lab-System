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
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userStore } from '../stores/user'
import { menuMap } from '../router/index'
import { Fold, Expand, HomeFilled } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

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

function doLogout() {
  ElMessageBox.confirm('确定退出登录？', '提示', { type: 'warning' })
    .then(() => {
      userStore.logout()
      router.push('/login')
    })
    .catch(() => {})
}
</script>

<style scoped>
.aside { background:#304156; }
.logo { height:60px; display:flex; align-items:center; justify-content:center;
  color:#fff; font-size:18px; font-weight:bold; cursor:pointer;
  border-bottom:1px solid rgba(255,255,255,0.1); }
.header { display:flex; align-items:center; justify-content:space-between;
  background:#fff; border-bottom:1px solid #e6e6e6; height:60px; }
.breadcrumb-bar { padding:12px 20px; background:#fff; border-bottom:1px solid #eee; }
</style>
