<template>
  <div class="space-y-6">
      <!-- P1.3 整体加载骨架屏 -->
      <div v-if="isLoading" class="animate-pulse space-y-6">
         <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div v-for="i in 4" :key="i" class="h-32 bg-gray-100 rounded-2xl"></div>
         </div>
         <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="h-[400px] lg:col-span-2 bg-gray-100 rounded-2xl"></div>
            <div class="h-[400px] bg-gray-100 rounded-2xl"></div>
         </div>
      </div>

      <div v-else class="space-y-6">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <!-- Card 1: 今日活跃会话 -->
          <div class="bg-gradient-to-br from-blue-50 to-white p-5 rounded-2xl shadow-sm border border-blue-100/80 flex flex-col relative overflow-hidden group hover:shadow-lg hover:scale-[1.02] transition-all duration-300 min-w-0 cursor-default">
            <div class="absolute -top-4 -right-4 p-8 bg-blue-500 rounded-full opacity-5 group-hover:scale-110 transition-transform duration-500"></div>
            <div class="absolute top-3 right-3 opacity-30 group-hover:opacity-70 transition-opacity">
               <svg class="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z"></path></svg>
            </div>
            <p class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1.5 z-10">今日活跃会话</p>
            <p class="text-3xl font-black text-blue-700 drop-shadow-sm z-10 truncate">{{ store.sessions ? store.sessions.length : 0 }}</p>
            <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-md mt-2 border inline-flex items-center gap-0.5 w-max bg-green-50 text-green-600 border-green-200">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"></path></svg>
              12%
            </span>
          </div>

          <!-- Card 2: 待处理干预请求 -->
          <div class="bg-gradient-to-br from-red-50 to-white p-5 rounded-2xl shadow-sm border border-red-100/80 flex flex-col relative overflow-hidden group hover:shadow-lg hover:scale-[1.02] transition-all duration-300 min-w-0 cursor-default">
            <div class="absolute -top-4 -right-4 p-8 bg-red-500 rounded-full opacity-5 group-hover:scale-110 transition-transform duration-500"></div>
            <div class="absolute top-3 right-3 opacity-30 group-hover:opacity-70 transition-opacity">
               <svg class="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
            </div>
            <p class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1.5 z-10">待处理干预请求</p>
            <p class="text-3xl font-black text-red-600 drop-shadow-sm z-10 truncate">{{ store.escalations ? store.escalations.length : 0 }}</p>
            <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-md mt-2 border inline-flex items-center gap-0.5 w-max bg-green-50 text-green-600 border-green-200">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"></path></svg>
              2
            </span>
          </div>

          <!-- Card 3: AI 独立解决率 -->
          <div class="bg-gradient-to-br from-indigo-50 to-white p-5 rounded-2xl shadow-sm border border-indigo-100/80 flex flex-col relative overflow-hidden group hover:shadow-lg hover:scale-[1.02] transition-all duration-300 min-w-0 cursor-default">
            <div class="absolute -top-4 -right-4 p-8 bg-indigo-500 rounded-full opacity-5 group-hover:scale-110 transition-transform duration-500"></div>
            <div class="absolute top-3 right-3 opacity-30 group-hover:opacity-70 transition-opacity">
               <svg class="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            </div>
            <p class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1.5 z-10">AI 独立解决率</p>
            <p class="text-2xl font-black text-indigo-600 drop-shadow-sm z-10 truncate">{{ store.stats?.satisfaction_rate || '0%' }}</p>
            <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-md mt-2 border inline-flex items-center gap-0.5 w-max bg-green-50 text-green-600 border-green-200">
              +0.5%
            </span>
          </div>

          <!-- Card 4: 成单转化率 -->
          <div class="bg-gradient-to-br from-purple-50 to-white p-5 rounded-2xl shadow-sm border border-purple-100/80 flex flex-col relative overflow-hidden group hover:shadow-lg hover:scale-[1.02] transition-all duration-300 min-w-0 cursor-default">
            <div class="absolute -top-4 -right-4 p-8 bg-purple-500 rounded-full opacity-5 group-hover:scale-110 transition-transform duration-500"></div>
            <div class="absolute top-3 right-3 opacity-30 group-hover:opacity-70 transition-opacity">
               <svg class="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
            </div>
            <p class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1.5 z-10">成单转化率</p>
            <p class="text-2xl font-black text-purple-600 drop-shadow-sm z-10 truncate">{{ store.stats?.conversion_rate || '0%' }}</p>
            <span class="text-[10px] font-bold px-1.5 py-0.5 rounded-md mt-2 border inline-flex items-center gap-0.5 w-max bg-green-50 text-green-600 border-green-200">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"></path></svg>
              1.2%
            </span>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 h-[440px] lg:col-span-2 flex flex-col">
                <div class="flex justify-between items-center mb-2">
                    <h2 class="text-lg font-bold text-gray-800">数据分时趋势</h2>
                    <!-- Day selector tabs -->
                    <div class="flex gap-1 bg-gray-100 rounded-lg p-0.5">
                       <button
                         v-for="(day, idx) in dayOptions"
                         :key="day.date"
                         @click="selectDay(idx)"
                         :class="[
                           'px-3 py-1.5 rounded-md text-[11px] font-bold transition-all duration-200',
                           selectedDayIdx === idx
                             ? 'bg-white shadow-sm text-gray-800'
                             : 'text-gray-400 hover:text-gray-600'
                         ]"
                       >
                         {{ day.label }}
                       </button>
                    </div>
                </div>
                <!-- Metric selector row -->
                <div class="flex gap-1.5 mb-2 flex-wrap">
                    <button
                      v-for="m in metricOptions"
                      :key="m.key"
                      @click="selectMetric(m.key)"
                      :class="[
                        'px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all duration-200 border',
                        selectedMetric === m.key
                          ? 'bg-gray-800 text-white border-gray-800 shadow-sm'
                          : 'bg-white text-gray-400 border-gray-200 hover:border-gray-300 hover:text-gray-600'
                      ]"
                    >
                      {{ m.icon }} {{ m.label }}
                    </button>
                </div>
                <!-- Day summary bar -->
                <div class="flex gap-4 mb-2 text-[11px]">
                    <span class="flex items-center gap-1.5">
                        <span class="w-2.5 h-2.5 rounded-full" :style="`background:${dayOptions[selectedDayIdx]?.color}`"></span>
                        <span class="font-bold text-gray-500">峰值</span>
                        <span class="font-black text-gray-800">{{ peakValue }}{{ currentUnit }}</span>
                    </span>
                    <span class="flex items-center gap-1.5">
                        <svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                        <span class="font-bold text-gray-500">均值</span>
                        <span class="font-black text-gray-800">{{ avgValue }}{{ currentUnit }}</span>
                    </span>
                    <span class="flex items-center gap-1.5">
                        <svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        <span class="font-bold text-gray-500">峰时</span>
                        <span class="font-black text-gray-800">{{ peakHour }}</span>
                    </span>
                </div>
                <div ref="chartRef" class="w-full flex-1"></div>
            </div>

            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 h-[400px] flex flex-col">
                <h2 class="text-lg font-bold text-gray-800 mb-4">核心业务看板</h2>

                <div class="flex-1 flex flex-col justify-center space-y-6">
                   <div class="p-5 bg-gradient-to-br from-orange-50 to-orange-100/50 border border-orange-100 rounded-xl shadow-sm">
                      <p class="text-xs font-bold text-orange-400 uppercase tracking-wider mb-1 flex items-center">
                        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        今日预估营收
                      </p>
                      <p class="text-3xl font-black text-orange-600 font-mono tracking-tight">{{ store.stats?.total_revenue || '¥ 0' }}</p>
                   </div>

                   <div>
                      <div class="flex justify-between text-xs font-bold mb-2">
                         <span class="text-gray-500">流水线制造中订单</span>
                         <span class="text-emerald-600 text-sm font-black">{{ store.stats?.active_orders || '0' }} 单</span>
                      </div>
                      <div class="w-full bg-gray-100 rounded-full h-2.5">
                         <div class="bg-emerald-500 h-2.5 rounded-full shadow-[0_0_8px_rgba(16,185,129,0.4)] transition-all duration-1000" style="width: 75%"></div>
                      </div>
                   </div>

                   <div>
                      <div class="flex justify-between text-xs font-bold mb-2">
                         <span class="text-gray-500">平均响应耗时</span>
                         <span class="text-indigo-600 text-sm font-black">{{ store.stats?.avg_response_time || '0s' }}</span>
                      </div>
                      <div class="w-full bg-gray-100 rounded-full h-2.5">
                         <!-- Fallback calculation for UI width based loosely on target SLA (e.g. 5s max) -->
                         <div class="bg-indigo-400 h-2.5 rounded-full shadow-[0_0_8px_rgba(129,140,248,0.4)] transition-all duration-1000" style="width: 24%"></div>
                      </div>
                   </div>
                </div>
            </div>
        </div>
      </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import * as echarts from 'echarts';
import { store } from '../store.js';
import { DEMO_MULTI_DAY, METRIC_OPTIONS, DEMO_HOURLY, DEMO_HOURLY_YESTERDAY } from '../demoData.js';

const chartRef = ref(null);
let chartInstance = null;
const isLoading = ref(true);
const selectedDayIdx = ref(DEMO_MULTI_DAY.length - 1); // 默认选中今日（最后一个）
const selectedMetric = ref('conversations');

const dayOptions = ref(DEMO_MULTI_DAY);
const metricOptions = METRIC_OPTIONS;

// 当前选中的指标元数据
const currentMetricMeta = computed(() => metricOptions.find(m => m.key === selectedMetric.value) || metricOptions[0]);
const currentUnit = computed(() => currentMetricMeta.value.unit);

// 根据选定的天 + 指标获取数据数组
const currentData = computed(() => {
    const d = dayOptions.value[selectedDayIdx.value];
    if (!d) return [];
    return d[selectedMetric.value] || [];
});

// 统计摘要
const peakValue = computed(() => {
    const data = currentData.value;
    if (!data.length) return 0;
    const max = Math.max(...data);
    return selectedMetric.value === 'responseTime' ? max.toFixed(1) : max;
});
const avgValue = computed(() => {
    const data = currentData.value;
    const nonZero = data.filter(v => v > 0);
    if (!nonZero.length) return 0;
    const avg = nonZero.reduce((a, b) => a + b, 0) / nonZero.length;
    return selectedMetric.value === 'responseTime' ? avg.toFixed(1) : Math.round(avg);
});
const peakHour = computed(() => {
    const d = dayOptions.value[selectedDayIdx.value];
    const data = currentData.value;
    if (!d || !data.length) return '-';
    const maxIdx = data.indexOf(Math.max(...data));
    return d.hours[maxIdx] || '-';
});

const initChart = () => {
  if (chartRef.value && !chartInstance) {
      chartInstance = echarts.init(chartRef.value);
  }
};

const selectDay = (idx) => {
    selectedDayIdx.value = idx;
    updateChart();
};

const selectMetric = (key) => {
    selectedMetric.value = key;
    updateChart();
};

const fetchHourly = async () => {
  try {
    const res = await fetch('/api/dashboard/stats/hourly', { headers: store._headers() });
    if (res.ok) {
        const data = await res.json();
        if (data && data.hours && data.hours.length > 0) {
            const todayIdx = dayOptions.value.length - 1;
            dayOptions.value[todayIdx] = {
                ...dayOptions.value[todayIdx],
                hours: data.hours,
                conversations: data.counts || dayOptions.value[todayIdx].conversations
            };
        }
    }
  } catch (e) {
    console.error(e);
  } finally {
    updateChart();
  }
};

const loadData = async () => {
    isLoading.value = true;
    await fetchHourly();
    setTimeout(() => {
        isLoading.value = false;
        nextTick(() => {
            initChart();
            updateChart();
        });
    }, 500);
}

const updateChart = () => {
  if (!chartInstance) return;

  const day = dayOptions.value[selectedDayIdx.value];
  if (!day) return;

  const mainColor = day.color || '#6366F1';
  const data = day[selectedMetric.value] || [];
  const unit = currentUnit.value;
  const metricLabel = currentMetricMeta.value.label;

  const option = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.96)',
        borderColor: '#E5E7EB',
        borderWidth: 1,
        textStyle: { color: '#374151', fontSize: 12 },
        formatter: (params) => {
            const p = params[0];
            return `<div style="font-weight:700;margin-bottom:4px">${p.axisValue}</div>
                    <div style="display:flex;align-items:center;gap:6px">
                      <span style="width:8px;height:8px;border-radius:50%;background:${mainColor}"></span>
                      <span>${metricLabel}</span>
                      <span style="font-weight:800;margin-left:auto">${p.value}${unit}</span>
                    </div>`;
        }
      },
      grid: { left: '3%', right: '3%', bottom: '14%', top: '8%', containLabel: true },
      xAxis: {
          type: 'category',
          boundaryGap: false,
          data: day.hours,
          axisLine: { lineStyle: { color: '#E5E7EB' } },
          axisLabel: { color: '#9CA3AF', margin: 12, interval: 2, fontSize: 11 }
      },
      yAxis: {
          type: 'value',
          minInterval: selectedMetric.value === 'responseTime' ? 0.1 : 1,
          splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
          axisLabel: {
              color: '#9CA3AF', fontSize: 11,
              formatter: (v) => selectedMetric.value === 'responseTime' ? v.toFixed(1) + 's' : (selectedMetric.value === 'aiRate' ? v + '%' : v)
          }
      },
      dataZoom: [
          {
              type: 'slider',
              start: 0,
              end: 100,
              height: 20,
              bottom: 4,
              borderColor: 'transparent',
              backgroundColor: '#F3F4F6',
              fillerColor: `${mainColor}18`,
              handleStyle: { color: mainColor, borderColor: mainColor },
              dataBackground: {
                  lineStyle: { color: `${mainColor}40` },
                  areaStyle: { color: `${mainColor}15` }
              },
              selectedDataBackground: {
                  lineStyle: { color: mainColor },
                  areaStyle: { color: `${mainColor}30` }
              },
              textStyle: { color: '#9CA3AF', fontSize: 10 }
          }
      ],
      animationDuration: 600,
      animationEasing: 'cubicInOut',
      series: [
          {
              name: metricLabel,
              data: data,
              type: 'line',
              smooth: 0.4,
              lineStyle: { color: mainColor, width: 3 },
              areaStyle: {
                  color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                      { offset: 0, color: `${mainColor}50` },
                      { offset: 0.7, color: `${mainColor}10` },
                      { offset: 1, color: `${mainColor}00` }
                  ])
              },
              itemStyle: { color: mainColor, borderWidth: 2, borderColor: '#fff' },
              symbolSize: 6,
              showSymbol: false,
              emphasis: {
                  focus: 'series',
                  itemStyle: { shadowBlur: 10, shadowColor: `${mainColor}40` }
              },
              markPoint: {
                  data: [
                      { type: 'max', name: '峰值', symbolSize: 45, label: { fontSize: 10, fontWeight: 'bold' } }
                  ],
                  itemStyle: { color: mainColor }
              },
              markLine: {
                  silent: true,
                  data: [
                      { type: 'average', name: '均值' }
                  ],
                  lineStyle: { color: `${mainColor}60`, type: 'dashed', width: 1 },
                  label: { fontSize: 10, color: '#9CA3AF', formatter: `均值: {c}${unit}` }
              }
          }
      ]
  };

  chartInstance.setOption(option, true);
};

onMounted(() => {
  loadData();
  window.addEventListener('resize', () => chartInstance?.resize());
});

watch(() => store.activePanel, async (newVal) => {
  if (newVal === 'statistics') {
      await nextTick();
      if (!isLoading.value) {
          initChart();
          fetchHourly();
          chartInstance?.resize();
      }
  }
});
</script>
