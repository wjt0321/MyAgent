# MyAgent 下一步迭代计划

> **目标**: 基于当前 v0.3.0 状态，规划接下来 2-3 个迭代周期的开发路线。

**当前状态**: TUI + QueryEngine 完整集成已完成（367 测试通过），具备真实 LLM 对话、工具循环、权限审批。

**技术栈**: Python, Textual, FastAPI, WebSocket, Pydantic

---

## 选项分析

### 路线 A: TUI 完善（短期，1-2 周）

让 TUI 真正可用，修复体验问题：

1. **Agent 切换真正生效** — 当前 `/agent explore` 只改了名字，没有切换 system prompt 和工具集
2. **Memory 集成** — 对话历史持久化到 `.myagent/memory/`
3. **配置持久化** — 保存用户偏好（provider、model、权限模式）
4. **TUI 错误恢复** — LLM 流中断后的重试机制
5. **多行输入支持** — Shift+Enter 换行，当前 Input 是单行

### 路线 B: Web UI（中期，2-3 周）

参考 OpenClaw 的 Web 界面设计：

1. **FastAPI 后端** — REST API + WebSocket 实时通信
2. **会话管理** — 多会话隔离、历史记录
3. **前端聊天界面** — 简单 HTML/JS（不引入 React 复杂度）
4. **文件浏览器** — 侧边栏显示项目文件树
5. **代码高亮** — 工具结果中的代码块语法高亮

### 路线 C: Gateway 完整实现（中期，2-3 周）

参考 Hermes-Agent 的网关设计：

1. **Discord 适配器** — discord.py 集成
2. **Slack 适配器** — slack-sdk 集成
3. **Telegram 适配器** — python-telegram-bot 集成
4. **Webhook 完善** — HTTP API 端点、签名验证
5. **会话池** — LRU 缓存，TTL 驱逐

### 路线 D: 生产级优化（长期，3-4 周）

1. **异步工具并行** — 多个工具同时执行
2. **上下文压缩** — 自动摘要早期对话
3. **结构化日志** — JSON 格式日志
4. **Docker 部署** — Dockerfile + Compose
5. **更多 LLM 提供商** — 百度、阿里、讯飞

---

## 推荐路线

**第一优先: 路线 A（TUI 完善）**

理由:
- TUI 是用户当前最直接的使用界面
- Agent 切换不生效是明显 bug
- Memory 集成让 Agent 有"记忆"能力
- 工作量可控，1 周内可完成

**第二优先: 路线 B（Web UI）**
- 用户之前表达过对 Web UI 的兴趣
- 可以让 Agent 远程访问
- 为 Gateway 打下基础

**第三优先: 路线 C（Gateway）**
- 让 Agent 可以接入 Discord/Slack/Telegram
- 扩展使用场景

---

## 详细任务: 路线 A — TUI 完善

### Task 1: Agent 切换真正生效

**Files:**
- Modify: `src/myagent/tui/app.py`
- Modify: `src/myagent/engine/query_engine.py`
- Test: `tests/test_tui_integration.py`

**问题**: 当前 `/agent explore` 只改了 `self.current_agent` 字符串，没有:
1. 切换 QueryEngine 的 system prompt
2. 限制工具集（explore 应该只有 Read/Glob/Grep）
3. 调整权限模式（explore 是 dontAsk）

**实现**:
1. `QueryEngine` 添加 `reconfigure()` 方法
2. `MyAgentApp._switch_agent()` 中调用 `reconfigure()`
3. 根据 AgentDefinition 过滤 ToolRegistry

---

### Task 2: Memory 集成

**Files:**
- Modify: `src/myagent/tui/app.py`
- Modify: `src/myagent/memory/manager.py`
- Test: `tests/test_memory.py`

**实现**:
1. TUI 启动时加载 project memory
2. 每次对话后自动保存关键信息到 memory
3. `/memory` 命令查看记忆

---

### Task 3: 配置持久化

**Files:**
- Create: `src/myagent/config/persistent.py`
- Modify: `src/myagent/tui/app.py`
- Test: `tests/test_config.py`

**实现**:
1. 保存 `~/.myagent/config.yaml`
2. 记录 last_provider、last_model、last_agent
3. 启动时自动加载

---

### Task 4: 多行输入支持

**Files:**
- Modify: `src/myagent/tui/app.py`
- Test: `tests/test_tui.py`

**实现**:
1. 使用 Textual 的 `TextArea` 替代 `Input`
2. Enter 发送，Shift+Enter 换行

---

## 详细任务: 路线 B — Web UI

### Task 1: FastAPI 后端骨架

**Files:**
- Create: `src/myagent/web/__init__.py`
- Create: `src/myagent/web/server.py`
- Create: `src/myagent/web/api.py`
- Test: `tests/test_web.py`

**实现**:
1. FastAPI app 创建
2. `/api/chat` POST 端点
3. `/ws` WebSocket 端点

---

### Task 2: 前端聊天界面

**Files:**
- Create: `src/myagent/web/static/index.html`
- Create: `src/myagent/web/static/app.js`
- Create: `src/myagent/web/static/style.css`

**实现**:
1. 简单 HTML 聊天界面
2. WebSocket 连接
3. 流式消息显示

---

### Task 3: 会话管理

**Files:**
- Create: `src/myagent/web/session.py`
- Modify: `src/myagent/web/api.py`

**实现**:
1. Session 模型（id、messages、created_at）
2. SessionStore（内存 + 文件）
3. `/api/sessions` CRUD

---

## 决策点

**请选择:**

1. **先完成路线 A（TUI 完善）** — 让终端界面真正好用
2. **直接开始路线 B（Web UI）** — 跳过 TUI 细节，做 Web 界面
3. **路线 A + B 并行** — TUI 修 bug 的同时开始 Web UI 骨架
4. **其他方向** — 你有别的优先级想法
