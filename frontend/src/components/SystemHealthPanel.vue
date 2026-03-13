<template>
  <div class="space-y-6 p-6">
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
          class="px-4 py-2 bg-white/80 border border-gray-200 rounded-2xl text-xs font-bold text-gray-600 hover:bg-white transition-all flex items-center gap-1.5">
          <span :class="loading ? 'animate-spin' : ''">↻</span>
          刷新
        </button>
      </div>
    </div>

    <!-- Pipeline Flow Visualization -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
      <div class="p-5 border-b bg-gray-50/50">
        <h3 class="text-sm font-bold text-gray-700 flex items-center gap-2">
          <span class="text-base">🔗</span>
          消息处理链路 (Message Pipeline Flow)
        </h3>
        <p class="text-[10px] text-gray-400 mt-1">买家消息 → AI 处理 → 回复投递 → 企微协同。点击节点查看配置详情。</p>
      </div>

      <div class="p-6">
        <div class="flex items-stretch justify-between gap-2 overflow-x-auto py-2">
          <div v-for="(comp, idx) in store.systemHealth.components" :key="comp.key"
            class="flex items-center gap-2 min-w-0">
            <div @click="openConfig(comp.key)"
              :class="['flex flex-col items-center p-4 rounded-2xl border min-w-[130px] transition-all duration-300 hover:shadow-md hover:-translate-y-0.5 cursor-pointer', getCardClass(comp.status)]">
              <span class="text-2xl mb-2">{{ comp.icon }}</span>
              <span class="text-xs font-black text-gray-800 text-center mb-1">{{ comp.name }}</span>
              <span :class="['text-[9px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full', getStatusBadge(comp.status)]">
                {{ getStatusLabel(comp.status) }}
              </span>
              <p class="text-[10px] text-gray-400 text-center mt-2 leading-tight">{{ comp.detail }}</p>
            </div>
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
    <div class="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
      <div class="p-5 border-b">
        <h3 class="text-sm font-bold text-gray-700 flex items-center gap-2">
          <span class="text-base">📊</span>
          各组件详细状态 (Component Details)
        </h3>
      </div>
      <div class="p-5">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <div v-for="comp in store.systemHealth.components" :key="comp.key"
            @click="openConfig(comp.key)"
            :class="['rounded-2xl border p-5 transition-all duration-300 hover:shadow-md cursor-pointer', getCardClass(comp.status)]">

            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-2">
                <span class="text-xl">{{ comp.icon }}</span>
                <span class="text-sm font-black text-gray-800">{{ comp.name }}</span>
              </div>
              <span :class="['w-3 h-3 rounded-full shrink-0', getDotClass(comp.status)]"></span>
            </div>

            <div class="mb-3">
              <span :class="['text-[10px] font-bold uppercase tracking-widest px-2.5 py-1 rounded-full', getStatusBadge(comp.status)]">
                {{ getStatusLabel(comp.status) }}
              </span>
            </div>

            <p class="text-xs text-gray-500 leading-relaxed">{{ comp.detail }}</p>

            <div class="mt-3 pt-3 border-t border-gray-100/50 flex items-center justify-between">
              <span class="text-[9px] font-mono text-gray-300 uppercase">{{ comp.key }}</span>
              <span class="text-[9px] text-blue-500 font-bold">点击查看配置 →</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Config Modal -->
    <Teleport to="body">
      <div v-if="showConfigModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click.self="showConfigModal = false">
        <div class="fixed inset-0 bg-black/40 backdrop-blur-sm" @click="showConfigModal = false"></div>
        <div class="relative bg-white rounded-2xl shadow-2xl border border-gray-200 w-full max-w-2xl max-h-[80vh] flex flex-col overflow-hidden z-10">
          <!-- Modal Header -->
          <div class="p-5 border-b bg-gray-50 flex items-center justify-between shrink-0">
            <div>
              <h3 class="text-lg font-black text-gray-800">{{ configData?.title || '加载中...' }}</h3>
              <p class="text-xs text-gray-400 mt-0.5 font-mono">{{ configData?.file_path || '' }}</p>
            </div>
            <button @click="showConfigModal = false"
              class="w-8 h-8 bg-gray-200 hover:bg-gray-300 rounded-full flex items-center justify-center text-gray-500 transition-colors">
              ✕
            </button>
          </div>

          <!-- Modal Body -->
          <div class="flex-1 overflow-y-auto p-5 space-y-4">
            <div v-if="configLoading" class="flex items-center justify-center py-12">
              <div class="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              <span class="ml-3 text-sm text-gray-500">加载配置中...</span>
            </div>

            <template v-else-if="configData">
              <!-- Env Vars -->
              <div v-if="configData.env_vars && Object.keys(configData.env_vars).length > 0">
                <h4 class="text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">环境变量</h4>
                <div class="bg-gray-50 rounded-xl border border-gray-100 overflow-hidden">
                  <div v-for="(val, key) in configData.env_vars" :key="key"
                    class="flex items-center justify-between px-4 py-2.5 border-b border-gray-100 last:border-b-0">
                    <span class="text-xs font-mono font-bold text-gray-700">{{ key }}</span>
                    <span class="text-xs font-mono text-gray-400">{{ val }}</span>
                  </div>
                </div>
              </div>

              <!-- File Content -->
              <div>
                <h4 class="text-xs font-bold text-gray-600 uppercase tracking-wider mb-2">配置文件内容</h4>
                <pre class="bg-gray-900 text-green-400 text-xs p-4 rounded-xl overflow-x-auto max-h-[400px] overflow-y-auto font-mono leading-relaxed whitespace-pre-wrap break-all">{{ configData.file_content }}</pre>
              </div>
            </template>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { store } from '../store.js';

const loading = computed(() => store.healthLoading);
const showConfigModal = ref(false);
const configLoading = ref(false);
const configData = ref(null);

const refresh = () => store.fetchSystemHealth();

onMounted(() => {
  store.fetchSystemHealth();
});

const openConfig = async (key) => {
  showConfigModal.value = true;
  configLoading.value = true;
  configData.value = null;
  try {
    const res = await fetch(`/api/dashboard/component-config/${key}`, {
      headers: store._headers(),
    });
    if (res.ok) {
      configData.value = await res.json();
    } else {
      configData.value = { title: '加载失败', file_path: '', file_content: `HTTP ${res.status}`, env_vars: {} };
    }
  } catch (e) {
    configData.value = { title: '网络错误', file_path: '', file_content: e.message, env_vars: {} };
  } finally {
    configLoading.value = false;
  }
};

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
