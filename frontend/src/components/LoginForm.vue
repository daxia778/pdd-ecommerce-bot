<template>
  <div class="min-h-screen w-full flex flex-col lg:flex-row bg-slate-900 font-sans">

    <!-- 原右侧动态视觉展示区，现改为左侧展示区 -->
    <div class="hidden lg:flex lg:w-7/12 relative overflow-hidden bg-[#0a0f1c] items-center justify-center">
      <!-- 极简背景点缀 -->
      <div class="absolute inset-0 opacity-[0.15] pointer-events-none" style="background-image: radial-gradient(circle at 2px 2px, rgba(255,87,77,0.4) 1px, transparent 0); background-size: 40px 40px;"></div>

      <!-- 动态装饰球体 -->
      <div class="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-red-600/20 rounded-full mix-blend-screen filter blur-[100px] animate-[pulse_6s_ease-in-out_infinite]"></div>
      <div class="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-orange-600/10 rounded-full mix-blend-screen filter blur-[120px] animate-[pulse_8s_ease-in-out_infinite_reverse]"></div>

      <!-- 核心轮播内容区 -->
      <div class="relative z-10 w-[90%] max-w-2xl px-0">

        <!-- 装饰性聊天气泡 (粘附于主卡片) -->
        <div class="absolute -top-6 -right-4 lg:-top-10 lg:-right-8 bg-white/5 backdrop-blur-md border border-white/10 p-3 lg:p-4 rounded-2xl rounded-tr-sm text-xs lg:text-sm text-white/90 shadow-2xl transform rotate-3 animate-float-slow z-20 max-w-[200px] lg:max-w-[280px]">
          “你好，我想做一套高质量的年终总结PPT”
        </div>
        <div class="absolute -bottom-10 -left-6 lg:-bottom-12 lg:-left-12 bg-red-500/10 backdrop-blur-md border border-red-500/20 p-3 lg:p-4 rounded-2xl rounded-bl-sm text-xs lg:text-sm text-red-100 shadow-2xl transform -rotate-2 animate-float z-20 max-w-[200px] lg:max-w-[280px]">
          “没问题！请问您对页数和色彩主体有什么偏好吗？”
        </div>

        <div class="relative z-10 bg-gradient-to-b from-white/[0.06] to-transparent backdrop-blur-xl rounded-[1.5rem] lg:rounded-[2rem] border border-white/10 p-5 lg:p-10 xl:p-12 shadow-[0_8px_32px_0_rgba(0,0,0,0.3)]">

          <!-- 实时数据统计栏 (滚动效果) -->
          <div class="flex items-center gap-4 lg:gap-6 mb-6 lg:mb-10 pb-4 lg:pb-6 border-b border-white/10 overflow-hidden h-12 lg:h-14 box-border">
            <div class="flex items-center gap-2 shrink-0 z-10 bg-green-500/10 border border-green-500/20 px-3 py-1.5 rounded-full">
              <span class="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse"></span>
              <span class="text-xs font-bold text-green-400 tracking-wider">系统运行中</span>
            </div>
            <div class="flex-1 overflow-hidden relative h-full mask-fade-edges flex items-center">
              <div class="absolute flex whitespace-nowrap items-center gap-10 animate-marquee text-xs font-mono text-white/60 leading-none h-full">
                <span>今日接待: <strong class="text-white">12,847 人</strong></span>
                <span>智能解决率: <strong class="text-green-400">98.2%</strong></span>
                <span>平均响应: <strong class="text-white">85ms</strong></span>
                <span>阻断异常: <strong class="text-red-400">423 次</strong></span>
                <span>转化工单: <strong class="text-white">8,492 单</strong></span>
                <!-- 重复以便无缝滚动 -->
                <span>今日接待: <strong class="text-white">12,847 人</strong></span>
                <span>智能解决率: <strong class="text-green-400">98.2%</strong></span>
                <span>平均响应: <strong class="text-white">85ms</strong></span>
              </div>
            </div>
          </div>

          <Transition name="slide-up" mode="out-in">
            <div :key="currentIndex" class="min-h-[160px] lg:min-h-[220px] flex flex-col justify-center">
              <div class="mb-4 lg:mb-6">
                <div class="inline-flex items-center justify-center w-12 h-12 lg:w-16 lg:h-16 rounded-xl lg:rounded-2xl bg-gradient-to-br from-white/10 to-white/5 border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.2)]">
                  <span class="text-2xl lg:text-4xl drop-shadow-md transform -translate-y-0.5">{{ features[currentIndex].icon }}</span>
                </div>
              </div>

              <h3 class="text-2xl lg:text-3xl xl:text-4xl font-extrabold mb-3 lg:mb-5 tracking-tight leading-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-red-100 to-[#FF574D]">
                {{ features[currentIndex].title }}
              </h3>

              <p class="text-sm lg:text-base xl:text-lg text-white/70 font-medium leading-relaxed mb-4 lg:mb-6">
                {{ features[currentIndex].desc }}
              </p>

              <!-- 标签/药丸展示 -->
              <div class="flex flex-wrap gap-1.5 lg:gap-2.5 mt-auto relative z-20">
                <span
                  v-for="(tag, tIdx) in features[currentIndex].tags"
                  :key="tIdx"
                  class="px-2.5 py-1 lg:px-3.5 lg:py-1.5 bg-white/10 border border-white/20 hover:bg-white/20 transition-colors rounded-full text-[10px] lg:text-xs font-bold text-white tracking-wide shadow-sm"
                >
                  {{ tag }}
                </span>
              </div>
            </div>
          </Transition>

          <!-- 指示器 -->
          <div class="flex gap-2 lg:gap-2.5 mt-6 lg:mt-10 bg-black/30 p-2 lg:p-2.5 rounded-full w-max backdrop-blur-md">
            <div
              v-for="(_, index) in features"
              :key="index"
              class="h-2 rounded-full transition-all duration-500 cursor-pointer"
              :class="index === currentIndex ? 'w-8 bg-gradient-to-r from-[#FF574D] to-red-400 shadow-[0_0_10px_rgba(255,87,77,0.5)]' : 'w-2 bg-white/20 hover:bg-white/40'"
              @click="setIndex(index)"
            ></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 原左侧登录区，现改为右侧表单区 -->
    <div class="w-full lg:w-5/12 flex flex-col justify-center items-center p-8 sm:p-12 relative z-10 box-border bg-slate-900 border-l border-white/5">
      <!-- 极简背景点缀 -->
      <div class="absolute inset-0 opacity-[0.03] pointer-events-none" style="background-image: radial-gradient(circle at 2px 2px, rgba(255,87,77,1) 1px, transparent 0); background-size: 32px 32px;"></div>

      <div class="w-full max-w-md relative">
        <!-- Logo 标题区 -->
        <div class="flex flex-col items-center gap-4 mb-12 text-center">
          <div class="w-12 h-12 bg-gradient-to-br from-[#FF574D] to-[#E02E24] rounded-xl flex items-center justify-center shadow-xl shadow-red-500/20 border border-white/10">
            <span class="text-white text-2xl font-black drop-shadow-md">多</span>
          </div>
          <div>
            <h1 class="text-3xl font-extrabold text-white tracking-tight">PDD AI 客服中枢</h1>
            <p class="text-sm font-bold text-slate-400 mt-2">请输入您的管理员凭证以进入控制台</p>
          </div>
        </div>

        <!-- 登录表单 -->
        <form @submit.prevent="handleLogin" class="space-y-6">
          <div class="space-y-6">
            <div class="flex flex-col gap-1.5 group">
              <label class="block text-sm font-bold text-slate-400 transition-colors group-hover:text-slate-300 ml-1">管理员账号</label>
              <div class="flex items-center bg-[#1e293b]/50 border border-slate-700/60 rounded-xl overflow-hidden focus-within:border-red-500 focus-within:ring-1 focus-within:ring-red-500/40 transition-all shadow-inner hover:border-slate-600">
                <div class="px-4 py-3.5 bg-[#0f172a]/40 text-slate-500 border-r border-slate-700/60 group-focus-within:text-red-400 group-focus-within:bg-red-500/5 transition-colors flex items-center justify-center">
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                  </svg>
                </div>
                <input
                  v-model="username"
                  type="text"
                  autocomplete="username"
                  placeholder="请输入账号"
                  class="w-full bg-transparent border-none px-4 py-3.5 text-white placeholder-slate-500 font-medium focus:outline-none focus:ring-0"
                  :disabled="loading"
                />
              </div>
            </div>

            <div class="flex flex-col gap-1.5 group">
              <label class="block text-sm font-bold text-slate-400 transition-colors group-hover:text-slate-300 ml-1">访问密码</label>
              <div class="flex items-center bg-[#1e293b]/50 border border-slate-700/60 rounded-xl overflow-hidden focus-within:border-red-500 focus-within:ring-1 focus-within:ring-red-500/40 transition-all shadow-inner hover:border-slate-600">
                <div class="px-4 py-3.5 bg-[#0f172a]/40 text-slate-500 border-r border-slate-700/60 group-focus-within:text-red-400 group-focus-within:bg-red-500/5 transition-colors flex items-center justify-center">
                  <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>
                  </svg>
                </div>
                <input
                  v-model="password"
                  type="password"
                  autocomplete="current-password"
                  placeholder="••••••••"
                  class="w-full bg-transparent border-none px-4 py-3.5 text-white placeholder-slate-500 font-medium tracking-widest focus:outline-none focus:ring-0"
                  :disabled="loading"
                />
              </div>
            </div>
          </div>

          <!-- 报错信息 -->
          <Transition name="fade">
            <div v-if="error" class="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl mt-4">
              <svg class="w-5 h-5 text-red-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="text-red-400 text-sm font-medium">{{ error }}</span>
            </div>
          </Transition>

          <button
            type="submit"
            :disabled="loading || !username || !password"
            class="w-full py-4 mt-8 bg-gradient-to-r from-[#FF574D] to-[#E02E24] hover:from-[#E02E24] hover:to-[#c02018] disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-xl shadow-lg shadow-red-500/25 transition-all transform hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-2 text-lg"
          >
            <svg v-if="loading" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            <span>{{ loading ? '身份验证中...' : '登录控制台' }}</span>
          </button>
        </form>

        <p class="text-center text-slate-500 text-xs mt-12 font-medium">PDD AI 智能客服系统 &copy; 2026</p>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { store } from '../store.js';

const username = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

// 轮播内容配置增强
const features = [
  { icon: '🤖', title: '7×24小时无休接待', desc: '基于超大规模语言模型，全天候秒级响应买家咨询，绝不错过任何潜在商机。', tags: ['毫秒级响应', '多并发处理', '永不离线'] },
  { icon: '🎯', title: '结构化意图精准提取', desc: 'AI自动引导买家提供主题、页数、风格等核心要素，将自然语言转化为标准化生产工单。', tags: ['意图识别', '表单填充', '智能引导'] },
  { icon: '🛡️', title: '全天候安全风控网', desc: '精准识别议价、客诉及违规词汇，自动触发警报并静默拦截，确保业务合规稳定运行。', tags: ['违规拦截', '客诉预警', '敏感词过滤'] },
  { icon: '🧠', title: 'RAG 动态知识增强', desc: '根据最新定价策略与业务活动动态更新知识盲区，让 AI 永远回答准确、基于事实。', tags: ['向量检索', '事实核实', '实时同步'] },
  { icon: '📸', title: '多模态意图解析', desc: '支持买家发送参考图片，AI 可精准提取设计风格、色彩倾向与排版要素供设计师参考。', tags: ['图像识别', '风格拆解'] },
  { icon: '📈', title: '全链路流失风控分析', desc: '实时监控从咨询到下单的核心流转节点，智能识别流失风险并及时介入促单。', tags: ['商业演进', '漏斗追踪', '促单逻辑'] },
  { icon: '🤝', title: '无缝人工协同接管', desc: '极速切换人工客服模式，完整继承历史上下文语境，让买家感知不到接管缝隙。', tags: ['平滑切换', '上下文继承', 'Shadow Chat'] },
  { icon: '🔒', title: '私有化数据安全隔离', desc: '所有商业机密与客户隐私数据完全落于本地化数据库，保障核心数据资产绝对安全。', tags: ['本地部署', '资产沉淀', '加密存储'] }
];

const currentIndex = ref(0);
let timer = null;

const nextSlide = () => {
  currentIndex.value = (currentIndex.value + 1) % features.length;
};

const setIndex = (i) => {
  currentIndex.value = i;
  resetTimer();
};

const resetTimer = () => {
  if (timer) clearInterval(timer);
  timer = setInterval(nextSlide, 5000); // 延长为5秒阅读时间
};

onMounted(() => {
  resetTimer();
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});

const handleLogin = async () => {
  error.value = '';
  loading.value = true;
  try {
    await store.login(username.value, password.value);
  } catch (e) {
    error.value = e.message || '登录失败，请检查用户名和密码';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
/* 报错信息动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 右侧内容滑动动画 */
.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}
.slide-up-enter-from {
  opacity: 0;
  transform: translateX(40px) scale(0.97);
}
.slide-up-leave-to {
  opacity: 0;
  transform: translateX(-40px) scale(0.97);
}

/* 跑马灯动画 */
@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
.animate-marquee {
  animation: marquee 20s linear infinite;
  padding-left: 20px;
}

/* 渐变遮罩边缘，使滚动条左右两端带有渐隐效果 */
.mask-fade-edges {
  mask-image: linear-gradient(to right, transparent, black 10%, black 90%, transparent);
  -webkit-mask-image: linear-gradient(to right, transparent, black 10%, black 90%, transparent);
}

/* 悬浮气泡微小晃动 */
@keyframes float {
  0%, 100% { transform: translateY(0) rotate(-2deg); }
  50% { transform: translateY(-12px) rotate(-1deg); }
}
.animate-float {
  animation: float 6s ease-in-out infinite;
}

@keyframes float-slow {
  0%, 100% { transform: translateY(0) rotate(3deg); }
  50% { transform: translateY(-18px) rotate(4deg); }
}
.animate-float-slow {
  animation: float-slow 9s ease-in-out infinite;
}

/* 修复浏览器自动填充导致的背景色改变 */
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus,
input:-webkit-autofill:active {
  -webkit-transition: "color 9999s ease-out, background-color 9999s ease-out";
  -webkit-transition-delay: 9999s;
  -webkit-text-fill-color: white !important;
}

</style>
