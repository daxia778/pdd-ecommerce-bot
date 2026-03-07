<template>
  <div class="h-full flex items-center justify-center bg-gray-50/50 p-4">
    <!-- Mobile Phone Container -->
    <div class="w-full max-w-[400px] h-[750px] max-h-full bg-white rounded-[2.5rem] shadow-2xl border-[8px] border-gray-900 overflow-hidden flex flex-col relative ring-4 ring-gray-200">

      <!-- Dynamic Island Notch -->
      <div class="h-8 w-full absolute top-0 z-30 flex justify-center pointer-events-none mt-2">
         <div class="w-32 h-7 bg-black rounded-full flex items-center justify-between px-2 shadow-sm ring-1 ring-black/10">
            <!-- Camera lens simulation -->
            <div class="w-3 h-3 rounded-full bg-gray-900 border border-gray-800 shadow-inner flex items-center justify-center">
                <div class="w-1 h-1 rounded-full bg-blue-900/30"></div>
            </div>
            <!-- Sensor simulation -->
            <div class="w-1.5 h-1.5 rounded-full bg-gray-800 opacity-80"></div>
         </div>
      </div>

      <!-- App Header -->
      <div class="pt-12 pb-3 px-4 bg-gray-50 flex items-center gap-3 border-b z-10 sticky top-0">
        <div class="w-10 h-10 bg-gradient-to-br from-[#FF574D] to-[#E02E24] rounded-full flex items-center justify-center shadow-sm">
          <span class="text-white text-lg font-black tracking-tighter">多</span>
        </div>
        <div>
          <h2 class="font-extrabold text-[#E02E24] text-lg leading-tight">拼多多商家客服</h2>
          <p class="text-[10px] text-gray-500 font-medium">PDD AI 金牌定制中心</p>
        </div>
        <div class="ml-auto flex items-center gap-2">
            <button @click="clearChat" class="text-[10px] bg-gray-200 text-gray-600 px-2 py-1 rounded-full font-bold hover:bg-gray-300">清空历史</button>
        </div>
      </div>

      <!-- Chat Area -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4 bg-[#f4f4f4] scrollbar-hide" ref="chatContainer">

        <!-- Welcome Message -->
        <div class="flex items-start gap-2 max-w-[85%]">
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#FF574D] to-[#E02E24] flex items-center justify-center flex-shrink-0 shadow-sm text-white font-bold text-xs mt-1">小设</div>
            <div class="bg-white p-3 rounded-2xl rounded-tl-sm shadow-sm border border-gray-100 relative">
                <p class="text-[13px] text-gray-800 leading-relaxed font-medium">亲亲在的呢！我是金牌设计顾问小设，请问有什么可以帮您的呀？😊</p>
            </div>
        </div>

        <!-- Chat History -->
        <div v-for="(msg, index) in messages" :key="index"
             class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">

            <div v-if="msg.role !== 'user'" class="flex items-start gap-2 max-w-[85%]">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#FF574D] to-[#E02E24] flex items-center justify-center flex-shrink-0 shadow-sm text-white font-bold text-xs mt-1">小设</div>
                <div class="bg-white p-3 rounded-2xl rounded-tl-sm shadow-sm border border-gray-100 flex flex-col">
                    <p class="text-[13px] text-gray-800 leading-relaxed font-medium whitespace-pre-wrap">{{ msg.content }}</p>
                    <div v-if="msg.escalated" class="mt-2 bg-red-50 text-red-600 text-[10px] px-2 py-1 rounded-md font-bold flex items-center gap-1">
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                        人工升级: {{ msg.escalation_reason }}
                    </div>
                </div>
            </div>

            <div v-else class="flex items-start gap-2 max-w-[85%] flex-row-reverse">
                <div class="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center flex-shrink-0 shadow-sm text-white font-bold text-xs mt-1">我</div>
                <div class="bg-[#E02E24] text-white p-3 rounded-2xl rounded-tr-sm shadow-md shadow-red-500/20">
                    <p class="text-[13px] font-medium leading-relaxed whitespace-pre-wrap">{{ msg.content }}</p>
                </div>
            </div>

        </div>

        <!-- Loading indicator -->
        <div v-if="loading" class="flex justify-start items-center gap-2 max-w-[85%]">
             <div class="w-8 h-8 rounded-full bg-gradient-to-br from-[#FF574D] to-[#E02E24] flex items-center justify-center flex-shrink-0 opacity-50 text-white font-bold text-xs mt-1">设</div>
             <div class="bg-white p-3 rounded-2xl rounded-tl-sm shadow-sm border border-gray-100 flex items-center gap-1.5 h-10">
                 <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></div>
                 <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.15s"></div>
                 <div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.3s"></div>
             </div>
        </div>

      </div>

      <!-- Input Area -->
      <div class="p-3 bg-gray-50 border-t flex items-end gap-2 shrink-0">
          <button class="p-2.5 text-gray-400 hover:text-gray-600 bg-white rounded-full border shadow-sm">
             <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>
          </button>
          <div class="flex-1 bg-white border border-gray-200 rounded-2xl flex items-end overflow-hidden shadow-sm focus-within:ring-2 focus-within:ring-[#E02E24]/20 focus-within:border-[#E02E24] transition-all">
              <textarea
                  v-model="inputMsg"
                  @keydown.enter.prevent="sendMessage"
                  placeholder="发送给商家..."
                  class="w-full bg-transparent border-none p-3 text-[13px] text-gray-700 outline-none resize-none max-h-24 overflow-y-auto placeholder:text-gray-400"
                  rows="1"
              ></textarea>
          </div>
          <button @click="sendMessage" :disabled="!inputMsg.trim() || loading"
              class="p-2.5 bg-[#E02E24] text-white rounded-full shadow-md shadow-red-500/30 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-red-700 transition-colors flex-shrink-0">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path></svg>
          </button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';

const inputMsg = ref('');
const messages = ref([]);
const loading = ref(false);
const chatContainer = ref(null);

// 使用一个固定的模拟买家 ID
const buyerId = 'demo_buyer_sim_' + Math.floor(Math.random() * 1000);

const scrollToBottom = () => {
    nextTick(() => {
        if (chatContainer.value) {
            chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
        }
    });
};

const clearChat = () => {
    messages.value = [];
    // 发送空消息清理后端缓存
    fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: buyerId,
            message: '',
            platform: 'sim',
            clear_history: true
        })
    }).catch(e => console.error(e));
};

const sendMessage = async () => {
    const text = inputMsg.value.trim();
    if (!text || loading.value) return;

    // Add user message to UI
    messages.value.push({ role: 'user', content: text });
    inputMsg.value = '';
    scrollToBottom();

    loading.value = true;

    try {
        const response = await fetch('/api/v1/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: buyerId,
                message: text,
                platform: 'simulator'
            })
        });

        const data = await response.json();

        if (response.ok) {
            messages.value.push({
                role: 'assistant',
                content: data.reply,
                escalated: data.escalated,
                escalation_reason: data.escalation_reason
            });
        } else {
            messages.value.push({
                role: 'system',
                content: '请求失败：' + (data.detail || data.message || '未知错误'),
                escalated: true,
                escalation_reason: '网络/服务端异常'
            });
        }
    } catch (error) {
        messages.value.push({
            role: 'system',
            content: '无法连接到服务器，请检查网络。',
            escalated: true,
            escalation_reason: '网络故障'
        });
    } finally {
        loading.value = false;
        scrollToBottom();
    }
};
</script>
