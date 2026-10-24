import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', component: () => import('../views/LoginView.vue') },
  { path: '/register', component: () => import('../views/RegisterView.vue') },
  { path: '/', component: () => import('../views/ChatView.vue'), meta: { auth: true } },
  { path: '/documents', component: () => import('../views/DocumentsView.vue'), meta: { auth: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

// 路由守卫：未登录跳转登录页
router.beforeEach((to) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.auth && !token) return '/login'
  if ((to.path === '/login' || to.path === '/register') && token) return '/'
  return true
})

export default router
