<template>
  <div class="max-w-5xl mx-auto py-8">
      <div class="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
          <div class="p-8 border-b border-gray-50 flex justify-between items-center bg-gray-50/50">
              <div>
                 <h2 class="text-xl font-black text-gray-800">系统配置中心 (System Settings)</h2>
                 <p class="text-xs text-gray-500 mt-1">维护基础参数、模型参数与自动回复边界</p>
              </div>
              <div class="px-3 py-1.5 bg-green-100 text-green-700 rounded-lg font-bold text-xs flex items-center">
                 <span class="w-2 h-2 rounded-full bg-green-500 mr-2 animate-pulse"></span> 服务运行中
              </div>
          </div>

          <div class="p-8 space-y-8">
              <!-- 基础参数 & 回调配置 -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                 <div>
                    <h3 class="text-sm font-bold text-gray-700 border-l-4 border-blue-500 pl-3 mb-4">基础参数 (Basic Config)</h3>
                    <div class="space-y-4">
                       <div>
                          <label class="block text-[11px] font-bold text-gray-500 uppercase mb-1">店铺名称 / Shop Name</label>
                          <input type="text" value="智小设PPT定制" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
                       </div>
                       <div>
                          <label class="block text-[11px] font-bold text-gray-500 uppercase mb-1">系统工作时间</label>
                          <div class="flex items-center gap-2">
                             <input type="time" value="00:00" class="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm" />
                             <span class="text-gray-400">-</span>
                             <input type="time" value="23:59" class="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm" />
                          </div>
                       </div>
                    </div>
                 </div>

                 <div>
                    <h3 class="text-sm font-bold text-gray-700 border-l-4 border-purple-500 pl-3 mb-4">平台回调配置 (Callback Config)</h3>
                    <div class="space-y-4">
                       <div>
                          <label class="block text-[11px] font-bold text-gray-500 uppercase mb-1">拼多多开放平台 App Key</label>
                          <input type="password" value="pdd_xxxxxxxxxxxxx" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-500 outline-none bg-gray-50" readonly />
                       </div>
                       <div>
                          <label class="block text-[11px] font-bold text-gray-500 uppercase mb-1">消息回调 URL (Webhook)</label>
                          <input type="text" value="https://api.zhixiaoshe.com/webhook/pdd" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-purple-500 outline-none" />
                       </div>
                    </div>
                 </div>
              </div>

              <hr class="border-gray-100" />

              <!-- 模型参数 & 接管阈值 -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                 <div>
                    <h3 class="text-sm font-bold text-gray-700 border-l-4 border-indigo-500 pl-3 mb-4">大模型参数 (Model Params)</h3>
                    <div class="space-y-4">
                       <div>
                          <label class="block text-[11px] font-bold text-gray-500 uppercase mb-1">主对话模型 (Main LLM)</label>
                          <select class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none bg-white">
                             <option>GLM-4 Flash (当前默认)</option>
                             <option>GPT-4o-mini</option>
                             <option>Claude-3.5-Haiku</option>
                          </select>
                       </div>
                       <div>
                          <label class="block text-[11px] font-bold text-gray-500 uppercase mb-2 flex justify-between">
                             <span>知识库检索阈值 (RAG Threshold)</span>
                             <span class="text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded">{{ ragThreshold }}</span>
                          </label>
                          <input type="range" v-model="ragThreshold" min="0" max="1" step="0.1" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600 shadow-inner" />
                       </div>
                       <div class="flex items-center justify-between bg-gradient-to-r from-indigo-50 to-white border border-indigo-50 p-4 rounded-xl shadow-[0_2px_10px_rgba(79,70,229,0.05)]">
                          <div>
                             <span class="text-sm font-bold text-indigo-900 block mb-0.5">实验性图像/内容生成</span>
                             <span class="text-[10px] text-gray-500 font-medium">允许 AI 自动绘制关联设计草图</span>
                          </div>
                          <!-- Modern Toggle Switch -->
                          <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" checked class="sr-only peer">
                            <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600 shadow-inner border border-gray-200 peer-checked:border-indigo-600"></div>
                          </label>
                       </div>
                    </div>
                 </div>

                 <div>
                    <h3 class="text-sm font-bold text-gray-700 border-l-4 border-orange-500 pl-3 mb-4">自动回复边界 & 接管 (Takeover Rules)</h3>
                    <div class="space-y-4">
                       <div>
                          <label class="block text-[11px] font-bold text-gray-500 uppercase mb-1">意图识别不确定性转人工阈值</label>
                          <select class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none bg-white">
                             <option>置信度低于 60% 时转人工</option>
                             <option>置信度低于 70% 时转人工</option>
                             <option>置信度低于 80% 时转人工</option>
                          </select>
                       </div>
                       <div>
                          <label class="block text-[11px] font-bold text-gray-500 uppercase mb-1">敏感词/风控策略 (Sensitive Policy)</label>
                          <textarea rows="3" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none resize-none leading-relaxed" placeholder="输入需立即转人工的关键词，用逗号分隔">投诉, 退款, 垃圾, 骗子, 差评, 人工, 怎么还没好</textarea>
                       </div>
                    </div>
                 </div>
              </div>

              <div class="pt-8 border-t border-gray-100 flex justify-end gap-4 mt-4">
                  <button @click="requestNotification" class="px-6 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-xl text-sm font-bold hover:bg-gray-50 transition-all shadow-sm hover:shadow active:scale-95">
                      🔔 开启桌面通知
                  </button>
                  <button class="px-8 py-2.5 bg-gray-900 text-white rounded-xl text-sm font-bold hover:bg-black transition-all shadow-md hover:shadow-lg active:scale-95 border border-gray-800">
                      保存系统配置
                  </button>
              </div>
          </div>
      </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const ragThreshold = ref(0.7);

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
