import api from './client'

export async function listChats() {
  return api.get('/chats')
}

export async function createChat(title = '新对话') {
  return api.post('/chats', { title })
}

export async function listMessages(chatId) {
  return api.get(`/chats/${chatId}/messages`)
}

export async function deleteChat(chatId) {
  return api.delete(`/chats/${chatId}`)
}

/**
 * SSE 流式问答：token → citations → done（done 附带免责声明）
 * POST 无法用 EventSource，这里用 fetch + ReadableStream 手工解析 SSE。
 */
export async function askStream(chatId, question, { onToken, onCitations, onDone }) {
  const resp = await fetch(`/api/v1/chats/${chatId}/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
    },
    body: JSON.stringify({ question }),
  })
  if (!resp.ok) {
    if (resp.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    throw new Error(`请求失败 (${resp.status})`)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  const parseEvent = (block) => {
    const eventMatch = block.match(/^event:\s*(.+)$/m)
    const dataMatch = block.match(/^data:\s*([\s\S]+)$/m)
    if (!eventMatch || !dataMatch) return
    const event = eventMatch[1].trim()
    const data = JSON.parse(dataMatch[1])
    if (event === 'token') onToken?.(data)
    else if (event === 'citations') onCitations?.(data)
    else if (event === 'done') onDone?.(data)
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() // 最后一块可能不完整，留到下一轮
    for (const block of blocks) if (block.trim()) parseEvent(block)
  }
  if (buffer.trim()) parseEvent(buffer)
}
