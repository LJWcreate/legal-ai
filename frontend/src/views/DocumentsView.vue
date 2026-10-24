<template>
  <div class="docs-page">
    <div class="topbar">
      <router-link to="/" class="back-link">← 返回对话</router-link>
      <div class="title-row">
        <span class="page-icon">📄</span>
        <h2>合同 / 协议风险分析</h2>
      </div>
      <p class="page-sub">上传合同文件，AI 逐条审查并输出结构化风险报告</p>
    </div>

    <el-upload
      drag
      class="upload-zone"
      :auto-upload="false"
      :show-file-list="false"
      accept=".pdf,.docx,.doc,.txt,.jpg,.jpeg,.png,.webp"
      :on-change="handleFile"
    >
      <el-icon class="upload-icon"><upload-filled /></el-icon>
      <div class="upload-text">拖拽文件到此处，或<em>点击上传</em></div>
      <template #tip>
        <div class="upload-tip">支持 pdf / docx / doc / txt / 图片（jpg·png·webp，自动 OCR 识别），最大 20MB，文件仅本人可见</div>
      </template>
    </el-upload>

    <el-card class="table-card" shadow="never">
      <el-table :data="docs" style="width: 100%" v-loading="loading" :header-cell-style="{ background: '#f8fafc', color: '#475569' }">
        <el-table-column prop="filename" label="文件名" min-width="200">
          <template #default="{ row }">
            <span class="file-name">📎 {{ row.filename }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="{ row }">{{ (row.file_size / 1024).toFixed(1) }} KB</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" effect="light" round>{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button size="small" type="primary" round :disabled="row.status !== 'analyzed'" @click="viewReport(row)">
              查看报告
            </el-button>
            <el-button size="small" type="danger" plain round @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="暂无文档，先上传一份合同试试" :image-size="90" />
        </template>
      </el-table>
    </el-card>

    <el-drawer v-model="drawer" size="56%" title="合同风险分析报告" class="report-drawer">
      <template v-if="report">
        <div class="report-section">
          <h3>📋 总体评价</h3>
          <p class="summary">{{ report.summary }}</p>
        </div>
        <div class="report-section">
          <h3>⚠️ 风险条目（{{ report.risk_items?.length || 0 }}）</h3>
          <div v-for="(item, i) in report.risk_items" :key="i" class="risk-item">
            <div class="risk-head">
              <el-tag :type="levelType(item.risk_level)" effect="dark" size="small">{{ item.risk_level }}风险</el-tag>
              <b>{{ item.clause }}</b>
            </div>
            <p class="risk-problem"><span class="label">问题：</span>{{ item.problem }}</p>
            <p class="risk-advice"><span class="label">建议：</span>{{ item.advice }}</p>
            <p class="risk-basis"><span class="label">依据：</span>{{ item.legal_basis }}</p>
          </div>
        </div>
        <Disclaimer />
      </template>
      <el-empty v-else description="暂无报告" />
    </el-drawer>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import Disclaimer from '../components/Disclaimer.vue'
import api from '../api/client'

const docs = ref([])
const loading = ref(false)
const drawer = ref(false)
const report = ref(null)
let pollTimer = null

onMounted(async () => {
  await loadDocs()
  pollTimer = setInterval(loadDocs, 5000) // 解析中的文档轮询状态
})
onUnmounted(() => clearInterval(pollTimer))

async function loadDocs() {
  loading.value = docs.value.length === 0
  try {
    docs.value = await api.get('/documents')
  } finally {
    loading.value = false
  }
}

async function handleFile(file) {
  const fd = new FormData()
  fd.append('file', file.raw)
  try {
    await api.post('/documents/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    ElMessage.success('上传成功，正在解析分析…')
    loadDocs()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '上传失败')
  }
}

async function viewReport(row) {
  report.value = await api.get(`/documents/${row.id}/report`)
  drawer.value = true
}

async function remove(row) {
  await api.delete(`/documents/${row.id}`)
  loadDocs()
}

function statusType(s) {
  return { pending: 'info', parsing: 'warning', analyzed: 'success', failed: 'danger' }[s] || 'info'
}
function statusText(s) {
  return { pending: '排队中', parsing: '分析中', analyzed: '已分析', failed: '失败' }[s] || s
}
function levelType(l) {
  return { 高: 'danger', 中: 'warning', 低: 'success' }[l] || 'info'
}
</script>

<style scoped>
.docs-page { max-width: 960px; margin: 0 auto; padding: 32px 24px; }
.topbar { margin-bottom: 24px; }
.back-link { font-size: 13px; color: #2563eb; text-decoration: none; }
.title-row { display: flex; align-items: center; gap: 10px; margin-top: 14px; }
.title-row h2 { margin: 0; color: #1e293b; }
.page-icon { font-size: 26px; }
.page-sub { margin: 6px 0 0; font-size: 13px; color: #94a3b8; }
.upload-zone :deep(.el-upload-dragger) {
  border-radius: 14px; padding: 36px 0;
  border-color: #cbd5e1; background: rgba(255, 255, 255, .7);
}
.upload-zone :deep(.el-upload-dragger:hover) { border-color: #2563eb; }
.upload-icon { font-size: 44px; color: #93c5fd; margin-bottom: 8px; }
.upload-text { color: #475569; }
.upload-text em { color: #2563eb; font-style: normal; }
.upload-tip { margin-top: 8px; font-size: 12px; color: #94a3b8; }
.table-card { margin-top: 20px; border-radius: 14px; border: 1px solid #e2e8f0; }
.file-name { color: #334155; }
.report-section { margin-bottom: 24px; }
.report-section h3 { color: #1e293b; margin: 0 0 12px; }
.summary {
  background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 10px;
  padding: 14px 16px; line-height: 1.8; color: #334155; font-size: 14px;
}
.risk-item {
  border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 16px;
  margin-bottom: 12px; background: #fff;
}
.risk-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.risk-head b { color: #1e293b; }
.risk-item p { margin: 4px 0; font-size: 13px; line-height: 1.7; color: #475569; }
.label { color: #94a3b8; }
</style>
