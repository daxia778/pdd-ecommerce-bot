# PDD 电商 AI — 设计规范文档 v1.0

> 适用范围：pdd-e-commerce-bot 管理后台及所有前端页面

---

## 字体系统 (Typography)

**引入方式**
```html
<!-- 中文优先，英文备用 -->
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
  }
</style>
```

| 用途               | 大小       | 字重      | 颜色              |
|--------------------|-----------|-----------|------------------|
| 页面主标题 (h1)     | 1.875rem  | 700 Bold  | `#1f2937` (gray-800) |
| 区块标题 (h2/h3)   | 1.25rem   | 600       | `#1f2937`         |
| 正文文字            | 0.875rem  | 400       | `#374151` (gray-700) |
| 辅助/说明文字       | 0.75rem   | 400       | `#6b7280` (gray-500) |
| 数据大字 (KPI)      | 1.5rem    | 700 Bold  | 见颜色系统         |
| 表格文字            | 0.813rem  | 400       | `#374151`          |

---

## 颜色系统 (Color Palette)

### 主色 (Accent Colors)
| 语义      | Tailwind 类            | HEX       | 用途                    |
|-----------|------------------------|-----------|------------------------|
| 蓝-主色   | `blue-600`             | `#2563eb` | 交互按钮、选中状态、KPI |
| 绿-成功   | `green-500 / green-600` | `#22c55e / #16a34a` | 成功状态、OK标志 |
| 红-警告   | `red-500 / red-600`    | `#ef4444 / #dc2626` | 需处理事项、危险操作 |
| 橙-注意   | `orange-500`           | `#f97316` | 待审核、中间状态 |
| 紫-AI专用 | `purple-600`           | `#9333ea` | AI 标签、AI 回复 |
| 靛-队列   | `indigo-600`           | `#4f46e5` | 引擎标签、技术标签 |

### 背景 (Backgrounds)
| 用途           | 颜色                 |
|----------------|----------------------|
| 页面底色       | `#f3f4f6` (gray-100) |
| 卡片/区块     | `#ffffff` (white)    |
| 侧边栏         | `#1e293b` (slate-800)|
| 侧边栏激活项   | `#2563eb` (blue-600) |
| 表格行 Hover  | `#f9fafb` (gray-50)  |

### 边框 & 阴影
```css
/* 卡片阴影 */
box-shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);

/* 边框 */
border: 1px solid #e5e7eb; /* gray-200 */

/* 圆角 */
border-radius: 0.75rem; /* rounded-xl */
```

---

## 间距系统 (Spacing)

- 页面边距：`p-6` (1.5rem 24px)
- 卡片内边距：`p-5` (1.25rem 20px)
- 区块间距：`gap-6` (1.5rem)
- 表格行内边距：`px-6 py-4`

---

## 布局模式 (Layout Pattern)

```
┌────────────────┬──────────────────────────────────────────────┐
│                │  Header (页面标题 + 全局统计)                │
│   Sidebar      ├──────────────────────────────────────────────┤
│  240px 固定宽  │                                              │
│                │         Main Content Area                    │
│  导航项目：    │      (根据菜单切换不同 Panel)                │
│  • 监控大屏    │                                              │
│  • 人工干预池  │                                              │
│  • 生产流水线  │                                              │
│  • 知识库管理  │                                              │
│  • 系统配置    │                                              │
└────────────────┴──────────────────────────────────────────────┘
```

---

## 组件规范 (Components)

### 侧边栏导航项
```html
<!-- 普通状态 -->
<div class="sidebar-item">
  <span class="icon">🔵</span>
  <span class="label">菜单名</span>
</div>

<!-- 激活状态 -->
<div class="sidebar-item active">...</div>
```
- 高度：`h-11` (44px)
- 字号：`text-sm`
- 激活：`bg-blue-600 text-white rounded-lg`

### KPI 卡片
- 数据数字：`text-2xl font-bold`
- 标签文字：`text-sm text-gray-500`
- 容器：`bg-white p-3 rounded-lg shadow`

### 数据表格
- 表头背景：`bg-gray-50`
- 表头文字：`text-xs font-medium text-gray-500 uppercase`
- 行间分隔：`divide-y divide-gray-200`
- 行 Hover：`hover:bg-gray-50`

### 操作按钮
- 主操作（批准/提交）：`bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700`
- 危险操作（删除）：`text-red-500 hover:text-red-700`
- 次要操作（取消）：`bg-gray-200 text-gray-700 rounded hover:bg-gray-300`

### 状态徽章 (Badge)
```css
/* 成功/已完成 */
.badge-green { @apply px-2 py-0.5 bg-green-100 text-green-800 rounded-full text-xs font-semibold; }

/* 处理中/生成中 */
.badge-blue  { @apply px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full text-xs font-semibold; }

/* 警告/待处理 */
.badge-red   { @apply px-2 py-0.5 bg-red-100 text-red-800 rounded-full text-xs font-semibold; }

/* 注意/审核中 */
.badge-orange { @apply px-2 py-0.5 bg-orange-100 text-orange-800 rounded-full text-xs font-semibold; }
```

---

## 动效规范 (Animations)

- 过渡默认：`transition-colors duration-150`
- Hover 变色时：背景或文字颜色渐变 150ms
- 加载中（生成状态）：`animate-spin` SVG spinner
- 数据更新：轮询间隔 3 秒，无动画淡入

---

## 设计原则 (Design Principles)

1. **清晰优先**：信息层次分明，KPI 大数字一眼可读
2. **低噪音**：背景灰白，仅用颜色标记状态（非装饰）
3. **状态驱动**：用颜色+图标传达系统状态（绿=正常，红=需处理，橙=待审核）
4. **操作集中**：相关操作挂载在数据行旁，不弹窗，减少跳转
5. **一致的侧边栏模式**：所有功能页共用同一侧边栏，导航状态常驻

---

*最后更新：2026-03-05*
