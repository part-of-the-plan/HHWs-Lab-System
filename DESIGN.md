---
name: 实验室设备管理系统
description: 高校实验室设备全生命周期管理 — 安静、精确、可信赖的设备运营中台
colors:
  haze-blue:
    value: "#5b7fff"
    role: primary
  haze-blue-light:
    value: "#a3baff"
    role: primary-light
  haze-blue-pale:
    value: "#e8edff"
    role: primary-pale
  slate-night:
    value: "#1e293b"
    role: neutral-dark
  slate-mist:
    value: "#cbd5e1"
    role: neutral-mid
  success-green:
    value: "#67c23a"
    role: semantic
  warning-amber:
    value: "#e6a23c"
    role: semantic
  danger-red:
    value: "#f56c6c"
    role: semantic
typography:
  body:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'PingFang SC', 'Microsoft YaHei', sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  sm: "4px"
  md: "6px"
  lg: "8px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "20px"
  xl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.haze-blue}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "10px 20px"
  button-primary-hover:
    backgroundColor: "#4a6de0"
  input-field:
    backgroundColor: "#ffffff"
    textColor: "#303133"
    rounded: "{rounded.md}"
    padding: "8px 12px"
  card-container:
    backgroundColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  sidebar:
    backgroundColor: "{colors.slate-night}"
    textColor: "{colors.slate-mist}"
  stat-card:
    rounded: "{rounded.lg}"
    padding: "{spacing.lg}"
---

# Design System: 实验室设备管理系统

## 1. Overview

**Creative North Star: "精密实验室"**

精密实验室隐喻科研仪器的操作台面——每一个刻度都有意义，每一个控件都经过校准。界面如同实验室中的精密天平：不喧哗、不装饰、只呈现必要的测量结果。设计师的角色是"设备校准师"：确保信息精确对齐、层级清晰可辨、操作反馈即时但安静。

这是一个产品表面（Product Surface），设计服务于设备数据的理解和管理流程的效率。美学方向是现代企业级 B 端 SaaS 数据看板与 AIoT 智能设备运营平台的交汇：克制、清晰、低饱和的雾霾蓝灰系统。拒绝传统后台管理模板感、大面积蓝紫渐变、高饱和四色数据卡、霓虹赛博朋克、厚重阴影、卡片套卡片和过量玻璃拟态。

色调策略是 **Restrained**（克制型）：单一品牌色（雾霾蓝）承担 ≤10% 的界面面积，其余由中性色和色调分层完成。在数据密集型界面中，色彩的稀缺性本身就是信号——蓝色只出现在可操作元素和选中态上。

**Key Characteristics:**
- 信息优先，装饰让步：每个像素都为数据理解或操作效率服务
- 色调分层代替阴影：通过背景色深浅微妙区分层级，不使用 box-shadow 作为默认分层手段
- 安静的技术感：精确间距、克制色彩、清晰排版传递专业信任
- 扁平为默认，阴影仅为状态信号：hover、focus、下拉菜单才出现极淡阴影
- 温润触感：8px 圆角、宽松间距、柔和过渡——降低长时间使用的视觉疲劳
- 无弹跳动画、无持续晃动、无渐变文字、无侧边条纹边框

## 2. Colors

雾霾蓝灰调色板——在 slate 中性色的基础上叠加微弱的蓝紫色相（chroma < 0.02），使灰色带有"仪器面板"的工业感而非"网页默认灰"的温吞感。

### Primary

- **Haze Blue** (`#5b7fff`, oklch(62% 0.19 280)): 唯一的品牌强调色。仅用于主按钮、选中态、链接、活跃菜单项。严格控制在界面面积的 ≤10%。
- **Haze Blue Light** (`#a3baff`, oklch(75% 0.10 270)): Haze Blue 的浅色变体。用于 hover 背景、选中行底色。
- **Haze Blue Pale** (`#e8edff`, oklch(93% 0.02 260)): 品牌色最淡层级。用于表格斑马纹、信息提示区背景。

### Neutral

- **Slate Night** (`#1e293b`, oklch(27% 0.02 260)): 侧边栏底色。深灰蓝替代纯黑，保持对比但不刺眼。
- **Slate Mist** (`#cbd5e1`, oklch(80% 0.01 250)): 侧边栏文字色。与 Slate Night 背景对比度 8.7:1，满足 WCAG AAA。
- **Element Plus 默认中性色阶**: 正文 (`#303133`)、次文 (`#606266`)、占位 (`#909399`)、边框 (`#dcdfe6`)、页面底色 (`#f2f3f5`)。当前系统沿用 Element Plus 原生灰色体系。

### Semantic

- **Success Green** (`#67c23a`): 空闲、通过、正常状态。
- **Warning Amber** (`#e6a23c`): 借出中、待处理、需要注意。
- **Danger Red** (`#f56c6c`): 逾期、驳回、禁用、删除。不可单独依赖颜色——始终配合图标或文字标签。

### Named Rules

**The One Voice Rule.** Haze Blue 在任一屏幕上占据 ≤10% 的像素面积。它的稀缺性就是它的力量。当蓝色出现在太多地方时，它就失去了"这是可操作的"信号意义。

**The Semantic Silence Rule.** 语义色（绿/琥珀/红）仅用于状态指示，不用于大面积底色或装饰。Home 页四色统计卡片（当前实现）将在 redesign 中替换为色调分层方案。

**The Gray Is Not Neutral Rule.** 所有灰色（边框、背景、占位文字）都朝向品牌色相（260–280°）偏移 0.005–0.015 chroma。纯中性灰 `oklch(X 0 0)` 在品牌界面中显得"不属于这里"。

## 3. Typography

**Body Font:** system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'PingFang SC', 'Microsoft YaHei', sans-serif

**Character:** 系统字体栈——零额外加载、零 FOUT、各平台原生渲染最优。中英文混排场景下，PingFang SC 和 Microsoft YaHei 提供可靠的中文呈现。专业工具不需要个性字体；清晰度和加载性能优先。

### Hierarchy

- **Title** (600, 18px, 1.3): 页面主标题。侧边栏 Logo 区域使用。
- **Body** (400, 14px, 1.5): 全局正文。表格、表单、描述文字。最大行宽 75ch。
- **Label** (400, 12px, 1.4): 辅助信息、角色描述、次要标注。使用 `--el-text-color-secondary` (#606266)。
- **Stat Value** (700, 32px, 1.2): 统计卡片数值。仅在 Home 页使用。

### Named Rules

**The System Font Rule.** 不引入 Web Font。系统字体栈在各平台都是最优解——macOS 的 SF Pro 通过 system-ui 获得，Windows 的 Segoe UI 同样。管理工具需要的是零延迟和原生清晰度，而非品牌字体个性。

**The 14px Baseline Rule.** 正文 14px 是中文管理后台的事实标准：在信息密度和可读性之间取得平衡。12px 仅用于三级辅助信息，且必须满足 ≥4.5:1 对比度。

## 4. Elevation

**Philosophy: 扁平为默认，阴影为信号。**

精密实验室的工作台面是平的——试剂架通过高度（z-index）而非投影来区分。这个系统采用色调分层（Tonal Layering）作为默认层级表达方式：通过背景色深浅的微妙差异（ΔL ≥ 8%）区分页面底色、卡片表面和悬浮层。

阴影仅作为交互状态的信号出现——hover 时卡片微微浮起、下拉菜单需要从页面中分离、对话框需要遮罩层。不使用阴影作为静止状态的装饰。

### Shadow Vocabulary

- **Hover Lift** (`box-shadow: 0 2px 8px rgba(0,0,0,0.08)`): 可点击卡片的 hover 状态。极淡、极小——仅用于提示"此元素可以交互"。
- **Menu Drop** (`box-shadow: 0 4px 16px rgba(0,0,0,0.10)`): 下拉菜单、弹出面板。从页面表面分离。
- **Modal Overlay** (`box-shadow: 0 8px 32px rgba(0,0,0,0.12)`): 对话框、抽屉。最高层级阴影。

### Named Rules

**The Flat-By-Default Rule.** 界面在静止状态下不使用任何 box-shadow。卡片、表格、侧边栏——全部通过色调分层（背景色差异）和 1px 边框区分。阴影的出现 = 状态变化正在发生。

**The Whisper Rule.** 任何阴影的 blur 半径 ≥ 其 offset 的 4 倍。`offset: 2px → blur: ≥8px`。小 offset + 大 blur = 柔和的氛围感；小 offset + 小 blur = 2014 年的硬投影。

## 5. Components

### Buttons

**Character:** 温润但明确。8px 圆角使按钮看起来"可以触碰"，而非"需要点击"。过渡柔和（200ms ease-out）。

- **Shape:** 8px 圆角（当前 6px，redesign 计划改为 8px 以匹配温润触感）。
- **Primary:** Haze Blue 背景，白色文字，padding 10px 20px。Hover 加深至 `#4a6de0`，无阴影、无上浮。
- **Hover / Focus:** 背景色 200ms ease-out 过渡。Focus-visible 使用 2px Haze Blue Pale 外环，无偏移。
- **Ghost / Text:** 透明背景 + Haze Blue 文字。Hover 时背景变为 Haze Blue Pale。
- **Danger:** Danger Red 文字 + 1px Danger Red 边框。Hover 时填充 Danger Red 背景 + 白色文字。

### Chips / Tags

- **Status Tag:** 8px 圆角，2px 内边距。使用浅色背景 + 同色系深色文字（如空闲=绿底+绿字）。不使用纯色填充。
- **Type:** `el-tag` 的 `type` 属性映射到语义色。`effect="plain"` 为首选样式（浅底深字）。

### Cards

**Character:** 色调分层代替阴影和边框。卡片通过比页面底色亮 5-8% 的背景来"浮起"，而非通过投影。

- **Corner Style:** 8px 圆角（redesign 计划值）。
- **Background:** 白色 (`#ffffff`) 在浅灰页面底色 (`#f2f3f5`) 之上。
- **Shadow Strategy:** 静止状态无阴影。Hover 时（仅限可点击卡片）出现 Hover Lift 阴影。
- **Border:** 无边框。背景色差异足够区分卡片和页面。
- **Internal Padding:** 20px。

### Inputs / Fields

- **Style:** 1px `#dcdfe6` 边框，白色背景，6px 圆角。
- **Focus:** 边框色过渡到 Haze Blue，外发光 0 0 0 2px Haze Blue Pale。
- **Error:** 边框色过渡到 Danger Red，下方显示红色错误提示。
- **Disabled:** 灰色背景 (`#f5f7fa`)，降低文字对比度。

### Navigation

- **Sidebar:** Slate Night (`#1e293b`) 背景。菜单项文字 Slate Mist (`#cbd5e1`)。活跃项使用 Haze Blue 文字 + 左侧 2px Haze Blue 指示条（无背景色填充）。
- **Breadcrumb:** 页面顶栏下方，白色背景，12px 内边距。
- **Top Header:** 白色背景，60px 高度，底部 1px 边框分隔。

### Stat Card (当前实现; redesign 待替换)

- **Shape:** 8px 圆角，纯色背景（蓝/绿/琥珀/红各一）。
- **Content:** 白色文字，标签在上（14px, 0.9 opacity），数值在下（32px, bold）。
- **Interaction:** Hover 上浮 2px + Hover Lift 阴影。
- **Redesign 方向:** 替换为色调分层方案——统一白色或浅色背景，通过左侧色条或图标颜色表达类别，数值使用正文色而非白色。

## 6. Do's and Don'ts

### Do:
- **Do** 使用色调分层（背景色深浅差异 ≥8% L）区分界面层级，而非阴影
- **Do** 保持 Haze Blue 在每屏 ≤10% 的像素面积——稀缺即力量
- **Do** 为所有状态指示配合图标或文字标签，不单独依赖颜色
- **Do** 使用 8px 圆角作为组件默认值（redesign 目标），营造温润触感
- **Do** 所有过渡动画使用 200ms ease-out，支持 `prefers-reduced-motion: reduce`
- **Do** 保持正文行宽在 65–75ch 以内
- **Do** 侧边栏活跃菜单项使用蓝色文字 + 左侧指示条，不用背景色填充整行

### Don't:
- **Don't** 使用传统后台管理模板风格（AdminLTE、Ant Design Pro 默认风格等）
- **Don't** 使用大面积蓝紫渐变背景
- **Don't** 并列高饱和四色数据统计卡片（红/蓝/绿/黄）
- **Don't** 使用霓虹赛博朋克风格配色
- **Don't** 使用厚重阴影（box-shadow blur < offset×4）
- **Don't** 卡片内部再嵌套卡片（卡片套卡片）
- **Don't** 过量使用玻璃拟态（glassmorphism）
- **Don't** 使用弹跳动画或持续晃动动画
- **Don't** 使用 `border-left` 或 `border-right` >1px 作为彩色强调条
- **Don't** 使用渐变文字（`background-clip: text` + gradient）
- **Don't** 在每个区块上方放小型大写跟踪眉题（"ABOUT" / "PROCESS" 类 kicker）
- **Don't** 用 01/02/03 数字编号作为默认区块脚手架
- **Don't** 将阴影作为静止状态下的默认分层方式
- **Don't** 纯黑 (`#000`) 或纯中性灰 (`#888`, `#999`)——所有灰色朝向品牌色相偏移
