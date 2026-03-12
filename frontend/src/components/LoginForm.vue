<template>
  <div class="min-h-screen w-full flex flex-col lg:flex-row font-sans relative overflow-hidden bg-[#0a0f1c]">

    <!-- 全局极简背景点缀 -->
    <div 
      class="absolute inset-0 pointer-events-none z-0 hidden lg:block opacity-[0.15]" 
      style="background-image: radial-gradient(circle at 2px 2px, rgba(255,87,77,0.4) 1px, transparent 0); background-size: 40px 40px;"
    ></div>

    <!-- 全局动态装饰球体 (光晕自然过渡渲染到双边) -->
    <div class="absolute top-[0%] left-[-10%] w-[600px] h-[600px] rounded-full mix-blend-screen filter blur-[120px] animate-[pulse_6s_ease-in-out_infinite] z-0 pointer-events-none hidden lg:block bg-red-600/20"></div>
    <div class="absolute bottom-[-10%] right-[10%] w-[800px] h-[800px] rounded-full mix-blend-screen filter blur-[150px] animate-[pulse_8s_ease-in-out_infinite_reverse] z-0 pointer-events-none hidden lg:block bg-orange-600/10"></div>

    <!-- 左侧展示区 -->
    <div class="hidden lg:flex lg:w-7/12 relative items-center justify-center z-10 overflow-hidden">

      <!-- 粒子动效背景 (三层视差) -->
      <div class="particle-container absolute inset-0 z-0">
        <div class="stars-layer stars-dark" id="stars1"></div>
        <div class="stars-layer stars-medium stars-dark" id="stars2"></div>
        <div class="stars-layer stars-large stars-dark" id="stars3"></div>
      </div>

      <!-- 核心轮播内容区 -->
      <div class="relative z-20 w-[90%] max-w-2xl px-0">

        <!-- 装饰性聊天气泡 (粘附于主卡片) -->
        <div class="absolute -top-6 -right-4 lg:-top-10 lg:-right-8 p-3 lg:p-4 rounded-2xl rounded-tr-sm text-xs lg:text-sm shadow-2xl transform rotate-3 animate-float-slow z-20 max-w-[200px] lg:max-w-[280px] bg-white/5 backdrop-blur-md border border-white/10 text-white/90">
          “你好，我想做一套高质量的年终总结PPT”
        </div>
        <div class="absolute -bottom-10 -left-6 lg:-bottom-12 lg:-left-12 p-3 lg:p-4 rounded-2xl rounded-bl-sm text-xs lg:text-sm shadow-2xl transform -rotate-2 animate-float z-20 max-w-[200px] lg:max-w-[280px] bg-red-500/10 backdrop-blur-md border border-red-500/20 text-red-100">
          “没问题！请问您对页数和色彩主体有什么偏好吗？”
        </div>

        <div class="relative z-10 rounded-[1.5rem] lg:rounded-[2rem] p-5 lg:p-10 xl:p-12 shadow-[0_8px_32px_0_rgba(0,0,0,0.3)] bg-gradient-to-b from-white/[0.06] to-transparent backdrop-blur-xl border border-white/10">

          <!-- 实时数据统计栏 (滚动效果) -->
          <div class="flex items-center gap-4 lg:gap-6 mb-6 lg:mb-10 pb-4 lg:pb-6 border-b overflow-hidden h-12 lg:h-14 box-border border-white/10">
            <div class="flex items-center gap-2 shrink-0 z-10 bg-green-500/10 border border-green-500/20 px-3 py-1.5 rounded-full">
              <span class="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse"></span>
              <span class="text-xs font-bold text-green-400 tracking-wider">系统运行中</span>
            </div>
            <div class="flex-1 overflow-hidden relative h-full mask-fade-edges flex items-center">
              <div class="absolute flex whitespace-nowrap items-center gap-10 animate-marquee text-xs font-mono leading-none h-full text-white/60">
                <span>今日接待: <strong class="text-white">12,847 人</strong></span>
                <span>智能解决率: <strong class="text-green-500">98.2%</strong></span>
                <span>平均响应: <strong class="text-white">85ms</strong></span>
                <span>阻断异常: <strong class="text-red-500">423 次</strong></span>
                <span>转化工单: <strong class="text-white">8,492 单</strong></span>
                <!-- 重复以便无缝滚动 -->
                <span>今日接待: <strong class="text-white">12,847 人</strong></span>
                <span>智能解决率: <strong class="text-green-500">98.2%</strong></span>
                <span>平均响应: <strong class="text-white">85ms</strong></span>
              </div>
            </div>
          </div>

          <Transition name="slide-up" mode="out-in">
            <div :key="currentIndex" class="min-h-[160px] lg:min-h-[220px] flex flex-col justify-center">
              <div class="mb-4 lg:mb-6">
                <div class="inline-flex items-center justify-center w-12 h-12 lg:w-16 lg:h-16 rounded-xl lg:rounded-2xl bg-gradient-to-br from-white/10 to-white/5 border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.2)]">
                  <div v-html="features[currentIndex].icon" class="flex items-center justify-center transform group-hover:scale-110 transition-transform duration-300"></div>
                </div>
              </div>

              <h3 class="text-2xl lg:text-3xl xl:text-4xl font-extrabold mb-3 lg:mb-5 tracking-tight leading-tight text-transparent bg-clip-text bg-gradient-to-r from-white via-red-100 to-[#FF574D]">
                {{ features[currentIndex].title }}
              </h3>

              <p class="text-sm lg:text-base xl:text-lg font-medium leading-relaxed mb-4 lg:mb-6 text-white/70">
                {{ features[currentIndex].desc }}
              </p>

              <!-- 标签/药丸展示 -->
              <div class="flex flex-wrap gap-1.5 lg:gap-2.5 mt-auto relative z-20">
                <span
                  v-for="(tag, tIdx) in features[currentIndex].tags"
                  :key="tIdx"
                  class="px-2.5 py-1 lg:px-3.5 lg:py-1.5 rounded-full text-[10px] lg:text-xs font-bold tracking-wide shadow-sm bg-white/10 border border-white/20 hover:bg-white/20 text-white"
                >
                  {{ tag }}
                </span>
              </div>
            </div>
          </Transition>

          <!-- 指示器 -->
          <div class="flex gap-2 lg:gap-2.5 mt-6 lg:mt-10 p-2 lg:p-2.5 rounded-full w-max backdrop-blur-md bg-black/30">
            <div
              v-for="(_, index) in features"
              :key="index"
              class="h-2 rounded-full transition-all duration-500 cursor-pointer"
              :class="index === currentIndex 
                  ? 'w-8 bg-gradient-to-r from-[#FF574D] to-red-400 shadow-[0_0_10px_rgba(255,87,77,0.5)]' 
                  : 'w-2 bg-white/20 hover:bg-white/40'"
              @click="setIndex(index)"
            ></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧表单区 (实底色) -->
    <div class="w-full lg:w-5/12 flex flex-col justify-center items-center p-8 sm:p-12 relative z-10 bg-[#0f172a]">
      <!-- 视觉连结元素：从左侧延伸过来的微小红色光带 -->
      <div class="absolute top-0 left-0 w-[1px] h-full bg-gradient-to-b from-transparent via-red-500/40 to-transparent hidden lg:block"></div>

      <div class="w-full max-w-md xl:max-w-lg relative z-20">
        <!-- 移动端 (lg hidden) -->
        <div class="lg:hidden flex flex-col items-center gap-4 mb-8 text-center">
          <h1 class="text-[32px] font-bold tracking-[0.08em] leading-tight text-white">AI客服后台系统</h1>
          <p class="text-[14px] font-normal text-slate-400">请输入管理员账号以登陆</p>
        </div>

        <!-- 桌面端：Brave 风格 — 无图标 + 超大排版 + 呼吸感间距 -->
        <div class="mb-10 hidden lg:block text-left">
          <h2 class="text-[48px] xl:text-[56px] font-bold leading-tight tracking-[0.06em] mb-2 whitespace-nowrap text-white">AI客服后台系统</h2>
          <p class="text-[16px] font-normal mt-2 text-slate-400">请输入管理员账号以登陆</p>
        </div>

        <!-- 登录表单 (Uiverse Floating Label 风格) -->
        <form @submit.prevent="handleLogin" class="login-form">
          <div class="input-field">
            <input
              v-model="username"
              type="text"
              placeholder=" "
              autocomplete="username"
              class="login-input"
              :disabled="loading"
              @focus="usernameFocused = true"
              @blur="usernameFocused = false"
              @animationstart="onUsernameAnimationStart"
            />
            <label class="floating-label" :class="{ 'label-float': usernameFocused || username || usernameAutofilled }">管理员账号</label>
          </div>

          <div class="input-field">
            <input
              v-model="password"
              type="password"
              placeholder=" "
              autocomplete="current-password"
              class="login-input"
              :disabled="loading"
              @focus="passwordFocused = true"
              @blur="passwordFocused = false"
              @animationstart="onPasswordAnimationStart"
            />
            <label class="floating-label" :class="{ 'label-float': passwordFocused || password || passwordAutofilled }">访问密码</label>
          </div>

          <!-- 报错信息 -->
          <Transition name="fade-down">
            <div v-if="error" class="flex items-center gap-3 p-3 bg-[#FF574D]/10 border border-[#FF574D]/20 rounded-lg mt-1">
              <svg class="w-4 h-4 text-[#FF574D] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="text-[#FF574D] text-[13px] font-semibold">{{ error }}</span>
            </div>
          </Transition>

          <!-- 主按钮 -->
          <button
            type="submit"
            :disabled="loading || !username || !password"
            class="submit-btn"
          >
            <svg v-if="loading" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            <span>{{ loading ? '连接验证中...' : '进入面板' }}</span>
          </button>
        </form>

        <div class="mt-14 pt-6 border-t border-white/5 flex justify-between items-center">
          <p class="text-slate-500 text-xs font-semibold">PDD AI 智能客服中枢 &copy; 2026</p>
          <div class="flex gap-2">
             <div class="w-1.5 h-1.5 rounded-full bg-slate-700"></div>
             <div class="w-1.5 h-1.5 rounded-full bg-slate-700"></div>
             <div class="w-1.5 h-1.5 rounded-full bg-red-500"></div>
          </div>
        </div>
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
const usernameFocused = ref(false);
const passwordFocused = ref(false);
const usernameAutofilled = ref(false);
const passwordAutofilled = ref(false);

// 检测浏览器自动填充
const onUsernameAnimationStart = (e) => { if (e.animationName === 'onAutoFillStart') usernameAutofilled.value = true; };
const onPasswordAnimationStart = (e) => { if (e.animationName === 'onAutoFillStart') passwordAutofilled.value = true; };

// 轮播内容配置增强 (带SVG图标)
const features = [
  { icon: '<svg class="w-8 h-8 lg:w-10 lg:h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>', title: '7×24小时无休接待', desc: '基于超大规模语言模型，全天候秒级响应买家咨询，绝不错过任何潜在商机。', tags: ['毫秒级响应', '多并发处理', '永不离线'] },
  { icon: '<svg class="w-8 h-8 lg:w-10 lg:h-10 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" /></svg>', title: '结构化意图精准提取', desc: 'AI自动引导买家提供主题、页数、风格等核心要素，将自然语言转化为标准化生产工单。', tags: ['意图识别', '表单填充', '智能引导'] },
  { icon: '<svg class="w-8 h-8 lg:w-10 lg:h-10 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>', title: '全天候安全风控网', desc: '精准识别议价、客诉及违规词汇，自动触发警报并静默拦截，确保业务合规稳定运行。', tags: ['违规拦截', '客诉预警', '敏感词过滤'] },
  { icon: '<svg class="w-8 h-8 lg:w-10 lg:h-10 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>', title: 'RAG 动态知识增强', desc: '根据最新定价策略与业务活动动态更新知识盲区，让 AI 永远回答准确、基于事实。', tags: ['向量检索', '事实核实', '实时同步'] },
  { icon: '<svg class="w-8 h-8 lg:w-10 lg:h-10 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" /></svg>', title: '多模态意图解析', desc: '支持买家发送参考图片，AI 可精准提取设计风格、色彩倾向与排版要素供设计师参考。', tags: ['图像识别', '风格拆解'] },
  { icon: '<svg class="w-8 h-8 lg:w-10 lg:h-10 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>', title: '全链路流失风控分析', desc: '实时监控从咨询到下单的核心流转节点，智能识别流失风险并及时介入促单。', tags: ['商业演进', '漏斗追踪', '促单逻辑'] },
  { icon: '<svg class="w-8 h-8 lg:w-10 lg:h-10 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" /></svg>', title: '无缝人工协同接管', desc: '极速切换人工客服模式，完整继承历史上下文语境，让买家感知不到接管缝隙。', tags: ['平滑切换', '上下文继承', 'Shadow Chat'] },
  { icon: '<svg class="w-8 h-8 lg:w-10 lg:h-10 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>', title: '私有化数据安全隔离', desc: '所有商业机密与客户隐私数据完全落于本地化数据库，保障核心数据资产绝对安全。', tags: ['本地部署', '资产沉淀', '加密存储'] }
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
.fade-down-enter-active, .fade-down-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-down-enter-from, .fade-down-leave-to {
  opacity: 0;
  transform: translateY(-5px);
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

</style>

<!-- 登录表单专用样式（非 scoped，完全复刻原版 Uiverse 代码逻辑） -->
<style>
.login-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.input-field {
  position: relative;
  width: 100%;
}

.login-input {
  margin-top: 15px;
  width: 100%;
  outline: none;
  border-radius: 8px;
  height: 48px;
  border: 1.5px solid rgba(255, 255, 255, 0.15);
  background: transparent;
  padding-left: 14px;
  padding-right: 14px;
  font-size: 15px;
  font-weight: 500;
  color: #ffffff;
  box-sizing: border-box;
}

.login-input:focus {
  border: 1.5px solid #FF574D;
}

.input-field .floating-label {
  position: absolute;
  top: 27px;
  left: 15px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  font-weight: 500;
  pointer-events: none;
  z-index: 2;
  transform: translate(0, 0) scale(1);
  transform-origin: left center;
  will-change: transform, color, background-color;
  transition: transform 0.3s ease,
              color 0.3s ease,
              background-color 0.2s ease,
              padding 0.3s ease;
}

.input-field .login-input:focus ~ .floating-label,
.input-field .login-input:not(:placeholder-shown) ~ .floating-label,
.input-field .login-input:-webkit-autofill ~ .floating-label,
.input-field .label-float {
  transform: translate(-7px, -21px) scale(0.85);
  color: #FF574D;
  background-color: #0f172a;
  padding-left: 5px;
  padding-right: 5px;
}

/* 失焦但有值时 label 颜色变回柔和 */
.input-field .login-input:not(:focus):not(:placeholder-shown) ~ .floating-label {
  color: rgba(255, 255, 255, 0.5);
}
.input-field .login-input:not(:focus) ~ .label-float {
  color: rgba(255, 255, 255, 0.5);
}

/* Autofill 检测 */
@keyframes onAutoFillStart { from { opacity: 1; } to { opacity: 1; } }
input:-webkit-autofill {
  animation-name: onAutoFillStart;
  animation-fill-mode: both;
}
.login-input:-webkit-autofill,
.login-input:-webkit-autofill:hover,
.login-input:-webkit-autofill:focus,
.login-input:-webkit-autofill:active {
  -webkit-box-shadow: 0 0 0 30px #0f172a inset !important;
  -webkit-text-fill-color: white !important;
  caret-color: white !important;
}

.submit-btn {
  margin-top: 24px;
  width: 100%;
  height: 52px;
  border-radius: 10px;
  border: 0;
  outline: none;
  color: #ffffff;
  font-size: 16px;
  font-weight: 700;
  background: linear-gradient(180deg, #FF574D 0%, #e0342a 50%, #c42016 100%);
  box-shadow: 0 4px 15px rgba(255, 87, 77, 0.25);
  transition: all 0.3s cubic-bezier(0.15, 0.83, 0.66, 1);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.submit-btn:hover {
  box-shadow: 0 6px 20px rgba(255, 87, 77, 0.4), 0 0 0 3px rgba(255, 87, 77, 0.15);
  transform: translateY(-1px);
}

.submit-btn:active {
  transform: scale(0.98);
}

.submit-btn:disabled {
  background: linear-gradient(180deg, #2a2a2e 0%, #1a1a1e 50%, #111115 100%);
  color: rgba(255, 255, 255, 0.3);
  cursor: not-allowed;
  box-shadow: none;
}

/* === 粒子星空动效 (三层视差) === */
.particle-container {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

.stars-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 1px;
  height: 1px;
  background: transparent;
  animation: animStar 50s linear infinite;
}

.stars-layer.stars-medium {
  width: 2px;
  height: 2px;
  animation-duration: 100s;
}

.stars-layer.stars-large {
  width: 3px;
  height: 3px;
  animation-duration: 150s;
}

.stars-layer::after {
  content: "";
  position: absolute;
  top: 2000px;
  width: inherit;
  height: inherit;
  background: transparent;
  box-shadow: inherit;
}

/* 深色模式粒子 (白色) */
.stars-dark#stars1 {
  box-shadow:
    1225px 1170px #fff, 1665px 988px #fff, 874px 1402px #fff, 332px 648px #fff,
    1890px 1567px #fff, 458px 224px #fff, 768px 1820px #fff, 1456px 312px #fff,
    210px 1650px #fff, 1800px 780px #fff, 540px 430px #fff, 920px 1100px #fff,
    1350px 1900px #fff, 100px 890px #fff, 1650px 150px #fff, 380px 1340px #fff,
    1100px 560px #fff, 1780px 1420px #fff, 640px 1780px #fff, 1520px 840px #fff,
    290px 200px #fff, 1050px 1620px #fff, 1920px 380px #fff, 710px 930px #fff,
    420px 1080px #fff, 1310px 470px #fff, 1560px 1750px #fff, 180px 1500px #fff,
    850px 270px #fff, 1700px 1050px #fff, 510px 1920px #fff, 1180px 710px #fff,
    60px 1200px #fff, 1420px 1600px #fff, 760px 110px #fff, 1600px 520px #fff,
    340px 1850px #fff, 1270px 960px #fff, 980px 1480px #fff, 1850px 1280px #fff,
    470px 650px #fff, 1130px 1830px #fff, 200px 400px #fff, 1480px 130px #fff,
    650px 1560px #fff, 1750px 850px #fff, 120px 70px #fff, 890px 1710px #fff,
    1380px 290px #fff, 560px 1170px #fff, 1640px 1380px #fff,
    45px 350px #fff, 1920px 1100px #fff, 730px 1250px #fff, 1550px 50px #fff,
    260px 980px #fff, 1830px 1750px #fff, 600px 180px #fff, 1200px 1500px #fff,
    420px 1800px #fff, 1700px 420px #fff, 150px 1100px #fff, 950px 30px #fff,
    1450px 870px #fff, 310px 1600px #fff, 1100px 1950px #fff, 800px 550px #fff,
    1600px 1200px #fff, 500px 920px #fff, 1350px 1650px #fff, 70px 500px #fff,
    1900px 250px #fff, 680px 1400px #fff, 1250px 100px #fff, 400px 1150px #fff,
    1750px 680px #fff, 130px 1850px #fff, 1050px 350px #fff, 550px 1700px #fff,
    1500px 950px #fff, 350px 270px #fff, 1800px 1450px #fff, 750px 780px #fff,
    1150px 1300px #fff, 20px 1550px #fff, 1650px 350px #fff, 450px 50px #fff,
    960px 1800px #fff, 1380px 600px #fff, 230px 750px #fff, 1550px 1150px #fff;
}

.stars-dark#stars2 {
  box-shadow:
    1744px 1689px #fff, 1081px 1296px #fff, 423px 807px #fff, 1567px 450px #fff,
    789px 1858px #fff, 312px 1120px #fff, 1890px 678px #fff, 645px 1456px #fff,
    1234px 234px #fff, 890px 890px #fff, 1456px 1567px #fff, 234px 345px #fff,
    1678px 1012px #fff, 567px 1789px #fff, 1123px 567px #fff, 345px 1345px #fff,
    1789px 178px #fff, 901px 1678px #fff, 456px 456px #fff, 1345px 1234px #fff,
    678px 78px #fff, 1012px 1890px #fff, 178px 789px #fff, 1567px 901px #fff,
    80px 1450px #fff, 1850px 320px #fff, 720px 1100px #fff, 1400px 1800px #fff,
    350px 530px #fff, 1100px 80px #fff, 580px 1650px #fff, 1650px 770px #fff,
    200px 1900px #fff, 1300px 420px #fff, 930px 1350px #fff, 450px 1750px #fff,
    1750px 1100px #fff, 680px 280px #fff, 1500px 1550px #fff, 150px 670px #fff,
    1050px 1950px #fff, 500px 100px #fff, 1850px 850px #fff, 300px 1200px #fff;
}

.stars-dark#stars3 {
  box-shadow:
    1300px 400px #fff, 600px 1500px #fff, 1800px 900px #fff, 200px 1200px #fff,
    1500px 1800px #fff, 900px 300px #fff, 400px 800px #fff, 1700px 1600px #fff,
    1100px 100px #fff, 700px 1900px #fff, 300px 1700px #fff, 1600px 600px #fff,
    100px 450px #fff, 1400px 1100px #fff, 850px 1750px #fff, 1750px 250px #fff,
    500px 1350px #fff, 1200px 700px #fff, 50px 1600px #fff, 1550px 1400px #fff,
    750px 50px #fff, 1900px 1000px #fff, 350px 550px #fff, 1050px 1850px #fff;
}

@keyframes animStar {
  from { transform: translateY(0px); }
  to { transform: translateY(-2000px); }
}
</style>
