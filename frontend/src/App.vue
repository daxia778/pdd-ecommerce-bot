<template>
  <div v-cloak>
    <!-- 未登录：显示登录页 -->
    <LoginForm v-if="!store.isLoggedIn" />

    <!-- 已登录：主界面 -->
    <div v-else class="flex w-full min-h-screen bg-gray-50 text-gray-800 font-sans">
      <Sidebar />
      <main class="flex-1 flex flex-col min-w-0 overflow-hidden h-screen">
        <Header />
        <div class="flex-1 overflow-y-auto p-8 scrollbar-hide">
          <MonitorPanel v-show="store.activePanel === 'monitor'" />
          <InterventionsPanel v-show="store.activePanel === 'interventions'" />
          <PipelinePanel v-show="store.activePanel === 'pipeline'" />
          <KnowledgePanel v-show="store.activePanel === 'knowledge'" />
          <StatisticsPanel v-show="store.activePanel === 'statistics'" />
          <SettingsPanel v-show="store.activePanel === 'settings'" />
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
