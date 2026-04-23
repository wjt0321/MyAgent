# MyAgent 项目全面审查报告

> **审查时间**: 2026-04-23
> **审查范围**: 架构、Web UI、工具系统、缺口分析、迭代建议
> **目标定位**: 成为 OpenClaw + HermesAgent 的融合体

---

## 一、项目概况与定位

MyAgent 是一个融合四大开源 Agent 项目（hermes-agent、claude-code、openclaw、OpenHarness）的自主 AI Agent 平台。当前版本（v0.11.0）已完成了核心引擎、工具系统、记忆管理、Web UI、TUI、Gateway 骨架等基础模块。

**整体评价**：架构设计成熟、模块划分清晰、文档详尽，是一个有相当工程深度的个人项目。离"OpenClaw + HermesAgent 融合体"的目标已有明确路径，但还有若干关键能力缺口需要填补。

---

## 二、Web UI 深度审查（重点）

### 2.1 当前状态

Web UI 已具备：侧边栏（会话/任务/团队/文件树/Workspace）、聊天区、设置弹窗（Agent/记忆/代码库/重置/外观/关于）、File Preview Panel、权限审批弹窗、主题切换（深色/浅色）。

CSS 使用了 CSS 变量 + 两套 Theme（Dark/Light），Inter 字体，初步的 glassmorphism 设计语言。

### 2.2 问题清单

#### 严重问题（用户体验断层）

| # | 问题 | 位置 | 说明 |
|---|------|------|------|
| 1 | **模型硬编码为 `glm-4.7`** | `server.py:253`, `app.js:607` | 用户无法在 UI 内切换 LLM 模型，逻辑上支持多 LLM 但界面不予暴露 |
| 2 | **`/api/sessions PATCH` 端点不存在** | `server.py` + `app.js:264` | `switchAgent()` 调用了 `PATCH /api/sessions/{id}`，但 server.py 没有该路由，会静默失败 |
| 3 | **权限弹窗传参错误：tool_use_id 实为 tool_name** | `app.js:831` | `sendPermissionResponse()` 把 `tool_name` 当 `tool_use_id` 传递，导致 permission loop 无法正确恢复 |
| 4 | **工具调用结果无折叠** | `app.js:735-740` | Tool result 直接展开在聊天区，长结果（如 bash 输出）导致消息区域极度拥挤 |
| 5 | **会话仅内存存储，刷新全部丢失** | `session.py` | `SessionStore` 无持久化，浏览器刷新后所有会话消失 |

#### 中等问题（视觉/功能缺陷）

| # | 问题 | 说明 |
|---|------|------|
| 6 | **缺少字体加载 link 标签** | CSS 声明了 Inter 字体但没有 Google Fonts CDN，回退到系统字体 |
| 7 | **模型选择器保存后不生效** | `saveSettings()` 没有发送 model 更新的 API 请求 |
| 8 | **文件树 XSS 风险** | `entry.name` 直接通过 innerHTML 插入，文件名含特殊字符可触发 XSS |
| 9 | **侧边栏信息过度密集** | 5 个区块同时展示，侧边栏体验极差 |
| 10 | **欢迎页面缺少引导** | 仅有 Logo + 一行文字，缺乏快捷操作卡片 |
| 11 | **代码块缺少 Copy 按钮** | Agent 工具的高频需求，当前完全没有 |
| 12 | **工具调用无执行动画** | Tool call 展示是静态的，无 loading 感 |

#### 小问题（体验打磨）

| # | 问题 |
|---|------|
| 13 | 消息气泡内没有时间戳 |
| 14 | 消息搜索只滚动到第一个匹配项，多个匹配无法依次导航 |
| 15 | Settings 弹窗没有 Esc 快捷键关闭 |
| 16 | 移动端侧边打开后，点击聊天区必须点击遮罩才能关闭 |
| 17 | Favicon 是内联 data URL，浏览器 tab 无法正常展示 |

### 2.3 对比 OpenClaw / Claude Code Web UI 的差距

| 功能 | 当前 MyAgent | OpenClaw/Claude Code |
|------|-------------|----------------------|
| 工具调用可折叠显示 | 不支持，全部展开 | 折叠面板 |
| 模型实时切换 | 界面不可用 | 下拉选择 |
| 代码块 Copy 按钮 | 不支持 | 支持 |
| 流式打字机动画 | 支持 | 支持 |
| 会话持久化 | 仅内存 | 文件/DB |
| 成本 Token 展示 | 不支持 | 支持 |
| 工具执行实时进度 | 不支持 | 支持 |
| 快捷指令卡片 | 不支持 | 支持 |
| 多 Agent 可视化 | 静态列表 | 实时状态 |
| 暗色主题 | 支持 | 支持 |

---

## 三、核心架构审查

### 3.1 QueryEngine — 良好，有小缺口

- 事件驱动的 AsyncIterator 模式（良好）
- 权限检查集成 ASK/DENY/ALLOW 三档（良好）
- 工具调用循环 tool-aware loop（良好）
- 只追踪最后一个 tool_use，多工具并行时丢失之前的调用（缺陷）
- auto_compact_threshold 参数存在于签名但实际未实现压缩逻辑（缺陷）
- MaxTurnsExceeded 异常没有被 WebSocket 层 catch，会导致 WS 中断（缺陷）

### 3.2 工具系统 — 基础扎实

- 标准化 BaseTool 接口（良好）
- Pydantic 输入验证（良好）
- 15 个内置工具 Read/Edit/Write/Bash/Glob/Grep/WebSearch/WebFetch/TTS/ImageAnalyze 等（良好）
- 缺少 Git 工具，是 OpenClaw 的核心能力（缺失）
- 工具执行没有超时保护，长跑 Bash 命令会永久阻塞（缺陷）

### 3.3 记忆系统 — 设计好，集成弱

- 4 种记忆类型 session/project/user/auto（良好）
- Markdown 文件存储，MEMORY.md 索引（良好）
- Web UI 对话不自动触发记忆收集，collect_memory 背后实现不明确（缺陷）
- TUI 完全不集成记忆，plan 文档中已记录但未完成（缺陷）

### 3.4 与 OpenClaw + HermesAgent 融合目标的差距

| 维度 | OpenClaw 特征 | HermesAgent 特征 | 当前 MyAgent 状态 |
|------|--------------|-----------------|-----------------|
| 插件系统 | 完整插件市场 | — | 骨架已建 |
| 智能上下文压缩 | 动态窗口管理 | — | 代码已写但未启用 |
| SSRF/Sandbox 防护 | 完整沙箱 | — | security 模块存在，完整度未知 |
| 多平台 Gateway | — | Discord/Slack/TG | README 声称，实现完整度存疑 |
| 轨迹追踪/ShareGPT | — | 支持 | trajectory 模块存在 |
| LSP 集成 | — | — | lsp 模块存在 |
| Swarm 协作 | — | 支持 | swarm/teams 模块存在 |
| Multi-modal | 支持 | — | image_analyze.py |
| Web UI 质量 | 5星 | 3星 | 2星（当前状态） |

---

## 四、后续迭代建议（优先级排序）

### 迭代 1：Web UI 重大升级（2-3周）

这是当前最短的"高价值回报"路径。

#### Bug 修复（必须先做）

1. **补充 `PATCH /api/sessions/{id}` 路由** — 修复 Agent 切换
2. **修复权限弹窗的 tool_use_id 传参 Bug** — 修复 permission loop
3. **会话持久化** — SessionStore 写入 `~/.myagent/sessions/` JSON 文件
4. **补充 Google Fonts CDN link** — Inter 字体正确加载
5. **模型选择器接通后端** — settings 界面的 model 选择真正生效

#### 前端视觉升级

**侧边栏重设计**
- 将 5 个区块折叠为标签式图标导航（Chat / Files / Memory / Settings）
- 侧边栏宽度可拖拽调节（参考 VS Code）
- Agent 切换升级为有图标的卡片式选择器（参考 Claude.ai model picker）

**聊天区升级**
- 工具调用改为可折叠面板，默认收起，仅显示工具名和用时
- 代码块增加 Copy 按钮（右上角悬浮出现）
- 消息气泡增加时间戳 tooltip
- 助手消息增加 Token 消耗角标
- 打字机动画期间显示 "正在思考..." + 已用工具计数

**欢迎页面升级**
- 添加 3-5 张快捷指令卡片（`/plan 分析当前代码库` 等）
- 展示当前 Agent 能力标签（工具列表）

#### 新增功能

- **成本看板**：右上角显示本次会话 token 消耗 + 预估费用
- **快捷指令 `/` 菜单**：输入框输入 `/` 弹出命令面板（/plan、/agent、/clear、/memory）
- **文件上传按钮**：允许上传本地文件到 context

---

### 迭代 2：OpenClaw 核心能力对齐（3-4周）

#### 上下文压缩真正上线

`engine/context_compression.py` 已存在，需要在 QueryEngine 的 `_run_loop()` 中，每轮之前检查 token 使用量，超过阈值自动触发压缩。

#### 插件热加载 UI

当前 `plugins/` 模块无法从 UI 管理。需要：
- Web UI 添加"插件"Tab
- `GET /api/plugins` 列出已安装插件
- `POST /api/plugins/install` 支持 git URL 安装
- `POST /api/plugins/enable|disable/{name}` 热开关

#### 工具超时与沙箱

在 bash.py 中使用 `asyncio.timeout()` 限制执行时长，在 web_fetch.py 中拦截内网地址 SSRF。

#### Git 工具

支持 status, diff, log, add, commit, push 操作。这是代码 Agent 的核心能力，当前完全缺失。

---

### 迭代 3：HermesAgent Gateway 完整实现（3-4周）

#### 验证现有 Gateway 实现

从最简单的 Telegram 适配器入手，验证消息路由、会话绑定、消息格式转换、权限审批在 IM 内的交互。

#### GitHub App 集成

监听 PR/Issue/Review 事件，自动分析、回复、创建代码改动。

#### Web UI 多用户支持

JWT Token 认证、每个用户独立 session namespace、可选密码保护。

---

### 迭代 4：高级能力与生态（持续）

| 能力 | 说明 |
|------|------|
| 浏览器自动化 | 接入 Playwright，AI 操控浏览器 |
| 数据库工具 | SQL 查询工具，支持 SQLite/PostgreSQL |
| LSP 深度集成 | 利用已有 lsp 模块实现语义跳转、补全辅助 |
| VS Code 插件 | 将 MyAgent 嵌入编辑器 |
| 训练数据导出 | trajectory 模块导出 ShareGPT 格式 |
| 成本控制面板 | 预算上限设置，超限自动暂停 |

---

## 五、技术债务清单

| 优先级 | 债务项 | 影响 |
|--------|--------|------|
| 紧急 | `PATCH /api/sessions` 端点缺失 | Agent 切换静默失败 |
| 紧急 | 权限弹窗 tool_use_id 传参错误 | 工具权限循环无法恢复 |
| 紧急 | 会话无持久化 | 刷新丢失全部历史 |
| 重要 | `auto_compact_threshold` 实现缺失 | 长会话上下文溢出 |
| 重要 | 多 tool_use 同时调用时只记最后一个 | 并行工具调用时出错 |
| 重要 | `MaxTurnsExceeded` 异常未被 WS 层 catch | WS 连接异常断开 |
| 重要 | 文件树 XSS（innerHTML 插入 entry.name） | 安全风险 |
| 重要 | 工具执行无超时 | Bash 死循环时服务永久阻塞 |
| 一般 | Inter 字体 CDN 未引入 | 字体回退，视觉质量下降 |
| 一般 | 设置保存后不重连 WS | 切换 Agent 后需手动刷新 |

---

## 六、总结

**MyAgent 已经是个有深度的平台**，架构眼光（事件驱动、插件化、多模态、轨迹追踪）走在了正确方向上。

离"OpenClaw + HermesAgent 结合体"最关键的三个补全点：

1. **Web UI 质量** — 用户感知最直接的门面，当前差距最大，性价比最高
2. **上下文压缩实装** — OpenClaw 最被称道的能力，MyAgent 已写了框架，需真正接通
3. **Gateway 实测验通** — HermesAgent 的灵魂，需至少跑通 Telegram，确认消息流通

**推荐下一个 Sprint**：Web UI 的 3 个紧急 Bug 修复 + 工具折叠/Copy按钮/欢迎页卡片视觉升级，预计 1 周内可完成，用户体验有质的飞跃。

---

*文档版本: v1.0 | 审查时间: 2026-04-23*
