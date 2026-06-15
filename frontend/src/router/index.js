import { createRouter, createWebHashHistory } from 'vue-router'
import { getToken, getPermissions } from '../utils/auth'

/** 菜单项定义：侧边栏渲染和路由均以此为准 */
export const menuMap = {
  home:       { title: '首页',         icon: 'HomeFilled',       perm: null },
  device:     { title: '设备管理',     icon: 'Monitor',          perm: 'device:list',
                children: [
                  { title: '设备列表', path: '/device/list',     perm: 'device:list' },
                  { title: '设备分类', path: '/device/category', perm: 'category:manage' },
                ]},
  borrow:     { title: '借用管理',     icon: 'Tickets',          perm: null,
                children: [
                  { title: '申请借用',   path: '/borrow/apply',   perm: 'borrow:apply' },
                  { title: '我的记录',   path: '/borrow/my',      perm: 'record:self' },
                  { title: '审批管理',   path: '/borrow/approve', perm: 'borrow:approve' },
                ]},
  user:       { title: '用户管理',     icon: 'UserFilled',       perm: 'user:list',
                children: [
                  { title: '用户列表',   path: '/user/list',      perm: 'user:list' },
                ]},
  security:   { title: '安全运维',     icon: 'Lock',             perm: 'log:view',
                children: [
                  { title: '操作日志',   path: '/security/logs',  perm: 'log:view' },
                ]},
}

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    children: [
      { path: '', name: 'Home', component: () => import('../views/Home.vue') },
      { path: 'device/list', name: 'DeviceList', component: () => import('../views/device/DeviceList.vue'), meta: { perm: 'device:list' } },
      { path: 'device/category', name: 'DeviceCategory', component: () => import('../views/device/DeviceCategory.vue'), meta: { perm: 'category:manage' } },
      { path: 'borrow/apply', name: 'BorrowApply', component: () => import('../views/borrow/BorrowApply.vue'), meta: { perm: 'borrow:apply' } },
      { path: 'borrow/my', name: 'BorrowMy', component: () => import('../views/borrow/BorrowMy.vue'), meta: { perm: 'record:self' } },
      { path: 'borrow/approve', name: 'BorrowApprove', component: () => import('../views/borrow/BorrowApprove.vue'), meta: { perm: 'borrow:approve' } },
      { path: 'user/list', name: 'UserList', component: () => import('../views/user/UserList.vue'), meta: { perm: 'user:list' } },
      { path: 'security/logs', name: 'SecurityLogs', component: () => import('../views/security/OperationLogs.vue'), meta: { perm: 'log:view' } },
      { path: '403', name: 'Forbidden', component: () => import('../views/Forbidden.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('../views/NotFound.vue') },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = getToken()
  const perms = getPermissions()

  // 未登录 → 只能去 login/register
  if (!token) {
    if (to.meta.guest) return next()
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }

  // 已登录 → login/register 重定向到首页
  if (to.meta.guest) return next('/')

  // 权限校验
  const required = to.meta.perm
  if (required && !perms.includes(required)) {
    return next('/403')
  }

  next()
})

export default router
