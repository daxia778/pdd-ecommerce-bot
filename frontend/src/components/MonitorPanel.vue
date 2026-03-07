<template>
  <div class="flex flex-col lg:flex-row gap-4 h-full w-full">
    <!-- Left: Session List -->
    <div class="w-full lg:w-[280px] flex flex-col h-full shrink-0">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col h-full overflow-hidden">
        <div class="p-4 border-b flex justify-between items-center">
          <h2 class="font-bold text-gray-800 flex items-center text-sm">
            <span class="w-1.5 h-3.5 bg-blue-600 rounded-sm mr-2"></span>
            实时对话队列
          </h2>
          <span class="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full font-semibold">
            {{ store.sessions.length }} 活跃
          </span>
        </div>
        <div class="flex-1 overflow-y-auto p-2 space-y-2 chat-scroll">
          <div
            v-for="session in store.sessions"
            :key="session.user_id"
            @click="selectUser(session.user_id)"
            :class="[
              'p-3 rounded-xl cursor-pointer transition-all duration-300 ease-in-out border relative group',
              store.selectedUser === session.user_id
                ? 'bg-blue-50/80 border-blue-200 ring-2 ring-blue-500/20 shadow-sm transform scale-[1.02]'
                : 'bg-white border-transparent hover:border-gray-200 hover:bg-gray-50 hover:shadow-sm hover:-translate-y-0.5'
            ]"
          >
            <!-- AI 暂停状态标签 -->
            <span
              v-if="store.pausedSessions[session.user_id]"
              class="absolute top-2 right-2 text-[9px] font-bold uppercase bg-orange-100 text-orange-600 px-1.5 py-0.5 rounded-full"
            >人工接管</span>

            <!-- 演示数据标签 -->
            <span
              v-else-if="session.is_demo"
              class="absolute top-2 right-2 text-[9px] font-bold uppercase bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded-full ring-1 ring-purple-200"
            >演示数据</span>

            <div class="flex justify-between items-start mb-1.5">
              <span class="font-bold text-gray-700 truncate w-2/3 text-sm">{{ formatUserId(session.user_id) }}</span>
              <span class="text-[9px] uppercase font-bold text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">{{ session.platform }}</span>
            </div>
            <div class="flex justify-between items-center text-[11px] text-gray-500 font-medium">
              <span class="flex items-center">
                <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                {{ session.message_count }} 条
              </span>
              <span>{{ (session.updated_at || '').split(' ')[1] }}</span>
            </div>
          </div>
          <div v-if="store.sessions.length === 0" class="flex flex-col items-center justify-center h-40 text-gray-400 font-medium">
            <p>📭 暂无活跃对话</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Center: Chat Window -->
    <div class="flex-1 flex flex-col h-full min-w-[320px]">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col h-full overflow-hidden">

        <!-- Chat Header — with AI Pause toggle -->
        <div v-if="store.selectedUser" class="p-4 border-b bg-gray-50 flex items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <div :class="['w-10 h-10 rounded-xl flex items-center justify-center text-white font-black text-lg shadow-lg ring-2 ring-white', getAvatarGradient(store.selectedUser)]">
              {{ formatUserId(store.selectedUser).slice(0, 1).toUpperCase() }}
            </div>
            <div>
              <p class="font-bold text-gray-800 text-sm">{{ formatUserId(store.selectedUser) }}</p>
              <p class="text-[11px] font-medium" :class="isPaused ? 'text-orange-500' : 'text-green-500'">
                <span class="inline-block w-1.5 h-1.5 rounded-full mr-1 align-middle" :class="isPaused ? 'bg-orange-500' : 'bg-green-500 animate-pulse'"></span>
                {{ isPaused ? '人工接管中' : 'AI 自动回复' }}
              </p>
            </div>
          </div>

          <!-- Controls -->
          <div class="flex items-center gap-2">
            <button
              @click="handleTogglePause"
              :disabled="togglingPause"
              :class="[
                'px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 border',
                isPaused
                  ? 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100'
                  : 'bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100'
              ]"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path v-if="isPaused" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6" />
              </svg>
              {{ togglingPause ? '切换中...' : (isPaused ? '恢复 AI' : '人工接管') }}
            </button>
          </div>
        </div>
        <div v-else class="p-5 border-b bg-gray-50">
          <p class="text-gray-400 font-medium text-sm">← 左侧选择一个会话查看对话记录</p>
        </div>

        <!-- Messages -->
        <div class="flex-1 overflow-y-auto p-4 space-y-4 chat-scroll" id="chat-window">
          <div v-if="!store.selectedUser" class="flex flex-col items-center justify-center h-full text-gray-300">
            <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <p class="font-medium">未选中用户</p>
          </div>

          <template v-for="(msg, index) in store.currentChat" :key="index">
            <!-- User message -->
            <div v-if="msg.role === 'user'" class="flex justify-end items-end gap-2 group mb-2">
              <div class="max-w-[75%] flex flex-col items-end">
                <div class="bg-gradient-to-br from-blue-500 to-blue-600 text-white px-4 py-2.5 rounded-2xl rounded-br-sm shadow-md transition-shadow hover:shadow-lg">
                  <p class="text-[13.5px] leading-relaxed break-words whitespace-pre-wrap">{{ msg.content }}</p>
                </div>
                <p class="text-[9px] text-gray-400 mt-1 mr-1 font-medium opacity-0 group-hover:opacity-100 transition-opacity">{{ msg.created_at }}</p>
              </div>
              <div :class="['w-8 h-8 rounded-lg shadow-md ring-1 ring-white/80 flex items-center justify-center text-white font-black text-[10px] flex-shrink-0 z-10 hover:scale-110 transition-transform', getAvatarGradient(store.selectedUser || 'user')]">
                客
              </div>
            </div>
            <!-- AI / Manual message -->
            <div v-else class="flex justify-start items-end gap-2 group mb-2">
              <div class="w-8 h-8 rounded-lg shadow-md ring-1 ring-white/80 flex items-center justify-center text-white font-black text-[10px] flex-shrink-0 z-10 hover:scale-110 transition-transform"
                   :class="msg.platform === 'manual' ? 'bg-gradient-to-br from-amber-400 to-orange-500' : 'bg-gradient-to-br from-violet-500 to-purple-600'">
                {{ msg.platform === 'manual' ? '人' : 'AI' }}
              </div>
              <div class="max-w-[75%] flex flex-col items-start">
                <div class="bg-white border border-gray-100 text-gray-800 px-4 py-2.5 rounded-2xl rounded-bl-sm shadow-sm transition-shadow hover:shadow-md">
                  <div class="flex items-center mb-1.5 gap-1.5">
                    <span v-if="msg.platform === 'manual'"
                      class="text-[9px] font-bold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded uppercase tracking-wider border border-amber-100">
                      人工客服
                    </span>
                    <span v-else class="text-[9px] font-bold text-purple-700 bg-purple-50 px-1.5 py-0.5 rounded uppercase tracking-wider border border-purple-100">
                      PDD AI Bot
                    </span>
                  </div>
                  <p class="text-[13.5px] leading-relaxed break-words whitespace-pre-wrap">{{ msg.content }}</p>
                </div>
                <p class="text-[9px] text-gray-400 mt-1 ml-1 font-medium opacity-0 group-hover:opacity-100 transition-opacity">{{ msg.created_at }}</p>
              </div>
            </div>
          </template>
        </div>

        <!-- Manual Send Message Bar — only when AI is paused -->
        <Transition name="slide-up">
          <div v-if="store.selectedUser && isPaused" class="p-3 border-t bg-amber-50/60">
            <div class="flex items-center gap-2 mb-2">
              <span class="w-2 h-2 bg-amber-500 rounded-full animate-pulse"></span>
              <span class="text-[11px] font-bold text-amber-700 uppercase tracking-wide">人工接管模式 — 直接发消息给买家</span>
            </div>
            <div class="flex gap-2">
              <input
                v-model="manualMessage"
                @keydown.enter.exact.prevent="handleSend"
                type="text"
                placeholder="输入消息后按 Enter 发送..."
                class="flex-1 bg-white border border-amber-200 rounded-xl px-3 py-2 text-sm font-medium text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-400/50 focus:border-amber-400 transition-all"
                :disabled="store.sendingMessage"
              />
              <button
                @click="handleSend"
                :disabled="store.sendingMessage || !manualMessage.trim()"
                class="px-4 py-2 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-xl shadow-md shadow-amber-200 transition-all flex items-center gap-1.5 text-sm"
              >
                <svg v-if="store.sendingMessage" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                发送
              </button>
            </div>
          </div>
        </Transition>

      </div>
    </div>

    <!-- Right: Extracted Requirements Pane -->
    <div v-if="store.selectedUser" class="w-full lg:w-[320px] flex flex-col h-full shrink-0">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col h-full overflow-hidden">
        <div class="p-4 border-b flex justify-between items-center bg-purple-50/50">
          <h2 class="font-bold text-purple-800 flex items-center text-sm">
            <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path></svg>
            结构化需求采集
          </h2>
          <span class="text-[9px] bg-purple-100 text-purple-600 px-2 py-0.5 rounded-full font-bold uppercase tracking-wider">
            AI 实时抽取
          </span>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-4">

          <div v-if="localReqData.topic" class="space-y-4">
             <!-- Progress Bar -->
             <div class="bg-gray-50 p-4 rounded-xl border border-gray-100 group hover:border-purple-200 transition-colors cursor-pointer" @click="autoFillDemo" title="点击自动补全缺失字段 (演示)">
                <div class="flex justify-between items-center mb-2">
                  <span class="text-xs font-bold text-gray-600 flex items-center"><span class="w-1.5 h-1.5 bg-purple-500 rounded-full mr-1.5 animate-pulse"></span>字段提纯度</span>
                  <span class="text-xs font-black text-purple-600">{{ completionRate }}%</span>
                </div>
                <!-- Risk Tags Row -->
                <div class="flex gap-1 mb-2 flex-wrap">
                  <span v-if="riskTags.urgent" class="text-[9px] px-1.5 py-0.5 rounded-sm font-bold bg-red-100 text-red-600 border border-red-200">⚡ 高优加急</span>
                  <span v-if="riskTags.highValue" class="text-[9px] px-1.5 py-0.5 rounded-sm font-bold bg-amber-100 text-amber-700 border border-amber-200">💰 高价值单</span>
                  <span v-if="riskTags.missing" class="text-[9px] px-1.5 py-0.5 rounded-sm font-bold bg-gray-200 text-gray-600 border border-gray-300">⚠️ 信息缺失</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden shadow-inner">
                  <div class="bg-gradient-to-r from-purple-400 to-purple-600 h-2 rounded-full transition-all duration-700 ease-out shadow-[0_0_8px_rgba(168,85,247,0.4)] relative" :style="`width: ${completionRate}%`">
                    <div class="absolute inset-0 bg-white/20 w-full rounded-full animate-[shimmer_2s_infinite]"></div>
                  </div>
                </div>
             </div>

             <div class="space-y-0.5">
               <!-- Core Fields -->
               <EditableField
                 label="主题/项目类型"
                 v-model="localReqData.topic"
                 :required="true"
                 :confidence="getConfidence('topic')"
                 :warningText="!localReqData.topic ? '必须填写主题' : ''"
                 fieldKey="topic"
                 @mark-edited="handleFieldEdit"
               />

               <EditableField
                 label="核心内容纲要"
                 v-model="localReqData.outline"
                 :confidence="getConfidence('outline')"
                 fieldKey="outline"
                 @mark-edited="handleFieldEdit"
               />

               <div class="grid grid-cols-2 gap-2">
                 <EditableField
                   label="页数范围"
                   v-model="localReqData.pages"
                   :required="true"
                   :confidence="getConfidence('pages')"
                   fieldKey="pages"
                   @mark-edited="handleFieldEdit"
                 />
                 <EditableField
                   label="风格偏好"
                   v-model="localReqData.style"
                   :required="true"
                   :confidence="getConfidence('style')"
                   fieldKey="style"
                   @mark-edited="handleFieldEdit"
                 />
               </div>

               <EditableField
                 label="素材/参考附件"
                 v-model="localReqData.assets"
                 :confidence="getConfidence('assets')"
                 fieldKey="assets"
                 @mark-edited="handleFieldEdit"
               />

               <div class="grid grid-cols-2 gap-2">
                 <EditableField
                   label="交付时间"
                   v-model="localReqData.deadline"
                   :highlight="riskTags.urgent"
                   :confidence="getConfidence('deadline')"
                   fieldKey="deadline"
                   @mark-edited="handleFieldEdit"
                 />
                 <EditableField
                   label="预算要求"
                   v-model="localReqData.budget"
                   :highlight="riskTags.highValue"
                   :confidence="getConfidence('budget')"
                   fieldKey="budget"
                   @mark-edited="handleFieldEdit"
                 />
               </div>

               <EditableField
                 label="用途/受众"
                 v-model="localReqData.audience"
                 :confidence="getConfidence('audience')"
                 fieldKey="audience"
                 @mark-edited="handleFieldEdit"
               />
             </div>

             <div class="mt-4 pt-4 border-t border-gray-100 flex gap-2">
                <!-- If completion is high enough, we can generate a quote -->
                <button
                  v-if="completionRate >= 60"
                  @click="openQuoteModal"
                  class="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-4 py-3 rounded-xl text-sm font-black hover:from-purple-700 hover:to-indigo-700 shadow-lg shadow-purple-200 transform hover:scale-[1.02] transition-all flex justify-center items-center gap-2"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                  生成正式报价单
                </button>
             </div>
          </div>

          <div v-else-if="store.currentChat && store.currentChat.length > 0" class="flex flex-col items-center justify-center h-full pt-10">
             <!-- Not yet extracted state -->
             <div v-if="!isExtracting" class="text-center w-full px-4">
                 <div class="w-16 h-16 bg-purple-50 rounded-2xl flex items-center justify-center mx-auto mb-4 text-purple-400">
                    <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                 </div>
                 <p class="font-bold text-gray-700 mb-2">需求尚不明确</p>
                 <p class="text-[11px] text-gray-400 mb-6 leading-relaxed">AI 正在与买家沟通中<br/>待买家提供"主题、页数"等核心要素后将自动提纯</p>
                 <button @click="simulateExtracting" class="bg-gray-50 text-purple-600 border border-purple-200 px-4 py-2 rounded-xl text-xs font-bold hover:bg-purple-50 transition-colors inline-block mx-auto">
                    (演示) 强制 AI 提纯
                 </button>
             </div>

             <!-- Extracting Loading State -->
             <div v-else class="text-center w-full px-4">
                 <div class="relative w-20 h-20 mb-6 mx-auto">
                    <svg class="absolute inset-0 w-full h-full text-gray-100" viewBox="0 0 100 100"><circle cx="50" cy="50" fill="none" stroke="currentColor" stroke-width="8" r="40"></circle></svg>
                    <svg class="absolute inset-0 w-full h-full text-purple-500 transform -rotate-90 origin-center transition-all duration-300" :style="`stroke-dasharray: 251.2; stroke-dashoffset: ${251.2 - (251.2 * extractProgress / 100)}`" viewBox="0 0 100 100"><circle cx="50" cy="50" fill="none" stroke="currentColor" stroke-width="8" stroke-linecap="round" r="40"></circle></svg>
                    <div class="absolute inset-0 flex items-center justify-center font-bold text-purple-600 text-sm">{{ extractProgress }}%</div>
                 </div>
                 <p class="font-bold text-gray-700 bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-indigo-600">AI 正在深度解析语义脉络...</p>
                 <p class="text-[11px] mt-2 text-gray-400 font-medium">识别关键参数组合中</p>
             </div>
          </div>

          <div v-else class="flex flex-col items-center justify-center h-full text-gray-400 text-sm mt-10">
             <!-- Empty Chat State -->
             <div class="relative w-16 h-16 mb-4">
                <div class="absolute inset-0 border-4 border-gray-100 rounded-full"></div>
                <div class="absolute inset-0 border-4 border-purple-400 rounded-full animate-[spin_3s_linear_infinite] border-t-transparent border-l-transparent"></div>
                <div class="absolute inset-0 flex items-center justify-center">
                   <svg class="w-6 h-6 text-purple-400 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                </div>
             </div>
             <p class="font-bold text-gray-500 bg-clip-text text-transparent bg-gradient-to-r from-gray-500 to-gray-400">AI 正在实时提纯语义...</p>
             <p class="text-[11px] mt-1.5 text-gray-400 uppercase tracking-widest font-medium">waiting for input</p>
          </div>

        </div>
      </div>
    </div>

    <!-- Quote Modal -->
    <QuoteModal
      :isOpen="isQuoteModalOpen"
      :reqData="localReqData"
      @close="isQuoteModalOpen = false"
      @send="handleSendQuote"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, reactive } from 'vue';
import { store } from '../store.js';
import EditableField from './EditableField.vue';
import QuoteModal from './QuoteModal.vue';

const manualMessage = ref('');
const togglingPause = ref(false);
const isQuoteModalOpen = ref(false);

// 根据用户名 hash 选择渐变色
const AVATAR_GRADIENTS = [
    'bg-gradient-to-br from-violet-500 to-purple-600',
    'bg-gradient-to-br from-rose-500 to-pink-600',
    'bg-gradient-to-br from-sky-500 to-cyan-600',
    'bg-gradient-to-br from-amber-500 to-orange-600',
    'bg-gradient-to-br from-emerald-500 to-teal-600',
    'bg-gradient-to-br from-fuchsia-500 to-pink-600',
    'bg-gradient-to-br from-blue-600 to-indigo-700',
    'bg-gradient-to-br from-red-500 to-rose-600',
];

const getAvatarGradient = (name) => {
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
    return AVATAR_GRADIENTS[Math.abs(hash) % AVATAR_GRADIENTS.length];
};

const formatUserId = (id) => {
    if (!id) return '';
    if (id.startsWith('demo_buyer_sim_')) {
        return '模拟买家_' + id.replace('demo_buyer_sim_', '');
    }
    if (id.startsWith('demo_buyer_')) {
        return '测试买家_' + id.replace('demo_buyer_', '');
    }
    return id;
};

const isPaused = computed(() =>
  store.selectedUser ? !!store.pausedSessions[store.selectedUser] : false
);

const MOCK_REQUIREMENTS = {
  '【大四】林同学': { topic: '毕业答辩PPT', pages: '25页', style: '学术严谨 / 校园风', deadline: '下周', budget: '约337元', audience: '导师/答辩委员会', outline: '研究背景 -> 方法论 -> 结论', assets: '论文摘要.doc' },
  '王总(找融资)': { topic: '大健康融资商业计划书(BP)', pages: '约20页', style: '高端科技 / 创投风', deadline: '下周一晚上 (特急)', budget: '5000元', audience: '风险投资人', outline: '核心痛点 -> 解决方案 -> 商业模式', assets: '官网资料.pdf' },
  'HR-Amanda': { topic: 'SaaS季度总结汇报', pages: '30页', style: '现代科技风', deadline: '本月底', budget: '约1800元', audience: '全公司员工', outline: '-', assets: '-' },
  '🔥急单-李先生': { topic: '市政工程投标方案', pages: '45页', style: '严肃正规 (纯美化排版)', deadline: '明早9点前', budget: '3600元', audience: '评标委员会', outline: '企业资质 -> 施工方案 -> 报价清单', assets: '标书原稿.doc' },
  '智创科技-陈总监': { topic: '展会全案', pages: '宽屏PPT(页数待定)', style: '智领未来·云端共生主题', deadline: '下个月', budget: '约30000元', audience: '展会参观者/行业客户', outline: '-', assets: 'VI规范.pdf' }
};

// Internal editable state for the current selected user
const localReqData = reactive({
  topic: '', pages: '', style: '', deadline: '', budget: '', audience: '', outline: '', assets: ''
});

// Mock AI Confidences (different fields have different confidence levels to show visual differences)
const getConfidence = (key) => {
  const confMap = {
    topic: 95, pages: 98, style: 85, deadline: 92, budget: 75, audience: 88, outline: 65, assets: 90
  };
  return confMap[key] || 80;
};

const isExtracting = ref(false);
const extractProgress = ref(0);

// Watch selected user changes to reset local form data
watch(() => store.selectedUser, (newVal) => {
  isExtracting.value = false;
  extractProgress.value = 0;

  if (newVal && MOCK_REQUIREMENTS[newVal]) {
    const data = MOCK_REQUIREMENTS[newVal];
    // Copy data
    Object.keys(localReqData).forEach(k => {
      localReqData[k] = data[k] || '-';
    });
  } else {
    // Clear
    Object.keys(localReqData).forEach(k => localReqData[k] = '');
  }
});

const simulateExtracting = () => {
    isExtracting.value = true;
    extractProgress.value = 0;

    // Simulate progress
    const interval = setInterval(() => {
        extractProgress.value += Math.floor(Math.random() * 15) + 5;
        if (extractProgress.value >= 100) {
            extractProgress.value = 100;
            clearInterval(interval);

            // Auto-fill some data based on chat history if possible, else random
            setTimeout(() => {
                localReqData.topic = '基于历史：商务合作计划书';
                localReqData.pages = '约 20 页';
                localReqData.style = '待确认';
                localReqData.deadline = '本周五';
                isExtracting.value = false; // complete
            }, 400);
        }
    }, 300);
};

const handleFieldEdit = ({ key, value }) => {
  console.log(`Field ${key} edited:`, value);
  // Send update to store or backend in real app
};

const completionRate = computed(() => {
  if (!localReqData.topic) return 0;
  let filled = 0;
  const fields = Object.keys(localReqData);
  fields.forEach(f => {
    if (localReqData[f] && localReqData[f] !== '-') filled++;
  });
  return Math.round((filled / fields.length) * 100);
});

// Calculate Risks
const riskTags = computed(() => {
  const tags = { urgent: false, highValue: false, missing: false };
  const d = localReqData.deadline || '';
  const b = localReqData.budget || '';

  if (d.includes('急') || d.includes('明早') || d.includes('马上')) tags.urgent = true;
  if (b.includes('5000') || b.includes('万') || b.includes('3600')) tags.highValue = true;
  if (completionRate.value < 60) tags.missing = true;

  return tags;
});

const openQuoteModal = () => {
  isQuoteModalOpen.value = true;
};

const handleSendQuote = async (quoteText) => {
  if (!store.selectedUser) return;
  // Make sure AI is paused so human can send the quote
  if (!isPaused.value) {
    await store.togglePause(store.selectedUser);
  }
  await store.sendManualMessage(store.selectedUser, quoteText);
  checkAndResolveEscalation(store.selectedUser);
};

const autoFillDemo = () => {
  // Easter egg: auto fill empty fields just for demo clicking effect
  if (localReqData.outline === '-') localReqData.outline = '系统架构 -> 核心优势 -> 落地案例';
  if (localReqData.assets === '-') localReqData.assets = '参考图.png';
};

const selectUser = async (userId) => {
  await store.viewChat(userId);
};

const handleTogglePause = async () => {
  if (!store.selectedUser) return;
  togglingPause.value = true;
  try {
    await store.togglePause(store.selectedUser);
  } finally {
    togglingPause.value = false;
  }
};

const handleSend = async () => {
  const msg = manualMessage.value.trim();
  if (!msg || !store.selectedUser) return;
  manualMessage.value = '';
  await store.sendManualMessage(store.selectedUser, msg);
  checkAndResolveEscalation(store.selectedUser);
};

// P0.1 当人工回复后，判断用户是否在干预工单池，闭环结束状态
const checkAndResolveEscalation = (userId) => {
  const escData = store.escalations.find(e => e.user_id === userId);
  if (escData) {
    // 稍作延时，避免与消息发送成功的UI动画冲突卡顿
    setTimeout(async () => {
      if (window.confirm(`【人工干预流转】\n消息已发送给买家 [${userId}]。\n是否已解决此异常，并同时关闭该异常触发工单（移出干预池）？`)) {
        await store.resolveEscalation(escData.id);
      }
    }, 400);
  }
};
</script>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.2s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
</style>
