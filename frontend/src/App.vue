<template>
  <div v-cloak class="w-full h-screen flex flex-col bg-gray-50 text-gray-800 font-sans overflow-hidden">
    <!-- 未登录：显示登录页 -->
    <LoginForm v-if="!store.isLoggedIn" class="flex-1" />

    <!-- 已登录：主界面 (SaaS Dashboard 布局) -->
    <div v-else class="flex-1 flex w-full h-full overflow-hidden">
      <!-- 侧边栏 (TailAdmin Style: 白底 + 右侧细灰线) -->
      <Sidebar class="shrink-0 z-20" />
      
      <!-- 右侧主内容区 -->
      <main class="flex-1 flex flex-col min-w-0 h-full overflow-hidden relative">
        <Header class="w-full shrink-0 z-30" />
        
        <!-- 工作区 (TailAdmin Style: bg-gray-50 + padding) -->
        <div class="flex-1 w-full overflow-hidden bg-gray-50 flex flex-col">
           <div class="w-full h-full flex flex-col overflow-hidden">
              <MonitorPanel v-show="store.activePanel === 'monitor'" class="flex-1 w-full min-h-0" />
              <InterventionsPanel v-show="store.activePanel === 'interventions'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide" />
              <PipelinePanel v-show="store.activePanel === 'pipeline'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide" />
              <KnowledgePanel v-show="store.activePanel === 'knowledge'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide" />
              <StatisticsPanel v-show="store.activePanel === 'statistics'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide" />
              <BuyerSimulator v-show="store.activePanel === 'simulator'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide" />
              <SettingsPanel v-show="store.activePanel === 'settings'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide" />
              <SystemHealthPanel v-show="store.activePanel === 'health'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide" />
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
