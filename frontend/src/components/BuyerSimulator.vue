<template>
  <div class="h-full flex gap-4 p-4 overflow-hidden">
    <!-- Left: Mobile Phone Container -->
    <div class="w-full lg:w-[400px] h-[750px] max-h-full bg-white rounded-[2.5rem] shadow-2xl border-[8px] border-gray-900 overflow-hidden flex flex-col relative ring-4 ring-gray-200 shrink-0 mx-auto">

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
            <div class="w-10 h-10 bg-gradient-to-br from-[#FF574D] to-[#E02E24] rounded-full flex items-center justify-center shadow-sm">
              <span class="text-white text-lg font-black tracking-tighter">多</span>
            </div>
            <div>
              <h2 class="font-extrabold text-[#E02E24] text-lg leading-tight">拼多多商家客服</h2>
              <p class="text-[10px] text-gray-500 font-medium">PDD AI 金牌定制中心</p>
            </div>
        </div>
        <div class="flex items-center gap-2">
            <button @click="clearChat" class="text-[10px] bg-gray-200 text-gray-600 px-2 py-1 rounded-full font-bold hover:bg-gray-300" title="清空历史">清空</button>
        </div>
      </div>

      <!-- Chat Area -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4 bg-[#f4f4f4] scrollbar-hide relative" ref="chatContainer">

        <!-- Welcome Message -->
        <div class="flex items-start gap-2 max-w-[85%]">
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#FF574D] to-[#E02E24] flex items-center justify-center flex-shrink-0 shadow-sm text-white font-bold text-xs mt-1">小设</div>
            <div class="bg-white p-3 rounded-2xl rounded-tl-sm shadow-sm border border-gray-100 relative">
                <p class="text-[13px] text-gray-800 leading-relaxed font-medium">亲亲在的呢！我是金牌设计顾问小设，请问有什么可以帮您的呀？😊</p>
            </div>
        </div>

        <!-- Chat History -->
        <div v-for="(msg, index) in messages" :key="index"
             class="flex flex-col" :class="msg.role === 'user' ? 'items-end' : 'items-start'">

            <div class="flex items-start gap-2 max-w-[85%]" :class="msg.role === 'user' ? 'flex-row-reverse' : ''">
                <!-- Avatar -->
                <div v-if="msg.role !== 'user'" class="w-8 h-8 rounded-full bg-gradient-to-br from-[#FF574D] to-[#E02E24] flex items-center justify-center flex-shrink-0 shadow-sm text-white font-bold text-xs mt-1">小设</div>
                <div v-else class="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center flex-shrink-0 shadow-sm text-white font-bold text-xs mt-1">我</div>

                <!-- Bubble -->
                <div :class="[
                    'p-3 rounded-2xl shadow-sm relative',
                    msg.role === 'user' ? 'bg-[#E02E24] text-white rounded-tr-sm shadow-md shadow-red-500/20' : 'bg-white rounded-tl-sm border border-gray-100 flex flex-col',
                    msg.error ? 'border-red-300 bg-red-50 text-red-700' : ''
                ]">
                    <p class="text-[13px] leading-relaxed font-medium whitespace-pre-wrap word-break">{{ msg.displayContent || msg.content }}</p>

                    <!-- Typing cursor -->
                    <span v-if="msg.isTyping" class="inline-block w-1.5 h-3.5 bg-gray-400 ml-1 animate-pulse align-middle"></span>

                    <!-- Escalation Label -->
                    <div v-if="msg.escalated && !msg.isTyping" class="mt-2 bg-red-50 text-red-600 text-[10px] px-2 py-1 rounded-md font-bold flex items-center gap-1 border border-red-100">
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                        人工升级: {{ msg.escalation_reason }}
                    </div>
                </div>
            </div>

            <!-- Metadata (Latency) -->
            <div v-if="msg.latency && !msg.isTyping" class="mt-1 flex items-center gap-1 text-[9px] text-gray-400 font-medium" :class="msg.role === 'user' ? 'mr-10' : 'ml-10'">
                <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                后端耗时: {{ msg.latency }}ms
            </div>
        </div>

        <!-- Waiting Indicator -->
        <div v-if="loading && !isTypingRender" class="flex justify-start items-center gap-2 max-w-[85%]">
             <div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#FF574D] to-[#E02E24] flex items-center justify-center flex-shrink-0 text-white font-bold text-xs mt-1">小设</div>
             <div class="bg-white p-3 rounded-2xl rounded-tl-sm shadow-sm border border-gray-100 flex items-center gap-1 h-10">
                 <span class="text-[11px] font-bold text-gray-400 mr-2">正在输入</span>
                 <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></div>
                 <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.15s"></div>
                 <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.3s"></div>
             </div>
        </div>

      </div>

      <!-- Quick Actions -->
      <div class="bg-gray-50 border-t px-2 py-2 shrink-0 flex gap-2 overflow-x-auto scrollbar-hide">
         <button v-for="tag in presetTags" :key="tag" @click="inputMsg = tag" class="shrink-0 text-[10px] whitespace-nowrap bg-white border border-gray-200 text-gray-600 px-2.5 py-1.5 rounded-full hover:bg-gray-50 hover:border-gray-300 transition-colors font-medium shadow-sm">
             {{ tag }}
         </button>
      </div>

      <!-- Input Area -->
      <div class="p-3 bg-gray-50 border-t flex items-end gap-2 shrink-0">
          <div class="flex-1 bg-white border border-gray-200 rounded-2xl flex items-end overflow-hidden shadow-sm focus-within:ring-2 focus-within:ring-[#E02E24]/20 focus-within:border-[#E02E24] transition-all">
              <textarea
                  v-model="inputMsg"
                  @keydown.enter.prevent="sendMessage"
                  placeholder="发送给商家..."
                  class="w-full bg-transparent border-none p-3 text-[13px] text-gray-700 outline-none resize-none max-h-24 overflow-y-auto placeholder:text-gray-400"
                  rows="1"
              ></textarea>
          </div>
          <button @click="sendMessage" :disabled="!inputMsg.trim() || loading || isTypingRender"
              class="p-2.5 bg-[#E02E24] text-white rounded-full shadow-md shadow-red-500/30 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-red-700 transition-colors flex-shrink-0">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path></svg>
          </button>
      </div>
    </div>

    <!-- Right: Extracted Requirements Pane + Concurrent Testing -->
    <div class="hidden lg:flex flex-col w-[350px] gap-4 shrink-0 h-full overflow-hidden">

      <!-- Concurrent Test Panel -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 shrink-0">
          <div class="flex justify-between items-center mb-3">
              <h2 class="font-bold text-gray-800 flex items-center text-sm">
                 <span class="text-xl mr-2">🚀</span> 极限并发压测
              </h2>
          </div>
          <p class="text-[10px] text-gray-500 mb-3 leading-relaxed">一键模拟多个买家针对同款商品瞬间发起询单，测试底层 <strong>LLM熔断、SQLite锁争用及异步并发能力</strong>。</p>

          <button @click="runConcurrentTest" :disabled="isTesting"
              class="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-2.5 rounded-xl text-sm shadow-md shadow-blue-500/30 transition-all flex justify-center items-center gap-2 disabled:opacity-75 disabled:cursor-not-allowed">
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
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col flex-1 overflow-hidden min-h-0">
        <div class="p-4 border-b flex justify-between items-center bg-purple-50/50 shrink-0">
          <h2 class="font-bold text-purple-800 flex items-center text-sm">
            <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path></svg>
            实时场景提取 (<span class="text-xs">{{ buyerId }}</span>)
          </h2>
          <span
            @click="triggerExtraction(false)"
            :class="[
              'text-[9px] px-2 py-1 rounded-full font-bold uppercase tracking-wider cursor-pointer transition-all',
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
               <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
                  <div class="flex justify-between items-center mb-2">
                    <span class="text-xs font-bold text-gray-600 flex items-center"><span class="w-1.5 h-1.5 bg-purple-500 rounded-full mr-1.5 animate-pulse"></span>字段提纯度</span>
                    <span class="text-xs font-black text-purple-600">{{ completionRate }}%</span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden shadow-inner">
                    <div class="bg-gradient-to-r from-purple-400 to-purple-600 h-2 rounded-full transition-all duration-700 ease-out shadow-[0_0_8px_rgba(168,85,247,0.4)] relative" :style="`width: ${completionRate}%`">
                      <div class="absolute inset-0 bg-white/20 w-full rounded-full animate-[shimmer_2s_infinite]"></div>
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
               </div>
            </div>

            <div v-else class="flex flex-col items-center justify-center h-full pt-10 text-center">
                 <div class="w-16 h-16 bg-purple-50 rounded-xl flex items-center justify-center mx-auto mb-4 text-purple-400">
                    <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                 </div>
                 <p class="font-bold text-gray-700 mb-2">需求尚不明确</p>
                 <p class="text-[11px] text-gray-400 mb-6 leading-relaxed">左侧对话互动后，<br/>AI将自动提纯要素</p>
                 <button v-if="messages.length > 0" @click="triggerExtraction(false)" class="bg-gray-50 text-purple-600 border border-purple-200 px-4 py-2 rounded-xl text-xs font-bold hover:bg-purple-50 transition-colors mx-auto">
                    尝试提取需求
                 </button>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, reactive, computed } from 'vue';
import { store } from '../store.js';
import EditableField from './EditableField.vue';

// ========== 1. 对话与流式渲染 ==========
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

// 流式打字机效果
const typeWriterEffect = async (msgObj, text) => {
    isTypingRender.value = true;
    msgObj.isTyping = true;
    msgObj.displayContent = '';

    // 按字切分，根据标点符号增加随机延迟
    const chars = Array.from(text);
    for (let i = 0; i < chars.length; i++) {
        msgObj.displayContent += chars[i];

        let delay = 15; // 极快流式
        if (['，', '。', '！', '？', '\n'].includes(chars[i])) delay = 150;

        scrollToBottom();
        await new Promise(r => setTimeout(r, delay));
    }

    msgObj.isTyping = false;
    isTypingRender.value = false;
    scrollToBottom();

    // 收到新消息并且打字完成后，静默触发需求提取
    triggerExtraction(true);
};

const sendMessage = async () => {
    const text = inputMsg.value.trim();
    if (!text || loading.value || isTypingRender.value) return;

    // User MSG
    messages.value.push({ role: 'user', content: text });
    inputMsg.value = '';
    scrollToBottom();

    loading.value = true;
    const startTime = performance.now();

    try {
        const response = await fetch('/api/v1/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: buyerId.value,
                message: text,
                platform: 'simulator'
            })
        });

        const data = await response.json();
        const latency = Math.round(performance.now() - startTime);

        if (response.ok) {
            const aiMsg = {
                role: 'assistant',
                content: data.reply,
                displayContent: '',
                escalated: data.escalated,
                escalation_reason: data.escalation_reason,
                latency: latency,
                isTyping: false
            };
            messages.value.push(aiMsg);

            // 触发流式渲染
            await typeWriterEffect(aiMsg, data.reply);

        } else {
            messages.value.push({
                role: 'system',
                content: '请求失败：' + (data.detail || data.message || '未知错误'),
                error: true
            });
        }
    } catch (error) {
        messages.value.push({
            role: 'system',
            content: '连接超时或服务器异常。',
            error: true
        });
    } finally {
        loading.value = false;
        scrollToBottom();
    }
};

// ========== 2. 结构化需求提取 ==========
const isExtracting = ref(false);
const localReqData = reactive({
  topic: '', pages: '', style: '', deadline: '', budget: '', audience: '', outline: ''
});
const fieldConfidence = reactive({});

const getConfidence = (key) => fieldConfidence[key] || 0;

const completionRate = computed(() => {
  let filled = 0;
  const fields = ['topic', 'pages', 'style', 'deadline', 'budget', 'audience', 'outline'];
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
            const fields = ['topic', 'pages', 'style', 'deadline', 'budget', 'audience', 'outline'];
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
        try {
            const res = await fetch('/api/v1/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: uid,
                    message: msg,
                    platform: 'simulator'
                })
            });
            const latency = Math.round(performance.now() - start);
            testResults.value[idx].pending = false;
            testResults.value[idx].latency = latency;
            testResults.value[idx].success = res.ok;
        } catch (err) {
            testResults.value[idx].pending = false;
            testResults.value[idx].success = false;
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
