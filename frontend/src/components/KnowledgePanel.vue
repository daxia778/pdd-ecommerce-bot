<template>
  <div class="space-y-6">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div class="p-6 border-b flex justify-between items-center bg-gray-50/50">
              <h2 class="text-xl font-black text-gray-800 flex items-center">
                  <svg class="w-6 h-6 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5.1.253v13m0-13c1.168-0.776 2.754-1.253 4.5-1.253s3.332 0.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332 0.477-4.5 1.253" />
                  </svg>
                  智小设 AI 专属知识库管理
              </h2>
              <button @click="showAddKnowledge = true"
                  class="bg-blue-600 text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-lg shadow-blue-200 hover:bg-blue-700 transition-all">+ 新增标准规则</button>
          </div>

          <div v-if="showAddKnowledge" class="p-6 bg-blue-50 border-b animate-in fade-in slide-in-from-top-4">
              <h3 class="font-bold text-blue-800 mb-4">入库新知识 (Markdown 格式)</h3>
              <div class="mb-4">
                 <select class="w-1/3 border-2 border-blue-200 rounded-xl p-2 text-sm focus:border-blue-500 outline-none mb-3">
                    <option>服务说明 / 交付政策</option>
                    <option>定价区间 / 报价策略</option>
                    <option>风格模板 / 案例话术</option>
                    <option>边界规则 / 敏感词拒单</option>
                 </select>
              </div>
               <textarea v-model="newKnowledgeContent" rows="5"
                   class="w-full border border-gray-200 rounded-xl p-4 text-sm focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 outline-none transition-all resize-none shadow-inner"
                   placeholder="例如：### 退换货政策\n本店支持7天无理由退货..."></textarea>
               <div class="flex justify-end space-x-3 mt-4">
                   <button @click="showAddKnowledge = false"
                       class="px-5 py-2.5 rounded-xl text-sm font-bold text-gray-500 hover:bg-white hover:shadow-sm transition-all border border-transparent hover:border-gray-200">取消</button>
                   <button @click="addKnowledge"
                       class="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl text-sm font-bold shadow-lg shadow-blue-200 hover:shadow-xl hover:-translate-y-0.5 transition-all">确认为 AI 入库</button>
               </div>
          </div>

          <div class="p-6 overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-100">
                  <thead class="bg-gray-50">
                      <tr>
                          <th class="px-6 py-4 text-left text-[10px] font-bold text-gray-400 uppercase tracking-widest w-32">Index ID / 版本</th>
                          <th class="px-6 py-4 text-left text-[10px] font-bold text-gray-400 uppercase tracking-widest w-40">规则分类</th>
                          <th class="px-6 py-4 text-left text-[10px] font-bold text-gray-400 uppercase tracking-widest">知识片段内容</th>
                          <th class="px-6 py-4 text-right text-[10px] font-bold text-gray-400 uppercase tracking-widest w-24">管理</th>
                      </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-50">
                      <tr v-for="(km, idx) in store.knowledgeBase" :key="km.id" class="hover:bg-gray-50/50 transition-colors">
                          <td class="px-6 py-4">
                             <div class="text-[10px] text-gray-400 font-mono">{{ km.id.slice(0, 8) }}...</div>
                             <div class="text-[9px] text-green-500 font-bold mt-1">v2.{{ idx }} (已生效)</div>
                          </td>
                          <td class="px-6 py-4">
                             <span v-if="km.content.includes('定价') || km.content.includes('价格')" class="px-2 py-1 bg-orange-100 text-orange-700 text-xs font-bold rounded-lg">定价与报价</span>
                             <span v-else-if="km.content.includes('交付') || km.content.includes('退款')" class="px-2 py-1 bg-purple-100 text-purple-700 text-xs font-bold rounded-lg">售后与交付</span>
                             <span v-else-if="km.content.includes('发票')" class="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-bold rounded-lg">财务发票</span>
                             <span v-else class="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-bold rounded-lg">通用规则</span>
                          </td>
                          <td class="px-6 py-4">
                               <div class="bg-white p-4 rounded-xl border border-gray-100 shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
                                  <p class="text-[13px] text-gray-700 leading-relaxed whitespace-pre-wrap font-medium">{{ km.content }}</p>
                               </div>
                          </td>
                          <td class="px-6 py-4 text-right">
                              <button @click="deleteKnowledge(km.id)"
                                  class="text-red-500 hover:text-red-700 font-bold text-xs uppercase tracking-wider transition-all bg-red-50 px-3 py-1.5 rounded-lg border border-red-100 hover:bg-red-100 hover:shadow-sm">下架</button>
                          </td>
                      </tr>
                      <tr v-if="store.knowledgeBase.length === 0">
                          <td colspan="4" class="px-6 py-12 text-center text-gray-400 font-medium">知识库为空，请先添加商品政策</td>
                      </tr>
                  </tbody>
              </table>
          </div>
      </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { store } from '../store.js';

const showAddKnowledge = ref(false);
const newKnowledgeContent = ref('');

const addKnowledge = async () => {
  if (!newKnowledgeContent.value.trim()) return;
  await fetch('/api/admin/knowledge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: newKnowledgeContent.value })
  });
  newKnowledgeContent.value = '';
  showAddKnowledge.value = false;
  await store.loadKnowledge();
};

const deleteKnowledge = async (id) => {
  if (!confirm("确定移除此知识？AI 将无法再引用它。")) return;
  await fetch(`/api/admin/knowledge/${id}`, { method: 'DELETE' });
  await store.loadKnowledge();
};
</script>
