<template>
  <div class="auth-wrap">
    <div class="auth-card">
      <div class="brand">
        <div class="logo">⚖️</div>
        <h2>LegalAI 法律智能助手</h2>
        <p class="subtitle">智能法律问答 · 合同风险审查</p>
      </div>
      <el-form :model="form" @submit.prevent="submit">
        <el-form-item>
          <el-input v-model="form.username" placeholder="用户名" size="large" prefix-icon="User" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" size="large" show-password prefix-icon="Lock" />
        </el-form-item>
        <el-button type="primary" :loading="loading" native-type="submit" class="submit-btn" size="large">
          登 录
        </el-button>
      </el-form>
      <div class="links">
        <router-link to="/register">没有账号？立即注册 →</router-link>
      </div>
      <div class="foot-note">AI 生成内容仅供参考，不构成法律意见</div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { login } from '../api/auth'

const router = useRouter()
const form = reactive({ username: '', password: '' })
const loading = ref(false)

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await login(form)
    router.push('/')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-wrap {
  display: flex; justify-content: center; align-items: center; min-height: 100vh;
  background: linear-gradient(135deg, #eef2ff 0%, #e0f2fe 45%, #f0fdfa 100%);
}
.auth-card {
  width: 400px; padding: 40px 36px 28px; border-radius: 16px;
  background: rgba(255, 255, 255, .85); backdrop-filter: blur(12px);
  box-shadow: 0 8px 40px rgba(30, 64, 175, .12); text-align: center;
}
.brand { margin-bottom: 28px; }
.logo {
  width: 64px; height: 64px; margin: 0 auto 14px; border-radius: 18px;
  background: linear-gradient(135deg, #2563eb, #0ea5e9);
  display: flex; align-items: center; justify-content: center; font-size: 32px;
  box-shadow: 0 6px 18px rgba(37, 99, 235, .35);
}
.brand h2 { margin: 0 0 6px; color: #1e293b; letter-spacing: 1px; }
.subtitle { margin: 0; font-size: 13px; color: #94a3b8; }
.submit-btn { width: 100%; margin-top: 4px; border-radius: 10px; letter-spacing: 6px; }
.links { margin-top: 16px; font-size: 13px; }
.links a { color: #2563eb; text-decoration: none; }
.foot-note { margin-top: 22px; font-size: 11px; color: #cbd5e1; }
</style>
