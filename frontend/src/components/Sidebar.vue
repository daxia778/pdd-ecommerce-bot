<template>
  <aside
    :class="[
      'min-h-screen flex flex-col fixed lg:static z-50 bg-white border-r border-gray-100 relative overflow-hidden transition-all duration-300 ease-in-out',
      collapsed ? 'w-[68px]' : 'w-72'
    ]"
    style="box-shadow: 1px 0 20px rgba(0,0,0,0.03)"
  >
    <!-- Background pattern -->
    <div v-if="!collapsed" class="absolute inset-0 w-full h-full pointer-events-none z-0" style="background-image: url('data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'60\' height=\'60\' viewBox=\'0 0 60 60\'%3E%3Cpath d=\'M30 15c-8.284 0-15 6.716-15 15s6.716 15 15 15 15-6.716 15-15-6.716-15-15-15zm0 2c7.18 0 13 5.82 13 13s-5.82 13-13 13-13-5.82-13-13 5.82-13 13-13z\' fill=\'%23E02E24\' fill-opacity=\'0.02\'/%3E%3Ctext x=\'30\' y=\'34\' font-family=\'Arial\' font-weight=\'900\' font-size=\'12\' fill=\'%23E02E24\' fill-opacity=\'0.03\' text-anchor=\'middle\'%3E多%3C/text%3E%3C/svg%3E'); background-repeat: repeat;"></div>

    <!-- Logo区域 -->
    <div :class="['flex items-center gap-3 z-10 relative', collapsed ? 'p-4 justify-center' : 'p-8']">
      <div class="w-10 h-10 bg-gradient-to-br from-[#FF574D] to-[#E02E24] rounded-xl flex items-center justify-center shadow-lg border border-white/20 shrink-0">
        <span class="text-white text-xl font-black drop-shadow-sm">多</span>
      </div>
      <transition name="fade-text">
        <div v-if="!collapsed">
          <h1 class="text-lg font-extrabold text-gray-800 tracking-tight leading-tight">PDD AI</h1>
          <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Center Hub</p>
        </div>
      </transition>
    </div>

    <!-- System Live 指示器 -->
    <div :class="['flex items-center gap-1.5 bg-emerald-50 rounded-full w-fit mb-4', collapsed ? 'px-2 py-1 mx-auto' : 'px-3 py-1 mx-6']">
      <div class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></div>
      <span v-if="!collapsed" class="text-[10px] font-bold text-emerald-700 uppercase tracking-tighter">System Live</span>
    </div>

    <!-- 导航菜单 -->
    <nav class="flex-1 z-10">
      <p v-if="!collapsed" class="px-8 mt-6 mb-2 text-[11px] font-bold text-gray-300 uppercase tracking-wider">General</p>
      <div class="mt-2" v-else></div>

      <div
        v-for="item in navItems"
        :key="item.id"
        @click="store.activePanel = item.id"
        :title="collapsed ? item.name : ''"
        :class="[
          'relative group flex items-center transition-all cursor-pointer border',
          collapsed
            ? 'mx-2 my-1 px-0 py-3 rounded-xl justify-center'
            : 'mx-4 my-1 px-4 py-3 rounded-2xl gap-3',
          store.activePanel === item.id
            ? 'bg-red-50 text-red-600 border-red-100'
            : 'text-gray-500 border-transparent hover:bg-red-50 hover:text-red-600'
        ]"
      >
        <span v-html="item.icon" class="w-5 h-5 shrink-0"></span>
        <span v-if="!collapsed" class="text-sm font-semibold">{{ item.name }}</span>

        <!-- 折叠态 tooltip -->
        <div
          v-if="collapsed"
          class="absolute left-full ml-2 px-2.5 py-1 bg-gray-800 text-white text-xs font-bold rounded-lg whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-200 z-50 shadow-lg"
        >
          {{ item.name }}
          <div class="absolute top-1/2 -left-1 -translate-y-1/2 w-2 h-2 bg-gray-800 rotate-45"></div>
        </div>

        <!-- 待办徽标 -->
        <span
          v-if="item.id === 'interventions' && store.escalations && store.escalations.length > 0 && collapsed"
          class="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-[8px] font-black rounded-full flex items-center justify-center shadow-md"
        >{{ store.escalations.length > 9 ? '9+' : store.escalations.length }}</span>
      </div>

      <div class="h-px bg-gradient-to-r from-transparent via-gray-100 to-transparent my-4 mx-6" v-if="!collapsed"></div>
      <div class="h-px bg-gray-100 my-4 mx-3" v-else></div>
    </nav>

    <!-- 折叠切换按钮 -->
    <div class="z-10 px-2 mb-2">
      <button
        @click="toggleCollapse"
        :class="[
          'w-full flex items-center gap-2 py-2 rounded-xl text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-all cursor-pointer',
          collapsed ? 'justify-center px-0' : 'px-4'
        ]"
        :title="collapsed ? '展开侧边栏' : '收起侧边栏'"
      >
        <svg :class="['w-4 h-4 transition-transform duration-300', collapsed ? '' : 'rotate-180']" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"></path>
        </svg>
        <span v-if="!collapsed" class="text-xs font-semibold">收起菜单</span>
      </button>
    </div>

    <!-- 用户信息 -->
    <div class="z-10" :class="collapsed ? 'px-2 pb-4' : 'px-6 pb-6'">
      <div :class="[
        'bg-gray-50 rounded-2xl border border-gray-100 flex items-center cursor-pointer hover:bg-white hover:shadow-lg hover:border-red-500 transition-all',
        collapsed ? 'p-2 justify-center' : 'p-4 gap-3'
      ]">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF574D] to-[#E02E24] text-white font-black flex items-center justify-center shadow-md shadow-red-100 shrink-0">A</div>
        <div v-if="!collapsed" class="flex-1 min-w-0">
          <p class="text-sm font-extrabold text-gray-800 truncate">Administrator</p>
          <p class="text-[10px] text-gray-400 font-bold uppercase">Root Access</p>
        </div>
      </div>
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

const navItems = [
  { id: 'monitor', name: '监控大屏', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>' },
  { id: 'statistics', name: '数据统计', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"></path></svg>' },
  { id: 'interventions', name: '人工干预池', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>' },
  { id: 'pipeline', name: '生产流水线', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>' },
  { id: 'knowledge', name: '知识库管理', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13c1.168-.776 2.754-1.253 4.5-1.253s3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18s-3.332.477-4.5 1.253"></path></svg>' },
  { id: 'simulator', name: '买家模拟器', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>' },
  { id: 'settings', name: '系统配置', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>' }
];
</script>

<style scoped>
.fade-text-enter-active,
.fade-text-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-text-enter-from,
.fade-text-leave-to {
  opacity: 0;
  transform: translateX(-8px);
}
</style>
