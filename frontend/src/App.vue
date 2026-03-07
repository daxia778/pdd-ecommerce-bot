<template>
  <div v-cloak class="w-full h-full flex flex-col">
    <!-- 未登录：显示登录页 -->
    <LoginForm v-if="!store.isLoggedIn" class="flex-1" />

    <!-- 已登录：主界面 -->
    <div v-else class="flex-1 flex w-full h-full bg-gray-50 text-gray-800 font-sans overflow-hidden">
      <Sidebar class="shrink-0" />
      <main class="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        <Header class="w-full shrink-0" />
        <div class="flex-1 w-full flex flex-col p-6 lg:p-8 overflow-hidden">
          <MonitorPanel v-show="store.activePanel === 'monitor'" class="flex-1 w-full min-h-0" />
          <InterventionsPanel v-show="store.activePanel === 'interventions'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide" />
          <PipelinePanel v-show="store.activePanel === 'pipeline'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide" />
          <KnowledgePanel v-show="store.activePanel === 'knowledge'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide" />
          <StatisticsPanel v-show="store.activePanel === 'statistics'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide" />
          <BuyerSimulator v-show="store.activePanel === 'simulator'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide" />
          <SettingsPanel v-show="store.activePanel === 'settings'" class="flex-1 w-full min-h-0 overflow-y-auto scrollbar-hide" />
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

watch(() => store.activePanel, (newVal) => {
  if (newVal === 'knowledge' && store.knowledgeBase.length === 0) {
    store.loadKnowledge();
  }
});

onMounted(() => {
  // 已有 token 时自动连接
  if (store.isLoggedIn) store.connect();
});

onUnmounted(() => {
  store.disconnect();
});
</script>
