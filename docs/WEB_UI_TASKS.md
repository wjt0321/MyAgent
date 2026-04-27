# MyAgent Web UI 迭代任务清单

> 来源：[WEB_UI_REVIEW.md](WEB_UI_REVIEW.md)
> 生成日期：2026-04-27
> 使用说明：每个 Step 包含若干可勾选子任务，完成后在 `- [ ]` 中打勾 `- [x]`

---

## Step 01 — 修复 P0 HTML/JS BUG

**目标**：消除功能崩溃级别的问题
**改动文件**：`index.html`、`app.js`
**预计耗时**：30 分钟

- [x] 1.1 在 `index.html` 第 282 行后加 `</div>` 闭合 `session-control-bar`
- [x] 1.2 将 `app.js` 第 3034 行 `this.previewFile(path)` 改为 `this.showFilePreview(path, path.split('/').pop())`
- [x] 1.3 在 `app.js` `ws.onclose` 中，对非致命 close code（非 1000/1005/1006/1011）调用 `this.attemptReconnect(sessionId)`，并在 1006/1011 时做一次延迟重试

**验证清单**：
- [x] 页面加载无 HTML 嵌套报错
- [x] 代码库搜索结果可正常点击预览
- [x] 手动关闭 WebSocket 后观察是否尝试重连

---

## Step 02 — 修复 CSS 未定义变量 + 统一按钮系统

**目标**：消除 CSS 渲染异常
**改动文件**：`style.css`
**预计耗时**：45 分钟

- [x] 2.1 全局搜索 `--border-color` 替换为 `--border-default`
- [x] 2.2 全局搜索 `--surface-2` 替换为 `--bg-secondary`
- [x] 2.3 将 `task-cancel-btn`、`task-retry-btn`、`task-restore-btn`、`task-empty-primary` 改为复用 `btn-ghost`/`btn-primary`/`btn-outline` class
- [x] 2.4 将硬编码的 `border-radius: 14px`、`border-radius: 12px`、`border-radius: 10px` 改为 `var(--radius-lg)` 或 `var(--radius-md)`

**验证清单**：
- [x] 浏览器中切换 Dark/Light 主题，Task 区域按钮样式正常
- [x] 无 CSS 变量未定义警告（DevTools Console）

---

## Step 03 — 修复 XSS 漏洞 + 安全问题

**目标**：消除所有 innerHTML 注入风险
**改动文件**：`app.js`、`auth.py`
**预计耗时**：1 小时

- [ ] 3.1 `renderMemoryList`：对 `mem.name`、`mem.description` 和 `data-name` 属性调用 `escapeHtml()`
- [ ] 3.2 `showPermissionModal`：对 `data.arguments` 的 key/value 调用 `escapeHtml()`
- [ ] 3.3 `renderWorkspace`：对 `mem.filename`、`mem.name`、`mem.description` 调用 `escapeHtml()`
- [ ] 3.4 `showPermissionModal` 改用 `addEventListener` 替代 `onclick="window.myAgentApp..."`
- [ ] 3.5 `auth.py` 将 `hashlib.sha256` 改为 `hashlib.pbkdf2_hmac('sha256', password, salt, 100000)`，附带随机 salt
- [ ] 3.6 `auth.py` 将 `datetime.utcnow()` 改为 `datetime.now(timezone.utc)`

**验证清单**：
- [ ] 在记忆名称中输入 `<img src=x onerror=alert(1)>` 测试 XSS 是否被拦截
- [ ] 旧密码仍可验证（向后兼容）
- [ ] Python 3.12 无 DeprecationWarning

---

## Step 04 — 修复数据一致性问题

**目标**：前端操作能正确持久化
**改动文件**：`app.js`
**预计耗时**：1 小时

- [ ] 4.1 `startRenameSession`：重命名后调用 `PATCH /api/sessions/:id` 持久化
- [ ] 4.2 `createSession`：读取 `this.modelSelect.value` 作为 model 参数，而非硬编码
- [ ] 4.3 `importSession`：同样读取当前选择的 model
- [ ] 4.4 `startRenameSession`：将 `prompt()` 替换为 inline 编辑模式（类似 `startEditMessage` 的实现方式）

**验证清单**：
- [ ] 新建会话 -> 检查 model 是否与下拉框一致
- [ ] 重命名会话 -> 刷新页面检查是否保留
- [ ] inline 编辑模式 UI 与 Workbench 风格一致

---

## Step 05 — 精简 Header 布局（对标 Codex）

**目标**：向 Codex 极简 Header 靠拢——Header 只做状态展示，不做控件操作
**改动文件**：`index.html`、`style.css`、`app.js`
**预计耗时**：2-3 小时

- [ ] 5.1 将 `model-select`（80+ option 的大下拉）从 Header 移入 Command Palette 命令（`Ctrl+K` -> 输入 model）
- [ ] 5.2 将 `agent-select` 从 Header 移入 Settings Modal
- [ ] 5.3 Header 精简为只保留：连接状态指示灯 + thread 标题（当前 agent）+ model 标签（只读）+ token 环形进度
- [ ] 5.4 删除 `context-help-strip`（移入 Welcome Page）
- [ ] 5.5 删除 `session-summary-line`（信息整合到 sidebar 的 session card 中）
- [ ] 5.6 调整 `chat-header` CSS：`height: 48px`，内容单行，大量留白形成 Codex 的「呼吸感」
- [ ] 5.7 Header 右侧只保留：搜索图标 + 命令面板图标 + 设置图标

**验证清单**：
- [ ] 对比 Codex 截图检查 Header 是否达到类似的简洁程度
- [ ] 模型切换通过 Command Palette 可正常使用
- [ ] Agent 切换通过 Settings Modal 可正常使用

---

## Step 06 — 重构 Welcome Page（对标 Codex）

**目标**：模仿 Codex 的极简首页——一个输入框 + 最近线程
**改动文件**：`app.js`（`renderWelcomeLanding` 方法）、`style.css`
**预计耗时**：3-4 小时

- [ ] 6.1 Welcome Page 简化为两区：居中的 Hero 输入区域（含 brand + 一句话 slogan + 大型输入框）+ 最近会话 thread 列表
- [ ] 6.2 删除 Positioning 卡片、Demo Path 卡片、文档入口卡片（移入 Settings -> 关于）
- [ ] 6.3 大型输入框可直接创建新 thread 并发送第一条消息（合并"新建会话"和"发送消息"两步操作）
- [ ] 6.4 最近会话以 Codex 风格的 thread card 展示：标题 + 时间 + 最后消息摘要
- [ ] 6.5 Quickstart 步骤只在检测到未配置 API Key 时以 banner 形式展示，而非占据主区域
- [ ] 6.6 入场动画：Hero 区域 `fadeInUp`（0.3s），thread 列表 stagger 延迟依次出现
- [ ] 6.7 整体大量留白，背景使用当前的 radial-gradient cyber 效果增加质感

**验证清单**：
- [ ] 启动 Web UI，与 Codex 首页对比，检查信息密度和视觉节奏
- [ ] 大型输入框可直接创建 thread 并发送首条消息
- [ ] 未配置 API Key 时显示 Quickstart banner

---

## Step 07 — 重构侧栏为 Codex 风格 Thread 列表

**目标**：侧栏像 Codex 一样只做 thread 管理，干净纯粹
**改动文件**：`index.html`、`style.css`、`app.js`
**预计耗时**：3-4 小时

- [ ] 7.1 删除侧栏中的 Workbench Nav 按钮（聊天/任务/文件/Workspace/团队）
- [ ] 7.2 将 Workbench 视图切换改为主内容区顶部的轻量 tab bar（icon + label 单行横向）
- [ ] 7.3 侧栏精简为三层：品牌标识 -> 新建 Thread 按钮 -> Thread（会话）列表
- [ ] 7.4 Thread 列表中每个 session card 展示：标题、agent 类型图标、最后消息时间、进行中的 task 状态指示器
- [ ] 7.5 增加 thread 分组：「进行中」和「历史」
- [ ] 7.6 底部只保留连接状态 + 设置按钮
- [ ] 7.7 移动端侧栏使用 Codex 风格的半透明 overlay + slide-in 动画

**验证清单**：
- [ ] 对比 Codex 的侧栏，检查布局和信息层级是否一致
- [ ] 视图切换通过顶部 tab bar 正常工作
- [ ] 移动端侧栏 slide-in 动画流畅

---

## Step 08 — 添加 Toast 通知系统

**目标**：替代 `alert()` 和消息流中的系统通知
**改动文件**：`app.js`、`style.css`、`index.html`
**预计耗时**：2 小时

- [ ] 8.1 实现一个 `showToast(message, type, duration)` 方法（type: success/error/info/warning）
- [ ] 8.2 Toast 样式：固定在右上角，`fadeInDown` 入场，自动消失
- [ ] 8.3 替换所有 `alert()` 调用为 `showToast()`（约 8 处）
- [ ] 8.4 替换所有非对话性质的 `addMessage('assistant', '设置已保存')` 为 `showToast()`
- [ ] 8.5 Agent/Model 切换成功、保存设置等场景使用 Toast 而不是在聊天中插入消息

**验证清单**：
- [ ] 保存设置、切换 Agent、删除记忆等操作确认 Toast 正常弹出
- [ ] Toast 自动消失，不阻塞用户操作
- [ ] 无 `alert()` 残留

---

## Step 09 — 添加骨架屏与加载状态

**目标**：消除页面加载时的空白感
**改动文件**：`app.js`、`style.css`
**预计耗时**：2 小时

- [ ] 9.1 定义 `.skeleton` CSS 类（条形闪烁动画）
- [ ] 9.2 `loadSessions` 加载中时在会话列表显示 3-5 条 skeleton 占位
- [ ] 9.3 `loadFileTree` 加载中时在文件树显示 skeleton 占位
- [ ] 9.4 `loadCurrentTask` 加载中时在任务面板显示 skeleton
- [ ] 9.5 发送按钮在 `isSending` 时显示旋转动画（替代 opacity 变化）

**验证清单**：
- [ ] 清空缓存刷新页面，观察加载过程中是否有 skeleton 闪烁
- [ ] 发送消息时按钮显示旋转动画

---

## Step 10 — 视图过渡动画

**目标**：Workbench 视图切换有动态感
**改动文件**：`style.css`、`app.js`
**预计耗时**：1.5 小时

- [ ] 10.1 给 `.workbench-view` 添加 `fade + slide` 过渡（CSS animation 或 `classList` 切换）
- [ ] 10.2 侧栏展开/收起改为 `transform + opacity` 动画
- [ ] 10.3 会话切换时消息区域添加 `fadeIn` 动画

**验证清单**：
- [ ] 在聊天/任务/文件/Workspace/团队之间切换，确认过渡流畅
- [ ] 侧栏展开/收起动画流畅
- [ ] 会话切换时消息区域有 fadeIn 效果

---

## Step 11 — 搜索体验优化

**目标**：搜索功能可用性提升
**改动文件**：`app.js`、`style.css`
**预计耗时**：1.5 小时

- [ ] 11.1 `performSearch` 只对第一个匹配项 `scrollIntoView`
- [ ] 11.2 搜索栏增加匹配计数显示（如 "3/12"）
- [ ] 11.3 添加"上一个/下一个"导航按钮或快捷键（Enter/Shift+Enter）
- [ ] 11.4 高亮匹配文本（在 `.content` 中用 `<mark>` 包裹）

**验证清单**：
- [ ] 搜索关键词后滚动到第一个结果
- [ ] 匹配计数显示正确
- [ ] 可上下导航匹配项
- [ ] 匹配文本高亮显示

---

## Step 12 — 右侧 Summary Pane（对标 Codex）

**目标**：将详情侧栏改造为 Codex 风格的 Summary Pane，展示 agent 的计划、文件变更和执行进度
**改动文件**：`index.html`、`style.css`、`app.js`
**预计耗时**：4-6 小时

- [ ] 12.1 桌面端将 Detail Sidebar 改为常驻的 split-pane（非 overlay），与消息区域并排
- [ ] 12.2 添加宽度可拖拽调整的 resize handle（默认 380px，最小 300px，最大 50%）
- [ ] 12.3 Summary Pane 分为多个 section：
  - [ ] **Agent 状态**：当前正在做什么（thinking / coding / reviewing），有呼吸灯动画
  - [ ] **计划概览**：展示 task plan 的步骤列表和进度
  - [ ] **文件变更**：展示本次对话中 agent 修改/创建/删除的文件列表（类似 Git status）
  - [ ] **工具调用详情**：点击消息中的工具卡片后展示详细内容
- [ ] 12.4 无内容时 Summary Pane 显示空状态提示（"开始对话后，agent 的计划和文件变更将在此显示"）
- [ ] 12.5 移动端保持全屏 sheet 模式，增加顶部返回/关闭按钮

**验证清单**：
- [ ] 发送一条消息后，Summary Pane 实时更新 agent 状态
- [ ] 文件变更列表与实际操作一致
- [ ] resize handle 可拖拽调整宽度
- [ ] 移动端 sheet 模式可正常打开/关闭

---

## Step 13 — 模型列表动态化

**目标**：消除 HTML 中 80+ 行硬编码的 model option
**改动文件**：`server.py`、`app.js`、`index.html`
**预计耗时**：2 小时

- [ ] 13.1 后端新增 `GET /api/models` 接口，返回可用模型列表（读取 `gateway.yaml`）
- [ ] 13.2 前端在 `constructor` 中调用 API 动态填充 model-select
- [ ] 13.3 删除 `index.html` 中所有 `<optgroup>` 硬编码
- [ ] 13.4 Settings Modal 或 Command Palette 中可切换模型

**验证清单**：
- [ ] 确认模型下拉列表内容来自后端配置
- [ ] 新增配置后刷新即可看到新模型
- [ ] 模型切换功能正常

---

## Step 14 — 前端 `app.js` 模块化拆分

**目标**：3300 行单文件拆分为可维护的模块
**改动文件**：`app.js` -> 多个文件
**预计耗时**：4-6 小时

- [ ] 14.1 拆分为以下模块：
  - [ ] `theme.js` — 主题切换逻辑
  - [ ] `websocket.js` — WebSocket 连接和重连
  - [ ] `session.js` — 会话 CRUD 和渲染
  - [ ] `message.js` — 消息渲染、流式更新、编辑
  - [ ] `task.js` — 任务创建、审批、轮询
  - [ ] `workspace.js` — 文件树、记忆、代码库
  - [ ] `ui.js` — 命令面板、Toast、Modal 等 UI 组件
  - [ ] `app.js` — 入口文件，组合各模块
- [ ] 14.2 使用 ES Module (`import`/`export`) 语法
- [ ] 14.3 `index.html` 中改为 `<script type="module" src="app.js">`

**验证清单**：
- [ ] 所有功能正常工作（会话管理、聊天、任务流、文件预览等）
- [ ] 无控制台报错
- [ ] 主题切换正常

---

## Step 15 — 前端 E2E 测试

**目标**：确保 UI 交互的回归安全
**改动文件**：新增测试文件
**预计耗时**：4-6 小时

- [ ] 15.1 选择 Playwright 作为测试框架
- [ ] 15.2 核心测试场景：
  - [ ] 创建会话 -> 发送消息 -> 验证消息出现
  - [ ] 切换视图（聊天/任务/文件/Workspace/团队）
  - [ ] 打开/关闭设置面板
  - [ ] Command Palette 搜索和执行
  - [ ] 主题切换
- [ ] 15.3 集成到 CI pipeline

**验证清单**：
- [ ] `npx playwright test` 全部通过
- [ ] CI pipeline 中自动运行测试

---

## Step 16 — Approval Gates 重新设计（对标 Codex）

**目标**：权限审批界面向 Codex 的 Approval Gates 靠拢
**改动文件**：`app.js`、`style.css`
**预计耗时**：3-4 小时

- [ ] 16.1 重新设计 Permission Modal 为 Codex 风格：全宽 banner 而非居中弹窗
- [ ] 16.2 Banner 内容：左侧展示操作描述 + 参数详情，右侧 Approve / Deny 按钮
- [ ] 16.3 Banner 出现时附带轻微的 `shake` 或 `glow` 动画吸引注意力
- [ ] 16.4 多个 pending 权限请求排队展示（而非只显示最后一个）
- [ ] 16.5 已审批/已拒绝的操作以简洁的 status chip 在消息流中展示
- [ ] 16.6 支持"始终允许此工具"的 checkbox（可选，减少重复审批）

**验证清单**：
- [ ] 触发工具调用权限请求，确认 banner 风格和交互与 Codex 类似
- [ ] 多个 pending 请求可排队展示
- [ ] 审批结果以 status chip 展示在消息流中

---

## Step 17 — Context Window 可视化

**目标**：让用户直观感知当前对话的 context 使用情况
**改动文件**：`app.js`、`style.css`、`index.html`
**预计耗时**：2-3 小时

- [ ] 17.1 将 `token-display`（当前 `display:none`）改为 Header 中的环形进度指示器
- [ ] 17.2 环形图使用 SVG `stroke-dasharray` 实现，颜色根据使用量变化：绿 -> 黄 -> 红
- [ ] 17.3 Hover 时显示 tooltip：`已使用 15,240 / 128,000 tokens (12%)`
- [ ] 17.4 接近上限（>80%）时自动变色提醒
- [ ] 17.5 后端 `WebEngineManager` 在每次响应后返回 token usage 数据

**验证清单**：
- [ ] 发送几条消息后检查环形图是否实时更新
- [ ] Hover 时显示详细 tooltip
- [ ] 超过 80% 时颜色变为红色

---

## 迭代节奏建议

| 阶段 | Steps | 预计耗时 | 目标 |
|:---|:---|:---|:---|
| **第一阶段：BUG 修复** | 01-04 | 1-2 天 | 消除功能异常，不涉及设计变更 |
| **第二阶段：核心布局重构** | 05-07 | 2-3 天 | 向 Codex 风格靠拢（极简 Header + Thread 侧栏 + 极简首页） |
| **第三阶段：交互增强** | 08-11 | 2-3 天 | Toast / 骨架屏 / 过渡动画 / 搜索优化 |
| **第四阶段：Codex 风格深化** | 12-13 | 2-3 天 | Summary Pane + 模型动态化 |
| **第五阶段：架构级改进** | 14-17 | 3-5 天 | 模块化 / E2E 测试 / Approval Gates / Context 可视化 |

> 每个 Step 完成后可独立验证、独立提交，互不阻塞。
