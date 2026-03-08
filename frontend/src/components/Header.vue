<template>
  <header class="h-16 border-b border-gray-200/80 bg-white/80 backdrop-blur-md flex items-center justify-between px-6 lg:px-8 shrink-0 w-full">
      <!-- 左侧：面包屑导航 -->
      <div class="flex items-center gap-2">
          <button
            @click="store.activePanel = 'monitor'"
            class="text-gray-400 text-sm font-medium hover:text-red-500 transition-colors cursor-pointer"
          >首页</button>
          <svg class="w-3.5 h-3.5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
          </svg>
          <span class="font-bold text-gray-800">{{ panelName }}</span>
      </div>

      <!-- 右侧：状态指标 + 通知 + 用户 -->
      <div class="flex items-center gap-4">
          <!-- 实时指标 -->
          <div class="hidden md:flex items-center gap-4 text-sm mr-2">
              <div class="flex items-center gap-1.5 bg-blue-50 px-2.5 py-1 rounded-lg">
                  <span class="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                  <span class="text-gray-500 font-medium text-xs">会话</span>
                  <span class="font-bold text-blue-700 text-xs">{{ store.sessions ? store.sessions.length : 0 }}</span>
              </div>
              <div class="flex items-center gap-1.5 bg-red-50 px-2.5 py-1 rounded-lg">
                  <span class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
                  <span class="text-gray-500 font-medium text-xs">待办</span>
                  <span class="font-bold text-red-600 text-xs">{{ store.escalations ? store.escalations.length : 0 }}</span>
              </div>
              <div class="flex items-center gap-1.5 bg-emerald-50 px-2.5 py-1 rounded-lg">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  <span class="text-gray-500 font-medium text-xs">生产</span>
                  <span class="font-bold text-emerald-700 text-xs">{{ store.orders ? store.orders.length : 0 }}</span>
              </div>
          </div>

          <!-- 分割线 -->
          <div class="hidden md:block w-px h-6 bg-gray-200"></div>

          <!-- 通知铃铛 -->
          <button
            @click="store.activePanel = 'interventions'"
            class="relative p-2 rounded-xl hover:bg-gray-100 transition-colors group"
            title="查看待处理干预"
          >
            <svg class="w-5 h-5 text-gray-400 group-hover:text-gray-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>
            </svg>
            <!-- 红点徽标 -->
            <span
              v-if="pendingCount > 0"
              class="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] bg-red-500 text-white text-[10px] font-black rounded-full flex items-center justify-center px-1 shadow-md shadow-red-200 animate-bounce-subtle"
            >{{ pendingCount > 99 ? '99+' : pendingCount }}</span>
          </button>

          <!-- 用户头像 + 下拉菜单 -->
          <div class="relative" ref="userMenuRef">
            <button
              @click="showUserMenu = !showUserMenu"
              class="flex items-center gap-2 p-1.5 rounded-xl hover:bg-gray-100 transition-colors"
            >
              <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-[#FF574D] to-[#E02E24] text-white font-black flex items-center justify-center text-sm shadow-md">A</div>
              <svg class="w-3.5 h-3.5 text-gray-400 transition-transform" :class="showUserMenu ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>

            <!-- 下拉菜单 -->
            <transition name="dropdown">
              <div
                v-if="showUserMenu"
                class="absolute right-0 top-full mt-2 w-52 bg-white rounded-xl shadow-xl border border-gray-100 py-2 z-50 overflow-hidden"
              >
                <div class="px-4 py-3 border-b border-gray-100">
                  <p class="text-sm font-bold text-gray-800">Administrator</p>
                  <p class="text-[11px] text-gray-400 font-medium">Root Access · v0.2.0</p>
                </div>
                <button
                  @click="store.activePanel = 'settings'; showUserMenu = false"
                  class="w-full px-4 py-2.5 text-left text-sm text-gray-600 hover:bg-gray-50 flex items-center gap-2.5 transition-colors"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                  系统配置
                </button>
                <div class="h-px bg-gray-100 mx-3"></div>
                <button
                  @click="handleLogout"
                  class="w-full px-4 py-2.5 text-left text-sm text-red-500 hover:bg-red-50 flex items-center gap-2.5 transition-colors font-medium"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H8a3 3 0 01-3-3V7a3 3 0 013-3h2a3 3 0 013 3v1"></path></svg>
                  退出登录
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
  'monitor': '监控大屏',
  'statistics': '数据统计',
  'interventions': '人工干预池',
  'pipeline': '生产流水线',
  'knowledge': '知识库管理',
  'simulator': '买家模拟器',
  'settings': '系统配置'
};

const panelName = computed(() => names[store.activePanel] || 'Dashboard');
const pendingCount = computed(() => store.escalations ? store.escalations.length : 0);

const handleLogout = () => {
  showUserMenu.value = false;
  store.logout();
};

// 点击外部关闭下拉菜单
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
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.95);
}

@keyframes bounce-subtle {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}
.animate-bounce-subtle {
  animation: bounce-subtle 2s ease-in-out infinite;
}
</style>
