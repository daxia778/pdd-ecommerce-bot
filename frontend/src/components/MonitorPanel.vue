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
            {{ store.sessions.length }}
          </span>
        </div>

        <!-- 搜索框 -->
        <div class="px-3 pt-3 pb-1">
          <div class="relative">
            <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索会话..."
              class="w-full pl-8 pr-3 py-1.5 text-xs bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition-all placeholder-gray-400"
            />
          </div>
        </div>

        <!-- 状态筛选 -->
        <div class="flex gap-1 px-3 py-2">
          <button
            v-for="tab in filterTabs" :key="tab.id"
            @click="sessionFilter = tab.id"
            :class="[
              'px-2.5 py-1 text-[10px] font-bold rounded-md transition-all cursor-pointer',
              sessionFilter === tab.id
                ? 'bg-blue-100 text-blue-700'
                : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
            ]"
          >{{ tab.name }}</button>
        </div>

        <div class="flex-1 overflow-y-auto p-2 space-y-2 chat-scroll">
          <div
            v-for="session in paginatedSessions"
            :key="session.user_id"
            @click="selectUser(session.user_id)"
            :class="[
              'p-3 rounded-xl cursor-pointer transition-all duration-300 ease-in-out border relative group',
              store.selectedUser === session.user_id
                ? 'bg-blue-50/80 border-blue-200 ring-2 ring-blue-500/20 shadow-sm transform scale-[1.02]'
                : 'bg-white border-transparent hover:border-gray-200 hover:bg-gray-50 hover:shadow-sm hover:-translate-y-0.5'
            ]"
          >
            <!-- 模拟器会话标签（最高优先级） -->
            <span
              v-if="session.platform === 'simulator'"
              class="absolute top-2 right-2 text-[9px] font-bold bg-cyan-100 text-cyan-700 px-1.5 py-0.5 rounded-full ring-1 ring-cyan-200 flex items-center gap-0.5"
            >🤖 模拟器</span>

            <!-- AI 暂停状态标签 -->
            <span
              v-else-if="store.pausedSessions[session.user_id]"
              class="absolute top-2 right-2 text-[9px] font-bold uppercase bg-orange-100 text-orange-600 px-1.5 py-0.5 rounded-full"
            >人工接管</span>

            <!-- 演示数据标签 -->
            <span
              v-else-if="session.is_demo"
              class="absolute top-2 right-2 text-[9px] font-bold uppercase bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded-full ring-1 ring-purple-200"
            >演示数据</span>

            <div class="flex items-center mb-1.5">
              <div :class="['w-7 h-7 rounded-lg flex items-center justify-center text-white font-black text-[10px] mr-2 shadow-sm shrink-0', getAvatarGradient(session.user_id)]">
                {{ extractChineseName(formatUserId(session.user_id)) }}
              </div>
              <span class="font-bold text-gray-700 truncate flex-1 text-sm mr-2">{{ formatUserId(session.user_id) }}</span>
              <span v-if="session.platform" class="text-[9px] uppercase font-bold text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded shrink-0">{{ session.platform }}</span>
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
          <div v-if="paginatedSessions.length === 0" class="flex flex-col items-center justify-center h-40 text-gray-400 font-medium">
            <svg class="w-10 h-10 mb-2 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
            <p class="text-xs">{{ searchQuery ? '无匹配结果' : '暂无活跃对话' }}</p>
          </div>
        </div>

        <!-- Pagination Controls -->
        <div v-if="totalPages > 1" class="p-2 border-t flex justify-between items-center bg-gray-50/50">
          <button
            @click="currentPage = Math.max(1, currentPage - 1)"
            :disabled="currentPage === 1"
            class="p-1 rounded text-gray-400 hover:text-gray-700 hover:bg-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
          </button>

          <span class="text-[10px] font-bold text-gray-500">
            {{ currentPage }} / {{ totalPages }} 页
          </span>

          <button
            @click="currentPage = Math.min(totalPages, currentPage + 1)"
            :disabled="currentPage === totalPages"
            class="p-1 rounded text-gray-400 hover:text-gray-700 hover:bg-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Center: Chat Window -->
    <div class="flex-1 flex flex-col h-full min-w-[320px]">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col h-full overflow-hidden">

        <!-- Chat Header — with AI Pause toggle -->
        <div v-if="store.selectedUser" class="p-4 border-b bg-gray-50 flex items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <div :class="['w-10 h-10 rounded-xl flex items-center justify-center text-white font-black shadow-lg ring-2 ring-white', extractChineseName(formatUserId(store.selectedUser)).length > 1 ? 'text-sm' : 'text-lg', getAvatarGradient(store.selectedUser)]">
              {{ extractChineseName(formatUserId(store.selectedUser)) }}
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
            <!-- 企业级空状态插画 -->
            <div class="relative w-28 h-28 mb-6">
              <div class="absolute inset-0 bg-gradient-to-b from-blue-50 to-transparent rounded-full"></div>
              <svg class="absolute inset-0 w-full h-full" viewBox="0 0 120 120" fill="none">
                <rect x="25" y="30" width="70" height="55" rx="8" fill="#f1f5f9" stroke="#e2e8f0" stroke-width="1.5"/>
                <rect x="32" y="40" width="35" height="4" rx="2" fill="#cbd5e1"/>
                <rect x="32" y="50" width="50" height="4" rx="2" fill="#e2e8f0"/>
                <rect x="32" y="60" width="20" height="4" rx="2" fill="#e2e8f0"/>
                <circle cx="85" cy="75" r="18" fill="#eff6ff" stroke="#bfdbfe" stroke-width="1.5"/>
                <path d="M80 75l3 3 7-7" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <p class="font-bold text-gray-400 text-sm mb-1">选择一个对话</p>
            <p class="text-xs text-gray-300 text-center leading-relaxed">从左侧列表点选买家会话<br/>查看实时对话记录</p>
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
          <span
            @click="simulateExtracting"
            :class="[
              'text-[9px] px-2 py-1 rounded-full font-bold uppercase tracking-wider cursor-pointer transition-all',
              isExtracting
                ? 'bg-purple-200 text-purple-700 animate-pulse'
                : 'bg-purple-100 text-purple-600 hover:bg-purple-200 hover:shadow-sm'
            ]"
          >
            {{ isExtracting ? 'AI 提取中...' : '重新 AI 提取' }}
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
                    🔄 AI 重新提取需求
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
const searchQuery = ref('');
const sessionFilter = ref('all');

const filterTabs = [
  { id: 'all', name: '全部' },
  { id: 'ai', name: 'AI 回复' },
  { id: 'manual', name: '人工接管' },
];

const currentPage = ref(1);
const ITEMS_PER_PAGE = 10;
let _searchDebounceTimer = null;

// Reset page when filter changes
watch(sessionFilter, () => {
  currentPage.value = 1;
});

// Debounced global search: calls backend API
watch(searchQuery, (newQ) => {
  currentPage.value = 1;
  if (_searchDebounceTimer) clearTimeout(_searchDebounceTimer);
  if (!newQ || !newQ.trim()) {
    store.searchMatchedUserIds = [];
    return;
  }
  // 200ms debounce for responsive feel
  _searchDebounceTimer = setTimeout(() => {
    store.searchMessages(newQ.trim());
  }, 200);
});

const filteredSessions = computed(() => {
  let list = store.sessions;

  // 状态筛选
  if (sessionFilter.value === 'manual') {
    list = list.filter(s => store.pausedSessions[s.user_id]);
  } else if (sessionFilter.value === 'ai') {
    list = list.filter(s => !store.pausedSessions[s.user_id]);
  }

  // 搜索过滤（通过后端 API 全局搜索）
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase();
    // 后端返回的匹配 user_id 列表
    const backendMatched = new Set(store.searchMatchedUserIds || []);
    list = list.filter(s => {
      // 1. 后端全局搜索命中
      if (backendMatched.has(s.user_id)) return true;
      // 2. 本地用户名匹配（秒级快速响应）
      if (formatUserId(s.user_id).toLowerCase().includes(q)) return true;
      return false;
    });
  }

  // 模拟器会话置顶
  return list.slice().sort((a, b) => {
    const aIsSim = a.platform === 'simulator' ? 1 : 0;
    const bIsSim = b.platform === 'simulator' ? 1 : 0;
    return bIsSim - aIsSim;
  });
});

const totalPages = computed(() => Math.ceil(filteredSessions.value.length / ITEMS_PER_PAGE));

const paginatedSessions = computed(() => {
  const start = (currentPage.value - 1) * ITEMS_PER_PAGE;
  return filteredSessions.value.slice(start, start + ITEMS_PER_PAGE);
});

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
    if (id.startsWith('sim_')) {
        return '🤖 模拟-' + id.replace('sim_', '');
    }
    if (id.startsWith('demo_buyer_sim_')) {
        return '🤖 模拟买家_' + id.replace('demo_buyer_sim_', '');
    }
    if (id.startsWith('demo_buyer_')) {
        return '测试买家_' + id.replace('demo_buyer_', '');
    }
    return id;
};

// 提取纯中文字符用于头像显示（最多2个字）
const extractChineseName = (name) => {
    if (!name) return '客';
    // 匹配所有中文字符
    const chineseChars = name.match(/[\u4e00-\u9fa5]/g);
    if (chineseChars && chineseChars.length > 0) {
        return chineseChars.slice(0, 2).join('');
    }
    // 如果没有中文，退回取前两大写字母缩写
    const cleanEn = name.replace(/[^a-zA-Z]/g, '');
    if (cleanEn) return cleanEn.slice(0, 2).toUpperCase();
    return name.slice(0, 1).toUpperCase() || '客';
};

const isPaused = computed(() =>
  store.selectedUser ? !!store.pausedSessions[store.selectedUser] : false
);

const MOCK_REQUIREMENTS = {
  '【大四】林同学': { topic: '毕业答辩PPT', pages: '25页', style: '学术严谨 / 校园风', deadline: '下周', budget: '约337元', audience: '导师/答辩委员会', outline: '研究背景 -> 方法论 -> 结论', assets: '论文摘要.doc' },
  '王总(找融资)': { topic: '大健康融资商业计划书(BP)', pages: '约20页', style: '高端科技 / 创投风', deadline: '下周一晚上 (特急)', budget: '5000元', audience: '风险投资人', outline: '核心痛点 -> 解决方案 -> 商业模式', assets: '官网资料.pdf' },
  '人事-小玉': { topic: 'SaaS季度总结汇报', pages: '30页', style: '现代科技风', deadline: '本月底', budget: '约1800元', audience: '全公司员工', outline: '-', assets: '-' },
  '🔥急单-李先生': { topic: '市政工程投标方案', pages: '45页', style: '严肃正规 (纯美化排版)', deadline: '明早9点前', budget: '3600元', audience: '评标委员会', outline: '企业资质 -> 施工方案 -> 报价清单', assets: '标书原稿.doc' },
  '智创科技-陈总监': { topic: '展会全案', pages: '宽屏PPT(页数待定)', style: '智领未来·云端共生主题', deadline: '下个月', budget: '约30000元', audience: '展会参观者/行业客户', outline: '-', assets: 'VI规范.pdf' },
  '微商加盟-赵姐': { topic: '微商招商加盟课件', pages: '40页', style: '前10高端定制+后30商务精装', deadline: '初稿2-3天', budget: '3000元', audience: '加盟代理', outline: '封面介绍 -> 核心产品 -> 盈利模式', assets: '原稿.pdf' },
  '婚礼策划-莹莹': { topic: '婚礼纪念动态相册', pages: '20多页', style: '浪漫温馨/动态视效', deadline: '半个月内', budget: '800元', audience: '婚礼现场宾客', outline: '-', assets: '照片与视频.zip' },
  '年终汇报-王经理': { topic: '集团年度汇报PPT翻新', pages: '15页', style: '集团级高端/Logo蓝', deadline: '后天下午彩排前 (加急)', budget: '约2340元', audience: '集团大老板', outline: '-', assets: '旧版PPT.pptx' },
  'sim_小张': { topic: 'PPT数据图表售后修改', pages: '第3页', style: '-', deadline: '15分钟内 (紧急)', budget: '-', audience: '下午汇报', outline: '-', assets: '修正数据.xlsx' }
};

// Internal editable state for the current selected user
const localReqData = reactive({
  topic: '', pages: '', style: '', deadline: '', budget: '', audience: '', outline: '', assets: ''
});

// Dynamic per-field confidence from backend
const fieldConfidence = reactive({
  topic: 0, pages: 0, style: 0, deadline: 0, budget: 0, audience: 0, outline: 0, assets: 0
});

const getConfidence = (key) => {
  return fieldConfidence[key] || 0;
};

const isExtracting = ref(false);
const extractProgress = ref(0);

// Watch selected user to load requirements from backend or demo data
watch(() => store.selectedUser, async (newVal) => {
  isExtracting.value = false;
  extractProgress.value = 0;

  if (newVal && MOCK_REQUIREMENTS[newVal]) {
    // Demo data: use local mock
    const data = MOCK_REQUIREMENTS[newVal];
    Object.keys(localReqData).forEach(k => {
      localReqData[k] = data[k] || '-';
    });
    // Demo data uses fixed confidence
    Object.keys(fieldConfidence).forEach(k => fieldConfidence[k] = data[k] && data[k] !== '-' ? 95 : 0);
  } else if (newVal) {
    // Real user: try extracting from backend
    Object.keys(localReqData).forEach(k => localReqData[k] = '');
    await triggerExtraction(newVal);
  } else {
    Object.keys(localReqData).forEach(k => localReqData[k] = '');
  }
});

// Watch currentChat changes to re-extract requirements from backend
let _lastChatLen = 0;
watch(() => store.currentChat, async (newVal) => {
    if (!store.selectedUser) return;
    // Only re-extract when new messages arrive (not on initial load)
    if (newVal && newVal.length > _lastChatLen && _lastChatLen > 0) {
        // Don't re-extract for demo users
        if (!MOCK_REQUIREMENTS[store.selectedUser]) {
            await triggerExtraction(store.selectedUser);
        }
    }
    _lastChatLen = newVal ? newVal.length : 0;
}, { deep: true });

async function triggerExtraction(userId) {
    isExtracting.value = true;
    extractProgress.value = 20;

    // Animate progress while waiting for backend
    const progressInterval = setInterval(() => {
        if (extractProgress.value < 90) {
            extractProgress.value += Math.floor(Math.random() * 10) + 3;
        }
    }, 200);

    try {
        const data = await store.extractRequirements(userId);
        extractProgress.value = 100;

        if (data && data.source !== 'none') {
            // Fill local form with extracted data
            Object.keys(localReqData).forEach(k => {
                if (data[k]) localReqData[k] = data[k];
            });
            // Update per-field confidence from backend
            if (data.confidence) {
                Object.keys(fieldConfidence).forEach(k => {
                    fieldConfidence[k] = data.confidence[k] || 0;
                });
            }
        } else {
            // No data found — clear confidence
            Object.keys(fieldConfidence).forEach(k => fieldConfidence[k] = 0);
        }
    } catch (e) {
        console.error('Extraction failed:', e);
    } finally {
        clearInterval(progressInterval);
        setTimeout(() => {
            isExtracting.value = false;
        }, 300);
    }
}

const simulateExtracting = async () => {
    if (store.selectedUser) {
        await triggerExtraction(store.selectedUser);
    }
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
