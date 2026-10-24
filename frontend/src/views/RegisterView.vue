<template>
  <div class="auth-wrap">
    <div class="auth-card">
      <div class="brand">
        <div class="logo">⚖️</div>
        <h2>创建账号</h2>
        <p class="subtitle">注册后即可使用法律问答与合同分析</p>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="submit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名（3-50 字符）" size="large" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="email">
          <el-input v-model="form.email" placeholder="邮箱" size="large" prefix-icon="Message" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码（至少 8 位）" size="large" show-password prefix-icon="Lock" />
        </el-form-item>
        <el-button type="primary" :loading="loading" native-type="submit" class="submit-btn" size="large">
          注 册
        </el-button>
      </el-form>
      <div class="links">
        <router-link to="/login">已有账号？返回登录 →</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { register } from '../api/auth'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', email: '', password: '' })

const rules = {
  username: [{ required: true, min: 3, max: 50, message: '用户名 3-50 字符', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少 8 位', trigger: 'blur' },
  ],
}

async function submit() {
  await formRef.value.validate().catch(() => Promise.reject())
  loading.value = true
  try {
    await register(form)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '注册失败')
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
</style>
