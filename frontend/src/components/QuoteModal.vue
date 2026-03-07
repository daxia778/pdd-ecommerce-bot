<template>
  <div v-if="isOpen" class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl w-full max-w-md shadow-2xl flex flex-col overflow-hidden animate-[modal-pop_0.2s_ease-out]">
      <!-- Header -->
      <div class="p-4 bg-gradient-to-r from-purple-600 to-indigo-600 flex justify-between items-center text-white">
        <h3 class="font-bold flex items-center">
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
          生成正规报价单
        </h3>
        <button @click="close" class="text-white/80 hover:text-white transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
      </div>

      <!-- Preview Body -->
      <div class="p-5 bg-gray-50 flex-1">
        <div class="bg-white border shadow-sm p-4 rounded-xl text-sm leading-relaxed text-gray-700 relative">
          <!-- Text content -->
          <pre class="whitespace-pre-wrap font-sans">{{ formattedQuote }}</pre>

          <button @click="copyToClipboard" class="absolute top-3 right-3 p-1.5 bg-gray-100 hover:bg-purple-100 text-gray-500 hover:text-purple-600 rounded-lg transition-colors border shadow-sm" title="一键复制">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
          </button>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-4 border-t bg-white flex justify-end gap-3">
        <button @click="close" class="px-4 py-2 text-sm font-bold text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">取消</button>
        <button @click="sendToChat" class="px-5 py-2 text-sm font-bold text-white bg-purple-600 hover:bg-purple-700 rounded-lg shadow-md shadow-purple-200 transition-all flex items-center">
          直接发送给买家
          <svg class="w-4 h-4 ml-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  isOpen: Boolean,
  reqData: Object
});

const emit = defineEmits(['close', 'send']);

const formattedQuote = computed(() => {
  if (!props.reqData) return '';
  const r = props.reqData;
  return `📋 【智小设 PPT 定制报价单】
─────────────────────
📝 项目类型：${r.topic || '-'}
📄 规划页数：${r.pages || '-'}
🎨 视觉风格：${r.style || '-'}
⏱️ 交付时间：${r.deadline || '-'}
🎯 交付人群：${r.audience || '-'}
${r.isUrgent ? '⚠️加急处理：是\n' : ''}
💰 参考报价：${r.budget || '待定'}
─────────────────────
如确认以上需求无误，请点击支付定金开始排期。感谢信任！`;
});

const close = () => {
  emit('close');
};

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(formattedQuote.value);
    alert('已复制到剪贴板！');
  } catch (err) {
    console.error('复制失败', err);
  }
};

const sendToChat = () => {
  emit('send', formattedQuote.value);
  close();
};
</script>

<style scoped>
@keyframes modal-pop {
  0% { transform: scale(0.95); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
</style>
