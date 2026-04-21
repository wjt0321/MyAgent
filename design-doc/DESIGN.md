# MyAgent 架构设计文档

> 基于 hermes-agent、claude-code-source-code、openclaw、OpenHarness 四大开源 Agent 项目的深度解析与最优设计融合。

---

## 1. 设计哲学

### 1.1 核心原则

1. **Agent 即配置**：任何 Agent 的行为、能力、个性都应通过声明式配置定义，而非硬编码
2. **工具即插件**：所有能力通过工具暴露，工具通过插件扩展
3. **事件驱动一切**：内部通信全部采用事件流，确保松耦合和可观测性
4. **上下文安全第一**：并发 Agent 的上下文绝对隔离，永不污染
5. **渐进式复杂**：简单任务简单处理，复杂任务自动分解

### 1.2 命名

**MyAgent** —— 一个融合四大开源项目最优设计的下一代 AI Agent 平台。

---

## 2. 整体架构

```
+-------------------+     +-------------------+     +-------------------+
|   User Interfaces |     |   Gateway Layer   |     |   External APIs   |
|  (CLI / TUI / Web)|     | (Discord/Slack/   |     |  (LLM / Search /  |
|                   |     |  Telegram / API)  |     |   Browser / LSP)  |
+--------+----------+     +--------+----------+     +--------+----------+
         |                         |                          |
         v                         v                          v
+--------+----------------------------------------------------------+
|                        Orchestration Layer                        |
|  +---------------+  +---------------+  +-----------------------+  |
|  | SessionManager|  | AgentRegistry |  |   CoordinatorEngine   |  |
|  +---------------+  +---------------+  +-----------------------+  |
+--------+----------------------------------------------------------+
         |
         v
+--------+----------------------------------------------------------+
|                         Agent Core Layer                          |
|  +---------------+  +---------------+  +-----------------------+  |
|  |  QueryEngine  |  |  ToolRunner   |  |   MemoryManager       |  |
|  |  (事件循环)    |  |  (工具执行)    |  |   (记忆管理)           |  |
|  +---------------+  +---------------+  +-----------------------+  |
|  +---------------+  +---------------+  +-----------------------+  |
|  | PromptBuilder |  | CostTracker   |  |   TrajectoryLogger    |  |
|  |  (提示构建)    |  |  (成本追踪)    |  |   (轨迹记录)           |  |
|  +---------------+  +---------------+  +-----------------------+  |
+--------+----------------------------------------------------------+
         |
         v
+--------+----------------------------------------------------------+
|                        Extension Layer                            |
|  +---------------+  +---------------+  +-----------------------+  |
|  | PluginSystem  |  |   MCPSupport  |  |   HookExecutor        |  |
|  |  (插件系统)    |  |  (MCP协议)     |  |   (钩子执行)           |  |
|  +---------------+  +---------------+  +-----------------------+  |
+--------+----------------------------------------------------------+
         |
         v
+--------+----------------------------------------------------------+
|                      Infrastructure Layer                         |
|  +-----------+ +-----------+ +-----------+ +-----------------+  |
|  |  Config   | |  Network  | |  Security | |   Persistence   |  |
|  |  (配置)    | |  (网络)    | |  (安全)    | |   (持久化)       |  |
|  +-----------+ +-----------+ +-----------+ +-----------------+  |
+-------------------------------------------------------------------+
```

---

## 3. 核心模块设计

### 3.1 Agent 定义系统（源自 OpenHarness）

**设计**：Agent 通过 Markdown + YAML frontmatter 文件定义。

```yaml
---
name: code-explorer
description: 专门用于探索代码库的只读 Agent
tools: [Glob, Grep, Read, WebFetch]
disallowed_tools: [Write, Edit, Bash]
model: sonnet
effort: medium
permission_mode: dontAsk
max_turns: 20
memory: project
color: cyan
isolation: worktree
critical_system_reminder: "你是只读探索模式，严禁修改任何文件"
---

你是一个代码探索专家。你的任务是帮助用户理解代码库结构、
查找特定功能的实现位置、分析代码依赖关系。

## 工作原则

1. 搜索时先广后深：先用 Glob 找文件模式，再用 Grep 搜索内容
2. 分析时多文件关联：不要孤立看一个文件，要理解调用链
3. 报告要简洁：给出关键文件路径和核心发现
```

**加载优先级**：
1. 内置 Agent（`agents/builtin/`）
2. 用户自定义 Agent（`~/.myagent/agents/`）
3. 插件提供的 Agent（运行时加载）

**内置 Agent 类型**：

| Agent | 职责 | 工具集 | 模式 |
|-------|------|--------|------|
| `general` | 通用任务 | 全部 | 默认 |
| `explore` | 代码探索 | 只读工具 | 只读 |
| `plan` | 架构规划 | 只读工具 | 规划模式 |
| `worker` | 编码实现 | 全部 | 实现模式 |
| `verify` | 验证测试 | 只读+测试 | 验证模式 |
| `fix` | 故障修复 | 全部 | 修复模式 |

### 3.2 查询引擎（源自 OpenHarness + Claude Code）

**QueryEngine** 是 Agent 的核心循环控制器：

```python
class QueryEngine:
    """拥有对话历史、工具感知循环和流事件输出。"""

    def __init__(
        self,
        api_client: SupportsStreamingMessages,
        tool_registry: ToolRegistry,
        permission_checker: PermissionChecker,
        model: str,
        system_prompt: str,
        max_tokens: int = 4096,
        context_window_tokens: int | None = None,
        auto_compact_threshold: int | None = None,
        max_turns: int | None = 50,
    ):
        ...

    async def submit_message(
        self, prompt: str | ConversationMessage
    ) -> AsyncIterator[StreamEvent]:
        """提交用户消息并执行查询循环，返回流事件。"""
        ...

    async def continue_pending(self) -> AsyncIterator[StreamEvent]:
        """继续中断的工具循环，不添加新用户消息。"""
        ...
```

**事件流类型**（融合 Claude Code 的 StreamEvent 设计）：

```python
class StreamEvent(ABC): ...

class AssistantTextDelta(StreamEvent):
    text: str

class ToolExecutionStarted(StreamEvent):
    tool_name: str
    tool_use_id: str
    arguments: dict

class ToolExecutionCompleted(StreamEvent):
    tool_use_id: str
    result: ToolResult

class AssistantTurnComplete(StreamEvent):
    message: ConversationMessage
    usage: UsageSnapshot

class CompactProgressEvent(StreamEvent):
    message: str

class ErrorEvent(StreamEvent):
    error: Exception
    recoverable: bool
```

**查询循环核心逻辑**：

```
用户输入 → 追加到历史 → 调用LLM → 流式接收响应
    ↑                                      |
    |                                      v
    |                              检测工具调用?
    |                                      |
    |                              是 → 权限检查 → 执行工具
    |                                      |        |
    |                              否 ← 返回结果 ←-+
    |                              |
    +--- 继续循环（直到无工具调用或达到max_turns）
```

### 3.3 工具系统（源自 Claude Code + OpenHarness）

**工具抽象基类**：

```python
class BaseTool(ABC):
    name: str
    description: str
    input_model: type[BaseModel]

    @abstractmethod
    async def execute(
        self, arguments: BaseModel, context: ToolExecutionContext
    ) -> ToolResult:
        ...

    def is_read_only(self, arguments: BaseModel) -> bool:
        return False

    def to_api_schema(self) -> dict[str, Any]:
        ...
```

**内置工具集**：

| 类别 | 工具 | 说明 |
|------|------|------|
| 文件操作 | Read, Edit, Write, Glob, Grep | 代码库操作 |
| Shell | Bash, PowerShell | 命令执行 |
| Web | WebFetch, WebSearch | 网络访问 |
| 代码 | LSPTool | LSP 语言服务器 |
| Agent | AgentTool | 子 Agent 调用 |
| 任务 | TodoWrite, TaskCreate, TaskGet | 任务管理 |
| 系统 | AskUser, Stop, Brief | 交互控制 |

**工具注册表**：

```python
class ToolRegistry:
    def register(self, tool: BaseTool) -> None: ...
    def get(self, name: str) -> BaseTool | None: ...
    def list_tools(self) -> list[BaseTool]: ...
    def to_api_schema(self) -> list[dict[str, Any]]: ...
```

### 3.4 记忆系统（源自 OpenHarness + OpenClaw）

**记忆类型**：

| 类型 | 作用域 | 存储位置 | 生命周期 |
|------|--------|----------|----------|
| `session` | 当前会话 | 内存 | 会话结束 |
| `project` | 当前项目 | `.myagent/memory/` | 持久 |
| `user` | 用户级 | `~/.myagent/memory/` | 持久 |
| `auto` | 自动摘要 | 项目级 | 持久 |

**记忆管理**：

```python
class MemoryManager:
    def add_entry(self, title: str, content: str) -> Path: ...
    def list_entries(self) -> list[MemoryEntry]: ...
    def search(self, query: str) -> list[MemoryEntry]: ...
    def build_context(self, max_tokens: int) -> str: ...
```

**自动记忆索引**：
- 每个记忆条目是一个 Markdown 文件
- `MEMORY.md` 作为自动维护的索引
- 文件锁保证并发安全
- 原子写入保证数据完整性

### 3.5 上下文管理（源自 OpenClaw）

**智能上下文窗口管理**：

```python
class ContextManager:
    def __init__(self):
        self.token_cache: dict[str, int] = {}  # 模型ID → 上下文窗口
        self.runtime_state: ContextRuntimeState

    def resolve_context_tokens(
        self,
        model: str,
        provider: str | None = None,
        fallback: int = 128_000,
    ) -> int:
        """解析模型的有效上下文窗口大小。"""
        ...

    def should_compact(self, messages: list[Message]) -> bool:
        """判断是否需要压缩上下文。"""
        ...

    def compact(self, messages: list[Message]) -> list[Message]:
        """压缩对话历史，保留关键信息。"""
        ...
```

**自动压缩策略**：
1. 监控当前 token 使用量
2. 达到 `auto_compact_threshold` 时触发压缩
3. 保留系统提示词、用户目标、最近对话
4. 将早期对话摘要化
5. 遇到 "prompt too long" 错误时紧急压缩并重试

### 3.6 插件系统（源自 OpenClaw）

**插件生命周期**：

```
发现 → 加载 → 验证契约 → 启用 → 运行 → 更新 → 禁用 → 卸载
```

**插件结构**：

```
my-plugin/
├── myagent-plugin.yaml      # 插件元数据
├── tools/                   # 插件工具
│   └── MyTool.py
├── agents/                  # 插件Agent定义
│   └── my-agent.md
├── hooks/                   # 生命周期钩子
│   └── on_startup.py
└── commands/                # CLI命令扩展
    └── my_command.py
```

**钩子事件**：

| 事件 | 触发时机 |
|------|----------|
| `SESSION_START` | 会话开始时 |
| `USER_PROMPT_SUBMIT` | 用户提交输入时 |
| `TOOL_EXECUTION_BEFORE` | 工具执行前 |
| `TOOL_EXECUTION_AFTER` | 工具执行后 |
| `ASSISTANT_TURN_COMPLETE` | Assistant 轮次完成时 |
| `SESSION_END` | 会话结束时 |

### 3.7 MCP 支持（源自 Claude Code）

**MCP 集成**：

```python
class MCPManager:
    def load_servers(self, configs: dict[str, MCPServerConfig]) -> None: ...
    def get_tools(self) -> list[Tool]: ...
    def get_resources(self) -> list[Resource]: ...
    def call_tool(self, server: str, tool: str, args: dict) -> ToolResult: ...
```

**工具池组装**：

```python
def assemble_tool_pool(
    built_in_tools: list[Tool],
    mcp_tools: list[Tool],
    permission_context: PermissionContext,
) -> list[Tool]:
    """组装内置工具 + MCP 工具，去重并排序。"""
    ...
```

### 3.8 多 Agent 协作（源自 OpenHarness + Claude Code）

**Agent 分工流水线**：

```
用户请求
    |
    v
+--------+    +--------+    +--------+    +--------+
| Explore| →  |  Plan  | →  | Worker | →  | Verify |
| 探索   |    | 规划   |    | 实现   |    | 验证   |
+--------+    +--------+    +--------+    +--------+
    |              |              |              |
    v              v              v              v
 找文件/代码    设计方案      编写代码      测试验证
 理解现状      确定步骤      运行测试      检查回归
```

**并发安全**：

```python
# 使用 AsyncLocalStorage（TypeScript）或 contextvars（Python）
# 确保并发 Agent 的上下文隔离

agent_context = contextvars.ContextVar("agent_context", default=None)

def run_with_agent_context(ctx: AgentContext, fn: Callable) -> T:
    token = agent_context.set(ctx)
    try:
        return fn()
    finally:
        agent_context.reset(token)
```

### 3.9 网关层（源自 Hermes-Agent）

**网关架构**：

```
+--------------------------------------------------+
|                   Gateway Runner                  |
|  +-----------+ +-----------+ +-----------+       |
|  |  Discord  | |   Slack   | | Telegram  |       |
|  |  Adapter  | |  Adapter  | |  Adapter  |       |
|  +-----+-----+ +-----+-----+ +-----+-----+       |
|        |             |             |              |
|        +-------------+-------------+              |
|                      |                            |
|              +-------v--------+                   |
|              | Message Router |                   |
|              +-------+--------+                   |
|                      |                            |
|              +-------v--------+                   |
|              |  Session Pool  |                   |
|              |  (LRU Cache)   |                   |
|              +----------------+                   |
+--------------------------------------------------+
```

**会话缓存**：
- LRU 策略，最大 128 个会话
- 1 小时空闲 TTL 自动驱逐
- 每个会话独立 QueryEngine 实例

### 3.10 轨迹追踪（源自 Hermes-Agent）

**轨迹记录**：

```python
class TrajectoryLogger:
    def log_turn(
        self,
        messages: list[Message],
        model: str,
        completed: bool,
    ) -> None:
        """记录一轮对话轨迹。"""
        ...

    def export_sharegpt(self, path: Path) -> None:
        """导出为 ShareGPT 格式训练数据。"""
        ...
```

**轨迹用途**：
- 调试和审计
- 训练数据收集
- Agent 行为分析
- 失败案例复盘

---

## 4. 数据模型

### 4.1 核心类型

```python
class Message:
    role: Literal["system", "user", "assistant"]
    content: list[TextBlock | ToolUseBlock | ToolResultBlock | ImageBlock]

class TextBlock:
    type: Literal["text"] = "text"
    text: str

class ToolUseBlock:
    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: dict[str, Any]

class ToolResultBlock:
    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str
    content: str | list[TextBlock | ImageBlock]
    is_error: bool = False

class ToolResult:
    output: str
    is_error: bool = False
    metadata: dict[str, Any] = {}
```

### 4.2 Agent 定义模型

```python
class AgentDefinition(BaseModel):
    name: str
    description: str
    system_prompt: str | None = None
    tools: list[str] | None = None           # None = 全部工具
    disallowed_tools: list[str] | None = None
    model: str | None = None                 # "inherit" 继承父级
    effort: str | int | None = None          # "low" | "medium" | "high"
    permission_mode: str | None = None
    max_turns: int | None = None
    skills: list[str] = []
    mcp_servers: list[str | dict] | None = None
    hooks: dict[str, Any] | None = None
    color: str | None = None
    background: bool = False
    initial_prompt: str | None = None
    memory: str | None = None                # "user" | "project" | "local"
    isolation: str | None = None             # "worktree" | "remote"
    critical_system_reminder: str | None = None
```

---

## 5. 接口设计

### 5.1 CLI 接口

```bash
# 交互式会话
myagent

# 指定Agent
myagent --agent code-explorer

# 非交互式执行
myagent -p "解释这个函数的作用" --file src/main.py

# 子命令
myagent plugin list
myagent plugin install <source>
myagent mcp list
myagent mcp add <name> <config>
myagent agent list
myagent agent create <name>

# 网关模式
myagent gateway --discord --slack
```

### 5.2 配置文件

```yaml
# ~/.myagent/config.yaml
model:
  default: "anthropic/claude-sonnet-4"
  fallback: "openai/gpt-4o"

providers:
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
  openai:
    api_key: "${OPENAI_API_KEY}"
  openrouter:
    api_key: "${OPENROUTER_API_KEY}"

context:
  auto_compact_threshold: 0.8
  max_turns: 50

memory:
  enabled: true
  scope: "project"

plugins:
  enabled:
    - my-plugin
    - another-plugin

mcp:
  servers:
    filesystem:
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/projects"]

gateway:
  discord:
    token: "${DISCORD_TOKEN}"
  slack:
    token: "${SLACK_TOKEN}"

logging:
  level: "info"
  trajectory: true
  trajectory_path: "~/.myagent/trajectories/"
```

---

## 6. 安全设计

### 6.1 权限系统

```python
class PermissionChecker:
    def check_tool_permission(
        self,
        tool_name: str,
        arguments: dict,
        context: PermissionContext,
    ) -> PermissionResult:
        ...
```

**权限模式**：

| 模式 | 说明 |
|------|------|
| `default` | 危险操作需确认 |
| `acceptEdits` | 自动接受文件编辑 |
| `bypassPermissions` | 绕过所有权限检查（危险） |
| `plan` | 计划模式，执行前需确认 |
| `dontAsk` | 静默模式，不询问用户 |

### 6.2 安全基础设施（源自 OpenClaw）

- **SSRF 防护**：限制内部网络访问
- **沙箱隔离**：敏感操作在沙箱中执行
- **文件锁**：防止并发文件操作冲突
- **敏感信息脱敏**：日志中自动脱敏 API Key、Token
- **命令审批**：危险命令需用户显式确认

---

## 7. 部署架构

### 7.1 本地模式

```
用户终端 → MyAgent CLI → LLM API
                ↓
           本地文件系统
```

### 7.2 网关模式

```
Discord/Slack/Telegram → Gateway → Session Pool → Agent Engine → LLM API
                              ↓
                         本地文件系统
```

### 7.3 Swarm 模式

```
+--------------------------------------------------+
|                    Team Lead                      |
|  +-------------------------------------------+   |
|  |  CoordinatorEngine                         |   |
|  |  - 任务分解                                |   |
|  |  - 结果汇总                                |   |
|  +-------------------------------------------+   |
+--+----------+----------+----------+----------+---+
   |          |          |          |          |
   v          v          v          v          v
+--+--+   +--+--+   +--+--+   +--+--+   +--+--+
|Explore|  |Plan |   |Worker|  |Worker|  |Verify|
+-------+  +-----+   +------+  +------+  +------+
```

---

## 8. 技术选型

| 领域 | 选型 | 理由 |
|------|------|------|
| **语言** | Python 3.11+ | 生态丰富，AI/ML 库支持最好 |
| **异步** | asyncio | 标准库，与 LLM 流式输出天然契合 |
| **CLI** | Typer + Rich | 现代 Python CLI，类型安全，TUI 美观 |
| **数据验证** | Pydantic v2 | 配置验证、工具输入验证、API 模式生成 |
| **LLM 接口** | Anthropic Messages API + OpenAI | 双协议支持，工具调用标准 |
| **状态管理** | 自定义 Store + dataclasses | 轻量，无需引入 Redux 复杂度 |
| **配置** | YAML + 环境变量 + Pydantic | 灵活且类型安全 |
| **网络** | httpx + 自研重试层 | 异步 HTTP + 企业级重试/退避 |
| **持久化** | 文件系统 + SQLite | 简单可靠，无需外部依赖 |
| **测试** | pytest + pytest-asyncio | Python 标准测试栈 |

---

## 9. 开发路线图

### Phase 1: 核心引擎（MVP）
- [x] QueryEngine 实现
- [x] 基础工具集（Read, Edit, Write, Bash, Glob, Grep）
- [x] Agent 定义系统
- [x] CLI 交互界面
- [x] 记忆系统

### Phase 2: 扩展能力
- [x] 插件系统
- [x] MCP 支持
- [x] Web 工具（WebFetch, WebSearch）
- [x] 子 Agent 调用
- [x] 任务管理（TodoWrite）

### Phase 3: 生产级
- [x] 网关层（Discord, Slack, Telegram）
- [x] Swarm 多 Agent 协作
- [x] 轨迹追踪与训练数据导出
- [x] 成本追踪
- [x] 安全基础设施

### Phase 4: 高级特性
- [ ] LSP 集成
- [ ] TTS/音频支持
- [ ] 图像理解
- [ ] 远程桥接
- [ ] 定时任务

---

## 10. 参考与致谢

本设计文档融合了以下四个优秀开源项目的最佳实践：

1. **[hermes-agent](d:\源码库\hermes-agent)** —— 网关架构、轨迹追踪、容器化执行
2. **[claude-code-source-code](d:\源码库\claude-code-source-code)** —— 事件驱动、工具插件化、AsyncLocalStorage、MCP、Swarm
3. **[openclaw](d:\源码库\openclaw)** —— 插件系统、智能上下文管理、企业级基础设施、多模态
4. **[OpenHarness](d:\源码库\OpenHarness)** —— Agent定义系统、查询引擎、专业化分工、Pydantic工具

---

*文档版本: 1.0*
*最后更新: 2026-04-21*
