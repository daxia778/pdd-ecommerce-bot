<template>
  <div class="h-full flex flex-col bg-gray-950 text-gray-200 rounded-2xl overflow-hidden border border-gray-800 shadow-2xl">
    <!-- Header -->
    <div class="px-4 py-3 bg-gray-900 border-b border-gray-800 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 rounded-full animate-pulse" :class="isLive ? 'bg-green-400' : 'bg-gray-600'"></div>
        <h3 class="text-sm font-bold text-white tracking-wide">🔬 模拟测试面板</h3>
        <span class="text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded font-mono">{{ logs.length }} 条</span>
      </div>
      <div class="flex items-center gap-1.5">
        <button @click="exportLogs" class="text-[10px] bg-gray-800 hover:bg-gray-700 text-gray-300 px-2 py-1 rounded font-bold transition">导出</button>
        <button @click="clearLogs" class="text-[10px] bg-gray-800 hover:bg-red-900/50 text-gray-400 hover:text-red-400 px-2 py-1 rounded font-bold transition">清空</button>
      </div>
    </div>

    <!-- Summary Bar -->
    <div v-if="logs.length" class="px-4 py-2 bg-gray-900/50 border-b border-gray-800/50 flex items-center gap-3 text-[10px] font-mono shrink-0 flex-wrap">
      <span class="text-gray-500">AVG TTFT:</span>
      <span :class="avgTTFT <= 3000 ? 'text-green-400' : avgTTFT <= 8000 ? 'text-yellow-400' : 'text-red-400'" class="font-bold">{{ avgTTFT }}ms</span>
      <span class="text-gray-700">|</span>
      <span class="text-gray-500">AVG Total:</span>
      <span class="text-blue-400 font-bold">{{ avgTotal }}ms</span>
      <span class="text-gray-700">|</span>
      <span class="text-gray-500">成功率:</span>
      <span class="font-bold" :class="successRate >= 95 ? 'text-green-400' : 'text-yellow-400'">{{ successRate }}%</span>
      <span class="text-gray-700">|</span>
      <span class="text-gray-500">流式:</span>
      <span class="text-purple-400 font-bold">{{ streamingRate }}%</span>
    </div>

    <!-- Log Entries -->
    <div class="flex-1 overflow-y-auto custom-scroll">
      <div v-if="!logs.length" class="flex flex-col items-center justify-center h-full text-gray-600 gap-2">
        <svg class="w-10 h-10 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
        <p class="text-xs font-medium">在买家模拟器中发送消息开始测试</p>
      </div>

      <div v-for="(log, idx) in logs" :key="idx"
           class="border-b border-gray-800/50 transition-all"
           :class="log.error ? 'bg-red-950/30' : ''">
        <!-- Compact Header -->
        <div @click="log.expanded = !log.expanded"
             class="px-4 py-2.5 cursor-pointer hover:bg-gray-900/80 flex items-center gap-2 transition">
          <span class="text-[10px] font-mono text-gray-600 w-5">#{{ idx + 1 }}</span>

          <!-- Status Icon -->
          <div class="w-4 h-4 rounded-full flex items-center justify-center text-[8px] shrink-0"
               :class="log.error ? 'bg-red-500/20 text-red-400' : log.d?.greeting_fastpath ? 'bg-blue-500/20 text-blue-400' : 'bg-green-500/20 text-green-400'">
            {{ log.error ? '✗' : '✓' }}
          </div>

          <!-- User Message Preview -->
          <span class="text-[11px] text-gray-300 truncate flex-1 font-medium">{{ log.userMessage }}</span>

          <!-- Key Metrics -->
          <div class="flex items-center gap-2 shrink-0">
            <span v-if="log.frontendTTFT" class="text-[10px] font-mono font-bold"
                  :class="log.frontendTTFT <= 3000 ? 'text-green-400' : log.frontendTTFT <= 8000 ? 'text-yellow-400' : 'text-red-400'">
              {{ log.frontendTTFT }}ms
            </span>
            <span v-if="log.d?.char_count" class="text-[10px] font-mono text-gray-500">{{ log.d.char_count }}字</span>
            <svg class="w-3 h-3 text-gray-600 transition-transform" :class="log.expanded ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
          </div>
        </div>

        <!-- Expanded Detail -->
        <div v-if="log.expanded" class="px-4 pb-3 space-y-2 animate-fadeIn">
          <!-- Timing Section -->
          <div class="bg-gray-900 rounded-lg p-3 space-y-1.5">
            <div class="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-1">⏱ 耗时指标</div>
            <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px]">
              <div class="flex justify-between">
                <span class="text-gray-500">前端 TTFT</span>
                <span class="font-mono font-bold" :class="ttftColor(log.frontendTTFT)">{{ log.frontendTTFT ?? '-' }}ms</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">后端 TTFT</span>
                <span class="font-mono font-bold" :class="ttftColor(log.d?.backend_ttft_ms)">{{ log.d?.backend_ttft_ms ?? '-' }}ms</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">LLM TTFT</span>
                <span class="font-mono font-bold" :class="ttftColor(log.d?.llm_ttft_ms)">{{ log.d?.llm_ttft_ms ?? '-' }}ms</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">后端总耗时</span>
                <span class="font-mono text-blue-400">{{ log.d?.backend_total_ms ?? '-' }}ms</span>
              </div>
            </div>
          </div>

          <!-- Model & Stream Section -->
          <div class="bg-gray-900 rounded-lg p-3 space-y-1.5">
            <div class="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-1">🤖 模型 & 传输</div>
            <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px]">
              <div class="flex justify-between">
                <span class="text-gray-500">模型</span>
                <span class="font-mono text-cyan-400">{{ log.d?.model ?? '-' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">厂商</span>
                <span class="font-mono text-gray-300">{{ log.d?.provider ?? '-' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">流式传输</span>
                <span class="font-bold" :class="log.d?.streaming ? 'text-green-400' : 'text-yellow-400'">{{ log.d?.streaming ? '✓ SSE' : '✗ 非流式' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Chunk 数</span>
                <span class="font-mono text-gray-300">{{ log.d?.chunk_count ?? '-' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">输出字数</span>
                <span class="font-mono text-gray-300">{{ log.d?.char_count ?? '-' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">快速通道</span>
                <span :class="log.d?.greeting_fastpath ? 'text-blue-400' : 'text-gray-600'">{{ log.d?.greeting_fastpath ? '⚡ 是' : '否' }}</span>
              </div>
            </div>
          </div>

          <!-- RAG & Safety Section -->
          <div class="bg-gray-900 rounded-lg p-3 space-y-1.5">
            <div class="text-[10px] text-gray-500 font-bold uppercase tracking-wider mb-1">📚 RAG & 安全</div>
            <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px]">
              <div class="flex justify-between">
                <span class="text-gray-500">RAG 检索</span>
                <span :class="log.d?.rag_used ? 'text-green-400' : 'text-gray-600'">{{ log.d?.rag_used ? '✓ 已调用' : '未调用' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">RAG 文档数</span>
                <span class="font-mono text-gray-300">{{ log.d?.rag_docs_count ?? 0 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">Guardrail</span>
                <span :class="log.d?.guardrail_blocked ? 'text-red-400 font-bold' : 'text-green-400'">{{ log.d?.guardrail_blocked ? '🛡 已拦截' : '通过' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-500">人工升级</span>
                <span :class="log.escalated ? 'text-orange-400 font-bold' : 'text-gray-600'">{{ log.escalated ? '⚠ 是' : '否' }}</span>
              </div>
            </div>
            <div v-if="log.d?.guardrail_rules?.length" class="mt-1 text-[10px] text-red-400 bg-red-950/50 rounded px-2 py-1">
              触发规则: {{ log.d.guardrail_rules.join(', ') }}
            </div>
          </div>

          <!-- Error Section -->
          <div v-if="log.error" class="bg-red-950/50 rounded-lg p-3 border border-red-900/50">
            <div class="text-[10px] text-red-400 font-bold uppercase tracking-wider mb-1">❌ 异常</div>
            <p class="text-[11px] text-red-300 font-mono break-all">{{ log.errorMessage }}</p>
          </div>

          <!-- Timestamp -->
          <div class="text-[9px] text-gray-600 text-right font-mono">{{ log.timestamp }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const logs = ref([]);
const isLive = ref(true);

// ====== Public API (called by BuyerSimulator) ======
const addLog = (entry) => {
  logs.value.unshift({
    ...entry,
    expanded: logs.value.length === 0, // auto-expand first entry
    timestamp: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
  });
};

// ====== Computed Stats ======
const validLogs = computed(() => logs.value.filter(l => !l.error && l.d));

const avgTTFT = computed(() => {
  const vals = validLogs.value.filter(l => l.frontendTTFT).map(l => l.frontendTTFT);
  return vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0;
});

const avgTotal = computed(() => {
  const vals = validLogs.value.filter(l => l.d?.backend_total_ms).map(l => l.d.backend_total_ms);
  return vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : 0;
});

const successRate = computed(() => {
  if (!logs.value.length) return 100;
  return Math.round((logs.value.filter(l => !l.error).length / logs.value.length) * 100);
});

const streamingRate = computed(() => {
  if (!validLogs.value.length) return 0;
  return Math.round((validLogs.value.filter(l => l.d?.streaming).length / validLogs.value.length) * 100);
});

// ====== Helpers ======
const ttftColor = (ms) => {
  if (!ms && ms !== 0) return 'text-gray-600';
  if (ms <= 2000) return 'text-green-400';
  if (ms <= 5000) return 'text-yellow-400';
  return 'text-red-400';
};

const clearLogs = () => { logs.value = []; };

const exportLogs = () => {
  const data = logs.value.map(l => ({
    timestamp: l.timestamp,
    userMessage: l.userMessage,
    frontendTTFT: l.frontendTTFT,
    error: l.error,
    errorMessage: l.errorMessage,
    diagnostics: l.d,
    escalated: l.escalated,
  }));
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `sim_test_${new Date().toISOString().slice(0, 16).replace(/[:-]/g, '')}.json`;
  a.click();
  URL.revokeObjectURL(url);
};

defineExpose({ addLog });
</script>

<style scoped>
.custom-scroll::-webkit-scrollbar { width: 4px; }
.custom-scroll::-webkit-scrollbar-track { background: transparent; }
.custom-scroll::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
.custom-scroll::-webkit-scrollbar-thumb:hover { background: #4B5563; }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn { animation: fadeIn 0.2s ease-out; }
</style>
