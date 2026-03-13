<template>
  <div class="max-w-5xl mx-auto py-8 px-6">
      <div class="bg-white rounded-2xl border border-gray-200 overflow-hidden">
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
                     <h3 class="text-sm font-bold text-gray-700 border-l-2 border-[#465FFF] pl-3 mb-4">基础参数 (Basic Config)</h3>
                    <div class="space-y-4">
                       <div>
                          <label class="block text-[11px] font-bold text-gray-500 uppercase mb-1">店铺名称 / Shop Name</label>
                          <input type="text" value="智小设PPT定制" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#465FFF]/30 focus:border-[#465FFF] outline-none" />
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
                     <h3 class="text-sm font-bold text-gray-700 border-l-2 border-[#465FFF] pl-3 mb-4">平台回调配置 (Callback Config)</h3>
                    <div class="space-y-4">
                       <div>
                          <label class="block text-[11px] font-bold text-gray-500 uppercase mb-1">拼多多开放平台 App Key</label>
                          <input type="password" value="pdd_xxxxxxxxxxxxx" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#465FFF]/30 focus:border-[#465FFF] outline-none bg-gray-50" readonly />
                       </div>
                       <div>
                          <label class="block text-[11px] font-bold text-gray-500 uppercase mb-1">消息回调 URL (Webhook)</label>
                          <input type="text" value="https://api.zhixiaoshe.com/webhook/pdd" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#465FFF]/30 focus:border-[#465FFF] outline-none" />
                       </div>
                    </div>
                 </div>
              </div>

              <hr class="border-gray-100" />

              <!-- 模型参数 & 接管阈值 -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                 <div>
                     <h3 class="text-sm font-bold text-gray-700 border-l-2 border-[#465FFF] pl-3 mb-4">大模型参数 (Model Params)</h3>
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
                             <span class="text-[#465FFF] bg-[#ecf3ff] px-2 py-0.5 rounded">{{ ragThreshold }}</span>
                          </label>
                          <input type="range" v-model="ragThreshold" min="0" max="1" step="0.1" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#465FFF] shadow-inner" />
                       </div>
                       <div class="flex items-center justify-between bg-gradient-to-r from-[#ecf3ff] to-white border border-[#dde9ff] p-4 rounded-2xl shadow-[0_2px_10px_rgba(79,70,229,0.05)]">
                          <div>
                             <span class="text-sm font-bold text-gray-800 block mb-0.5">实验性图像/内容生成</span>
                             <span class="text-[10px] text-gray-500 font-medium">允许 AI 自动绘制关联设计草图</span>
                          </div>
                          <!-- Modern Toggle Switch -->
                          <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" checked class="sr-only peer">
                            <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#465FFF] shadow-inner border border-gray-200 peer-checked:border-[#465FFF]"></div>
                          </label>
                       </div>
                    </div>
                 </div>

                 <div>
                     <h3 class="text-sm font-bold text-gray-700 border-l-2 border-[#465FFF] pl-3 mb-4">自动回复边界 & 接管 (Takeover Rules)</h3>
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
                <!-- Model API Keys (TailAdmin Style) -->
              <div>
                <div class="flex flex-col justify-between gap-5 border-b border-gray-100 pb-4 sm:flex-row sm:items-center">
                  <div>
                    <h3 class="text-sm font-bold text-gray-700 border-l-2 border-[#465FFF] pl-3">API Keys</h3>
                    <p class="text-xs text-gray-500 mt-1 pl-4">API keys are used to authentication requests to the LLM API.</p>
                  </div>
                  <div>
                    <button @click="isModalOpen = true" class="bg-[#465FFF] hover:bg-[#3B50E0] inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-xs font-bold text-white transition shadow-sm">
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 20 20" fill="none">
                        <path d="M5 10.0002H15.0006M10.0002 5V15.0006" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      Add API Key
                    </button>

                    <!-- Add API Key Modal -->
                    <div v-show="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto p-5">
                      <div class="fixed inset-0 h-full w-full bg-gray-900/50 backdrop-blur-sm" @click="isModalOpen = false"></div>
                      <div class="relative w-full max-w-[500px] rounded-2xl bg-white p-6 lg:p-8 shadow-xl">
                        <button @click="isModalOpen = false" class="absolute top-4 right-4 z-50 flex h-8 w-8 items-center justify-center rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-800 transition">
                          <svg class="fill-current" width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path fill-rule="evenodd" clip-rule="evenodd" d="M6.04289 16.5413C5.65237 16.9318 5.65237 17.565 6.04289 17.9555C6.43342 18.346 7.06658 18.346 7.45711 17.9555L11.9987 13.4139L16.5408 17.956C16.9313 18.3466 17.5645 18.3466 17.955 17.956C18.3455 17.5655 18.3455 16.9323 17.955 16.5418L13.4129 11.9997L17.955 7.4576C18.3455 7.06707 18.3455 6.43391 17.955 6.04338C17.5645 5.65286 16.9313 5.65286 16.5408 6.04338L11.9987 10.5855L7.45711 6.0439C7.06658 5.65338 6.43342 5.65338 6.04289 6.0439C5.65237 6.43442 5.65237 7.06759 6.04289 7.45811L10.5845 11.9997L6.04289 16.5413Z" fill=""/>
                          </svg>
                        </button>
                        <div>
                          <h4 class="text-lg font-bold text-gray-800 mb-1">Generate API key</h4>
                          <p class="mb-6 text-xs text-gray-500">To enable secure access to the LLM services, add your API key. Naming it makes it easier to manage.</p>
                          <form @submit.prevent="generateApiKey">
                            <div class="mb-4">
                              <label class="mb-1.5 block text-xs font-bold text-gray-700 uppercase">Key Name</label>
                              <input type="text" v-model="newKeyName" placeholder="e.g. Production Key" class="h-10 w-full rounded-lg border border-gray-300 bg-transparent px-3 py-2 text-sm text-gray-800 outline-none focus:border-[#465FFF] focus:ring-2 focus:ring-[#465FFF]/20 transition" required />
                            </div>
                            <div class="mb-4">
                              <label class="mb-1.5 block text-xs font-bold text-gray-700 uppercase">API Key Value</label>
                              <input type="password" v-model="newKeyValue" placeholder="sk-xxxxxxxx" class="h-10 w-full rounded-lg border border-gray-300 bg-transparent px-3 py-2 text-sm text-gray-800 outline-none focus:border-[#465FFF] focus:ring-2 focus:ring-[#465FFF]/20 transition" required />
                            </div>
                            <div class="mb-4">
                              <label class="mb-1.5 block text-xs font-bold text-gray-700 uppercase">Model</label>
                              <select v-model="newKeyModel" class="h-10 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-800 outline-none focus:border-[#465FFF] focus:ring-2 focus:ring-[#465FFF]/20 transition">
                                <option value="glm-4-flash">GLM-4 Flash</option>
                                <option value="glm-4-air">GLM-4 Air</option>
                                <option value="glm-4-plus">GLM-4 Plus</option>
                              </select>
                            </div>
                            <div class="mt-6 flex w-full items-center justify-between gap-3">
                              <button @click.prevent="isModalOpen = false" type="button" class="flex w-full justify-center rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-bold text-gray-700 hover:bg-gray-50 transition shadow-sm">Cancel</button>
                              <button type="submit" class="bg-[#465FFF] hover:bg-[#3B50E0] flex w-full justify-center rounded-lg px-4 py-2.5 text-sm font-bold text-white transition shadow-sm">Save key</button>
                            </div>
                          </form>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="overflow-x-auto pt-4">
                  <table class="min-w-full">
                    <thead>
                      <tr class="border-b border-gray-100">
                        <th class="py-2 pr-4 text-left text-[11px] font-bold text-gray-400 uppercase tracking-wider">Name / Key</th>
                        <th class="px-4 py-2 text-left text-[11px] font-bold text-gray-400 uppercase tracking-wider">Status</th>
                        <th class="px-4 py-2 text-left text-[11px] font-bold text-gray-400 uppercase tracking-wider">Model</th>
                        <th class="px-4 py-2 text-left text-[11px] font-bold text-gray-400 uppercase tracking-wider">Action</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-50">
                      <tr v-for="(key, index) in apiKeysList" :key="index" class="hover:bg-gray-50/50 transition-colors">
                        <td class="py-4 pr-4 whitespace-nowrap">
                          <div class="flex flex-col gap-1.5">
                            <span class="text-sm font-bold text-gray-700">{{ key.name }}</span>
                            <div class="flex items-center gap-2">
                              <div class="relative w-[280px]">
                                <input :value="key.maskedValue" type="password" readonly class="h-9 w-full rounded-lg border border-gray-200 bg-gray-50/50 py-1.5 pr-16 pl-3 text-xs text-gray-600 font-mono outline-none" />
                                <button type="button" @click="copyToClipboard(key.value, index)" class="absolute top-1/2 right-1 -translate-y-1/2 inline-flex h-7 items-center justify-center rounded-md bg-white border border-gray-200 px-2.5 text-[10px] font-bold text-gray-600 hover:bg-gray-50 transition shadow-sm">
                                  {{ copiedIndex === index ? 'Copied' : 'Copy' }}
                                </button>
                              </div>
                            </div>
                          </div>
                        </td>
                        <td class="px-4 py-4 whitespace-nowrap">
                          <span v-if="key.active" class="inline-flex items-center justify-center gap-1 rounded-full bg-green-50 px-2.5 py-1 text-[10px] font-bold text-green-600 border border-green-100">
                             Active
                          </span>
                          <span v-else class="inline-flex items-center justify-center gap-1 rounded-full bg-gray-50 px-2.5 py-1 text-[10px] font-bold text-gray-500 border border-gray-200">
                             Disabled
                          </span>
                        </td>
                        <td class="px-4 py-4 text-xs font-bold text-gray-600 whitespace-nowrap uppercase">{{ key.model }}</td>
                        <td class="px-4 py-4 whitespace-nowrap">
                          <div class="flex items-center gap-3">
                            <button @click="testApiKeyFn(key)" :disabled="testLoading && testingIndex === index" class="text-xs font-bold px-3 py-1.5 rounded-lg transition-all" :class="key.testSuccess === true ? 'bg-green-100 text-green-700' : key.testSuccess === false ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'">
                              <span v-if="testLoading && testingIndex === index" class="animate-spin inline-block">↻</span>
                              <span v-else>{{ key.testSuccess === true ? '✅ OK' : key.testSuccess === false ? '❌ Failed' : 'Test' }}</span>
                            </button>
                            <button @click="deleteApiKey(index)" class="text-gray-400 hover:text-red-500 transition-colors p-1.5 rounded-lg hover:bg-red-50">
                              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </td>
                      </tr>
                      
                      <tr v-if="apiKeysList.length === 0">
                        <td colspan="4" class="py-8 text-center text-sm text-gray-500">
                           No API keys configured yet. Click "Add API Key" to create one.
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <hr class="border-gray-100" />

              <!-- L2 Prompt 动态外挂配置 (全屏宽) -->
              <div>
                  <div class="flex justify-between items-end mb-4">
                      <div>
                          <h3 class="text-sm font-bold text-gray-700 border-l-2 border-[#465FFF] pl-3">AI 话术规则配置 (Prompt YAML)</h3>
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
                  <button @click="requestNotification" class="px-6 py-2 bg-white border border-gray-200 text-gray-700 rounded-lg text-sm font-bold hover:bg-gray-50 transition-all shadow-sm">
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

// API Keys Management (TailAdmin Style)
const isModalOpen = ref(false);
const newKeyName = ref('');
const newKeyValue = ref('');
const newKeyModel = ref('glm-4-flash');
const testLoading = ref(false);
const testingIndex = ref(-1);
const copiedIndex = ref(-1);

// Initialize with some dummy data if needed, or empty array
const apiKeysList = ref([]);

const copyToClipboard = (text, index) => {
  navigator.clipboard.writeText(text);
  copiedIndex.value = index;
  setTimeout(() => { copiedIndex.value = -1; }, 2000);
};

const maskApiKey = (key) => {
  if (!key || key.length < 8) return '********';
  return key.substring(0, 4) + '********' + key.substring(key.length - 4);
};

const generateApiKey = () => {
  if (!newKeyName.value || !newKeyValue.value) return;
  apiKeysList.value.push({
    name: newKeyName.value,
    value: newKeyValue.value,
    maskedValue: maskApiKey(newKeyValue.value),
    model: newKeyModel.value,
    active: true,
    testSuccess: null
  });
  // Reset modal
  newKeyName.value = '';
  newKeyValue.value = '';
  newKeyModel.value = 'glm-4-flash';
  isModalOpen.value = false;
  // TODO: Save to backend
  saveToEnv(apiKeysList.value[apiKeysList.value.length - 1]);
};

const deleteApiKey = (index) => {
  if (confirm('Are you sure you want to delete this API Key?')) {
    apiKeysList.value.splice(index, 1);
  }
};

const testApiKeyFn = async (keyData) => {
  const index = apiKeysList.value.findIndex(k => k === keyData);
  testingIndex.value = index;
  testLoading.value = true;
  keyData.testSuccess = null;
  
  try {
    const token = localStorage.getItem('pdd_admin_token');
    const res = await fetch('/api/dashboard/llm-test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        api_key: keyData.value,
        model: keyData.model,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    keyData.testSuccess = data.success;
  } catch (e) {
    keyData.testSuccess = false;
  } finally {
    testLoading.value = false;
    testingIndex.value = -1;
  }
};

const saveToEnv = async (keyData) => {
  try {
    const token = localStorage.getItem('pdd_admin_token');
    await fetch('/api/dashboard/llm-config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        api_key: keyData.value,
        model: keyData.model,
      }),
    });
  } catch (e) {
    console.error('Failed to save to env:', e);
  }
};

onMounted(() => {
  store.loadPrompt('ppt_consultant');
  loadCurrentLLMConfig();
});

const loadCurrentLLMConfig = async () => {
  try {
    const token = localStorage.getItem('pdd_admin_token');
    const res = await fetch('/api/dashboard/llm-config', {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
    });
    if (!res.ok) return;
    const data = await res.json();
    if (data.configured && data.api_key_full) {
      apiKeysList.value.push({
        name: 'Production Key (Auto Loaded)',
        value: data.api_key_full,
        maskedValue: maskApiKey(data.api_key_full),
        model: data.model || 'glm-4-flash',
        active: true,
        testSuccess: null
      });
    }
  } catch (e) {
    console.warn('加载 LLM 配置失败:', e);
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
