<template>
  <header class="sticky top-0 h-16 border-b border-gray-200 bg-white flex items-center justify-between px-6 shrink-0 w-full z-30">
      <!-- 左侧：面包屑导航 / 页面标题 -->
      <div class="flex items-center gap-2">
          <span class="text-sm font-semibold text-gray-500 cursor-pointer hover:text-gray-900 transition-colors" @click="store.activePanel = 'monitor'">控制台</span>
          <svg class="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
          </svg>
          <span class="font-bold text-gray-900 text-sm">{{ panelName }}</span>
      </div>

      <!-- 右侧：全局搜索栏 (如果是监控页面不需要这里搜，或者保留占位) + 用户区 -->
      <div class="flex items-center gap-5">
          
          <!-- 通知铃铛 (轻量化) -->
          <button
            @click="store.activePanel = 'interventions'"
            class="relative p-1.5 rounded-md hover:bg-gray-100 transition-colors text-gray-500 focus:outline-none"
            title="查看待处理工单"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
            </svg>
            <!-- 静态小红点，不使用过度弹跳动画 -->
            <span
              v-if="pendingCount > 0"
              class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full border-2 border-white"
            ></span>
          </button>

          <!-- 分割线 -->
          <div class="w-px h-5 bg-gray-200 hidden sm:block"></div>

          <!-- 用户头像 + 下拉菜单 -->
          <div class="relative" ref="userMenuRef">
            <button
              @click="showUserMenu = !showUserMenu"
              class="flex items-center gap-2 p-1 rounded-md hover:bg-gray-50 transition-colors focus:outline-none"
            >
              <div class="w-7 h-7 rounded-full bg-slate-800 text-white font-medium flex items-center justify-center text-xs">AD</div>
              <span class="text-sm font-medium text-gray-700 hidden sm:block">Admin</span>
              <svg class="w-4 h-4 text-gray-400 transition-transform" :class="showUserMenu ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>

            <!-- 下拉菜单 -->
            <transition name="dropdown">
              <div
                v-if="showUserMenu"
                class="absolute right-0 top-full mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50 overflow-hidden"
              >
                <div class="px-4 py-3 border-b border-gray-100">
                  <p class="text-sm font-medium text-gray-900">Administrator</p>
                  <p class="text-xs text-gray-500">Super Admin</p>
                </div>
                <button
                  @click="store.activePanel = 'settings'; showUserMenu = false"
                  class="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2 transition-colors"
                >
                  <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                  系统偏好
                </button>
                <div class="h-px bg-gray-100 my-1"></div>
                <button
                  @click="handleLogout"
                  class="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 transition-colors"
                >
                  <svg class="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H8a3 3 0 01-3-3V7a3 3 0 013-3h2a3 3 0 013 3v1"></path></svg>
                  退出系统
                </button>
              </div>
            </transition>
          </div>
      </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { store } from '../store.js';

const showUserMenu = ref(false);
const userMenuRef = ref(null);

const names = {
  'monitor': '对话监控',
  'statistics': '数据看板',
  'interventions': '工单处理',
  'pipeline': '订单追踪',
  'health': '系统状态',
  'knowledge': '知识库管理',
  'simulator': '买家模拟测试',
  'settings': '偏好设置'
};

const panelName = computed(() => names[store.activePanel] || '工作台');
const pendingCount = computed(() => store.escalations ? store.escalations.length : 0);

const handleLogout = () => {
  showUserMenu.value = false;
  store.logout();
};

const handleClickOutside = (e) => {
  if (userMenuRef.value && !userMenuRef.value.contains(e.target)) {
    showUserMenu.value = false;
  }
};

onMounted(() => document.addEventListener('click', handleClickOutside));
onUnmounted(() => document.removeEventListener('click', handleClickOutside));
</script>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease-out;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}
</style>
