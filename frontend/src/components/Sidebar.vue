<template>
  <aside class="w-72 min-h-screen p-4 flex flex-col fixed lg:static z-50 bg-white shadow-[1px_0_20px_rgba(0,0,0,0.03)] border-r border-gray-100 relative overflow-hidden transition-all duration-400">
    <!-- Background pattern -->
    <div class="absolute inset-0 w-full h-full pointer-events-none z-0" style="background-image: url('data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'60\' height=\'60\' viewBox=\'0 0 60 60\'%3E%3Cpath d=\'M30 15c-8.284 0-15 6.716-15 15s6.716 15 15 15 15-6.716 15-15-6.716-15-15-15zm0 2c7.18 0 13 5.82 13 13s-5.82 13-13 13-13-5.82-13-13 5.82-13 13-13z\' fill=\'%23E02E24\' fill-opacity=\'0.02\'/%3E%3Ctext x=\'30\' y=\'34\' font-family=\'Arial\' font-weight=\'900\' font-size=\'12\' fill=\'%23E02E24\' fill-opacity=\'0.03\' text-anchor=\'middle\'%3E多%3C/text%3E%3C/svg%3E'); background-repeat: repeat;"></div>

    <div class="p-8 flex items-center gap-3 z-10 relative">
      <div class="w-10 h-10 bg-gradient-to-br from-[#FF574D] to-[#E02E24] rounded-xl flex items-center justify-center shadow-lg border border-white/20">
        <span class="text-white text-xl font-black drop-shadow-sm">多</span>
      </div>
      <div>
        <h1 class="text-lg font-extrabold text-gray-800 tracking-tight leading-tight">PDD AI</h1>
        <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Center Hub</p>
      </div>
    </div>

    <div class="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 rounded-full mx-6 mb-4 w-fit">
      <div class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></div>
      <span class="text-[10px] font-bold text-emerald-700 uppercase tracking-tighter">System Live</span>
    </div>

    <nav class="flex-1 z-10">
      <p class="px-8 mt-6 mb-2 text-[11px] font-bold text-gray-300 uppercase tracking-wider">General</p>
      <div v-for="item in navItems" :key="item.id" @click="store.activePanel = item.id"
          :class="['mx-4 my-1 px-4 py-3 rounded-2xl text-sm font-semibold flex items-center gap-3 transition-all cursor-pointer border', store.activePanel === item.id ? 'bg-red-50 text-red-600 border-red-100' : 'text-gray-500 border-transparent hover:bg-red-50 hover:text-red-600']">
          <span v-html="item.icon" class="w-5 h-5"></span>
          <span>{{ item.name }}</span>
      </div>
      <div class="h-px bg-gradient-to-r from-transparent via-gray-100 to-transparent my-4 mx-6"></div>
    </nav>

    <div class="mt-auto z-10">
      <div class="m-6 p-4 bg-gray-50 rounded-2xl border border-gray-100 flex items-center gap-3 cursor-pointer hover:bg-white hover:shadow-lg hover:border-red-500 transition-all">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-[#FF574D] to-[#E02E24] text-white font-black flex items-center justify-center shadow-md shadow-red-100">A</div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-extrabold text-gray-800 truncate">Administrator</p>
          <p class="text-[10px] text-gray-400 font-bold uppercase">Root Access</p>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { store } from '../store.js';

const navItems = [
  { id: 'monitor', name: '监控大屏', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>' },
  { id: 'statistics', name: '数据统计', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z"></path></svg>' },
  { id: 'interventions', name: '人工干预池', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>' },
  { id: 'pipeline', name: '生产流水线', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>' },
  { id: 'knowledge', name: '知识库管理', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5.1.253v13m0-13c1.168-0.776 2.754-1.253 4.5-1.253s3.332 0.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332 0.477-4.5 1.253"></path></svg>' },
  { id: 'settings', name: '系统配置', icon: '<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>' }
];
</script>
