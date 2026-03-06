<template>
  <div class="max-w-4xl mx-auto py-10">
      <div class="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
          <div class="p-10">
              <h2 class="text-2xl font-black text-gray-800 mb-8">系统控制中心</h2>
              <div class="space-y-8">
                  <div class="flex items-center justify-between p-6 bg-gray-50 rounded-2xl">
                      <div>
                          <p class="font-bold text-gray-800">服务状态</p>
                          <p class="text-sm text-gray-500 font-medium">当前 Uvicorn 节点运行正常</p>
                      </div>
                      <div class="px-4 py-2 bg-green-100 text-green-700 rounded-xl font-bold text-sm">ONLINE</div>
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                      <div class="p-6 border border-gray-100 rounded-2xl">
                          <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">LLM Engine</p>
                          <p class="font-bold text-gray-800">GLM-4 Flash</p>
                      </div>
                      <div class="p-6 border border-gray-100 rounded-2xl">
                          <p class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">RAG Threshold</p>
                          <p class="font-bold text-gray-800">0.3 Relevance</p>
                      </div>
                  </div>
                  <div class="pt-6 border-t border-gray-100 flex gap-4">
                      <button @click="requestNotification" class="w-1/2 py-4 bg-blue-50 text-blue-600 rounded-2xl font-bold hover:bg-blue-100 transition-all shadow-sm">
                          🔔 开启桌面通知
                      </button>
                      <button class="w-1/2 py-4 bg-gray-800 text-white rounded-2xl font-bold hover:bg-black transition-all shadow-lg">
                          导出系统运行日志 (Full JSON)
                      </button>
                  </div>
              </div>
          </div>
      </div>
  </div>
</template>

<script setup>
const requestNotification = () => {
  if ('Notification' in window) {
    Notification.requestPermission().then(perm => {
      if (perm === 'granted') {
        new Notification('✅ 通知已开启', { body: '您将收到转人工等重要提醒' });
      } else {
        alert('通知权限已被拒绝，请在浏览器设置中开启。');
      }
    });
  } else {
    alert('您的浏览器不支持桌面通知。');
  }
};
</script>
