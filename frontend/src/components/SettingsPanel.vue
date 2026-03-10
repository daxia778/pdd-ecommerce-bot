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

              <hr class="border-gray-100" />

              <!-- 模型 API 接入测试 -->
              <div>
                  <div class="flex items-center justify-between mb-4">
                    <h3 class="text-sm font-bold text-gray-700 border-l-4 border-red-500 pl-3">🔌 模型 API 接入测试 (LLM Connection Test)</h3>
                    <span v-if="llmConfigured" class="flex items-center gap-1.5 px-3 py-1 bg-green-50 border border-green-200 rounded-full text-xs font-bold text-green-600">
                      <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                      API 已配置 · {{ testModel }}
                    </span>
                    <span v-else class="flex items-center gap-1.5 px-3 py-1 bg-amber-50 border border-amber-200 rounded-full text-xs font-bold text-amber-600">
                      <span class="w-2 h-2 rounded-full bg-amber-400"></span>
                      未配置
                    </span>
                  </div>
                  <p class="text-xs text-gray-400 mb-4 pl-4">当前正在使用的 API Key 已自动加载。您可以修改后点击测试按钮验证，确认无误后保存到 .env 文件。</p>
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                     <div class="md:col-span-2">
                        <label class="block text-[11px] font-bold text-gray-500 uppercase mb-1">API Key</label>
                        <input type="text" v-model="testApiKey" placeholder="输入完整的 API Key（如 83af...agSf）"
                          class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-red-500 outline-none" />
                     </div>
                     <div>
                        <label class="block text-[11px] font-bold text-gray-500 uppercase mb-1">模型</label>
                        <select v-model="testModel" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none bg-white">
                           <option value="glm-4-flash">GLM-4 Flash (快速)</option>
                           <option value="glm-4-air">GLM-4 Air (均衡)</option>
                           <option value="glm-4-plus">GLM-4 Plus (高级)</option>
                           <option value="glm-4.7">GLM-4.7 (最新旗舰)</option>
                        </select>
                     </div>
                  </div>
                  <div class="flex items-center gap-3 mb-4">
                     <button @click="runLLMTest" :disabled="testLoading || !testApiKey.trim()"
                       class="px-5 py-2 bg-gradient-to-r from-red-500 to-orange-500 text-white rounded-xl text-sm font-bold hover:from-red-600 hover:to-orange-600 transition-all shadow-sm shadow-red-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
                       <span v-if="testLoading" class="animate-spin">↻</span>
                       <span v-else>⚡</span>
                       {{ testLoading ? '测试中...' : '发起连通测试' }}
                     </button>
                     <button v-if="testResult && testResult.success" @click="saveLLMConfig" :disabled="saveLoading"
                       class="px-5 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl text-sm font-bold hover:from-green-600 hover:to-emerald-700 transition-all shadow-sm shadow-green-200 disabled:opacity-50 flex items-center gap-2">
                       <span v-if="saveLoading" class="animate-spin">↻</span>
                       <span v-else>💾</span>
                       {{ saveLoading ? '保存中...' : '保存到 .env' }}
                     </button>
                     <span v-if="testResult" class="text-xs font-bold" :class="testResult.success ? 'text-green-600' : 'text-red-600'">
                        {{ testResult.success ? '✅ 连通成功' : '❌ 连接失败' }}
                     </span>
                     <span v-if="saveMsg" class="text-xs font-bold text-blue-600">{{ saveMsg }}</span>
                  </div>
                  <!-- 测试结果 -->
                  <div v-if="testResult" class="rounded-xl border p-4 transition-all" :class="testResult.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'">
                     <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
                        <div>
                          <div class="text-[10px] text-gray-500 font-bold uppercase">延迟</div>
                          <div class="text-lg font-black" :class="testResult.latency_ms <= 3000 ? 'text-green-600' : testResult.latency_ms <= 8000 ? 'text-amber-600' : 'text-red-600'">
                            {{ testResult.latency_ms }}ms
                          </div>
                        </div>
                        <div>
                          <div class="text-[10px] text-gray-500 font-bold uppercase">模型</div>
                          <div class="text-sm font-bold text-gray-800">{{ testResult.model }}</div>
                        </div>
                        <div>
                          <div class="text-[10px] text-gray-500 font-bold uppercase">Key</div>
                          <div class="text-sm font-mono font-bold text-gray-600">{{ testResult.key_suffix }}</div>
                        </div>
                        <div>
                          <div class="text-[10px] text-gray-500 font-bold uppercase">Tokens</div>
                          <div class="text-sm font-bold text-gray-800">{{ testResult.tokens_used || '-' }}</div>
                        </div>
                     </div>
                     <div v-if="testResult.reply" class="mt-3 pt-3 border-t border-green-200">
                        <div class="text-[10px] text-gray-500 font-bold uppercase mb-1">AI 回复</div>
                        <div class="text-xs text-gray-700 bg-white/60 rounded-lg p-2 font-mono">{{ testResult.reply }}</div>
                     </div>
                     <div v-if="testResult.error" class="mt-3 pt-3 border-t border-red-200">
                        <div class="text-[10px] text-red-600 font-bold uppercase mb-1">错误详情</div>
                        <div class="text-xs text-red-700 bg-white/60 rounded-lg p-2 font-mono break-all">{{ testResult.error }}</div>
                     </div>
                  </div>
              </div>

              <hr class="border-gray-100" />

              <!-- L2 Prompt 动态外挂配置 (全屏宽) -->
              <div>
                  <div class="flex justify-between items-end mb-4">
                      <div>
                          <h3 class="text-sm font-bold text-gray-700 border-l-4 border-green-500 pl-3">AI 话术规则配置 (Prompt YAML)</h3>
                          <p class="text-xs text-gray-400 mt-1 mb-0 pl-4">在线编辑 YAML 格式的 Prompt 提示词外挂，保存后立即热重载生效。</p>
                      </div>
                      <div class="flex items-center gap-2">
                        <button @click="store.loadPrompt('ppt_consultant')" :disabled="store.promptLoading"
                          class="px-3 py-1.5 bg-gray-50 border border-gray-200 text-gray-600 rounded-lg text-xs font-bold hover:bg-gray-100 transition-all flex items-center gap-1">
                          <span v-if="store.promptLoading" class="animate-spin text-[10px]">↻</span>
                          <span v-else class="text-[10px]">↻</span>
                          刷新远程
                        </button>
                        <button @click="store.savePrompt('ppt_consultant')" :disabled="store.promptSaving"
                          class="px-4 py-1.5 bg-green-600 text-white rounded-lg text-xs font-bold hover:bg-green-700 transition-all flex items-center gap-1.5 shadow-sm shadow-green-100">
                          <span v-if="store.promptSaving" class="animate-spin text-[10px]">↻</span>
                          <span v-else>💾</span>
                          保存热更新
                        </button>
                      </div>
                  </div>
                  <div class="relative bg-[#1e1e1e] rounded-xl overflow-hidden shadow-inner border border-gray-800">
                      <div class="flex items-center justify-between px-4 py-2 bg-[#2d2d2d] border-b border-black/50">
                           <span class="text-[10px] font-mono font-bold text-gray-300 flex items-center gap-1.5"><svg class="w-3 h-3 text-yellow-500" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"></path></svg> data/prompts/ppt_consultant.yaml</span>
                           <span class="text-[9px] font-bold text-green-400 uppercase tracking-widest px-2 py-0.5 bg-green-900/30 rounded ring-1 ring-green-500/30">L2 热重载生效中</span>
                      </div>
                      <textarea
                          v-model="store.promptContent"
                          spellcheck="false"
                          placeholder="Loading prompt YAML..."
                          class="w-full h-[400px] bg-transparent text-gray-300 font-mono text-xs px-5 py-4 focus:outline-none resize-y leading-loose border-none focus:ring-0 custom-scrollbar"
                      ></textarea>
                  </div>
              </div>

              <div class="pt-8 border-t border-gray-100 flex justify-end gap-3 mt-4">
                  <button @click="requestNotification" class="px-6 py-2 bg-white border border-gray-200 text-gray-700 rounded-xl text-sm font-bold hover:bg-gray-50 transition-all shadow-sm">
                      🔔 开启桌面通知
                  </button>
              </div>
          </div>
      </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { store } from '../store.js';

const ragThreshold = ref(0.7);

// LLM API 测试相关
const testApiKey = ref('');
const testModel = ref('glm-4-flash');
const testLoading = ref(false);
const testResult = ref(null);
const saveLoading = ref(false);
const saveMsg = ref('');
const llmConfigured = ref(false);

const loadCurrentLLMConfig = async () => {
  try {
    const token = localStorage.getItem('pdd_admin_token');
    const res = await fetch('/api/dashboard/llm-config', {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
    });
    if (!res.ok) return;
    const data = await res.json();
    if (data.configured && data.api_key_full) {
      testApiKey.value = data.api_key_full;
      testModel.value = data.model || 'glm-4-flash';
      llmConfigured.value = true;
    }
  } catch (e) {
    console.warn('加载 LLM 配置失败:', e);
  }
};

onMounted(() => {
  store.loadPrompt('ppt_consultant');
  loadCurrentLLMConfig();
});

const runLLMTest = async () => {
  testLoading.value = true;
  testResult.value = null;
  try {
    const token = localStorage.getItem('pdd_admin_token');
    const res = await fetch('/api/dashboard/llm-test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        api_key: testApiKey.value.trim(),
        model: testModel.value,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    testResult.value = await res.json();
  } catch (e) {
    testResult.value = {
      success: false,
      latency_ms: 0,
      model: testModel.value,
      reply: null,
      tokens_used: null,
      key_suffix: `***${testApiKey.value.slice(-4)}`,
      error: `请求异常: ${e.message}`,
    };
  } finally {
    testLoading.value = false;
  }
};

const saveLLMConfig = async () => {
  saveLoading.value = true;
  saveMsg.value = '';
  try {
    const token = localStorage.getItem('pdd_admin_token');
    const res = await fetch('/api/dashboard/llm-config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        api_key: testApiKey.value.trim(),
        model: testModel.value,
      }),
    });
    const data = await res.json();
    saveMsg.value = data.success ? `✅ ${data.msg}` : `❌ ${data.error}`;
  } catch (e) {
    saveMsg.value = `❌ 保存失败: ${e.message}`;
  } finally {
    saveLoading.value = false;
    setTimeout(() => { saveMsg.value = ''; }, 5000);
  }
};

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

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 10px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #1e1e1e;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 5px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #555;
}
</style>
