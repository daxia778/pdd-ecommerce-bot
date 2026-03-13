---
name: 组件样式指南
description: 将页面元素标准化为可复用的 UI 组件（如按钮、卡片、输入框、标签），规定它们的具体样式类(HTML/CSS/Tailwind)，保持统一的交互反馈。
---

# 组件样式指南

本指南定义了项目中常用 UI 组件的标准化实现，要求所有新页面及改造页面强制使用此类样式，避免过度设计。

## 1. 按钮 (Buttons)

每个按钮必须有明确的层级和统一高度，**禁止给所有按钮加渐变色和投影**。

### Primary 按钮（主操作 / Call to Action）
仅用于页面中最重要的单步操作，如提交、保存、发送。
```html
<button class="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
  主要操作
</button>
```

### Secondary 按钮（次操作 / 常规按钮）
用于大部分平级操作，如取消、刷新、导出。
```html
<button class="px-4 py-2 bg-white text-gray-700 text-sm font-medium rounded-md border border-gray-300 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors disabled:opacity-50">
  次要操作
</button>
```

### Ghost / Text 按钮（辅助链接 / 图标按钮）
```html
<button class="px-3 py-2 text-gray-600 text-sm font-medium hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors">
  辅助操作
</button>
```

## 2. 卡片 (Cards)

用于承载独立的业务信息模块（如统计图表、信息列表），**禁止过度包裹渐变框和弥散阴影**。

```html
<div class="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
  <!-- Card Header (可选) -->
  <div class="px-5 py-4 border-b border-gray-100 flex justify-between items-center">
    <h3 class="text-base font-semibold text-gray-800">模块标题</h3>
    <span class="text-xs text-gray-500">辅助操作区</span>
  </div>
  <!-- Card Body -->
  <div class="p-5">
    组件内容主体
  </div>
  <!-- Card Footer (可选) -->
  <div class="px-5 py-3 bg-gray-50 border-t border-gray-100">
    底部动作或备注
  </div>
</div>
```

## 3. 标签与微章 (Badges & Tags)

用于显示状态、分类或轻量级过滤。应采用纯色或极低浓度(10%透明度)底色，**禁止使用 `text-[8px]` 等不可读字号**。

### 状态 Badge
```html
<!-- 成功 / 正常 -->
<span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-green-50 text-green-700 border border-green-200">
  正常 / 已解决
</span>

<!-- 异常 / 需要注意 -->
<span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-red-50 text-red-700 border border-red-200">
  干预中 / 异常
</span>

<!-- 中性 / 分类 -->
<span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
  模拟器
</span>
```

## 4. 表单与输入 (Forms & Inputs)

提供纯净的输入体验。**不需要发光框**。

```html
<div class="space-y-1">
  <label class="block text-sm font-medium text-gray-700">表单标题</label>
  <div class="relative">
    <input 
      type="text" 
      class="block w-full px-3 py-2 sm:text-sm border border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500 transition-colors placeholder-gray-400" 
      placeholder="请输入内容..."
    />
  </div>
</div>
```

## 5. 空状态 (Empty States)

**不要过度设计庞大的渐变插画**，使用简洁的图标搭配结构清晰的文案。

```html
<div class="text-center py-12 px-6">
  <svg class="mx-auto h-12 w-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <!-- Icon path here -->
  </svg>
  <h3 class="mt-4 text-sm font-semibold text-gray-900">暂无数据</h3>
  <p class="mt-2 text-sm text-gray-500 max-w-sm mx-auto">
    目前还没有收到任何系统警报或干预请求，当有新警报时会在这里显示。
  </p>
  <div class="mt-6">
    <!-- 如果有初始操作按钮放在这里 (Primary Button) -->
  </div>
</div>
```

---

## 禁止使用的类（Banned Classes Checklist）
审查代码时，若包含以下模式之一，**均不符合本企业级样式要求**：
- `bg-gradient-to-*` （除了极少数大背景或图表修饰，禁止作为组件底色）
- `shadow-red-*` 或任何带有色值的投影
- `text-[XXpx]` 极小的自定义字号
- `scale-[X]` 对于悬浮放大的滥用
- `animate-*` 滥用动画效果，除了正常的 `spin` 和骨架屏加载
