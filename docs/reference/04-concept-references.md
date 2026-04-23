# MyAgent 概念引用与出处

> 本文档记录 MyAgent 中每个核心概念的设计来源和参考出处。
> 方便追溯每个功能的设计意图和技术选型依据。

---

## 1. 概念出处总览

| 概念 | MyAgent 模块 | 主要参考项目 | 参考路径 | 借鉴程度 |
|------|-------------|-------------|----------|---------|
| **Workspace** | `workspace/` | OpenHarness | `memory/`, `config/paths.py` | 高 |
| **Memory System** | `memory/` | Claude Code | `memory/types.ts` | 高 |
| **Agent Definition** | `agents/` | OpenHarness | `coordinator/agent_definitions.py` | 高 |
| **Tool Base Class** | `tools/base.py` | OpenHarness | `tools/base.py` | 高 |
| **Tool Plugin** | `tools/` | Claude Code | `tools.ts`, `tools/*/` | 高 |
| **Task/Plan** | `tasks/` | Hermes Agent | `agent/` | 高 |
| **Agent Teams** | `teams/` | Hermes Agent | `agent/` | 高 |
| **Swarm/Multi-Agent** | `teams/` | Claude Code | `coordinator/` | 中 |
| **Gateway Pattern** | `gateway/` | Hermes Agent | `gateway/run.py` | 高 |
| **TUI Framework** | `tui/` | OpenHarness | `ui/app.py` | 高 |
| **流式输出** | `engine/` | OpenHarness | `engine/query_engine.py` | 高 |
| **Context Compression** | `engine/` | OpenHarness | `engine/query.py` | 高 |
| **Permission System** | `security/` | Claude Code | `utils/permissions/` | 中 |
| **Cost Tracking** | `cost/` | OpenHarness | `engine/cost_tracker.py` | 高 |
| **Session Store** | `web/session.py` | Hermes Agent | `gateway/run.py` | 高 |
| **LLM Provider** | `llm/providers/` | OpenHarness | `engine/` | 高 |

---

## 2. 按参考项目分类

### 2.1 Claude Code (`d:\源码库\claude-code-source-code`)

Claude Code 是 Anthropic 官方的 CLI 编程助手，代码质量极高。

#### Memory 系统 (memory/types.ts)

**借鉴概念**:
- 五级记忆类型分层
- MEMORY.md 作为索引文件
- Frontmatter 格式 (name, description, type)

**MyAgent 实现**:
- `memory/manager.py` — `MemoryManager` 类
- `memory/collection.py` — `MemoryCollector` 自动收集
- `memory/models.py` — `MemoryEntry` 数据类

**关键代码映射**:
```
Claude Code: memory/types.ts
  └─→ enum MemoryType { User, Project, Local, Managed, AutoMem, TeamMem }

MyAgent: memory/models.py
  └─→ enum MemoryType { user, feedback, project, reference }
```

#### 工具插件系统 (tools.ts, tools/*/)

**借鉴概念**:
- 每个工具独立目录
- 抽象基类 `Tool`
- 工具注册表 `ToolPool`
- MCP (Model Context Protocol) 集成
- 权限过滤 `filterToolsByDenyRules()`

**MyAgent 实现**:
- `tools/base.py` — `BaseTool` 抽象基类
- `tools/registry.py` — `ToolRegistry`
- `tools/read.py`, `tools/write.py`, `tools/edit.py`, `tools/glob.py`, `tools/grep.py`, `tools/bash.py`

**关键代码映射**:
```
Claude Code: tools.ts
  └─→ assembleToolPool() 动态组装工具池

MyAgent: tools/registry.py
  └─→ ToolRegistry.register_tools() 注册内置工具
```

#### Swarm/团队协作 (coordinator/)

**借鉴概念**:
- 协调器模式 `coordinator/`
- 团队上下文 `teamContext`
- 子 Agent 调用 `AgentTool`
- tmux/iTerm2 面板可视化

**MyAgent 实现**:
- `teams/models.py` — `Team`, `TeamMember` 数据类
- `teams/orchestrator.py` — `TeamOrchestrator` 编排引擎
- `tools/agent.py` — Agent 工具

### 2.2 Hermes Agent (`d:\源码库\hermes-agent`)

Hermes Agent 是 Python 写的多平台网关式 AI Agent。

#### Gateway 网关模式 (gateway/run.py)

**借鉴概念**:
- 多平台统一接入 (Discord, Slack, Telegram)
- LRU 会话缓存 (最大 128，1 小时 TTL)
- 轨迹记录 `trajectory.py`
- ShareGPT 格式导出

**MyAgent 实现**:
- `gateway/base.py` — `Platform` 基类
- `gateway/manager.py` — `GatewayManager` 会话池
- `gateway/feishu.py`, `gateway/slack.py`, `gateway/discord.py`, `gateway/telegram.py`

**关键代码映射**:
```
Hermes: gateway/run.py
  └─→ class AIAgent { batch_runner, trajectory, session_cache }

MyAgent: gateway/manager.py
  └─→ class GatewayManager { _sessions, _agents, _platforms }
```

#### Plan→Execute→Review 工作流

**借鉴概念**:
- Agent 循环 `agent/agent_loop.py`
- 记忆管理 `agent/memory_manager.py`
- Prompt 构建 `agent/prompt_builder.py`
- 轨迹追踪 `agent/trajectory.py`

**MyAgent 实现**:
- `tasks/models.py` — `Task`, `TaskStatus`, `SubTask` 数据类
- `tasks/engine.py` — `TaskEngine` 编排引擎
- 9 个状态: pending → planning → planned → executing → executed → reviewing → done/failed/cancelled

#### 配置管理 (config.yaml)

**借鉴概念**:
- YAML 配置文件
- 环境变量桥接
- 多层配置覆盖

**MyAgent 实现**:
- `config.yaml` — Agent 配置
- `gateway.yaml` — Gateway 配置
- `.env` — API Keys

### 2.3 OpenHarness (`d:\源码库\OpenHarness`)

OpenHarness 是开源的 Claude Code 替代品，Python 实现。

#### Workspace 结构 (memory/, config/paths.py)

**借鉴概念**:
- `SOUL.md` — Agent 灵魂/人格
- `user.md` — 用户画像模板
- `IDENTITY.md` — Agent 身份
- `memory/` — 持久化记忆目录
- `skills/` — 技能目录

**MyAgent 实现**:
- `workspace/templates.py` — 模板文件生成
- `workspace/manager.py` — `WorkspaceManager`
- 模板: `soul.md`, `user.md`, `identity.md`, `MEMORY.md`

**关键代码映射**:
```
OpenHarness: memory/paths.py
  └─→ get_memory_dir() → ~/.ohmo/memory/

MyAgent: workspace/manager.py
  └─→ get_workspace_dir() → ~/.myagent/
```

#### Agent 定义系统 (coordinator/agent_definitions.py)

**借鉴概念**:
- Markdown + YAML Frontmatter 定义 Agent
- `AgentDefinition` Pydantic 模型
- 专业化分工 (Explore, Plan, worker, verification)
- 三层加载 (内置 → 用户 → 插件)

**MyAgent 实现**:
- `agents/definitions.py` — `AgentDefinition` Pydantic 模型
- `agents/loader.py` — `AgentLoader` 三层加载
- 内置 Agent: general, plan, worker, explore, reviewer

**关键代码映射**:
```
OpenHarness: coordinator/agent_definitions.py
  └─→ AgentDefinition { name, role, system_prompt, tools, permissions }

MyAgent: agents/definitions.py
  └─→ AgentDefinition { name, system_prompt, tools, permission_mode, memory_scope }
```

#### 查询引擎 (engine/query_engine.py, engine/query.py)

**借鉴概念**:
- `QueryEngine` 拥有对话历史
- 流式事件 `AsyncIterator[StreamEvent]`
- 上下文压缩 `auto_compact_threshold_tokens`
- 工具感知循环 `run_query()`
- `MaxTurnsExceeded` 防止无限循环

**MyAgent 实现**:
- `engine/query_engine.py` — `QueryEngine` 主引擎
- `engine/stream_events.py` — `StreamEvent` 事件类型
- `engine/query.py` — `_run_loop()` 核心循环

**关键代码映射**:
```
OpenHarness: engine/query_engine.py
  └─→ class QueryEngine { _messages, _cost_tracker, submit_message() }

MyAgent: engine/query_engine.py
  └─→ class QueryEngine { _messages, _tools, submit_message() async }
```

#### 工具抽象基类 (tools/base.py)

**借鉴概念**:
- `BaseTool` 抽象基类
- Pydantic 输入验证
- `ToolRegistry` 注册表
- `to_api_schema()` 生成 API 格式

**MyAgent 实现**:
- `tools/base.py` — `BaseTool` 基类
- `tools/registry.py` — `ToolRegistry`
- 所有工具继承 `BaseTool`

### 2.4 OpenClaw (`d:\源码库\openclaw`)

OpenClaw 是 TypeScript 的可扩展 AI Agent 平台。

#### 插件系统 (plugins/)

**借鉴概念**:
- 完整生命周期 (加载 → 启用 → 运行 → 更新 → 卸载)
- 插件契约测试 `contracts/`
- SDK 支持 `plugin-sdk/`
- 钩子集成 `hooks/`

**MyAgent 实现** (部分):
- `plugins/loader.py` — 插件加载器 (待完善)
- `hooks/executor.py` — 钩子执行器

#### 上下文管理 (agents/context.ts)

**借鉴概念**:
- 极复杂的上下文窗口管理
- 多层缓存 `MODEL_CONTEXT_TOKEN_CACHE`
- 模型上下文窗口自动发现

**MyAgent 实现** (参考):
- `engine/query.py` — 上下文管理逻辑

#### 身份分层系统 (agents/identity.ts)

**借鉴概念**:
- 四层配置优先级
- 动态前缀
- 表情反馈

**MyAgent 实现** (参考):
- `agents/definitions.py` — `identity` 字段

---

## 3. 关键概念详解

### 3.1 Memory 系统设计

**来源**: Claude Code + OpenHarness

Claude Code 的 Memory 系统是最成熟的实现：
1. `MEMORY.md` 作为索引 (200行/25KB 上限)
2. 每个记忆独立文件
3. Frontmatter 格式: name, description, type
4. 自动收集: LLM 识别并保存

OpenHarness 的文件级记忆：
1. `memory/manager.py` 管理
2. 原子写入
3. 文件锁防止并发

**MyAgent 整合**:
- Frontmatter 格式 (Claude Code)
- 文件管理 (OpenHarness)
- 自动收集 (Claude Code)
- 增量缓冲 (自定义)

### 3.2 Workspace 结构

**来源**: OpenHarness

OpenHarness 的 Workspace 最完整：
- `SOUL.md` — Agent 灵魂
- `user.md` — 用户画像
- `IDENTITY.md` — Agent 身份
- `BOOTSTRAP.md` — 首次引导
- `memory/` — 记忆目录
- `skills/` — 技能目录

**MyAgent 整合**:
- 保留核心模板
- 增加 `MEMORY.md` 索引 (Claude Code)
- 支持多项目 `projects/`

### 3.3 Task Engine

**来源**: Hermes Agent + OpenHarness

Hermes 的 Plan→Execute→Review：
- 三个独立阶段
- 用户审批点
- 循环直到通过

OpenHarness 的任务聚焦：
- `tool_metadata` 中的状态追踪
- 目标、产物、验证

**MyAgent 整合**:
- Hermes 的三阶段模型
- OpenHarness 的状态追踪
- 9 状态机

### 3.4 流式输出

**来源**: OpenHarness

OpenHarness 的 `AsyncIterator[StreamEvent]`：
- `AssistantTextDelta` — 文本增量
- `ToolExecutionStarted` — 工具开始
- `ToolExecutionCompleted` — 工具完成
- `ErrorEvent` — 错误

**MyAgent 实现**:
- 完全复用 `engine/stream_events.py`
- 支持 TUI/Web UI 双端流式

---

## 4. 未直接借鉴但受启发的概念

| 概念 | 来源项目 | 说明 |
|------|----------|------|
| React Ink TUI | Claude Code | 终端富交互体验 |
| MCP 协议 | Claude Code | Model Context Protocol |
| 特性开关 | Claude Code | `feature()` 死代码消除 |
| SSRF 防护 | OpenClaw | 安全基础设施 |
| 文件锁 | OpenClaw | 原子写入 |
| 定时任务 | OpenClaw | Cron 调度器 |
| 远程桥接 | Claude Code | claude.ai WebSocket |
| 螺旋体 | Hermes | Docker/Singularity 支持 |

---

## 5. 如何使用本文档

### 5.1 追溯设计意图

当你发现某个功能设计不理想时，可以：
1. 找到对应的 MyAgent 模块
2. 查看"主要参考项目"和"参考路径"
3. 阅读原始实现
4. 理解设计意图后改进

### 5.2 避免重复造轮子

在实现新功能前，先检查：
1. Claude Code 是否有类似实现
2. OpenHarness 是否更简洁
3. Hermes Agent 是否有成熟方案
4. OpenClaw 是否有完整生态

### 5.3 保持一致性

如果需要修改已有功能：
1. 确保修改不破坏核心概念引用
2. 如果有更好的参考方案，先更新本文档
3. 提交时更新相关文档注释
