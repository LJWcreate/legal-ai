import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // SSE 流式接口不能走 axios 拦截器包装，直连后端；其余接口同代理
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
