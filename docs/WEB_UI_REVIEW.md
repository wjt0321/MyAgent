# MyAgent Web UI 完整审查报告

> **审查日期**: 2026-04-27
> **审查范围**: `src/myagent/web/` 全部文件
> **审查文件**: `index.html` (700行) · `app.js` (3317行) · `style.css` (3555行) · `server.py` (967行) · `engine_manager.py` (393行) · `session.py` (148行) · `auth.py` (138行) · `test_web.py` (528行)

---

## 第一部分：BUG 清单

### 🔴 P0 — 功能异常（必须修复）

| # | 文件 | 行号 | 问题 | 影响 |
|---|------|------|------|------|
| B01 | `index.html` | 146 | `session-control-bar` 缺少 `</div>` 闭合标签，导致 `session-summary-line`、`context-help-strip` 被意外嵌套 | Header 布局错乱，移动端尤其明显 |
| B02 | `app.js` | 3034 | 调用 `this.previewFile(path)` 但方法不存在，应为 `this.showFilePreview(path, name)` | 代码库搜索结果点击后报 TypeError |
| B03 | `app.js` | 1554-1574 | `attemptReconnect()` 方法存在但从未被调用（`ws.onclose` 中所有分支都直接 return） | WebSocket 断线后无法自动重连 |

### 🟡 P1 — 功能缺陷（需要修复）

| # | 文件 | 行号 | 问题 |
|---|------|------|------|
| B04 | `app.js` | 1348-1361 | `startRenameSession` 仅修改前端内存，未调用 `PATCH /api/sessions/:id` 持久化 |
| B05 | `app.js` | 1457, 3167 | `createSession` 硬编码 `model: 'glm-4.7'`；`importSession` 硬编码 `model: 'glm-4'`。model-select 列表中无此选项 |
| B06 | `app.js` | 1671-1679 | Slash command 走 `executeSlashCommand` 后消息已被 `addMessage` 显示并清空输入框，但不经过 WebSocket 发送 |
| B07 | `app.js` | 2838-2843 | `renderMemoryList` 中 `mem.name`、`mem.description` 未 `escapeHtml`，存在 XSS |
| B08 | `app.js` | 1778  | `showPermissionModal` 中 `data.arguments` 的 key/value 直接拼 innerHTML，XSS 风险 |
| B09 | `app.js` | 1052-1054 | `renderWorkspace` 中 `mem.filename`、`mem.name`、`mem.description` 未转义 |
| B10 | `app.js` | 1790-1791 | permission modal 用 `onclick="window.myAgentApp.handlePermission(...)"` 依赖全局变量名 |
| B11 | `style.css` | 3401-3476 | 多处使用 `--border-color`、`--surface-2` 等**未定义的 CSS 变量**（应为 `--border-default`、`--bg-secondary`） |

### 🟢 P2 — 体验问题

| # | 文件 | 行号 | 问题 |
|---|------|------|------|
| B12 | `app.js` | 780-786 | 搜索结果 `scrollIntoView` 对每个匹配项调用，最终停留在最后一个 |
| B13 | `app.js` | 1352 | `startRenameSession` 使用原生 `prompt()` 弹窗，与 Workbench 风格不符 |
| B14 | `auth.py` | 109 | 密码用 `hashlib.sha256` 无 salt，不安全 |
| B15 | `auth.py` | 50 | `datetime.utcnow()` 在 Python 3.12 已弃用 |

---

## 第二部分：UI/UX 设计审查

### 2.1 当前设计基础评估

**已有的好基础：**
- CSS 变量 (Design Token) 体系完整：颜色、圆角、过渡、阴影等 token 齐全
- Dark/Light 双主题 + Auto 跟随系统
- Glassmorphism 风格的 sidebar 和 header（`backdrop-filter: blur`）
- 消息气泡有渐变背景、入场动画、代码复制按钮
- Command Palette（Ctrl+K）快捷操作
- 工具卡片有状态芯片（pending/success/error）和 collapsible 详情

**核心问题：**

#### 问题 1：Header 信息密度过高、布局混乱

当前 Header 塞入了：mobile-view-chip、session-status-chip、agent-badge、model-badge、model-selector（含 80+ 个 option 的 select）、session-summary-line、context-help-strip、token-display、agent-selector、search-toggle、settings-btn、command-palette-btn。

**结果**：Header 在桌面端看起来像一排密集的控件工具栏，在移动端因 flex-wrap 导致 header 高度不可控。缺乏视觉层级。

#### 问题 2：Welcome Page 信息过载

Welcome Page 一次展示了：Hero 区域、3 步 Quickstart、3 张 Positioning 卡片、3 张 Demo Path 卡片、4 张推荐动作卡片、最近会话列表、帮助提示列表、3 张文档入口卡片。总计 **20+ 个卡片/区块**。

**结果**：首次进入的用户被大量信息淹没，无法快速找到关键入口。

#### 问题 3：侧栏导航功能堆叠

Sidebar 同时承载：品牌标识、新建会话按钮、Workbench 5 个导航入口（聊天/任务/文件/Workspace/团队）、会话列表、文件树、Task Panel、Team Panel、连接状态、设置入口。

**结果**：侧栏内容很长，需要大量滚动。Workbench Nav 按钮占据过多空间。

#### 问题 4：消息区域与详情侧栏的交互割裂

点击工具卡片会更新右侧详情侧栏，但详情侧栏在桌面端是 `position: fixed` 的 overlay 面板，会遮挡消息区域。缺少 split-view 或 drawer 的平滑过渡。

#### 问题 5：CSS 中的设计不一致

- task 相关组件（第 3398-3478 行）使用了 `--border-color`、`--surface-2` 等未定义变量，与主设计系统脱节
- task 按钮（`task-cancel-btn`、`task-retry-btn`、`task-restore-btn`）没有使用通用按钮 class（`btn-primary`、`btn-ghost` 等）
- `task-review-card` 的 `border-radius: 14px` 与全局 `--radius-lg: 14px` 一致但没有使用变量

#### 问题 6：缺乏状态反馈与微交互

- 没有骨架屏 (skeleton)：加载会话列表、文件树时无 loading 状态
- 消息发送后只有 `opacity: 0.5` 的按钮禁用，缺少发送中动画
- 导航切换视图时没有过渡动画，直接 `display: none/flex` 切换
- Agent/Model 切换没有 Toast 提示

#### 问题 7：移动端适配不完整

- Header 中 `padding-left: 58px` 在 768px 断点被覆盖但逻辑不清晰
- 详情侧栏在移动端占满 100% 宽度但没有返回手势
- `session-status-chip` 在 <=768px 时 `display: none`，用户无法看到连接状态
- Workbench Nav 在移动端横向滚动，但没有指示器

### 2.2 设计对标：OpenAI Codex 界面

用户明确要求 UI 趋近于 **OpenAI Codex** 的界面风格。以下是 Codex 的核心设计特征与 MyAgent 现状的差距分析：

| Codex 设计特征 | 具体表现 | MyAgent 现状 | 差距 |
|:---|:---|:---|:---:|
| **Thread 管理范式** | 左侧 sidebar 以 thread 列表为核心，每个 thread 是一个独立上下文的任务线程，支持并行管理多个 agent 任务 | 已有 session 列表，但 session 等同于聊天对话，缺乏"任务线程"的语义 | 中 |
| **极简克制的 Header** | Header 几乎为空白，仅显示 thread 标题 + 极少量状态信息，无多余控件 | Header 塞满了 12+ 个控件元素 | 大 |
| **Summary Pane（计划摘要面板）** | 右侧专用面板展示 agent 的当前计划、修改的文件列表、测试结果等；强调可追溯的透明性 | 有 Detail Sidebar 但只展示工具调用详情，不展示 agent 计划/思路 | 大 |
| **Visual Diff + File Tree** | 实时展示 agent 正在修改的文件树和代码变更 diff，用户可"看到"文件被写入 | 有文件树浏览但无 diff 视图，无法观察 agent 的文件操作过程 | 大 |
| **Approval Gates（审批门控）** | 关键操作（代码提交、文件删除等）有明确的 approve/deny 界面，强调 human-in-the-loop | 有 Permission Modal 但设计粗糙、不够醒目 | 中 |
| **Context Window 指示器** | 可视化显示当前 context 使用量（圆形进度条或 token 计数） | 有 token-display 但默认隐藏 (`display:none`) | 中 |
| **Barely-There UI（极简动态布局）** | 界面干净克制，用微妙的动画暗示 agent 状态（thinking/executing），而非堆叠信息 | 有动画基础但 Welcome Page 信息过载，缺乏"呼吸感" | 大 |
| **项目总览 Dashboard** | 支持查看多个 thread 的全局进度和状态 | 无全局视图 | 中 |

### 2.3 设计改进方向

| 维度 | 改进建议 |
|------|---------|
| **整体风格** | 向 Codex「Barely-There UI」靠拢：大留白、克制的信息密度、用动画而非文字传达状态 |
| **信息架构** | 精简 Header（趋近 Codex 的极简 Header），把模型/Agent 选择移入设置或命令面板 |
| **左侧 Sidebar** | 改造为 Codex 风格的 Thread 列表（而非 Workbench Nav 堆叠），每个 session 展示为 thread card |
| **右侧 Summary Pane** | 新增持久化的 Summary Pane，展示 agent 计划、文件变更 diff、执行进度 |
| **Welcome Page** | 精简为 Codex 风格：一个输入框 + 最近 thread 列表，不展示产品文档内容 |
| **消息体验** | 增加 skeleton loading、发送中动画、流式渲染进度条 |
| **视图过渡** | 添加 fade/slide 过渡动画 |
| **Toast 通知** | 统一用 toast 替代 `alert()`、`addMessage('assistant', ...)` |
| **Approval Gates** | 重新设计 Permission Modal，使其更醒目、更符合 Codex 的 approve/deny 风格 |
| **Context 指示器** | 默认显示 token 使用进度条/环形图，帮助用户感知 context 容量 |
| **组件复用** | 统一按钮系统，修复未定义 CSS 变量 |

---

## 第三部分：有序迭代 Plan

> 每个 Step 是一个**独立可交付**的迭代单元，完成后可直接看到效果。建议按编号顺序执行。

### Step 01 — 修复 P0 HTML/JS BUG

**目标**：消除功能崩溃级别的问题
**改动文件**：`index.html`、`app.js`

- [ ] 1.1 在 `index.html` 第 282 行后加 `</div>` 闭合 `session-control-bar`
- [ ] 1.2 将 `app.js` 第 3034 行 `this.previewFile(path)` 改为 `this.showFilePreview(path, path.split('/').pop())`
- [ ] 1.3 在 `app.js` `ws.onclose` 中，对非致命 close code（非 1000/1005/1006/1011）调用 `this.attemptReconnect(sessionId)`，并在 1006/1011 时做一次延迟重试

**验证**：打开浏览器 DevTools Console，分别测试：(1) 页面加载无报错；(2) 代码库搜索结果可正常点击预览；(3) 手动关闭 WebSocket 后观察是否尝试重连

---

### Step 02 — 修复 CSS 未定义变量 + 统一按钮系统

**目标**：消除 CSS 渲染异常
**改动文件**：`style.css`

- [ ] 2.1 全局搜索 `--border-color` 替换为 `--border-default`
- [ ] 2.2 全局搜索 `--surface-2` 替换为 `--bg-secondary`
- [ ] 2.3 将 `task-cancel-btn`、`task-retry-btn`、`task-restore-btn`、`task-empty-primary` 改为复用 `btn-ghost`/`btn-primary`/`btn-outline` class
- [ ] 2.4 将硬编码的 `border-radius: 14px`、`border-radius: 12px`、`border-radius: 10px` 改为 `var(--radius-lg)` 或 `var(--radius-md)`

**验证**：浏览器中切换 Dark/Light 主题，检查 Task 区域的按钮和卡片样式是否正常

---

### Step 03 — 修复 XSS 漏洞 + 安全问题

**目标**：消除所有 innerHTML 注入风险
**改动文件**：`app.js`、`auth.py`

- [ ] 3.1 `renderMemoryList`：对 `mem.name`、`mem.description` 和 `data-name` 属性调用 `escapeHtml()`
- [ ] 3.2 `showPermissionModal`：对 `data.arguments` 的 key/value 调用 `escapeHtml()`
- [ ] 3.3 `renderWorkspace`：对 `mem.filename`、`mem.name`、`mem.description` 调用 `escapeHtml()`
- [ ] 3.4 `showPermissionModal` 改用 `addEventListener` 替代 `onclick="window.myAgentApp..."`
- [ ] 3.5 `auth.py` 将 `hashlib.sha256` 改为 `hashlib.pbkdf2_hmac('sha256', password, salt, 100000)`，附带随机 salt
- [ ] 3.6 `auth.py` 将 `datetime.utcnow()` 改为 `datetime.now(timezone.utc)`

**验证**：在记忆名称中输入 `<img src=x onerror=alert(1)>` 测试 XSS 是否被拦截；旧密码仍可验证

---

### Step 04 — 修复数据一致性问题

**目标**：前端操作能正确持久化
**改动文件**：`app.js`

- [ ] 4.1 `startRenameSession`：重命名后调用 `PATCH /api/sessions/:id` 持久化
- [ ] 4.2 `createSession`：读取 `this.modelSelect.value` 作为 model 参数，而非硬编码
- [ ] 4.3 `importSession`：同样读取当前选择的 model
- [ ] 4.4 `startRenameSession`：将 `prompt()` 替换为 inline 编辑模式（类似 `startEditMessage` 的实现方式）

**验证**：新建会话 -> 检查 model 是否与下拉框一致；重命名会话 -> 刷新页面检查是否保留

---

### Step 05 — 精简 Header 布局（对标 Codex）

**目标**：向 Codex 极简 Header 靠拢——Header 只做状态展示，不做控件操作
**改动文件**：`index.html`、`style.css`、`app.js`
**设计参考**：Codex 的 Header 仅展示 thread 标题 + 连接状态

- [ ] 5.1 将 `model-select`（80+ option 的大下拉）从 Header 移入 Command Palette 命令（`Ctrl+K` -> 输入 model）
- [ ] 5.2 将 `agent-select` 从 Header 移入 Settings Modal
- [ ] 5.3 Header 精简为只保留：连接状态指示灯 + thread 标题（当前 agent）+ model 标签（只读）+ token 环形进度
- [ ] 5.4 删除 `context-help-strip`（移入 Welcome Page）
- [ ] 5.5 删除 `session-summary-line`（信息整合到 sidebar 的 session card 中）
- [ ] 5.6 调整 `chat-header` CSS：`height: 48px`，内容单行，大量留白形成 Codex 的「呼吸感」
- [ ] 5.7 Header 右侧只保留：搜索图标 + 命令面板图标 + 设置图标

**验证**：对比 Codex 截图检查 Header 是否达到类似的简洁程度

---

### Step 06 — 重构 Welcome Page（对标 Codex）

**目标**：模仿 Codex 的极简首页——一个输入框 + 最近线程
**改动文件**：`app.js`（`renderWelcomeLanding` 方法）、`style.css`
**设计参考**：Codex 首页核心是一个居中的大输入框，下面是最近的 thread 列表

- [ ] 6.1 Welcome Page 简化为两区：居中的 Hero 输入区域（含 brand + 一句话 slogan + 大型输入框）+ 最近会话 thread 列表
- [ ] 6.2 删除 Positioning 卡片、Demo Path 卡片、文档入口卡片（移入 Settings -> 关于）
- [ ] 6.3 大型输入框可直接创建新 thread 并发送第一条消息（合并"新建会话"和"发送消息"两步操作）
- [ ] 6.4 最近会话以 Codex 风格的 thread card 展示：标题 + 时间 + 最后消息摘要
- [ ] 6.5 Quickstart 步骤只在检测到未配置 API Key 时以 banner 形式展示，而非占据主区域
- [ ] 6.6 入场动画：Hero 区域 `fadeInUp`（0.3s），thread 列表 stagger 延迟依次出现
- [ ] 6.7 整体大量留白，背景使用当前的 radial-gradient cyber 效果增加质感

**验证**：启动 Web UI，与 Codex 首页对比，检查信息密度和视觉节奏

---

### Step 07 — 重构侧栏为 Codex 风格 Thread 列表

**目标**：侧栏像 Codex 一样只做 thread 管理，干净纯粹
**改动文件**：`index.html`、`style.css`、`app.js`
**设计参考**：Codex 左侧 sidebar = Thread 列表 + 新建 Thread 按钮，无其他内容

- [ ] 7.1 删除侧栏中的 Workbench Nav 按钮（聊天/任务/文件/Workspace/团队）
- [ ] 7.2 将 Workbench 视图切换改为主内容区顶部的轻量 tab bar（icon + label 单行横向）
- [ ] 7.3 侧栏精简为三层：品牌标识 -> 新建 Thread 按钮 -> Thread（会话）列表
- [ ] 7.4 Thread 列表中每个 session card 展示：标题、agent 类型图标、最后消息时间、进行中的 task 状态指示器
- [ ] 7.5 增加 thread 分组：「进行中」和「历史」
- [ ] 7.6 底部只保留连接状态 + 设置按钮
- [ ] 7.7 移动端侧栏使用 Codex 风格的半透明 overlay + slide-in 动画

**验证**：对比 Codex 的侧栏，检查布局和信息层级是否一致

---

### Step 08 — 添加 Toast 通知系统

**目标**：替代 `alert()` 和消息流中的系统通知
**改动文件**：`app.js`、`style.css`、`index.html`

- [ ] 8.1 实现一个 `showToast(message, type, duration)` 方法（type: success/error/info/warning）
- [ ] 8.2 Toast 样式：固定在右上角，`fadeInDown` 入场，自动消失
- [ ] 8.3 替换所有 `alert()` 调用为 `showToast()`（约 8 处）
- [ ] 8.4 替换所有非对话性质的 `addMessage('assistant', '设置已保存')` 为 `showToast()`
- [ ] 8.5 Agent/Model 切换成功、保存设置等场景使用 Toast 而不是在聊天中插入消息

**验证**：保存设置、切换 Agent、删除记忆等操作确认 Toast 正常弹出

---

### Step 09 — 添加骨架屏与加载状态

**目标**：消除页面加载时的空白感
**改动文件**：`app.js`、`style.css`

- [ ] 9.1 定义 `.skeleton` CSS 类（条形闪烁动画）
- [ ] 9.2 `loadSessions` 加载中时在会话列表显示 3-5 条 skeleton 占位
- [ ] 9.3 `loadFileTree` 加载中时在文件树显示 skeleton 占位
- [ ] 9.4 `loadCurrentTask` 加载中时在任务面板显示 skeleton
- [ ] 9.5 发送按钮在 `isSending` 时显示旋转动画（替代 opacity 变化）

**验证**：清空缓存刷新页面，观察加载过程中是否有 skeleton 闪烁

---

### Step 10 — 视图过渡动画

**目标**：Workbench 视图切换有动态感
**改动文件**：`style.css`、`app.js`

- [ ] 10.1 给 `.workbench-view` 添加 `fade + slide` 过渡（CSS animation 或 `classList` 切换）
- [ ] 10.2 侧栏展开/收起改为 `transform + opacity` 动画
- [ ] 10.3 会话切换时消息区域添加 `fadeIn` 动画

**验证**：在聊天/任务/文件/Workspace/团队之间切换，确认过渡流畅

---

### Step 11 — 搜索体验优化

**目标**：搜索功能可用性提升
**改动文件**：`app.js`、`style.css`

- [ ] 11.1 `performSearch` 只对第一个匹配项 `scrollIntoView`
- [ ] 11.2 搜索栏增加匹配计数显示（如 "3/12"）
- [ ] 11.3 添加"上一个/下一个"导航按钮或快捷键（Enter/Shift+Enter）
- [ ] 11.4 高亮匹配文本（在 `.content` 中用 `<mark>` 包裹）

**验证**：搜索一个关键词，确认滚动到第一个结果，计数正确，可上下导航

---

### Step 12 — 右侧 Summary Pane（对标 Codex）

**目标**：将详情侧栏改造为 Codex 风格的 Summary Pane，展示 agent 的计划、文件变更和执行进度
**改动文件**：`index.html`、`style.css`、`app.js`
**设计参考**：Codex 右侧 Summary Pane 展示 agent plan、修改的文件列表、diff 预览、测试结果

- [ ] 12.1 桌面端将 Detail Sidebar 改为常驻的 split-pane（非 overlay），与消息区域并排
- [ ] 12.2 添加宽度可拖拽调整的 resize handle（默认 380px，最小 300px，最大 50%）
- [ ] 12.3 Summary Pane 分为多个 section：
  - **Agent 状态**：当前正在做什么（thinking / coding / reviewing），有呼吸灯动画
  - **计划概览**：展示 task plan 的步骤列表和进度
  - **文件变更**：展示本次对话中 agent 修改/创建/删除的文件列表（类似 Git status）
  - **工具调用详情**：点击消息中的工具卡片后展示详细内容
- [ ] 12.4 无内容时 Summary Pane 显示空状态提示（"开始对话后，agent 的计划和文件变更将在此显示"）
- [ ] 12.5 移动端保持全屏 sheet 模式，增加顶部返回/关闭按钮

**验证**：发送一条消息后，检查 Summary Pane 是否实时更新 agent 状态和文件变更

---

### Step 13 — 模型列表动态化

**目标**：消除 HTML 中 80+ 行硬编码的 model option
**改动文件**：`server.py`、`app.js`、`index.html`

- [ ] 13.1 后端新增 `GET /api/models` 接口，返回可用模型列表（读取 `gateway.yaml`）
- [ ] 13.2 前端在 `constructor` 中调用 API 动态填充 model-select
- [ ] 13.3 删除 `index.html` 中所有 `<optgroup>` 硬编码
- [ ] 13.4 Settings Modal 或 Command Palette 中可切换模型

**验证**：确认模型下拉列表内容来自后端配置；新增配置后刷新即可看到

---

### Step 14 — 前端 `app.js` 模块化拆分

**目标**：3300 行单文件拆分为可维护的模块
**改动文件**：`app.js` -> 多个文件

- [ ] 14.1 拆分为以下模块：
  - `theme.js` — 主题切换逻辑
  - `websocket.js` — WebSocket 连接和重连
  - `session.js` — 会话 CRUD 和渲染
  - `message.js` — 消息渲染、流式更新、编辑
  - `task.js` — 任务创建、审批、轮询
  - `workspace.js` — 文件树、记忆、代码库
  - `ui.js` — 命令面板、Toast、Modal 等 UI 组件
  - `app.js` — 入口文件，组合各模块
- [ ] 14.2 使用 ES Module (`import`/`export`) 语法
- [ ] 14.3 `index.html` 中改为 `<script type="module" src="app.js">`

**验证**：所有功能正常工作（会话管理、聊天、任务流、文件预览等）

---

### Step 15 — 前端 E2E 测试

**目标**：确保 UI 交互的回归安全
**改动文件**：新增测试文件

- [ ] 15.1 选择 Playwright 作为测试框架
- [ ] 15.2 核心测试场景：
  - 创建会话 -> 发送消息 -> 验证消息出现
  - 切换视图（聊天/任务/文件/Workspace/团队）
  - 打开/关闭设置面板
  - Command Palette 搜索和执行
  - 主题切换
- [ ] 15.3 集成到 CI pipeline

**验证**：`npx playwright test` 全部通过

---

### Step 16 — Approval Gates 重新设计（对标 Codex）

**目标**：权限审批界面向 Codex 的 Approval Gates 靠拢
**改动文件**：`app.js`、`style.css`

- [ ] 16.1 重新设计 Permission Modal 为 Codex 风格：全宽 banner 而非居中弹窗
- [ ] 16.2 Banner 内容：左侧展示操作描述 + 参数详情，右侧 Approve / Deny 按钮
- [ ] 16.3 Banner 出现时附带轻微的 `shake` 或 `glow` 动画吸引注意力
- [ ] 16.4 多个 pending 权限请求排队展示（而非只显示最后一个）
- [ ] 16.5 已审批/已拒绝的操作以简洁的 status chip 在消息流中展示
- [ ] 16.6 支持"始终允许此工具"的 checkbox（可选，减少重复审批）

**验证**：触发工具调用权限请求，确认 banner 风格和交互与 Codex 类似

---

### Step 17 — Context Window 可视化

**目标**：让用户直观感知当前对话的 context 使用情况
**改动文件**：`app.js`、`style.css`、`index.html`

- [ ] 17.1 将 `token-display`（当前 `display:none`）改为 Header 中的环形进度指示器
- [ ] 17.2 环形图使用 SVG `stroke-dasharray` 实现，颜色根据使用量变化：绿 -> 黄 -> 红
- [ ] 17.3 Hover 时显示 tooltip：`已使用 15,240 / 128,000 tokens (12%)`
- [ ] 17.4 接近上限（>80%）时自动变色提醒
- [ ] 17.5 后端 `WebEngineManager` 在每次响应后返回 token usage 数据

**验证**：发送几条消息后检查环形图是否实时更新

---

## 第四部分：总体评价

MyAgent Web UI 有一个扎实的技术底座（CSS 变量主题系统、WebSocket 实时通信、任务流可视化），但当前处于功能堆叠阶段——功能多但缺乏设计收敛。

**设计方向**：向 OpenAI Codex 的界面风格看齐——**极简克制、留白呼吸、以 Thread 为核心、Summary Pane 透明追溯、Approval Gates 门控审批**。Codex 的设计哲学是「Barely-There UI」：用最少的 UI 元素传达最关键的信息，让 agent 的工作过程可追溯而不扰人。

**建议迭代节奏**：
- **Step 01-04**（1-2 天）：纯 BUG 修复，不涉及设计变更
- **Step 05-07**（2-3 天）：**核心布局重构，向 Codex 风格靠拢**（极简 Header + Thread 侧栏 + 极简首页）
- **Step 08-11**（2-3 天）：交互增强（Toast / 骨架屏 / 过渡动画 / 搜索优化）
- **Step 12-13**（2-3 天）：**Codex 风格深化**（Summary Pane + 模型动态化）
- **Step 14-17**（3-5 天）：架构级改进 + Codex 风格收尾（模块化 / E2E 测试 / Approval Gates / Context 可视化）

每个 Step 完成后可独立验证、独立提交，互不阻塞。
