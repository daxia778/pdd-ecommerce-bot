<template>
  <div class="space-y-6">
    <!-- Overall Health Banner -->
    <div :class="['rounded-2xl shadow-sm border overflow-hidden transition-all', overallBannerClass]">
      <div class="p-6 flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div :class="['w-14 h-14 rounded-2xl flex items-center justify-center text-2xl shadow-inner', overallIconBg]">
            {{ overallIcon }}
          </div>
          <div>
            <h2 class="text-xl font-black text-gray-800">系统链路健康度</h2>
            <p class="text-xs text-gray-500 mt-0.5">全链路 7 节点实时巡检 — <span class="font-bold" :class="overallTextClass">{{ overallLabel }}</span></p>
          </div>
        </div>
        <button @click="refresh"
          :disabled="loading"
          class="px-4 py-2 bg-white/80 border border-gray-200 rounded-xl text-xs font-bold text-gray-600 hover:bg-white transition-all flex items-center gap-1.5">
          <span :class="loading ? 'animate-spin' : ''">↻</span>
          刷新
        </button>
      </div>
    </div>

    <!-- Pipeline Flow Visualization -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="p-5 border-b bg-gray-50/50">
        <h3 class="text-sm font-bold text-gray-700 flex items-center gap-2">
          <span class="text-base">🔗</span>
          消息处理链路 (Message Pipeline Flow)
        </h3>
        <p class="text-[10px] text-gray-400 mt-1">买家消息 → AI 处理 → 回复投递 → 企微协同。每个节点独立呈现健康状态。</p>
      </div>

      <div class="p-6">
        <!-- Pipeline Flow -->
        <div class="flex items-stretch justify-between gap-2 overflow-x-auto py-2">
          <div v-for="(comp, idx) in store.systemHealth.components" :key="comp.key"
            class="flex items-center gap-2 min-w-0">
            <!-- Node card -->
            <div :class="['flex flex-col items-center p-4 rounded-2xl border min-w-[130px] transition-all duration-300 hover:shadow-md hover:-translate-y-0.5', getCardClass(comp.status)]">
              <span class="text-2xl mb-2">{{ comp.icon }}</span>
              <span class="text-xs font-black text-gray-800 text-center mb-1">{{ comp.name }}</span>
              <span :class="['text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full', getStatusBadge(comp.status)]">
                {{ getStatusLabel(comp.status) }}
              </span>
              <p class="text-[10px] text-gray-400 text-center mt-2 leading-tight">{{ comp.detail }}</p>
            </div>

            <!-- Arrow connector -->
            <div v-if="idx < store.systemHealth.components.length - 1"
              class="flex items-center px-1 shrink-0">
              <svg class="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Detailed Component Grid -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="p-5 border-b">
        <h3 class="text-sm font-bold text-gray-700 flex items-center gap-2">
          <span class="text-base">📊</span>
          各组件详细状态 (Component Details)
        </h3>
      </div>
      <div class="p-5">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <div v-for="comp in store.systemHealth.components" :key="comp.key"
            :class="['rounded-xl border p-5 transition-all duration-300 hover:shadow-md', getCardClass(comp.status)]">

            <!-- Header -->
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-2">
                <span class="text-xl">{{ comp.icon }}</span>
                <span class="text-sm font-black text-gray-800">{{ comp.name }}</span>
              </div>
              <span :class="['w-3 h-3 rounded-full shrink-0', getDotClass(comp.status)]"></span>
            </div>

            <!-- Status badge -->
            <div class="mb-3">
              <span :class="['text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full', getStatusBadge(comp.status)]">
                {{ getStatusLabel(comp.status) }}
              </span>
            </div>

            <!-- Detail -->
            <p class="text-xs text-gray-500 leading-relaxed">{{ comp.detail }}</p>

            <!-- Key identifier -->
            <div class="mt-3 pt-3 border-t border-gray-100/50">
              <span class="text-[9px] font-mono text-gray-300 uppercase">{{ comp.key }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { store } from '../store.js';

const loading = computed(() => store.healthLoading);

const refresh = () => store.fetchSystemHealth();

onMounted(() => {
  store.fetchSystemHealth();
});

// Overall status styling
const overallBannerClass = computed(() => {
  const s = store.systemHealth.overall;
  if (s === 'error') return 'bg-red-50 border-red-200';
  if (s === 'warning' || s === 'degraded') return 'bg-amber-50 border-amber-200';
  return 'bg-emerald-50 border-emerald-200';
});

const overallIconBg = computed(() => {
  const s = store.systemHealth.overall;
  if (s === 'error') return 'bg-red-100';
  if (s === 'warning' || s === 'degraded') return 'bg-amber-100';
  return 'bg-emerald-100';
});

const overallIcon = computed(() => {
  const s = store.systemHealth.overall;
  if (s === 'error') return '❌';
  if (s === 'warning' || s === 'degraded') return '⚠️';
  return '✅';
});

const overallLabel = computed(() => {
  const s = store.systemHealth.overall;
  if (s === 'error') return '存在故障';
  if (s === 'warning' || s === 'degraded') return '部分降级';
  return '全部正常';
});

const overallTextClass = computed(() => {
  const s = store.systemHealth.overall;
  if (s === 'error') return 'text-red-600';
  if (s === 'warning' || s === 'degraded') return 'text-amber-600';
  return 'text-emerald-600';
});

// Component-level styling
const getCardClass = (status) => {
  const map = {
    healthy: 'bg-emerald-50/30 border-emerald-100/50',
    warning: 'bg-amber-50/30 border-amber-100/50',
    degraded: 'bg-orange-50/30 border-orange-100/50',
    error: 'bg-red-50/30 border-red-100/50',
    inactive: 'bg-gray-50/30 border-gray-100/50',
  };
  return map[status] || 'bg-gray-50/30 border-gray-100/50';
};

const getStatusBadge = (status) => {
  const map = {
    healthy: 'bg-emerald-100 text-emerald-700',
    warning: 'bg-amber-100 text-amber-700',
    degraded: 'bg-orange-100 text-orange-700',
    error: 'bg-red-100 text-red-700',
    inactive: 'bg-gray-100 text-gray-500',
  };
  return map[status] || 'bg-gray-100 text-gray-500';
};

const getStatusLabel = (status) => {
  const map = {
    healthy: '● 正常',
    warning: '◐ 告警',
    degraded: '◑ 降级',
    error: '✕ 故障',
    inactive: '○ 未启用',
  };
  return map[status] || status;
};

const getDotClass = (status) => {
  const map = {
    healthy: 'bg-emerald-500',
    warning: 'bg-amber-500 animate-pulse',
    degraded: 'bg-orange-500 animate-pulse',
    error: 'bg-red-500 animate-pulse',
    inactive: 'bg-gray-300',
  };
  return map[status] || 'bg-gray-300';
};
</script>
