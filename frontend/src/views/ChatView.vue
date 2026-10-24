<template>
  <el-container class="chat-page">
    <el-aside width="250px" class="sidebar">
      <div class="brand-row">
        <span class="mini-logo">⚖️</span>
        <span class="brand-name">LegalAI</span>
      </div>
      <el-button type="primary" class="new-chat-btn" round @click="newChat">＋ 新建对话</el-button>
      <div class="chat-list">
        <div
          v-for="c in chats"
          :key="c.id"
          class="chat-item"
          :class="{ active: c.id === currentChatId }"
          @click="switchChat(c.id)"
        >
          <span class="title">{{ c.title }}</span>
          <el-icon class="del" @click.stop="removeChat(c.id)"><Delete /></el-icon>
        </div>
      </div>
      <div class="sidebar-footer">
        <router-link to="/documents" class="doc-link">📄 合同分析</router-link>
        <el-button link size="small" @click="doLogout">退出登录</el-button>
      </div>
    </el-aside>

    <el-container class="right">
      <el-header class="topbar">
        <span class="topbar-title">智能法律问答</span>
        <span class="topbar-sub">回答基于法条知识库检索，仅供参考</span>
      </el-header>

      <div ref="listRef" class="messages">
        <div v-if="!messages.length" class="empty-state">
          <div class="empty-logo">⚖️</div>
          <h3>您好，我是法律智能助手</h3>
          <p>咨询法律问题，或点击输入框左侧 ＋ 上传合同 / 图片进行风险分析</p>
          <div class="suggests">
            <el-button v-for="s in suggests" :key="s" round size="small" @click="input = s; send()">
              {{ s }}
            </el-button>
          </div>
        </div>

        <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
          <div class="avatar">{{ m.role === 'user' ? '我' : '⚖️' }}</div>
          <div class="bubble">
            <!-- 附件消息：上传的合同/图片 -->
            <div v-if="m.attachment" class="attach-card" :class="m.attachment.status">
              <div class="attach-row">
                <span class="attach-icon">{{ attachIcon(m.attachment) }}</span>
                <span class="attach-name">{{ m.attachment.filename }}</span>
                <el-tag :type="statusType(m.attachment.status)" effect="light" size="small" round>
                  {{ statusText(m.attachment.status) }}
                </el-tag>
              </div>
              <el-button
                v-if="m.attachment.status === 'analyzed'"
                type="primary" size="small" round
                @click="openReport(m.attachment)"
              >查看风险报告</el-button>
            </div>

            <!-- 分析报告消息 -->
            <template v-else-if="m.report">
              <div class="report-mini">
                <h4>📋 合同分析完成：{{ m.report.filename }}</h4>
                <p class="report-summary">{{ m.report.summary }}</p>
                <div class="risk-tags">
                  <el-tag
                    v-for="(r, j) in (m.report.risk_items || [])" :key="j"
                    :type="levelType(r.risk_level)" size="small" effect="plain"
                  >{{ r.risk_level }}风险·{{ r.clause }}</el-tag>
                </div>
              </div>
              <el-button type="primary" size="small" round @click="openReport(m.report)">
                查看完整报告
              </el-button>
              <Disclaimer v-if="m.done" />
            </template>

            <!-- 普通文本消息 -->
            <template v-else>
              <div v-if="m.role === 'assistant'" class="md" v-html="renderMarkdown(m.content)"></div>
              <template v-else>{{ m.content }}</template>

              <el-collapse v-if="m.citations?.length" class="citations">
                <el-collapse-item :title="`📚 引用法条（${m.citations.length}）`">
                  <div v-for="(c, j) in m.citations" :key="j" class="citation">
                    <b>《{{ c.law_name }}》{{ c.article_no || '' }}</b>
                    <p>{{ c.chunk_text }}</p>
                  </div>
                </el-collapse-item>
              </el-collapse>

              <Disclaimer v-if="m.role === 'assistant' && m.done" />
            </template>
          </div>
        </div>
      </div>

      <div class="input-bar">
        <input
          ref="fileInput"
          type="file"
          accept=".pdf,.docx,.doc,.txt,.jpg,.jpeg,.png,.webp"
          style="display: none"
          @change="onFileSelected"
        />
        <el-tooltip content="上传合同 / 协议 / 图片进行风险分析" placement="top">
          <el-button
            class="plus-btn" circle :icon="Plus"
            :loading="uploading" @click="fileInput?.click()"
          />
        </el-tooltip>
        <el-input
          v-model="input"
          type="textarea"
          :rows="2"
          :autosize="{ minRows: 2, maxRows: 6 }"
          placeholder="请输入法律问题…（Enter 发送，Shift+Enter 换行）"
          @keydown.enter.exact.prevent="send"
        />
        <el-button type="primary" class="send-btn" :loading="streaming" @click="send">
          {{ streaming ? '回答中' : '发送' }}
        </el-button>
      </div>
    </el-container>

    <!-- 完整报告抽屉 -->
    <el-drawer v-model="reportDrawer" size="56%" title="合同风险分析报告">
      <template v-if="reportData">
        <div class="report-section">
          <h3>📋 总体评价</h3>
          <p class="drawer-summary">{{ reportData.summary }}</p>
        </div>
        <div class="report-section">
          <h3>⚠️ 风险条目（{{ reportData.risk_items?.length || 0 }}）</h3>
          <div v-for="(item, i) in reportData.risk_items" :key="i" class="risk-item">
            <div class="risk-head">
              <el-tag :type="levelType(item.risk_level)" effect="dark" size="small">{{ item.risk_level }}风险</el-tag>
              <b>{{ item.clause }}</b>
            </div>
            <p class="risk-line"><span class="label">问题：</span>{{ item.problem }}</p>
            <p class="risk-line"><span class="label">建议：</span>{{ item.advice }}</p>
            <p class="risk-line"><span class="label">依据：</span>{{ item.legal_basis }}</p>
          </div>
        </div>
        <Disclaimer />
      </template>
      <el-empty v-else description="暂无报告" />
    </el-drawer>
  </el-container>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Plus } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import Disclaimer from '../components/Disclaimer.vue'
import api from '../api/client'
import { askStream, createChat, deleteChat, listChats, listMessages } from '../api/chat'
import { logout } from '../api/auth'

const router = useRouter()
const chats = ref([])
const currentChatId = ref(null)
const messages = ref([])
const input = ref('')
const streaming = ref(false)
const uploading = ref(false)
const listRef = ref()
const fileInput = ref()
const reportDrawer = ref(false)
const reportData = ref(null)
const pollTimers = new Map()  // docId -> interval，避免组件销毁后残留轮询

const suggests = [
  '劳动合同不签有什么风险？',
  '租房合同违约金过高怎么办？',
  '离婚时财产如何分割？',
]

onMounted(loadChats)
onUnmounted(() => pollTimers.forEach((t) => clearInterval(t)))

async function loadChats() {
  chats.value = await listChats()
  if (chats.value.length) switchChat(chats.value[0].id)
}

async function newChat() {
  const chat = await createChat()
  chats.value.unshift(chat)
  switchChat(chat.id)
}

async function switchChat(id) {
  currentChatId.value = id
  messages.value = await listMessages(id)
  scrollBottom()
}

async function removeChat(id) {
  await deleteChat(id)
  chats.value = chats.value.filter((c) => c.id !== id)
  if (currentChatId.value === id) {
    currentChatId.value = null
    messages.value = []
    if (chats.value.length) switchChat(chats.value[0].id)
  }
}

// ---------- 附件上传（＋号按钮） ----------
function attachIcon(a) {
  const s = (a.file_type || a.filename || '').toLowerCase()
  if (/\.(jpg|jpeg|png|webp)/.test(s)) return '🖼️'
  if (s.endsWith('.pdf')) return '📕'
  if (s.endsWith('.txt')) return '📄'
  return '📄'
}
function statusType(s) {
  return { pending: 'info', parsing: 'warning', analyzed: 'success', failed: 'danger' }[s] || 'info'
}
function statusText(s) {
  return { pending: '排队中', parsing: '分析中…', analyzed: '✓ 已分析', failed: '分析失败' }[s] || s
}
function levelType(l) {
  return { 高: 'danger', 中: 'warning', 低: 'success' }[l] || 'info'
}

async function onFileSelected(e) {
  const file = e.target.files?.[0]
  e.target.value = '' // 允许重复选择同一文件
  if (!file) return
  if (!currentChatId.value) await newChat()

  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', file)
    const doc = await api.post('/documents/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    // 在对话流中插入附件卡片
    const msg = ref({ role: 'user', attachment: { ...doc } })
    messages.value.push(msg.value)
    scrollBottom()
    watchDocument(doc.id, msg, file.name)
    ElMessage.success('上传成功，正在分析…')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

function watchDocument(docId, msgRef, filename) {
  const timer = setInterval(async () => {
    try {
      const doc = await api.get(`/documents/${docId}/status`)
      msgRef.value.attachment = { ...msgRef.value.attachment, ...doc }
      if (doc.status === 'analyzed' || doc.status === 'failed') {
        clearInterval(timer)
        pollTimers.delete(docId)
        if (doc.status === 'failed') {
          messages.value.push({
            role: 'assistant', done: true,
            content: `抱歉，「${filename}」分析失败，可能是文件损坏或内容无法识别。请尝试重新上传，或使用清晰度更高的图片。`,
          })
          scrollBottom()
          return
        }
        // 分析完成：拉取报告，作为助手消息插入对话流
        const report = await api.get(`/documents/${docId}/report`)
        messages.value.push({
          role: 'assistant', done: true,
          report: { ...report, filename, document_id: docId },
        })
        scrollBottom()
      }
    } catch {
      clearInterval(timer)
      pollTimers.delete(docId)
    }
  }, 4000)
  pollTimers.set(docId, timer)
}

async function openReport(r) {
  // r 可能是 attachment（只有 doc_id）或完整报告
  if (r.risk_items) {
    reportData.value = r
    reportDrawer.value = true
    return
  }
  try {
    reportData.value = await api.get(`/documents/${r.id}/report`)
    reportDrawer.value = true
  } catch {
    ElMessage.warning('报告尚未生成，请稍后再试')
  }
}

// ---------- 文字问答 ----------
async function send() {
  const question = input.value.trim()
  if (!question || streaming.value) return
  if (!currentChatId.value) await newChat()

  input.value = ''
  messages.value.push({ role: 'user', content: question })
  const assistant = ref({ role: 'assistant', content: '', citations: [], done: false })
  messages.value.push(assistant.value)
  streaming.value = true
  scrollBottom()

  try {
    await askStream(currentChatId.value, question, {
      onToken: (t) => {
        assistant.value.content += t
        scrollBottom()
      },
      onCitations: (c) => (assistant.value.citations = c),
      onDone: () => (assistant.value.done = true),
    })
  } catch (e) {
    ElMessage.error(e.message || '问答失败')
  } finally {
    streaming.value = false
    scrollBottom()
  }
}

function renderMarkdown(text) {
  return marked.parse(text || '', { async: false })
}

function scrollBottom() {
  nextTick(() => listRef.value?.scrollTo({ top: listRef.value.scrollHeight, behavior: 'smooth' }))
}

function doLogout() {
  logout()
  router.push('/login')
}
</script>

<style scoped>
.chat-page { height: 100vh; }
.sidebar {
  background: #1e293b; color: #cbd5e1; padding: 16px 12px;
  display: flex; flex-direction: column;
}
.brand-row { display: flex; align-items: center; gap: 8px; padding: 0 6px 14px; }
.mini-logo { font-size: 20px; }
.brand-name { font-weight: 600; color: #f1f5f9; letter-spacing: 1px; }
.new-chat-btn { width: 100%; border-radius: 10px; }
.chat-list { flex: 1; overflow-y: auto; margin-top: 14px; }
.chat-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 9px 10px; margin-bottom: 2px; border-radius: 8px;
  cursor: pointer; font-size: 13px; color: #cbd5e1;
}
.chat-item:hover { background: rgba(255, 255, 255, .08); }
.chat-item.active { background: rgba(59, 130, 246, .25); color: #fff; }
.chat-item .title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chat-item .del { opacity: 0; transition: opacity .15s; }
.chat-item:hover .del { opacity: .8; }
.sidebar-footer {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; border-top: 1px solid rgba(255, 255, 255, .1); padding-top: 12px;
}
.doc-link { color: #93c5fd; text-decoration: none; }
.right { display: flex; flex-direction: column; background: #f1f5f9; }
.topbar {
  background: #fff; border-bottom: 1px solid #e2e8f0;
  display: flex; align-items: baseline; gap: 12px; height: 52px;
}
.topbar-title { font-weight: 600; color: #1e293b; font-size: 15px; }
.topbar-sub { font-size: 12px; color: #94a3b8; }
.messages { flex: 1; overflow-y: auto; padding: 24px 8%; }
.empty-state { text-align: center; margin-top: 12vh; color: #64748b; }
.empty-logo { font-size: 48px; margin-bottom: 10px; }
.empty-state h3 { color: #334155; margin: 0 0 6px; }
.empty-state p { font-size: 13px; margin: 0 0 14px; }
.suggests { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
.msg { display: flex; margin-bottom: 18px; gap: 10px; }
.msg.user { flex-direction: row-reverse; }
.avatar {
  flex-shrink: 0; width: 34px; height: 34px; border-radius: 50%;
  background: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 13px; box-shadow: 0 1px 3px rgba(0, 0, 0, .1);
}
.msg.user .avatar { background: linear-gradient(135deg, #2563eb, #0ea5e9); color: #fff; font-size: 12px; }
.bubble {
  max-width: 78%; background: #fff; border-radius: 12px; padding: 12px 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, .06); font-size: 14px; line-height: 1.7;
}
.msg.user .bubble {
  background: linear-gradient(135deg, #2563eb, #3b82f6); color: #fff;
  border-top-right-radius: 4px;
}
.msg.assistant .bubble { border-top-left-radius: 4px; }
.msg.user .bubble:has(.attach-card) {
  background: #fff; color: #334155; border-top-right-radius: 12px;
}
.attach-card { min-width: 260px; }
.attach-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.attach-icon { font-size: 22px; }
.attach-name { font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 220px; }
.report-mini h4 { margin: 0 0 8px; color: #1e293b; }
.report-summary { font-size: 13px; color: #475569; margin: 0 0 10px; line-height: 1.7; }
.risk-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; }
.md :deep(p) { margin: 6px 0; }
.md :deep(ul), .md :deep(ol) { padding-left: 20px; margin: 6px 0; }
.citations { margin-top: 10px; border: none; --el-collapse-header-height: 32px; }
.citations :deep(.el-collapse-item__header) { font-size: 12px; color: #64748b; }
.citation { font-size: 13px; margin-bottom: 10px; padding: 8px 10px; background: #f8fafc; border-radius: 8px; }
.citation b { color: #2563eb; font-weight: 600; }
.citation p { margin: 4px 0 0; color: #475569; font-size: 12px; }
.input-bar {
  display: flex; gap: 10px; padding: 14px 8%; background: #fff;
  border-top: 1px solid #e2e8f0; align-items: flex-end;
}
.input-bar :deep(.el-textarea__inner) { border-radius: 10px; }
.plus-btn { height: 44px; width: 44px; font-size: 18px; border-radius: 50%; }
.send-btn { border-radius: 10px; min-width: 90px; height: 44px; }
.report-section { margin-bottom: 24px; }
.report-section h3 { color: #1e293b; margin: 0 0 12px; }
.drawer-summary {
  background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 10px;
  padding: 14px 16px; line-height: 1.8; color: #334155; font-size: 14px;
}
.risk-item {
  border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 16px;
  margin-bottom: 12px; background: #fff;
}
.risk-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.risk-head b { color: #1e293b; }
.risk-line { margin: 4px 0; font-size: 13px; line-height: 1.7; color: #475569; }
.label { color: #94a3b8; }
</style>
