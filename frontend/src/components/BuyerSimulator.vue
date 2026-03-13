<template>
  <div class="h-full flex gap-4 p-4 overflow-hidden">
    <!-- Left: Mobile Phone Container -->
    <div class="w-full lg:w-[380px] h-[750px] max-h-full card-enterprise overflow-hidden flex flex-col shrink-0 mx-auto lg:mx-0">

      <!-- Dynamic Island Notch -->
      <div class="h-8 w-full absolute top-0 z-30 flex justify-center pointer-events-none mt-2">
         <div class="w-32 h-7 bg-black rounded-full flex items-center justify-between px-2 shadow-sm ring-1 ring-black/10">
            <div class="w-3 h-3 rounded-full bg-gray-900 border border-gray-800 shadow-inner flex items-center justify-center">
                <div class="w-1 h-1 rounded-full bg-blue-900/30"></div>
            </div>
            <div class="w-1.5 h-1.5 rounded-full bg-gray-800 opacity-80"></div>
         </div>
      </div>

      <!-- App Header -->
      <div class="pt-12 pb-3 px-4 bg-gray-50 flex items-center justify-between border-b z-10 sticky top-0 shrink-0">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-gray-50 border border-gray-200 rounded-md flex items-center justify-center shadow-sm">
              <span class="text-white text-lg font-black tracking-tighter">多</span>
            </div>
            <div>
              <h2 class="font-extrabold text-[#E02E24] text-lg leading-tight">拼多多商家客服</h2>
              <p class="text-[10px] text-gray-500 font-medium">云芊艺小店 · 智小设AI客服</p>
            </div>
        </div>
        <div class="flex items-center gap-2">
            <button @click="clearChat" class="text-xs bg-white border border-gray-300 text-gray-600 px-3 py-1 rounded-md font-medium hover:bg-gray-50" title="清空历史">清空</button>
        </div>
      </div>

      <!-- Chat Area -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4 bg-[#f4f4f4] scrollbar-hide relative" ref="chatContainer">

        <!-- Welcome Message -->
        <div class="flex items-start gap-2 max-w-[85%]">
            <div class="w-8 h-8 rounded-full bg-gray-200 border border-gray-300 flex items-center justify-center flex-shrink-0 text-gray-600 font-semibold text-xs mt-1">系</div>
            <div class="bg-[#F2F4F7] p-3 rounded-lg rounded-tl-sm">
                <p class="text-[13px] text-gray-800 leading-relaxed font-medium">亲，在的呢！我是云芊艺小店的智小设AI客服，专注PPT/BP/课件定制，请问有什么可以帮您的呀？</p>
            </div>
        </div>

        <!-- Chat History -->
        <div v-for="(msg, index) in messages" :key="index"
             class="flex flex-col" :class="msg.role === 'user' ? 'items-end' : 'items-start'">

            <div class="flex items-start gap-2 max-w-[85%]" :class="msg.role === 'user' ? 'flex-row-reverse' : ''">
                <!-- Avatar -->
                <div v-if="msg.role !== 'user'" class="w-8 h-8 rounded-full bg-gray-200 border border-gray-300 flex items-center justify-center flex-shrink-0 text-gray-600 font-semibold text-xs mt-1">系</div>
                <div v-else class="w-8 h-8 rounded-full bg-gray-100 border border-gray-200 flex items-center justify-center flex-shrink-0 text-gray-500 font-semibold text-xs mt-1">客</div>

                <!-- Bubble -->
                <div :class="[
                    'p-3 rounded-lg shadow-sm border',
                    msg.role === 'user' ? 'bg-[#465FFF] text-white rounded-tr-sm' : 'bg-[#F2F4F7] rounded-tl-sm flex flex-col',
                    msg.error ? 'border-red-300 bg-red-50 text-red-700' : ''
                ]">
                    <p class="text-[13px] leading-relaxed font-medium whitespace-pre-wrap word-break">{{ msg.displayContent || msg.content }}</p>

                    <!-- Typing cursor -->
                    <span v-if="msg.isTyping" class="inline-block w-1.5 h-3.5 bg-gray-400 ml-1 animate-pulse align-middle"></span>

                    <!-- Escalation Label -->
                    <div v-if="msg.escalated && !msg.isTyping" class="mt-2 text-red-600 text-[10px] font-medium flex items-center gap-1">
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                        人工升级: {{ msg.escalation_reason }}
                    </div>
                </div>
            </div>

            <!-- Metadata (Latency) -->
            <div v-if="msg.latency && !msg.isTyping" class="mt-1 flex items-center gap-1 text-[9px] font-medium"
                 :class="[
                     msg.role === 'user' ? 'mr-10' : 'ml-10',
                     msg.latency <= 3000 ? 'text-green-500' : (msg.latency <= 8000 ? 'text-orange-400' : 'text-red-500')
                 ]">
                <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                后端耗时: {{ msg.latency }}ms
            </div>
        </div>

        <!-- Waiting Indicator: only show before AI message bubble is created -->
        <div v-if="loading && !messages.some(m => m.isTyping)" class="flex justify-start items-center gap-2 max-w-[85%]">
             <div class="w-8 h-8 rounded-full bg-gray-200 border border-gray-300 flex items-center justify-center flex-shrink-0 text-gray-600 font-semibold text-xs mt-1">系</div>
             <div class="bg-[#F2F4F7] p-3 rounded-lg rounded-tl-sm flex items-center gap-1 h-10">
                 <span class="text-[11px] font-bold text-gray-400 mr-2">正在输入</span>
                 <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></div>
                 <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.15s"></div>
                 <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.3s"></div>
             </div>
        </div>

      </div>

      <!-- Quick Actions -->
      <div class="bg-gray-50 border-t px-2 py-2 shrink-0 flex gap-2 overflow-x-auto scrollbar-hide">
         <button v-for="tag in presetTags" :key="tag" @click="inputMsg = tag" class="shrink-0 text-xs whitespace-nowrap bg-white border border-gray-200 text-gray-600 px-3 py-1.5 rounded-md hover:bg-gray-50 transition-colors font-medium">
             {{ tag }}
         </button>
      </div>

      <!-- Input Area -->
      <div class="p-3 bg-gray-50 border-t flex items-end gap-2 shrink-0">
          <div class="flex-1 bg-white border border-gray-300 rounded-md flex items-end overflow-hidden focus-within:border-gray-500 transition-all">
              <textarea
                  v-model="inputMsg"
                  @keydown.enter.prevent="sendMessage"
                  placeholder="发送给商家..."
                  class="w-full bg-transparent border-none p-3 text-[13px] text-gray-700 outline-none resize-none max-h-24 overflow-y-auto placeholder:text-gray-400"
                  rows="1"
              ></textarea>
          </div>
          <button @click="sendMessage" :disabled="!inputMsg.trim() || loading || isTypingRender"
              class="p-2.5 bg-gray-800 text-white rounded-md shadow-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-900 transition-colors flex-shrink-0">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path></svg>
          </button>
      </div>
    </div>

    <!-- Middle: Extracted Requirements Pane + Concurrent Testing -->
    <div class="hidden lg:flex flex-col w-[300px] gap-4 shrink-0 h-full overflow-hidden">

      <!-- Concurrent Test Panel -->
      <div class="card-enterprise p-4 shrink-0">
          <div class="flex justify-between items-center mb-3">
              <h2 class="font-bold text-gray-800 flex items-center text-sm">
                 <span class="text-xl mr-2">🚀</span> 极限并发压测
              </h2>
          </div>
          <p class="text-[10px] text-gray-500 mb-3 leading-relaxed">一键模拟多个买家针对同款商品瞬间发起询单，测试底层 <strong>LLM熔断、SQLite锁争用及异步并发能力</strong>。</p>

          <button @click="runConcurrentTest" :disabled="isTesting"
              class="w-full btn-primary font-medium py-2.5 flex justify-center items-center gap-2 disabled:opacity-75 disabled:cursor-not-allowed">
              <template v-if="!isTesting">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                  发起 5 并发请求
              </template>
              <template v-else>
                  <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  压测进行中...
              </template>
          </button>

          <!-- Test Results -->
          <div v-if="testResults.length > 0" class="mt-3 space-y-2">
              <div v-for="(res, idx) in testResults" :key="idx" class="bg-gray-50 rounded-lg p-2 flex items-center justify-between border border-gray-100">
                  <div class="flex items-center gap-2">
                      <span class="w-2 h-2 rounded-full" :class="res.success ? 'bg-green-500' : (res.pending ? 'bg-amber-400 animate-pulse' : 'bg-red-500')"></span>
                      <span class="text-[10px] font-bold text-gray-700">{{ res.userId }}</span>
                  </div>
                  <span v-if="res.pending" class="text-[10px] text-gray-400">请求中...</span>
                  <span v-else class="text-[10px] font-mono text-gray-500">{{ res.latency }}ms</span>
              </div>
          </div>
      </div>

      <!-- AI Requirement Extraction Panel -->
      <div class="card-enterprise flex flex-col flex-1 overflow-hidden min-h-0">
        <div class="p-4 border-b flex justify-between items-center bg-purple-50/50 shrink-0">
          <h2 class="font-bold text-purple-800 flex items-center text-sm">
            <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path></svg>
            实时场景提取 (<span class="text-xs">{{ buyerId }}</span>)
          </h2>
          <span
            @click="triggerExtraction(false)"
            :class="[
              'text-[10px] px-2 py-1 rounded-md font-medium cursor-pointer transition-all border',
              isExtracting
                ? 'bg-purple-200 text-purple-700 animate-pulse'
                : 'bg-purple-100 text-purple-600 hover:bg-purple-200 hover:shadow-sm'
            ]"
          >
            {{ isExtracting ? '提取中...' : '手动刷新' }}
          </span>
        </div>

        <div class="flex-1 overflow-y-auto p-4 space-y-4">

            <div v-if="localReqData.topic || localReqData.pages" class="space-y-4">
               <!-- Progress Bar -->
               <div class="bg-gray-50 p-4 border-b border-gray-100">
                  <div class="flex justify-between items-center mb-2">
                    <span class="text-xs font-semibold text-gray-600 flex items-center">提取完成度</span>
                    <span class="text-xs font-black text-purple-600">{{ completionRate }}%</span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div class="bg-gray-600 h-2 rounded-full transition-all duration-700 ease-out" :style="`width: ${completionRate}%`">
                    </div>
                  </div>
               </div>

               <div class="space-y-0.5">
                 <EditableField label="主题/项目类型" v-model="localReqData.topic" :confidence="getConfidence('topic')" fieldKey="topic"/>
                 <EditableField label="核心内容纲要" v-model="localReqData.outline" :confidence="getConfidence('outline')" fieldKey="outline"/>
                 <div class="grid grid-cols-2 gap-2">
                   <EditableField label="页数范围" v-model="localReqData.pages" :confidence="getConfidence('pages')" fieldKey="pages"/>
                   <EditableField label="风格偏好" v-model="localReqData.style" :confidence="getConfidence('style')" fieldKey="style"/>
                 </div>
                 <div class="grid grid-cols-2 gap-2">
                   <EditableField label="交付时间" v-model="localReqData.deadline" :confidence="getConfidence('deadline')" fieldKey="deadline"/>
                   <EditableField label="预算要求" v-model="localReqData.budget" :confidence="getConfidence('budget')" fieldKey="budget"/>
                 </div>
                 <EditableField label="用途/受众" v-model="localReqData.audience" :confidence="getConfidence('audience')" fieldKey="audience"/>
                 <EditableField label="📝 备注" v-model="localReqData.notes" :confidence="getConfidence('notes')" fieldKey="notes"/>
               </div>
            </div>

            <div v-else class="flex flex-col items-center justify-center h-full pt-10 text-center">
                 <div class="w-16 h-16 bg-gray-50 border border-gray-200 rounded-lg flex items-center justify-center mx-auto mb-4 text-gray-400">
                    <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                 </div>
                 <p class="font-bold text-gray-700 mb-2">需求尚不明确</p>
                 <p class="text-[11px] text-gray-400 mb-6 leading-relaxed">左侧对话互动后，<br/>AI将自动提纯要素</p>
                 <button v-if="messages.length > 0" @click="triggerExtraction(false)" class="bg-white text-gray-700 border border-gray-300 px-4 py-2 rounded-md text-xs font-medium hover:bg-gray-50 transition-colors mx-auto">
                    尝试重新提取
                 </button>
            </div>
        </div>
      </div>
    </div>

    <!-- Right: Diagnostics Panel -->
    <div class="hidden xl:flex flex-col flex-1 min-w-[280px] h-full overflow-hidden">
      <DiagnosticsPanel ref="diagnosticsPanel" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, reactive, computed } from 'vue';
import { store } from '../store.js';
import EditableField from './EditableField.vue';
import DiagnosticsPanel from './DiagnosticsPanel.vue';

// ========== 1. 对话与流式渲染 ==========
const diagnosticsPanel = ref(null);
const inputMsg = ref('');
const messages = ref([]);
const loading = ref(false);
const chatContainer = ref(null);
const isTypingRender = ref(false); // 控制打字机效果的 flag

const presetTags = ['在吗？', '做一个医疗行业BP，大概20页', '多少钱？', '有案例吗？', '我很急，今晚就要', '做的太丑了退钱！', '我是学生能便宜点吗'];

// 隔离的模拟器 ID，带随机后缀避免污染历史
const buyerId = ref(`sim_test_${Math.floor(Math.random() * 10000)}`);

const scrollToBottom = () => {
    nextTick(() => {
        if (chatContainer.value) {
            chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
        }
    });
};

const clearChat = () => {
    messages.value = [];
    // 重置所有需求字段
    Object.keys(localReqData).forEach(k => { localReqData[k] = ''; });
    // 清空置信度
    Object.keys(fieldConfidence).forEach(k => { delete fieldConfidence[k]; });

    fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: buyerId.value,
            message: '',
            platform: 'sim',
            clear_history: true
        })
    }).catch(e => console.error(e));
};

// 移除假动画 typeWriterEffect，保留基于真实 SSE 流输出的逻辑

const sendMessage = async () => {
    const text = inputMsg.value.trim();
    if (!text || loading.value || isTypingRender.value) return;

    const currentUserMessage = text;  // 保存用于诊断日志

    // User MSG
    messages.value.push({ role: 'user', content: text });
    inputMsg.value = '';
    scrollToBottom();

    loading.value = true;
    const startTime = performance.now();

    // 预先插入 AI 回复的空白占位泡泡
    const aiMsg = reactive({
        role: 'assistant',
        content: '',
        displayContent: '',
        escalated: false,
        escalation_reason: '',
        latency: null,
        isTyping: true,
        error: false
    });
    messages.value.push(aiMsg);
    scrollToBottom();

    try {
        const response = await fetch('/api/v1/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: buyerId.value,
                message: text,
                platform: 'simulator'
            })
        });

        if (!response.ok) {
            let errorText = '未知错误';
            try {
                const errData = await response.json();
                errorText = errData.detail || errData.message || errorText;
            } catch (e) { }
            aiMsg.content = '请求失败：' + errorText;
            aiMsg.displayContent = aiMsg.content;
            aiMsg.error = true;
            aiMsg.isTyping = false;
            loading.value = false;
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let done = false;
        let isFirstChunk = true;

        while (!done) {
            const { value, done: readerDone } = await reader.read();
            done = readerDone;
            if (value) {
                const chunkStr = decoder.decode(value, { stream: !done });
                const lines = chunkStr.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataStr = line.slice(6).trim();
                        if (!dataStr) continue;

                        try {
                            const data = JSON.parse(dataStr);

                            // 首次收到数据（包括空的 heartbeat），停止 loading
                            if (isFirstChunk) {
                                loading.value = false;
                                isFirstChunk = false;
                            }

                            // 有实际内容，追加显示
                            if (data.chunk) {
                                if (!aiMsg.latency) {
                                    aiMsg.latency = Math.round(performance.now() - startTime);
                                }
                                aiMsg.displayContent += data.chunk;
                                scrollToBottom();
                            }

                            if (data.done) {
                                aiMsg.isTyping = false;
                                aiMsg.escalated = data.escalated || false;
                                aiMsg.escalation_reason = data.escalation_reason || '';
                                aiMsg.content = aiMsg.displayContent;
                                if (!aiMsg.latency) {
                                    aiMsg.latency = Math.round(performance.now() - startTime);
                                }
                                // 记录诊断日志
                                diagnosticsPanel.value?.addLog({
                                    userMessage: currentUserMessage,
                                    frontendTTFT: aiMsg.latency,
                                    d: data.diagnostics || null,
                                    escalated: data.escalated || false,
                                    error: false,
                                });
                                // 对话结束触发提取
                                triggerExtraction(true);
                            }
                        } catch (e) {
                            console.error('SSE JSON parse error:', e, dataStr);
                        }
                    }
                }
            }
        }
    } catch (error) {
        aiMsg.content = '连接超时或服务器异常。';
        aiMsg.displayContent = aiMsg.content;
        aiMsg.error = true;
        aiMsg.isTyping = false;
        // 记录错误诊断日志
        diagnosticsPanel.value?.addLog({
            userMessage: currentUserMessage,
            frontendTTFT: null,
            d: null,
            escalated: false,
            error: true,
            errorMessage: error?.message || '连接超时或服务器异常',
        });
    } finally {
        loading.value = false;
        aiMsg.isTyping = false;
        scrollToBottom();
    }
};

// ========== 2. 结构化需求提取 ==========
const isExtracting = ref(false);
const localReqData = reactive({
  topic: '', pages: '', style: '', deadline: '', budget: '', audience: '', outline: '', notes: ''
});
const fieldConfidence = reactive({});

const getConfidence = (key) => fieldConfidence[key] || 0;

const completionRate = computed(() => {
  let filled = 0;
  const fields = ['topic', 'pages', 'style', 'deadline', 'budget', 'audience', 'outline', 'notes'];
  fields.forEach(f => {
    if (localReqData[f] && localReqData[f] !== '-') filled++;
  });
  return Math.round((filled / fields.length) * 100);
});

const triggerExtraction = async (silent = false) => {
    if (!silent) isExtracting.value = true;
    try {
        // 直接调用公开的提取 API（无需 JWT），绕过 dashboard 鉴权
        const res = await fetch(`/api/v1/extract_requirements/${buyerId.value}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        if (data && data.source !== 'none') {
            // 更新需求数据
            const fields = ['topic', 'pages', 'style', 'deadline', 'budget', 'audience', 'outline', 'notes'];
            fields.forEach(k => {
                if (data[k]) localReqData[k] = data[k];
            });
            // 更新置信度
            if (data.confidence) {
                fields.forEach(k => {
                    if (data.confidence[k]) fieldConfidence[k] = data.confidence[k];
                });
            }
        }
    } catch (e) {
        console.error('Extraction error:', e);
    } finally {
        if (!silent) isExtracting.value = false;
    }
};

// ========== 3. 并发压测功能 ==========
const isTesting = ref(false);
const testResults = ref([]);

const runConcurrentTest = async () => {
    isTesting.value = true;
    testResults.value = [];

    const queries = [
        "你好，我想做一份开题报告PPT，20页，要多少钱？",
        "在吗？老板让我明天必须把去年的总结做完，你能不能帮我加急？钱好说",
        "请问能不能给我开发票？我这边要报销的！！！",
        "太难看了！你们设计的什么鬼东西？马上退款给我！",
        "这个产品介绍有点长，大概50页，做高端一点，需要多久能好？"
    ];

    // Initialize state
    for (let i = 0; i < 5; i++) {
        testResults.value.push({
            userId: `LoadUser_${i + 1}`,
            pending: true,
            latency: 0,
            success: false
        });
    }

    const promises = queries.map(async (msg, idx) => {
        const uid = `LoadUser_${idx + 1}`;
        const start = performance.now();

        // Setup abort controller for timeout and prevent hanging the UI infinitely
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s max per request

        try {
            const res = await fetch('/api/v1/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: uid,
                    message: msg,
                    platform: 'simulator'
                }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            const latency = Math.round(performance.now() - start);
            testResults.value[idx].pending = false;
            testResults.value[idx].latency = latency;
            testResults.value[idx].success = res.ok;
        } catch (err) {
            clearTimeout(timeoutId);
            testResults.value[idx].pending = false;
            testResults.value[idx].success = false;
            console.error(`Concurrent Load Test Error (User ${idx + 1}):`, err);
        }
    });

    await Promise.all(promises);
    isTesting.value = false;
};

</script>

<style scoped>
.word-break {
    word-break: break-word;
}
@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
</style>
