# OpenHarness 源代码架构解析报告

## 1. 项目概览

| 属性 | 内容 |
|------|------|
| **语言** | Python 3.10+ |
| **核心定位** | 开源 Claude Code 替代品，AI 驱动的编程助手 |
| **架构风格** | 分层架构 + Agent 定义系统 + Swarm 协作 |
| **依赖核心** | Pydantic、Typer、YAML、Anthropic API |

## 2. 目录结构与模块划分

```
OpenHarness/src/openharness/
├── __main__.py                 # 程序入口
├── cli.py                      # Typer CLI（子命令丰富）
├── engine/                     # 核心引擎
│   ├── query_engine.py         # 查询引擎：对话历史 + 工具感知循环
│   ├── query.py                # 核心查询循环：工具执行、流事件、上下文压缩
│   ├── messages.py             # 消息类型定义
│   ├── stream_events.py        # 流事件类型
│   └── cost_tracker.py         # 成本追踪
├── coordinator/                # 协调器
│   ├── agent_definitions.py    # Agent 定义系统（YAML frontmatter）
│   └── coordinator_mode.py     # 协调器模式
├── tools/                      # 工具系统
│   ├── base.py                 # 工具基类 + 注册表
│   └── agent_tool.py           # Agent 工具（子 Agent 调用）
├── memory/                     # 记忆系统
│   ├── manager.py              # 记忆文件管理
│   └── paths.py                # 记忆路径
├── swarm/                      # Swarm 集群
│   ├── types.py                # Swarm 类型定义（PaneBackend 协议等）
│   └── ...
├── bridge/                     # 桥接层
│   └── manager.py              # 前后端桥接
├── ui/                         # 用户界面
│   └── app.py                  # TUI/React 前端
├── api/                        # API 客户端
│   └── client.py               # 流式消息客户端
├── permissions/                # 权限系统
│   └── checker.py              # 权限检查器
├── hooks/                      # 钩子系统
│   └── executor.py             # 钩子执行器
├── config/                     # 配置管理
│   └── paths.py                # 配置路径
├── services/                   # 服务层
│   └── cron_scheduler.py       # Cron 调度器
└── plugins/                    # 插件系统
    ├── installer.py            # 插件安装器
    └── loader.py               # 插件加载器
```

## 3. 核心架构设计

### 3.1 查询引擎 (`engine/query_engine.py`)
- **对话所有权**：`QueryEngine` 拥有完整的对话历史和工具感知循环
- **状态管理**：内部维护 `_messages` 列表和 `_cost_tracker`
- **可变性设计**：支持运行时更新 API 客户端、模型、系统提示词、最大轮数
- **协调器上下文**：`_build_coordinator_context_message()` 支持协调器模式注入上下文
- **挂起检测**：`has_pending_continuation()` 检测工具结果等待后续模型轮次
- **流式输出**：`submit_message()` 和 `continue_pending()` 返回 `AsyncIterator[StreamEvent]`

### 3.2 查询循环 (`engine/query.py`)
- **工具感知循环**：核心 `run_query()` 函数驱动 Agent 循环
- **流事件系统**：`StreamEvent` 层次结构（文本增量、工具执行、错误、状态等）
- **上下文压缩**：`auto_compact_threshold_tokens` 自动压缩对话记忆
- **过长处理**：`_is_prompt_too_long_error()` 检测并自动压缩重试
- **任务聚焦**：`tool_metadata` 中的 `task_focus_state` 追踪目标、产物、验证状态
- **最大轮数**：`MaxTurnsExceeded` 异常防止无限循环
- **钩子集成**：`HookEvent` 在关键节点触发外部逻辑

### 3.3 Agent 定义系统 (`coordinator/agent_definitions.py`)
- **YAML Frontmatter**：Agent 定义使用 Markdown + YAML 前置元数据
- **Pydantic 模型**：`AgentDefinition` 类完整定义 Agent 配置
- **内置 Agent**：general-purpose、Explore、Plan、worker、verification、claude-code-guide、statusline-setup 等
- **专业化分工**：
  - `Explore`：只读代码探索专家
  - `Plan`：架构规划专家（只读）
  - `worker`：实现执行专家
  - `verification`：验证专家（尝试破坏实现）
- **权限模式**：`default`, `acceptEdits`, `bypassPermissions`, `plan`, `dontAsk`
- **记忆作用域**：`user`, `project`, `local`
- **隔离模式**：`worktree`, `remote`
- **三层加载**：内置 → 用户定义 (~/.openharness/agents/) → 插件

### 3.4 工具系统 (`tools/base.py`)
- **抽象基类**：`BaseTool` 定义工具接口（名称、描述、输入模型、执行）
- **Pydantic 输入**：所有工具输入通过 Pydantic 模型验证
- **注册表模式**：`ToolRegistry` 管理工具注册和查找
- **API 模式生成**：`to_api_schema()` 自动生成 Anthropic Messages API 格式
- **只读标记**：`is_read_only()` 支持权限系统判断

### 3.5 记忆系统 (`memory/manager.py`)
- **文件级记忆**：每个记忆条目是一个 Markdown 文件
- **索引管理**：`MEMORY.md` 作为记忆索引，自动维护
- **文件锁**：`exclusive_file_lock` 防止并发写入
- **原子写入**：`atomic_write_text` 确保写入安全

### 3.6 Swarm 系统 (`swarm/types.py`)
- **协议设计**：`PaneBackend` 协议抽象 tmux/iTerm2 终端面板
- **后端类型**：`subprocess`, `in_process`, `tmux`, `iterm2`
- **队友身份**：`TeammateIdentity` 标识团队成员
- **生成配置**：`TeammateSpawnConfig` 完整配置队友生成参数
- **消息传递**：`TeammateMessage` 支持团队成员间通信

## 4. 关键技术选型

| 技术领域 | 选型 | 评价 |
|---------|------|------|
| LLM 接口 | Anthropic Messages API | 原生支持工具调用和流式输出 |
| CLI 框架 | Typer | 现代 Python CLI，类型安全 |
| 数据验证 | Pydantic v2 | 配置验证、工具输入验证 |
| 配置格式 | YAML + Markdown | Agent 定义使用 YAML frontmatter，优雅 |
| 异步框架 | asyncio | 标准库，流式事件处理 |
| 状态持久化 | 文件系统 | 简单可靠，记忆使用 Markdown |

## 5. 独特功能特性

1. **Agent 定义系统**：Markdown + YAML frontmatter 定义 Agent，极其优雅
2. **专业化 Agent 分工**：Explore/Plan/worker/verification 的专业分工模式
3. **三层 Agent 加载**：内置 → 用户 → 插件的优先级加载机制
4. **自动上下文压缩**：token 阈值触发自动压缩，保持对话流畅
5. **任务聚焦状态**：`tool_metadata` 中的结构化任务追踪
6. **Swarm 终端可视化**：tmux/iTerm2 面板支持多 Agent 可视化协作
7. **成本追踪**：内置 `CostTracker` 追踪 API 调用成本
8. **钩子系统**：`HookEvent` 在关键生命周期节点触发外部逻辑
9. **Cron 调度器**：内置定时任务支持
10. **记忆索引**：自动维护的 Markdown 记忆索引系统

## 6. 代码质量与可扩展性评估

| 维度 | 评分 | 说明 |
|------|------|------|
| 代码组织 | ★★★★★ | 分层清晰，模块职责单一 |
| 类型安全 | ★★★★★ | Python 3.10+ 类型注解 + Pydantic，非常严格 |
| 可测试性 | ★★★★☆ | 核心引擎可测试，CLI 层测试需额外工具 |
| 可扩展性 | ★★★★★ | Agent 定义、插件、工具注册表，扩展性优秀 |
| 文档 | ★★★★☆ | 代码注释详尽，Agent 定义有完整字段文档 |

## 7. 设计亮点总结

- **Agent 即配置**：通过 YAML frontmatter 定义 Agent 是最优雅的设计之一
- **专业化分工**：Explore → Plan → worker → verification 的流水线分工
- **查询引擎封装**：`QueryEngine` 将对话历史、工具循环、流事件完美封装
- **任务聚焦元数据**：`tool_metadata` 中的结构化状态追踪是智能 Agent 的关键
- **Swarm 协议抽象**：`PaneBackend` 协议让多后端支持变得简洁
- **自动压缩策略**：智能的上下文压缩避免手动管理 token 限制

## 8. 潜在改进点

- 相比 Claude Code，工具数量较少（但可通过 MCP 扩展）
- UI 层相对简单，TUI 体验有待提升
- 缺少内置的代码搜索工具（LSP、Grep 等）
- 插件系统相比 OpenClaw 的成熟度有差距
- 多模态支持（图像、音频）尚未体现
