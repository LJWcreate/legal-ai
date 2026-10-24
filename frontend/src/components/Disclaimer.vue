<template>
  <div class="disclaimer">{{ text }}</div>
</template>

<script setup>
// 免责声明组件：所有 AI 输出区域统一挂载，文案与后端 config.disclaimer 一致
const text =
  '本内容仅作参考，不构成法律意见，不能代替执业律师的专业判断，请结合实际情况甄别。'
</script>

<style scoped>
.disclaimer {
  margin-top: 8px;
  padding: 6px 10px;
  font-size: 12px;
  color: #909399;
  background: #f4f4f5;
  border-left: 3px solid #dcdfe6;
  border-radius: 4px;
}
</style>
