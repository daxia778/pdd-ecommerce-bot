<template>
  <div v-cloak class="w-full h-screen flex flex-col bg-gray-50 text-gray-800 font-sans overflow-hidden">
    <!-- 未登录：显示登录页 -->
    <LoginForm v-if="!store.isLoggedIn" class="flex-1" />

    <!-- 已登录：主界面 (SaaS Dashboard 布局) -->
    <div v-else class="flex-1 flex w-full h-full overflow-hidden">
      <!-- 深色侧边栏 -->
      <Sidebar class="shrink-0 shadow-lg z-20" />
      
      <!-- 右侧主内容区 -->
      <main class="flex-1 flex flex-col min-w-0 h-full overflow-hidden relative">
        <Header class="w-full shrink-0 shadow-sm z-30 relative" />
        
        <!-- 带有灰色底色/波浪背景的工作区，内部页面作为玻璃材质白卡片展示 -->
        <div class="flex-1 w-full p-4 lg:p-6 overflow-hidden bg-background bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(224,46,36,0.1),rgba(255,255,255,0))] dark:bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(224,46,36,0.15),rgba(255,255,255,0))] flex flex-col items-center relative">
           
           <!-- 背景装饰球 -->
           <div class="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/20 rounded-full mix-blend-multiply filter blur-[100px] opacity-50 animate-pulse-slow"></div>
           <div class="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-500/10 rounded-full mix-blend-multiply filter blur-[100px] opacity-50 animate-pulse-slow" style="animation-delay: 1.5s;"></div>

           <div class="w-full h-full max-w-[1600px] flex flex-col overflow-hidden relative z-10 
                       bg-card/60 dark:bg-card/40 backdrop-blur-3xl border border-white/20 dark:border-white/10 rounded-2xl shadow-glass transition-all duration-300">
              <MonitorPanel v-show="store.activePanel === 'monitor'" class="flex-1 w-full min-h-0 animate-fade-in-up" />
              <InterventionsPanel v-show="store.activePanel === 'interventions'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide animate-fade-in-up" />
              <PipelinePanel v-show="store.activePanel === 'pipeline'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide animate-fade-in-up" />
              <KnowledgePanel v-show="store.activePanel === 'knowledge'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide animate-fade-in-up" />
              <StatisticsPanel v-show="store.activePanel === 'statistics'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide animate-fade-in-up" />
              <BuyerSimulator v-show="store.activePanel === 'simulator'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide animate-fade-in-up" />
              <SettingsPanel v-show="store.activePanel === 'settings'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide animate-fade-in-up" />
              <SystemHealthPanel v-show="store.activePanel === 'health'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide animate-fade-in-up" />
           </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, watch } from 'vue';
import { store } from './store.js';
import LoginForm from './components/LoginForm.vue';
import Sidebar from './components/Sidebar.vue';
import Header from './components/Header.vue';
import MonitorPanel from './components/MonitorPanel.vue';
import InterventionsPanel from './components/InterventionsPanel.vue';
import PipelinePanel from './components/PipelinePanel.vue';
import KnowledgePanel from './components/KnowledgePanel.vue';
import StatisticsPanel from './components/StatisticsPanel.vue';
import BuyerSimulator from './components/BuyerSimulator.vue';
import SettingsPanel from './components/SettingsPanel.vue';
import SystemHealthPanel from './components/SystemHealthPanel.vue';

watch(() => store.activePanel, (newVal) => {
  if (newVal === 'knowledge' && store.knowledgeBase.length === 0) {
    store.loadKnowledge();
  }
});

onMounted(() => {
  if (store.isLoggedIn) store.connect();
});

onUnmounted(() => {
  store.disconnect();
});
</script>
