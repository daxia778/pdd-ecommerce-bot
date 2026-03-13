<template>
  <aside
    :class="[
      'h-screen flex flex-col shrink-0 z-50 bg-white border-r border-gray-200 relative transition-all duration-300 ease-in-out',
      collapsed ? 'w-[72px]' : 'w-[260px]'
    ]"
  >
    <!-- Logo区域 -->
    <div :class="['flex items-center z-10 relative transition-all duration-300 py-6 shrink-0', collapsed ? 'justify-center px-3' : 'px-5']">
      <div class="w-9 h-9 bg-[#465FFF] rounded-xl flex items-center justify-center shrink-0 shadow-sm">
        <span class="text-white text-[13px] font-black tracking-tighter">PD</span>
      </div>
      <div
        class="transition-all duration-300 overflow-hidden whitespace-nowrap ml-3"
        :class="collapsed ? 'w-0 opacity-0 ml-0' : 'w-auto opacity-100'"
      >
        <h1 class="text-[15px] font-semibold text-gray-900 tracking-tight">智能客服中心</h1>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="flex-1 z-10 overflow-y-auto pb-6">
      
      <!-- 分组: 核心运营 -->
      <div class="mb-4">
        <p
          class="px-5 text-xs font-medium text-gray-400 uppercase tracking-wider whitespace-nowrap transition-all duration-300 overflow-hidden"
          :class="collapsed ? 'h-0 opacity-0 mb-0' : 'h-5 opacity-100 mb-3'"
        >核心运营</p>

        <div class="flex flex-col gap-1 px-3">
          <div
            v-for="item in navGroups.workspace"
            :key="item.id"
            @click="store.activePanel = item.id"
            :class="[
              'relative group flex items-center transition-all cursor-pointer rounded-lg',
              collapsed ? 'px-3 py-2.5 justify-center' : 'px-3 py-2.5 gap-3',
              store.activePanel === item.id
                ? 'bg-[#ecf3ff] text-[#465FFF]'
                : 'text-gray-700 hover:bg-gray-100'
            ]"
            :title="collapsed ? item.name : ''"
          >
            <span v-html="item.icon" :class="['w-5 h-5 shrink-0', store.activePanel === item.id ? 'text-[#465FFF]' : 'text-gray-500 group-hover:text-gray-700']"></span>
            <span
              class="text-sm font-medium whitespace-nowrap transition-all duration-300 overflow-hidden"
              :class="collapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'"
            >{{ item.name }}</span>

            <!-- 待办徽标 -->
            <span
              v-if="item.id === 'interventions' && store.escalations?.length > 0"
              :class="[
                'absolute flex items-center justify-center font-semibold',
                collapsed ? '-top-1 -right-1 w-4 h-4 text-[9px] rounded-full bg-[#465FFF] text-white ring-2 ring-white' : 'right-2 px-2 py-0.5 text-[10px] rounded-full bg-[#ecf3ff] text-[#465FFF] border border-[#dde9ff]'
              ]"
            >
              {{ store.escalations.length > 99 ? '99+' : store.escalations.length }}
            </span>
          </div>
        </div>
      </div>

      <!-- 分组: 业务洞察 -->
      <div class="mb-4">
        <p
          class="px-5 text-xs font-medium text-gray-400 uppercase tracking-wider whitespace-nowrap transition-all duration-300 overflow-hidden"
          :class="collapsed ? 'h-0 opacity-0 mb-0' : 'h-5 opacity-100 mb-3'"
        >业务洞察</p>

        <div class="flex flex-col gap-1 px-3">
          <div
            v-for="item in navGroups.insights"
            :key="item.id"
            @click="store.activePanel = item.id"
            :class="[
              'group flex items-center transition-all cursor-pointer rounded-lg',
              collapsed ? 'px-3 py-2.5 justify-center' : 'px-3 py-2.5 gap-3',
              store.activePanel === item.id
                ? 'bg-[#ecf3ff] text-[#465FFF]'
                : 'text-gray-700 hover:bg-gray-100'
            ]"
            :title="collapsed ? item.name : ''"
          >
            <span v-html="item.icon" :class="['w-5 h-5 shrink-0', store.activePanel === item.id ? 'text-[#465FFF]' : 'text-gray-500 group-hover:text-gray-700']"></span>
            <span
              class="text-sm font-medium whitespace-nowrap transition-all duration-300 overflow-hidden"
              :class="collapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'"
            >{{ item.name }}</span>
          </div>
        </div>
      </div>

      <!-- 分组: 管理工具 -->
      <div>
        <p
          class="px-5 text-xs font-medium text-gray-400 uppercase tracking-wider whitespace-nowrap transition-all duration-300 overflow-hidden"
          :class="collapsed ? 'h-0 opacity-0 mb-0' : 'h-5 opacity-100 mb-3'"
        >管理工具</p>

        <div class="flex flex-col gap-1 px-3">
          <div
            v-for="item in navGroups.tools"
            :key="item.id"
            @click="store.activePanel = item.id"
            :class="[
              'group flex items-center transition-all cursor-pointer rounded-lg',
              collapsed ? 'px-3 py-2.5 justify-center' : 'px-3 py-2.5 gap-3',
              store.activePanel === item.id
                ? 'bg-[#ecf3ff] text-[#465FFF]'
                : 'text-gray-700 hover:bg-gray-100'
            ]"
            :title="collapsed ? item.name : ''"
          >
            <span v-html="item.icon" :class="['w-5 h-5 shrink-0', store.activePanel === item.id ? 'text-[#465FFF]' : 'text-gray-500 group-hover:text-gray-700']"></span>
            <span
              class="text-sm font-medium whitespace-nowrap transition-all duration-300 overflow-hidden"
              :class="collapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'"
            >{{ item.name }}</span>
          </div>
        </div>
      </div>
    </nav>

    <!-- 底部区域 -->
    <div class="shrink-0 border-t border-gray-200 py-4 px-3 space-y-1">
      
      <!-- 状态指示 -->
      <div 
        class="flex items-center rounded-lg px-3 py-2 transition-all duration-300"
        :class="collapsed ? 'justify-center' : ''"
      >
        <div class="w-1.5 h-1.5 bg-emerald-500 rounded-full shrink-0 relative">
          <div class="absolute inset-0 bg-emerald-400 rounded-full animate-pulse opacity-60"></div>
        </div>
        <span
          class="text-xs font-medium text-gray-500 ml-2.5 whitespace-nowrap transition-all duration-300 overflow-hidden"
          :class="collapsed ? 'w-0 opacity-0 ml-0' : 'w-auto opacity-100'"
        >系统在线</span>
      </div>

      <!-- 折叠按钮 -->
      <button
        @click="toggleCollapse"
        class="w-full flex items-center text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-all cursor-pointer rounded-lg"
        :class="collapsed ? 'px-3 py-2.5 justify-center' : 'px-3 py-2 gap-3'"
        :title="collapsed ? '展开侧边栏' : '收起侧边栏'"
      >
        <svg :class="['w-5 h-5 shrink-0 transition-transform duration-300', collapsed ? 'rotate-180' : '']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"></path>
        </svg>
        <span
          class="text-sm font-medium whitespace-nowrap transition-all duration-300 overflow-hidden"
          :class="collapsed ? 'w-0 opacity-0' : 'w-auto opacity-100'"
        >收起菜单</span>
      </button>

    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue';
import { store } from '../store.js';

const collapsed = computed(() => store.sidebarCollapsed);

const toggleCollapse = () => {
  store.sidebarCollapsed = !store.sidebarCollapsed;
  localStorage.setItem('pdd_sidebar_collapsed', store.sidebarCollapsed);
};

const navGroups = {
  workspace: [
    { id: 'monitor', name: '对话监控', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>' },
    { id: 'interventions', name: '工单处理', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path></svg>' },
    { id: 'pipeline', name: '订单追踪', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>' }
  ],
  insights: [
    { id: 'statistics', name: '数据看板', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"></path></svg>' },
    { id: 'health', name: '系统状态', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>' }
  ],
  tools: [
    { id: 'knowledge', name: '知识库管理', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13c1.168-.776 2.754-1.253 4.5-1.253s3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18s-3.332.477-4.5 1.253"></path></svg>' },
    { id: 'simulator', name: '买家模拟测试', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>' },
    { id: 'settings', name: '偏好设置', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>' }
  ]
};
</script>
