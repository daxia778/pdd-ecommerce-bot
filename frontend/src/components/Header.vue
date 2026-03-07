<template>
  <header class="h-16 border-b border-gray-200 bg-white flex items-center justify-between px-8 shrink-0 w-full">
      <div class="flex items-center space-x-2">
          <span class="text-gray-400 text-sm font-medium">当前模块 /</span>
          <span class="font-bold text-gray-800">{{ panelName }}</span>
      </div>
      <div class="flex items-center space-x-6">
          <div class="flex items-center space-x-5 text-sm">
              <div class="flex items-center">
                  <span class="w-2 h-2 rounded-full bg-blue-500 mr-2"></span>
                  <span class="text-gray-500 font-medium">会话:</span>
                  <span class="ml-1 font-bold">{{ store.sessions ? store.sessions.length : 0 }}</span>
              </div>
              <div class="flex items-center">
                  <span class="w-2 h-2 rounded-full bg-red-500 mr-2"></span>
                  <span class="text-gray-500 font-medium">待办:</span>
                  <span class="ml-1 font-bold text-red-600">{{ store.escalations ? store.escalations.length : 0 }}</span>
              </div>
              <div class="flex items-center">
                  <span class="w-2 h-2 rounded-full bg-green-500 mr-2"></span>
                  <span class="text-gray-500 font-medium">生产:</span>
                  <span class="ml-1 font-bold">{{ store.orders ? store.orders.length : 0 }}</span>
              </div>
          </div>
      </div>
  </header>
</template>

<script setup>
import { computed } from 'vue';
import { store } from '../store.js';

const names = {
  'monitor': '监控大屏',
  'statistics': '数据统计',
  'interventions': '人工干预池',
  'pipeline': '生产流水线',
  'knowledge': '知识库管理',
  'settings': '系统配置'
};

const panelName = computed(() => names[store.activePanel] || 'Dashboard');
</script>
