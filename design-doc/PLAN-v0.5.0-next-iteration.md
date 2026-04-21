# MyAgent v0.5.0 下一步迭代计划

> **目标**: 基于当前 v0.4.0 状态（379 测试通过，TUI 完善完成），规划接下来的开发路线。

**当前状态**: TUI 完善已完成（Agent 切换生效、Memory 集成、配置持久化、多行输入）。

**技术栈**: Python, Textual, FastAPI, WebSocket, Pydantic

---

## 当前各 Phase 完成度

| Phase | 模块 | 完成度 | 说明 |
|-------|------|--------|------|
| Phase 1 | 核心引擎 | 95% | QueryEngine、工具、Agent 定义、CLI 都就绪 |
| Phase 2 | 扩展能力 | 90% | 插件、MCP、Web 工具、子 Agent、Todo 都就绪 |
| Phase 3 | 生产级 | 60% | Swarm、轨迹、成本、安全就绪；Gateway 只有骨架 |
| Phase 4 | 高级特性 | 80% | LSP、TTS、图像、远程桥接、定时任务就绪 |
| Phase 5 | TUI | 95% | 核心框架、对话、工具可视化、权限、配置都完成 |
| Phase 6 | Web UI | 0% | 未开始 |
| Phase 7 | Gateway | 20% | 只有抽象基类和 Manager，无具体适配器 |
| Phase 8 | 生产优化 | 10% | 只有基础 CostTracker |
| Phase 9 | 生态扩展 | 30% | 7 个 LLM 提供商，6 个核心工具 |

---

## 可选迭代路线

### 路线 B: Web UI（推荐下一步，2-3 周）

用户之前表达过对 Web UI 的兴趣。TUI 已经完善，Web UI 是自然的下一步扩展。

**价值**:
- 远程访问 Agent（不局限于终端）
- 更友好的文件浏览和代码展示
- 为 Gateway 的 Webhook 提供前端界面
- 多用户场景的基础

**任务分解**:

#### Task 1: FastAPI 后端骨架
- 创建 `src/myagent/web/server.py` — FastAPI app + lifespan
- 创建 `src/myagent/web/api.py` — REST API 路由
- 创建 `src/myagent/web/websocket.py` — WebSocket 端点
- 创建 `src/myagent/web/session.py` — Session 管理
- 测试: `tests/test_web.py`

#### Task 2: 前端聊天界面
- 创建 `src/myagent/web/static/index.html` — 单页应用
- 创建 `src/myagent/web/static/app.js` — WebSocket 客户端
- 创建 `src/myagent/web/static/style.css` — 样式
- 功能: 消息列表、输入框、流式显示、工具结果展示

#### Task 3: 会话管理 API
- `/api/sessions` — CRUD 会话
- `/api/sessions/{id}/messages` — 获取/发送消息
- `/ws/{session_id}` — WebSocket 实时通信
- SessionStore: 内存 + 文件持久化

#### Task 4: 与 TUI 共享核心逻辑
- Web 后端复用 QueryEngine、ToolRegistry
- 统一的 Agent 配置加载
- 共享 MemoryManager

---

### 路线 C: Gateway 完整实现（2-3 周）

让 Agent 可以接入 Discord、Slack、Telegram。

**价值**:
- 扩展使用场景到群聊
- 异步消息处理
- 多平台统一接入

**任务分解**:

#### Task 1: Discord 适配器
- `src/myagent/gateway/discord.py` — discord.py 集成
- 斜杠命令注册
- 线程对话支持

#### Task 2: Slack 适配器
- `src/myagent/gateway/slack.py` — slack-sdk 集成
- Block Kit 消息格式
- 提及触发 (@myagent)

#### Task 3: Telegram 适配器
- `src/myagent/gateway/telegram.py` — python-telegram-bot
- 命令菜单 (/start, /help)
- 内联查询

#### Task 4: 会话池
- LRU 缓存，最大 128 会话
- 1 小时 TTL 自动驱逐
- 每个会话独立 QueryEngine

---

### 路线 D: 生产级优化（3-4 周）

**任务分解**:

#### Task 1: 上下文压缩
- 监控 token 使用量
- 达到阈值时自动摘要早期对话
- 保留系统提示词和最近对话

#### Task 2: 结构化日志
- JSON 格式日志输出
- 按模块分类（engine、tools、llm、security）
- 日志轮转

#### Task 3: Docker 部署
- Dockerfile
- docker-compose.yml（Agent + 可选 Redis）
- 环境变量配置

#### Task 4: 更多国内 LLM 提供商
- 百度文心一言
- 阿里通义千问
- 讯飞星火

---

## 我的推荐

**第一优先: 路线 B（Web UI）**

理由:
1. **用户之前明确表达过兴趣** — "我首先要保证能有 TUI 在保证能用，最后在来完善 webui"
2. **TUI 已经完成** — 现在正是做 Web UI 的时候
3. **技术栈自然延伸** — FastAPI + WebSocket 是 Python 生态的标准选择
4. **工作量适中** — 2-3 周可以做出可用的 Web 界面
5. **为 Gateway 打基础** — Webhook 适配器可以直接复用 Web 后端

**第二优先: 路线 C（Gateway）**
- 如果用户更关注多平台接入

**第三优先: 路线 D（生产优化）**
- 如果用户要部署到生产环境

---

## 决策点

**请选择:**

1. **路线 B: Web UI** — FastAPI + WebSocket + 前端聊天界面（推荐）
2. **路线 C: Gateway** — Discord/Slack/Telegram 适配器
3. **路线 D: 生产优化** — 上下文压缩、日志、Docker、更多 LLM
4. **其他方向** — 你有别的优先级想法
