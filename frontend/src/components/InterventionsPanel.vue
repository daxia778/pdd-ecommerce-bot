<template>
  <div class="space-y-6">
      <div class="bg-white rounded-2xl shadow-sm border-l-4 border-red-500 overflow-hidden">
          <div class="p-6">
              <div class="flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4">
                  <h2 class="text-xl font-bold text-gray-800 flex items-center">
                      <svg class="w-6 h-6 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      人工干预池 (Manual Intervention Pool)
                  </h2>

                  <!-- P1.1 过滤标签栏 -->
                  <div class="flex gap-2 flex-wrap">
                     <button @click="filterType = 'all'" :class="['px-3 py-1.5 rounded-lg text-xs font-bold transition-all', filterType === 'all' ? 'bg-red-500 text-white shadow-md shadow-red-200' : 'bg-gray-100 text-gray-600 hover:bg-gray-200']">全部 ({{ store.escalations.length }})</button>
                     <button @click="filterType = 'urgent'" :class="['px-3 py-1.5 rounded-lg text-xs font-bold transition-all', filterType === 'urgent' ? 'bg-red-500 text-white shadow-md shadow-red-200' : 'bg-gray-100 text-gray-600 hover:bg-gray-200']">高优/急单</button>
                     <button @click="filterType = 'conflict'" :class="['px-3 py-1.5 rounded-lg text-xs font-bold transition-all', filterType === 'conflict' ? 'bg-red-500 text-white shadow-md shadow-red-200' : 'bg-gray-100 text-gray-600 hover:bg-gray-200']">售后冲突</button>
                     <button @click="filterType = 'rule'" :class="['px-3 py-1.5 rounded-lg text-xs font-bold transition-all', filterType === 'rule' ? 'bg-red-500 text-white shadow-md shadow-red-200' : 'bg-gray-100 text-gray-600 hover:bg-gray-200']">规则触发</button>
                  </div>
              </div>

              <!-- P1.3 骨架屏 -->
              <div v-if="isLoading" class="space-y-4">
                  <div v-for="i in 3" :key="i" class="h-16 bg-gray-100 rounded-xl animate-pulse"></div>
              </div>

              <div v-else class="overflow-x-auto rounded-xl border border-gray-100">
                  <table class="min-w-full divide-y divide-gray-200">
                      <thead class="bg-gray-50">
                          <tr>
                              <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-widest">买家ID</th>
                              <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-widest">优先级/接管类型</th>
                              <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-widest">原因/标签</th>
                              <th class="px-6 py-4 text-left text-xs font-bold text-gray-500 uppercase tracking-widest">触发内容记录</th>
                              <th class="px-6 py-4 text-right text-xs font-bold text-gray-500 uppercase tracking-widest">操作</th>
                          </tr>
                      </thead>
                      <tbody class="bg-white divide-y divide-gray-100">
                          <tr v-for="(esc, idx) in filteredEscalations" :key="esc.id" class="hover:bg-red-50/30 transition-colors">
                              <td class="px-6 py-4 whitespace-nowrap font-bold text-gray-700">
                                <div class="flex items-center gap-3">
                                  <div class="relative flex-shrink-0">
                                     <div :class="['w-10 h-10 rounded-xl flex items-center justify-center text-white font-black shadow-md ring-2 ring-white', extractChineseName(esc.user_id).length > 1 ? 'text-[11px]' : 'text-sm', getAvatarGradient(esc.user_id)]">
                                       {{ extractChineseName(esc.user_id) }}
                                     </div>
                                     <div v-if="idx === 0 && filterType === 'all'" class="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-white animate-pulse shadow-sm shadow-red-300"></div>
                                  </div>
                                  <span class="text-sm truncate max-w-[120px]">{{ esc.user_id }}</span>
                                </div>
                              </td>
                              <td class="px-6 py-4 whitespace-nowrap">
                                  <div class="flex flex-col gap-1.5">
                                      <!-- Priority Badge -->
                                      <span v-if="getPriorityValue(esc) === 3" class="px-2 py-0.5 text-[10px] font-black rounded text-white bg-red-500 inline-flex items-center w-max shadow-sm shadow-red-200">
                                         🚨 紧急干预
                                      </span>
                                      <span v-else-if="getPriorityValue(esc) === 2" class="px-2 py-0.5 text-[10px] font-bold rounded text-orange-700 bg-orange-100 inline-flex items-center w-max border border-orange-200">
                                         ⚠️ 优先处理
                                      </span>

                                      <span v-if="(esc.priority === 'urgent' || idx % 2 === 0)" class="px-2.5 py-1 text-[10px] font-bold rounded-md bg-purple-50 text-purple-700 border border-purple-100 flex items-center gap-1 w-max mt-1">
                                         <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                                         系统自动拦截
                                      </span>
                                      <span v-else class="px-2.5 py-1 text-[10px] font-bold rounded-md bg-orange-50 text-orange-700 border border-orange-100 flex items-center gap-1 w-max mt-1">
                                         <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                                         人工介入请求
                                      </span>
                                  </div>
                              </td>
                              <td class="px-6 py-4 whitespace-nowrap">
                                  <span class="px-3 py-1 text-[10.5px] font-black rounded-full bg-red-50 text-red-600 uppercase tracking-wide border border-red-100 shadow-sm max-w-[150px] truncate block">
                                      {{ esc.reason_label || '需人工处理' }}
                                  </span>
                              </td>
                              <td class="px-6 py-4">
                                 <div class="text-[13px] text-gray-700 line-clamp-2 max-w-sm bg-gray-50/80 p-2.5 rounded-lg border border-gray-100" :title="esc.trigger_message">
                                     "{{ esc.trigger_message }}"
                                 </div>
                              </td>
                              <td class="px-6 py-4 text-right space-x-2 whitespace-nowrap">
                                  <button @click="goToChat(esc.user_id)" class="bg-white border border-gray-200 text-gray-700 px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-gray-50 transition-all">
                                      去回复
                                  </button>
                                  <button @click="resolveEscalation(esc.id)" class="bg-red-600 text-white px-3 py-1.5 rounded-lg text-xs font-bold hover:bg-red-700 shadow-sm shadow-red-200 transition-all">
                                      直接关闭
                                  </button>
                              </td>
                          </tr>
                          <tr v-if="filteredEscalations.length === 0">
                              <td colspan="5" class="px-6 py-12 text-center">
                                  <div class="flex flex-col items-center">
                                      <span class="text-4xl mb-4">🎉</span>
                                      <p class="text-gray-500 font-bold">暂无此类待介入请求</p>
                                  </div>
                              </td>
                          </tr>
                      </tbody>
                  </table>
              </div>
          </div>
      </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { store } from '../store.js';

const isLoading = ref(true);
const filterType = ref('all');

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

// 提取纯中文字符用于头像显示（最多2个字）
const extractChineseName = (name) => {
    if (!name) return '客';
    const chineseChars = name.match(/[\u4e00-\u9fa5]/g);
    if (chineseChars && chineseChars.length > 0) {
        return chineseChars.slice(0, 2).join('');
    }
    const cleanEn = name.replace(/[^a-zA-Z]/g, '');
    if (cleanEn) return cleanEn.slice(0, 2).toUpperCase();
    return name.slice(0, 1).toUpperCase() || '客';
};

onMounted(() => {
    // Simulate initial loading for Skeleton
    setTimeout(() => {
        isLoading.value = false;
    }, 600);
});

// 计算优先级值（用于排序）
const getPriorityValue = (esc) => {
    if (esc.priority === 'urgent') return 3;
    if (esc.priority === 'high' || (esc.reason_label && esc.reason_label.includes('冲突'))) return 2;
    return 1;
};

// 过滤和排序
const filteredEscalations = computed(() => {
    let result = store.escalations;

    if (filterType.value === 'urgent') {
        result = result.filter(e => getPriorityValue(e) >= 2 || (e.reason_label && e.reason_label.includes('大客户')));
    } else if (filterType.value === 'conflict') {
        result = result.filter(e => e.reason_label && e.reason_label.includes('售后'));
    } else if (filterType.value === 'rule') {
        result = result.filter(e => e.reason_label && e.reason_label.includes('规则触发'));
    }

    // 按优先级降序排序
    return result.slice().sort((a, b) => getPriorityValue(b) - getPriorityValue(a));
});

const resolveEscalation = async (id) => {
  if (!confirm('确认直接结束接管？（建议在回复后操作）')) return;
  await store.resolveEscalation(id);
};

const goToChat = (userId) => {
  store.selectedUser = userId;
  store.activePanel = 'monitor';
  // AI 自动暂停已经在 monitor 里处理
};
</script>
