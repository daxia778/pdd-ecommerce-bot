---
name: SaaS 布局模板
description: 定义了标准 SaaS 后台的基础页面骨架，包括 Sidebar（侧边栏）、Header（顶导）和 Main Content（主内容区）的尺寸比例及交互规范。
---

# SaaS 布局模板 (Layout Guidelines)

本指南确保应用有一个结构化、专业且一致的 SaaS 管理后台布局。

## 1. 结构概览 (The Shell)

整个应用应该包裹在一个满屏且无法滚动的容器中（`h-screen overflow-hidden`）。主内容区独立控制滚动，不要依赖 global body scrolling。

```html
<!-- App.vue 骨架 -->
<template>
  <div class="flex h-screen w-full bg-gray-50 overflow-hidden text-gray-800 font-sans">
    
    <!-- Sidebar -->
    <Sidebar class="w-64 flex-shrink-0" />
    
    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden relative z-0">
      
      <!-- Top Header -->
      <Header class="h-16 flex-shrink-0" />
      
      <!-- Page Content: 可滚动的区域 -->
      <main class="flex-1 overflow-y-auto outline-none" tabindex="-1">
         <div class="p-6 md:p-8 max-w-7xl mx-auto w-full">
            <!-- 各个 Panel 实现在此呈现 -->
         </div>
      </main>

    </div>

  </div>
</template>
```

## 2. 侧边栏 (Sidebar) 规范

侧边栏应该是工具菜单的主要汇集处，不承载过度复杂的装饰。

### 原则
1. **尺寸控制**：默认宽度 `w-64` (256px)。如果允许折叠，折叠态为 `w-16` (64px) 或 `w-20` (80px)。禁止 `w-72` 等超宽侧边栏。
2. **背景色**：使用标准的 `#1E293B`（深色侧边栏，对比更清晰）或纯白 `bg-white` 配合细边框。
3. **菜单分组**：菜单应该有清晰的分类 (`text-xs` uppercase 标题)，如 `WORKSPACE`、`TOOLS`、`SETTINGS`。
4. **禁止项**：禁止添加各种发光的装饰、纹理背景或巨大的圆角。

### 示例
```html
<aside class="w-64 bg-white border-r border-gray-200 flex flex-col h-full overflow-y-auto">
  <!-- Logo -->
  <div class="h-16 flex items-center px-6 border-b border-gray-100 shrink-0">
     <div class="w-8 h-8 bg-red-600 rounded-md text-white flex items-center justify-center font-bold">PD</div>
     <span class="ml-3 font-semibold text-lg text-gray-900 tracking-tight">客服工作台</span>
  </div>
  
  <!-- Navigation Group -->
  <nav class="flex-1 px-4 py-6 space-y-8">
    <div>
       <h3 class="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">核心运营</h3>
       <div class="space-y-1">
          <a href="#" class="group flex items-center px-3 py-2 text-sm font-medium rounded-md bg-red-50 text-red-700">监控大屏</a>
          <a href="#" class="group flex items-center px-3 py-2 text-sm font-medium rounded-md text-gray-700 hover:text-gray-900 hover:bg-gray-50">人工干预</a>
       </div>
    </div>
  </nav>
</aside>
```

## 3. 顶导 (Header) 规范

用于标题定位和全局操作（用户菜单、通知、搜索）。

### 原则
1. **高度固定**：始终保持 `h-16` (64px) 或 `h-14` (56px)。
2. **主要构成**：
   - 左侧：页面标题（Page Title）或面包屑（Breadcrumbs），而不仅仅是当前选中的面板名。应提供完整的上下文。
   - 右侧：全局搜索栏（如果适用）、通知中心、用户偏好或设置菜单。
3. **分离状态指引**：诸如“处理数”、“并发数”等指标，如果并非时刻需要重点提醒的，建议在 Panel 内部去呈现，不要塞满整个 Header，容易造成视觉焦虑。

## 4. 主干板面 (Main Panel) 规范

主板面应当为宽广的工作白板留有余地，限制过密和臃肿。

### 原则
1. **统一的内边距**：`p-6`，如果是更大的屏幕（如宽于 `1280px`），可以是 `md:p-8`。
2. **限制最大宽度**：如果不希望超宽屏下卡片被拉得非常扁长，给内容主包裹层加上 `max-w-7xl mx-auto`（即最高 1280px）是一种典型的安全做法，如果业务本身适合平铺拉伸，也可以保持 `w-full`。
3. **两栏 / 多栏划分**：比如 Monitor Panel：
   - 使用典型的侧重比列，如左侧导航或者 List 采用 `w-80` 定宽，右侧详单自适应 `flex-1`。左侧卡片化或通过明确的内底色做屏障，以区分视差逻辑。

## 5. Mobile (响应式) 的妥协
- SaaS 优先照顾 Desktop。当进入移动端（或屏幕很窄的情况）: `w-full overflow-x-hidden` 应该被启用。
- 侧边栏转为 Drawer(抽屉)，顶部出现汉堡菜单按钮(Hamburger Menu)。
- 界面内各分屏自动按 Stack 顺序排列，由行（Flex Row）转换成列（Flex Col）。
