<template>
  <div class="px-4 sm:px-6 lg:px-8 py-8 w-full max-w-9xl mx-auto bg-gray-50 min-h-full">

    <!-- Dashboard Header -->
    <div class="sm:flex sm:justify-between sm:items-center mb-8">
      <!-- Left: Title -->
      <div class="mb-4 sm:mb-0">
        <h1 class="text-2xl md:text-3xl text-gray-800 font-bold">数据看板</h1>
      </div>

      <!-- Right: Actions -->
      <div class="grid grid-flow-col sm:auto-cols-max justify-start sm:justify-end gap-2">
        <!-- Datepicker -->
        <div class="bg-white border border-gray-200 text-gray-500 hover:text-gray-600 px-4 py-2 rounded-lg shadow-sm flex items-center justify-between min-w-[240px] cursor-pointer">
          <svg class="w-4 h-4 text-gray-400 -ml-1 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
          <span class="text-sm font-medium">过去 7 天</span>
        </div>
        <!-- Add View Button -->
        <button class="bg-gray-900 text-gray-100 hover:bg-gray-800 px-4 py-2 rounded-lg text-sm font-medium shadow-sm flex items-center transition-colors">
          <svg class="fill-current w-4 h-4 mr-2" viewBox="0 0 16 16">
            <path d="M15 7H9V1c0-.6-.4-1-1-1S7 .4 7 1v6H1c-.6 0-1 .4-1 1s.4 1 1 1h6v6c0 .6.4 1 1 1s1-.4 1-1V9h6c.6 0 1-.4 1-1s-.4-1-1-1z" />
          </svg>
          导出报表
        </button>
      </div>
    </div>

    <!-- Cards Layout -->
    <div class="grid grid-cols-12 gap-6">

      <!-- ============================================== -->
      <!-- Top Row KPI Cards with Sparklines (Mosaic Style) -->
      <!-- ============================================== -->

      <!-- KPI Card 1 -->
      <div class="flex flex-col col-span-full sm:col-span-6 xl:col-span-3 bg-white shadow-sm rounded-2xl border border-gray-200 overflow-hidden relative">
        <div class="px-5 pt-5 pb-2 border-b border-transparent">
          <header class="flex justify-between items-start mb-2">
            <h2 class="text-lg font-semibold text-gray-800 tracking-tight">系统对话总量</h2>
            <!-- Menu Dot Icon -->
            <button class="text-gray-400 hover:text-gray-500 rounded-full transition-colors flex items-center justify-center -mr-2">
              <svg class="w-8 h-8 fill-current" viewBox="0 0 32 32">
                <circle cx="16" cy="16" r="2" />
                <circle cx="10" cy="16" r="2" />
                <circle cx="22" cy="16" r="2" />
              </svg>
            </button>
          </header>
          <div class="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">总对话数</div>
          <div class="flex items-start">
            <div class="text-3xl font-bold text-gray-800 mr-2">{{ kpiData.conversations }}</div>
            <div class="text-sm font-medium text-green-700 px-1.5 py-0.5 bg-green-500/20 rounded-full">+14%</div>
          </div>
        </div>
        <!-- Sparkline container (no padding) -->
        <div class="grow h-16 w-full -mt-2 -mb-2" ref="sparkChart1"></div>
      </div>

      <!-- KPI Card 2 -->
      <div class="flex flex-col col-span-full sm:col-span-6 xl:col-span-3 bg-white shadow-sm rounded-2xl border border-gray-200 overflow-hidden relative">
        <div class="px-5 pt-5 pb-2 border-b border-transparent">
          <header class="flex justify-between items-start mb-2">
            <h2 class="text-lg font-semibold text-gray-800 tracking-tight">人工接单率</h2>
            <button class="text-gray-400 hover:text-gray-500 rounded-full transition-colors flex items-center justify-center -mr-2">
              <svg class="w-8 h-8 fill-current" viewBox="0 0 32 32"><circle cx="16" cy="16" r="2" /><circle cx="10" cy="16" r="2" /><circle cx="22" cy="16" r="2" /></svg>
            </button>
          </header>
          <div class="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">干预频次</div>
          <div class="flex items-start">
            <div class="text-3xl font-bold text-gray-800 mr-2">{{ kpiData.humanRate }}%</div>
            <div class="text-sm font-medium text-amber-700 px-1.5 py-0.5 bg-amber-500/20 rounded-full">-3%</div>
          </div>
        </div>
        <div class="grow h-16 w-full -mt-2 -mb-2" ref="sparkChart2"></div>
      </div>

      <!-- KPI Card 3 -->
      <div class="flex flex-col col-span-full sm:col-span-6 xl:col-span-3 bg-white shadow-sm rounded-2xl border border-gray-200 overflow-hidden relative">
        <div class="px-5 pt-5 pb-2 border-b border-transparent">
          <header class="flex justify-between items-start mb-2">
            <h2 class="text-lg font-semibold text-gray-800 tracking-tight">AI 独立解决率</h2>
            <button class="text-gray-400 hover:text-gray-500 rounded-full transition-colors flex items-center justify-center -mr-2">
              <svg class="w-8 h-8 fill-current" viewBox="0 0 32 32"><circle cx="16" cy="16" r="2" /><circle cx="10" cy="16" r="2" /><circle cx="22" cy="16" r="2" /></svg>
            </button>
          </header>
          <div class="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">成功率</div>
          <div class="flex items-start">
            <div class="text-3xl font-bold text-gray-800 mr-2">{{ kpiData.aiRate }}%</div>
            <div class="text-sm font-medium text-green-700 px-1.5 py-0.5 bg-green-500/20 rounded-full">+8%</div>
          </div>
        </div>
        <div class="grow h-16 w-full -mt-2 -mb-2" ref="sparkChart3"></div>
      </div>

      <!-- KPI Card 4 -->
      <div class="flex flex-col col-span-full sm:col-span-6 xl:col-span-3 bg-white shadow-sm rounded-2xl border border-gray-200 overflow-hidden relative">
        <div class="px-5 pt-5 pb-2 border-b border-transparent">
          <header class="flex justify-between items-start mb-2">
            <h2 class="text-lg font-semibold text-gray-800 tracking-tight">意向转化率</h2>
            <button class="text-gray-400 hover:text-gray-500 rounded-full transition-colors flex items-center justify-center -mr-2">
              <svg class="w-8 h-8 fill-current" viewBox="0 0 32 32"><circle cx="16" cy="16" r="2" /><circle cx="10" cy="16" r="2" /><circle cx="22" cy="16" r="2" /></svg>
            </button>
          </header>
          <div class="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">成单转化</div>
          <div class="flex items-start">
            <div class="text-3xl font-bold text-gray-800 mr-2">{{ kpiData.successRate }}%</div>
            <div class="text-sm font-medium text-green-700 px-1.5 py-0.5 bg-green-500/20 rounded-full">+29%</div>
          </div>
        </div>
        <div class="grow h-16 w-full -mt-2 -mb-2" ref="sparkChart4"></div>
      </div>


      <!-- ============================================== -->
      <!-- Bottom Section: Large Charts (Direct VS Indirect Style & Real Time Value) -->
      <!-- ============================================== -->

      <!-- Big Line Data (Real Time Value Clone, but for Average Response Time) -->
      <div class="flex flex-col col-span-full xl:col-span-8 bg-white shadow-sm border border-gray-200 rounded-2xl">
        <header class="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 class="font-semibold text-gray-800">系统平均响应耗时 <span class="text-gray-400 font-normal ml-1 border border-gray-200 rounded-md text-[10px] px-1 shadow-sm">ms</span></h2>
        </header>
        <div class="p-5">
           <!-- Hero Metric for Real Time -->
           <div class="flex items-start mb-2">
             <div class="text-3xl font-bold text-gray-800 mr-2">{{ kpiData.responseTime }}ms</div>
             <div class="text-sm font-medium text-green-700 px-1.5 py-0.5 bg-green-500/20 rounded-full">+3.58%</div>
           </div>
           <!-- The large line chart -->
           <div class="grow h-[260px] w-full" ref="lineChartRef"></div>
        </div>
      </div>

      <!-- Big Bar Data (Direct vs Indirect Clone, mapped to AI vs Human Processed) -->
      <div class="flex flex-col col-span-full xl:col-span-4 bg-white shadow-sm border border-gray-200 rounded-2xl">
        <header class="px-5 py-4 border-b border-gray-100">
          <h2 class="font-semibold text-gray-800">每日会话量对比 (人工 vs AI)</h2>
        </header>
        <div class="p-5">
          <!-- Legend Header -->
          <div class="flex items-end mb-4 gap-6">
             <div class="flex items-center gap-2 whitespace-nowrap">
                <span class="w-3 h-3 rounded-full border-2 border-[#38bdf8] bg-transparent flex-shrink-0"></span>
                <span class="text-2xl font-bold text-gray-800 font-mono flex items-baseline gap-1">{{ kpiData.humanTotal }} <span class="text-sm font-normal text-gray-500">今日人工接管</span></span>
             </div>
             <div class="flex items-center gap-2 whitespace-nowrap">
                <span class="w-3 h-3 rounded-full border-2 border-[#818cf8] bg-transparent flex-shrink-0"></span>
                <span class="text-2xl font-bold text-gray-800 font-mono flex items-baseline gap-1">{{ kpiData.aiTotal }} <span class="text-sm font-normal text-gray-500">今日AI处理</span></span>
             </div>
          </div>
          <!-- Bar chart -->
          <div class="grow h-[260px] w-full" ref="barChartRef"></div>
        </div>
      </div>

      <!-- ============================================== -->
      <!-- Bottom Section: Marketing KPI & Sales Target     -->
      <!-- ============================================== -->
      <div class="col-span-full xl:col-span-8 flex flex-col gap-4 md:gap-6">
        <MarketingMetrics />
        <MonthlySalesChart />
      </div>
      <div class="col-span-full xl:col-span-4 flex flex-col">
        <MonthlyTargetChart />
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, shallowRef, watch, nextTick } from 'vue';
import * as echarts from 'echarts';
import { store } from '../store.js';
import { DEMO_MULTI_DAY } from '../demoData.js';
import MarketingMetrics from './MarketingMetrics.vue';
import MonthlySalesChart from './MonthlySalesChart.vue';
import MonthlyTargetChart from './MonthlyTargetChart.vue';

const isLoading = ref(true);

// Refs for Echarts DOM Containers
const sparkChart1 = ref(null);
const sparkChart2 = ref(null);
const sparkChart3 = ref(null);
const sparkChart4 = ref(null);
const barChartRef = ref(null);
const lineChartRef = ref(null);

const echartsInstances = shallowRef([]);

// Dummy data calculation for charts
const todayData = computed(() => DEMO_MULTI_DAY[DEMO_MULTI_DAY.length - 1] || {});

const calculateSum = (arr) => {
    if (!arr || !arr.length) return 0;
    return arr.reduce((a, b) => a + b, 0);
};

const calculateAvg = (arr) => {
    if (!arr || !arr.length) return 0;
    const items = arr.filter(x => x > 0);
    if (!items.length) return 0;
    return (items.reduce((a, b) => a + b, 0) / items.length);
};

const kpiData = computed(() => {
    const today = todayData.value;
    const sumConv = calculateSum(today.conversations) || 1; 
    const sumEsc = calculateSum(today.escalations);
    const sumConvsn = calculateSum(today.conversions);
    
    return {
        conversations: sumConv.toLocaleString(),
        humanRate: ((sumEsc / sumConv) * 100).toFixed(1),
        aiRate: Math.round(calculateAvg(today.aiRate)),
        successRate: ((sumConvsn / sumConv) * 100).toFixed(1),
        responseTime: (calculateAvg(today.responseTime) || 1.85).toFixed(2),
        humanTotal: sumEsc.toLocaleString(),
        aiTotal: (sumConv - sumEsc).toLocaleString()
    };
});

// Sparkline configuration identical to Mosaic
const initSparkline = (el, dataArr, colorStr) => {
    if (!el) return null;
    const chart = echarts.init(el);
    const mockData = dataArr || [12, 14, 13, 16, 15, 18, 17, 19, 21, 16, 14, 25]; // use demo array if empty
    
    // Add slightly randomized overlapping second line as shadow (like Mosaic lines)
    const mockDataBg = mockData.map(v => v * 0.8 + Math.random() * 5);

    const option = {
        grid: { top: 0, bottom: 0, left: -5, right: -5 },
        xAxis: { type: 'category', show: false, boundaryGap: false },
        yAxis: { type: 'value', show: false, min: 'dataMin' },
        series: [
            {
                type: 'line',
                data: mockData,
                smooth: 0.1,
                symbol: 'none',
                lineStyle: { width: 2, color: colorStr },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: `${colorStr}20` }, // 12% alpha
                        { offset: 1, color: `${colorStr}00` }
                    ])
                }
            },
            {
                type: 'line',
                data: mockDataBg,
                smooth: 0.1,
                symbol: 'none',
                lineStyle: { width: 2, color: '#9CA3AF40' } // gray subtle shadow line
            }
        ]
    };
    chart.setOption(option);
    return chart;
};

// Mosaic Specific "Direct VS Indirect" Stacked/Side by side Bar Chart
const initBarChart = (el) => {
    if (!el) return null;
    const chart = echarts.init(el);
    
    // Calculate daily totals for all days in the dataset
    const labels = DEMO_MULTI_DAY.map(d => d.label);
    const humanData = DEMO_MULTI_DAY.map(d => calculateSum(d.escalations));
    const aiData = DEMO_MULTI_DAY.map(d => calculateSum(d.conversations) - calculateSum(d.escalations));
    
    const option = {
        grid: { top: 20, right: 10, bottom: 20, left: 45 },
        tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#e5e7eb', textStyle: {color: '#374151'} },
        xAxis: {
            type: 'category',
            data: labels,
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: { color: '#6b7280', fontSize: 11, margin: 12 }
        },
        yAxis: {
            type: 'value',
            min: 0,
            splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
            axisLabel: { color: '#6b7280', fontSize: 11 }
        },
        series: [
            {
                name: '人工接管',
                type: 'bar',
                data: humanData,
                itemStyle: { color: '#38bdf8', borderRadius: [2, 2, 0, 0] }, // sky-400
                barWidth: '15%',
            },
            {
                name: 'AI独立处理',
                type: 'bar',
                data: aiData,
                itemStyle: { color: '#8b5cf6', borderRadius: [2, 2, 0, 0] }, // violet-500
                barWidth: '15%',
                barGap: '30%'
            }
        ]
    };
    chart.setOption(option);
    return chart;
};

// Mosaic Specific "Real Time Value" Line chart
const initLineChart = (el) => {
    if (!el) return null;
    const chart = echarts.init(el);
    
    const sampleData = todayData.value.responseTime;
    const dates = todayData.value.hours;
    
    const option = {
        grid: { top: 20, right: 10, bottom: 20, left: 30 },
        tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#e5e7eb', textStyle: {color: '#374151'} },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: dates,
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: { color: '#6b7280', fontSize: 11, margin: 12, showMaxLabel: true }
        },
        yAxis: {
            type: 'value',
            min: 0,
            splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
            axisLabel: { color: '#6b7280', fontSize: 11, formatter: '{value} s' }
        },
        series: [{
            name: '响应耗时',
            type: 'line',
            data: sampleData,
            smooth: 0.2, // slight smoothing
            symbol: 'none',
            lineStyle: { width: 2, color: '#8b5cf6' }, // violet-500
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#8b5cf620' }, // shadow alpha
                    { offset: 1, color: '#8b5cf600' }
                ])
            }
        }]
    };
    chart.setOption(option);
    return chart;
};

const mountCharts = () => {
    // Destroy existing instances to prevent memory leaks in dev
    echartsInstances.value.forEach(inst => inst?.dispose?.());
    
    // Use today's last 12 hours data logic for sparklines
    const tData = todayData.value;
    const s1 = tData.conversations.slice(12, 24);
    const s2 = tData.escalations.slice(12, 24);
    const s3 = tData.aiRate.slice(12, 24);
    const s4 = tData.conversions.slice(12, 24);

    // Create new maps based on precise Mosaic styling
    const insts = [
      initSparkline(sparkChart1.value, s1, '#8b5cf6'), // violet
      initSparkline(sparkChart2.value, s2, '#38bdf8'), // sky blue
      initSparkline(sparkChart3.value, s3, '#10b981'), // emerald
      initSparkline(sparkChart4.value, s4, '#f59e0b'), // amber
      initBarChart(barChartRef.value),
      initLineChart(lineChartRef.value)
    ].filter(Boolean);
    
    echartsInstances.value = insts;
};

onMounted(() => {
    isLoading.value = false;
    setTimeout(() => mountCharts(), 100);
    
    window.addEventListener('resize', () => {
        echartsInstances.value.forEach(chart => chart.resize());
    });
});

watch(() => store.activePanel, async (newVal) => {
    if (newVal === 'statistics') {
        await nextTick();
        mountCharts();
    }
});
</script>
