---
name: Design Token 规范
description: 企业级 SaaS 前端设计令牌(Design Tokens)规范，定义颜色、间距、圆角、阴影、字号等核心视觉变量，确保全局一致性。
---

# Design Token 规范

本 Skill 定义了项目前端 UI 的所有设计令牌（Design Tokens），所有组件的样式应基于这些变量构建，禁止使用硬编码的颜色、间距等值。

---

## 1. 色彩体系

### 品牌色 (Brand)
仅用于 CTA 按钮、Logo、关键交互高亮。**不可大面积使用**。

| Token | 值 | 用途 |
|-------|------|------|
| `--brand-500` | `#E02E24` | 主按钮背景 |
| `--brand-600` | `#C82520` | 主按钮 hover |
| `--brand-50` | `#FEF2F2` | 轻量提示背景 |
| `--brand-100` | `#FEE2E2` | 品牌色边框 |

### 中性色 (Neutral) — 界面主色调
大面积使用，构成界面骨架。

| Token | 值 | 用途 |
|-------|------|------|
| `--gray-50` | `#F8FAFC` | 页面背景 |
| `--gray-100` | `#F1F5F9` | 卡片背景、分隔区域 |
| `--gray-200` | `#E2E8F0` | 边框、分割线 |
| `--gray-300` | `#CBD5E1` | 禁用态文字 |
| `--gray-400` | `#94A3B8` | 次要文字、占位符 |
| `--gray-500` | `#64748B` | 二级文字 |
| `--gray-600` | `#475569` | 一级正文 |
| `--gray-700` | `#334155` | 标题文字 |
| `--gray-800` | `#1E293B` | 强调标题 |
| `--gray-900` | `#0F172A` | 最深文字 |

### 语义色 (Semantic) — 仅用于状态指示
不可用作装饰，仅通过小图标/文字/小色块表达状态。

| Token | 值 | 用途 |
|-------|------|------|
| `--success-500` | `#22C55E` | 成功/在线状态 |
| `--success-50` | `#F0FDF4` | 成功背景 |
| `--warning-500` | `#F59E0B` | 警告/等待状态 |
| `--warning-50` | `#FFFBEB` | 警告背景 |
| `--danger-500` | `#EF4444` | 错误/紧急状态 |
| `--danger-50` | `#FEF2F2` | 错误背景 |
| `--info-500` | `#3B82F6` | 信息/链接 |
| `--info-50` | `#EFF6FF` | 信息背景 |

---

## 2. 间距系统

基于 4px 基准，使用 Tailwind 的间距比例尺：

| Token | Tailwind Class | 像素 | 用途 |
|-------|---------------|------|------|
| `--space-1` | `p-1` | 4px | 紧凑内边距 |
| `--space-2` | `p-2` | 8px | 小元素间距 |
| `--space-3` | `p-3` | 12px | 默认内边距 |
| `--space-4` | `p-4` | 16px | 卡片内边距 |
| `--space-5` | `p-5` | 20px | 区域间距 |
| `--space-6` | `p-6` | 24px | 大区块间距（最大常用值） |

**规则**：
- 卡片内边距：`p-4`（16px），不超过 `p-5`
- 页面内边距：`p-4` 至 `p-6`
- 元素间距：`gap-2`(8px) 到 `gap-4`(16px)
- 禁止使用 `p-8`(32px) 及以上的内边距

---

## 3. 圆角系统

| Token | Tailwind Class | 像素 | 用途 |
|-------|---------------|------|------|
| `--radius-sm` | `rounded` | 4px | 小标签、Badge |
| `--radius-md` | `rounded-md` | 6px | 按钮、输入框 |
| `--radius-lg` | `rounded-lg` | 8px | 卡片、弹窗 |
| `--radius-xl` | `rounded-xl` | 12px | 大面板（谨慎使用） |
| `--radius-full` | `rounded-full` | 9999px | 头像、状态指示灯 |

**规则**：
- 卡片/面板：`rounded-lg`（8px）。**禁止** `rounded-2xl`(16px) 及以上
- 按钮：`rounded-md`（6px）
- 输入框：`rounded-md`（6px）
- 头像/Badge：`rounded-full`

---

## 4. 阴影系统

| Token | CSS 值 | 用途 |
|-------|--------|------|
| `--shadow-xs` | `0 1px 2px rgba(0,0,0,0.05)` | 输入框 |
| `--shadow-sm` | `0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)` | 卡片默认 |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)` | 卡片悬浮 |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05)` | 弹窗/下拉 |

**规则**：
- **禁止彩色阴影**（如 `shadow-red-500/25`、`shadow-purple-200`）
- **禁止辉光效果**（如 `shadow-[0_0_8px_rgba(168,85,247,0.4)]`）
- 卡片默认：`shadow-sm`，hover 态：`shadow-md`
- 弹窗/下拉菜单：`shadow-lg`

---

## 5. 字体与字号

### 字体栈
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
```

### 字号比例

| Token | Tailwind | 像素 | 用途 |
|-------|----------|------|------|
| `--text-xs` | `text-xs` | 12px | 辅助信息、时间戳 |
| `--text-sm` | `text-sm` | 14px | 正文、列表项 |
| `--text-base` | `text-base` | 16px | 大段正文 |
| `--text-lg` | `text-lg` | 18px | 卡片标题 |
| `--text-xl` | `text-xl` | 20px | 页面标题 |
| `--text-2xl` | `text-2xl` | 24px | 大数字指标 |

**规则**：
- 最小可用字号：`text-xs`(12px)。**禁止** `text-[10px]`、`text-[9px]`、`text-[11px]` 等自定义小字号
- 按钮文字：`text-sm`(14px)
- 数据指标数字：`text-2xl`(24px)，不超过 `text-3xl`

---

## 6. 动画与过渡

### 允许的过渡
```css
transition: all 0.15s ease;          /* 默认 hover 过渡 */
transition: all 0.2s ease;           /* 展开/收起 */
transition: all 0.3s ease;           /* 面板切换 */
```

### 禁止的动画
- ❌ `animate-pulse`（除状态指示灯外）
- ❌ `animate-bounce` / `animate-bounce-subtle`
- ❌ `animate-float` / `animate-float-slow`
- ❌ 持续旋转的装饰动画
- ❌ shimmer/辉光类效果
- ❌ `hover:scale-[1.02]` 卡片放大效果

### 允许的动画
- ✅ 状态指示灯的 `animate-pulse`（仅 `w-2 h-2` 小圆点）
- ✅ 加载中的 `animate-spin`（仅 spinner 图标）
- ✅ 页面切换的 `fade` / `slide` 过渡
- ✅ 下拉菜单的 `opacity` + `translateY` 进出动画
