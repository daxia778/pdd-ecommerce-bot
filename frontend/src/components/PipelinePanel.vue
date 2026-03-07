<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="p-6 border-b flex justify-between items-center">
        <h2 class="text-xl font-bold text-gray-800 flex items-center">
          <svg class="w-6 h-6 text-indigo-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          PPT 订单工作台
        </h2>
        <div class="flex items-center gap-3">
          <!-- 显示已完成 toggle -->
          <button @click="showAll = !showAll; store.fetchData()"
            :class="['text-[11px] font-bold px-3 py-1.5 rounded-lg border transition-all', showAll ? 'bg-gray-100 border-gray-200 text-gray-600' : 'bg-white border-gray-200 text-gray-400 hover:bg-gray-50']">
            {{ showAll ? '📋 全部工单' : '📋 全部工单' }}
          </button>
          <div class="flex items-center gap-1.5">
            <span :class="['w-2 h-2 rounded-full', pendingCount > 0 ? 'bg-orange-500 animate-pulse' : 'bg-green-400']"></span>
            <span class="text-xs font-bold text-gray-400 uppercase tracking-widest">
              {{ pendingCount > 0 ? `${pendingCount} 待处理` : '全部完成' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Order cards -->
      <div class="p-6">
        <div v-if="store.orders.length === 0" class="text-center py-16">
          <svg class="w-12 h-12 text-gray-200 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p class="text-gray-400 font-medium">暂无待处理的 PPT 工单</p>
          <p class="text-gray-300 text-xs mt-1">当买家的需求收集完成后，工单会自动出现在这里</p>
        </div>

        <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div v-for="order in store.orders" :key="order.id"
            :class="['border border-gray-100 rounded-2xl overflow-hidden shadow-sm transition-all duration-300 hover:shadow-md hover:-translate-y-1 group relative', getCardClass(order.status)]">

            <!-- Colored Left Border based on status -->
            <div :class="['absolute top-0 bottom-0 left-0 w-1.5', getBorderClass(order.status)]"></div>

            <!-- Card Header -->
            <div class="px-6 py-4 flex justify-between items-center bg-white border-b border-gray-50/80">
              <div class="pl-2">
                <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-0.5">订单号 Order_SN</p>
                <p class="font-mono font-black text-gray-800 text-[15px]">{{ order.order_sn }}</p>
              </div>
              <div class="flex items-center gap-2">
                <span :class="['px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest', getStatusClass(order.status)]">
                  {{ getStatusLabel(order.status) }}
                </span>
              </div>
            </div>

            <!-- Requirement block -->
            <div class="bg-gray-50/50 px-6 py-5 relative">
              <div class="flex justify-between items-center mb-3">
                <p class="text-[10px] font-bold text-gray-500 uppercase tracking-widest flex items-center gap-1.5"><span class="w-1.5 h-1.5 rounded-full bg-gray-400"></span>需求摘要</p>
                <button @click="copyRequirement(order)"
                  class="text-[10px] font-bold text-indigo-500 bg-indigo-50 px-2 py-1 rounded hover:bg-indigo-100 hover:text-indigo-700 flex items-center gap-1 transition-colors">
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  一键复制需求
                </button>
              </div>

              <!-- 格式化需求展示 -->
              <div class="space-y-1.5">
                <div v-for="(item, idx) in parseRequirement(order.requirement)" :key="idx"
                  class="flex items-start gap-2">
                  <span class="text-[10px] font-bold text-gray-400 w-12 shrink-0 mt-0.5">{{ item.label }}</span>
                  <span class="text-xs text-gray-700 leading-relaxed font-medium">{{ item.value }}</span>
                </div>
              </div>
            </div>

            <!-- Card Footer: actions -->
            <div class="px-6 py-4 bg-white flex items-center justify-between border-t border-gray-50">
              <div class="flex items-center gap-2">
                 <div :class="['w-8 h-8 rounded-lg flex items-center justify-center text-white font-black text-[10px] shadow-md ring-1 ring-white/80', getAvatarGradient(order.user_id || '?')]">
                    {{ order.user_id?.slice(0,1) || '?' }}
                 </div>
                 <div class="flex flex-col">
                    <span class="text-[11px] font-bold text-gray-700">{{ order.user_id?.split('-')[order.user_id?.split('-').length - 1] || order.user_id }}</span>
                    <span class="text-[9px] text-gray-400 font-medium">{{ order.created_at?.split(' ')[0] }}</span>
                 </div>
              </div>

              <!-- 待接单 -->
              <button v-if="order.status === 'req_fixed'"
                @click="handleClaim(order.id)"
                class="bg-indigo-600 text-white px-4 py-2 rounded-xl text-xs font-black shadow-lg shadow-indigo-100 hover:bg-indigo-700 transition-all flex items-center gap-1.5">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11" />
                </svg>
                接单处理
              </button>

              <!-- 处理中：标记交付 -->
              <div v-else-if="order.status === 'processing' || order.status === 'awaiting_review'"
                class="flex items-center gap-2">
                <span class="text-[10px] text-orange-500 font-bold">已接单，请生成 PPT 后标记交付</span>
                <button @click="handleDeliver(order.id)"
                  class="bg-green-600 text-white px-4 py-2 rounded-xl text-xs font-black shadow-lg shadow-green-100 hover:bg-green-700 transition-all flex items-center gap-1.5">
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                  </svg>
                  标记已交付
                </button>
              </div>

              <!-- 已交付 -->
              <div v-else-if="order.status === 'shipped'"
                class="flex items-center gap-1.5 text-green-600">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
                <span class="text-xs font-bold">已交付</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { store } from '../store.js';

const showAll = ref(false);

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

const pendingCount = computed(() =>
  store.orders.filter(o => o.status === 'req_fixed').length
);

const handleClaim = async (id) => {
  if (!confirm('确认接单？接单后请尽快生成 PPT 并交付。')) return;
  await store.claimOrder(id);
};

const handleDeliver = async (id) => {
  if (!confirm('确认已完成 PPT 制作并交付给买家？')) return;
  await store.deliverOrder(id);
};

const parseRequirement = (str) => {
  const labelMap = {
    topic: '主题',
    pages: '页数',
    style: '风格',
    details: '备注',
    deadline: '截止日',
    format: '格式',
  };
  try {
    const obj = JSON.parse(str || '{}');
    return Object.entries(obj).map(([k, v]) => ({
      label: labelMap[k] || k,
      value: String(v) || '—',
    }));
  } catch {
    return [{ label: '需求', value: str || '（未填写）' }];
  }
};

const copyRequirement = (order) => {
  const items = parseRequirement(order.requirement);
  const text = `【PPT制作需求】\n订单号：${order.order_sn}\n` +
    items.map(i => `${i.label}：${i.value}`).join('\n');
  navigator.clipboard.writeText(text).then(() => {
    alert('✅ 需求已复制到剪贴板！可直接粘贴到 AI 工具生成 PPT。');
  });
};

const getCardClass = (status) => {
  const map = {
    'req_fixed': 'bg-gradient-to-br from-orange-50/10 to-white',
    'processing': 'bg-gradient-to-br from-blue-50/10 to-white',
    'awaiting_review': 'bg-gradient-to-br from-purple-50/10 to-white',
    'shipped': 'bg-gradient-to-br from-green-50/10 to-white opacity-80',
    'generating': 'bg-gradient-to-br from-indigo-50/10 to-white',
  };
  return map[status] || 'bg-white';
};

const getBorderClass = (status) => {
  const map = {
    'req_fixed': 'bg-orange-500',
    'processing': 'bg-blue-500',
    'awaiting_review': 'bg-purple-500',
    'shipped': 'bg-green-500',
    'generating': 'bg-indigo-500',
  };
  return map[status] || 'bg-gray-200';
};

const getStatusClass = (status) => {
  const map = {
    'generating': 'bg-blue-100 text-blue-700',
    'processing': 'bg-blue-100 text-blue-700',
    'awaiting_review': 'bg-purple-100 text-purple-700',
    'shipped': 'bg-green-100 text-green-700',
    'req_fixed': 'bg-orange-100 text-orange-700',
  };
  return map[status] || 'bg-gray-100 text-gray-700';
};

const getStatusLabel = (status) => {
  const map = {
    'generating': 'AI 生成中',
    'processing': '处理中',
    'awaiting_review': '待审核',
    'shipped': '✓ 已交付',
    'req_fixed': '待接单',
  };
  return map[status] || status;
};
</script>
