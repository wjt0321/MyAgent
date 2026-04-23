# MyAgent 系统架构总览

> 本文档描述 MyAgent 的整体架构设计、模块划分和技术选型。
> 基于 v0.11.0 版本，涵盖 Workspace、Memory、Task Engine、Agent Teams、Codebase 五大子系统。

---

## 1. 架构全景

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interfaces                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   TUI    │  │  Web UI  │  │ Gateway  │  │   CLI    │       │
│  │ (Textual)│  │(FastAPI) │  │(Multi-  │  │ (Click)  │       │
│  │          │  │          │  │ platform)│  │          │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┘
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             │
              ┌──────────────┴──────────────┐
              │      MyAgent Core Layer      │
              │  ┌────────────────────────┐  │
              │  │     Query Engine       │  │
              │  │  (对话循环 + 工具调用)  │  │
              │  └────────────────────────┘  │
              │  ┌────────┐  ┌────────────┐  │
              │  │ Agent  │  │ Tool       │  │
              │  │ Loader │  │ Registry   │  │
              │  └────────┘  └────────────┘  │
              │  ┌────────┐  ┌────────────┐  │
              │  │Memory  │  │ Cost       │  │
              │  │Manager │  │ Tracker    │  │
              │  └────────┘  └────────────┘  │
              └──────────────┬──────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
   │ Workspace│         │  Task   │         │  Team   │
   │  Layer   │         │ Engine  │         │Orchestr.│
   └────┬────┘         └────┬────┘         └────┬────┘
        │                   │                   │
   ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
   │ Codebase │         │  Plan   │         │  Agent  │
   │  Search  │         │ Execute │         │ Members │
   │          │         │ Review  │         │         │
   └─────────┘         └─────────┘         └─────────┘
```

---

## 2. 核心模块

### 2.1 Query Engine

**职责**: 对话循环的核心引擎，管理消息历史、工具调用、流式输出。

**关键类**:
- `QueryEngine` — 主引擎，维护 `_messages` 和工具注册表
- `StreamEvent` — 流事件层次结构（文本增量、工具执行、错误等）
- `PermissionChecker` — 权限审批系统

**参考来源**:
- **OpenHarness** (`engine/query_engine.py`) — 对话所有权、状态管理、流式输出
- **Claude Code** (`main.tsx`) — 事件驱动架构、React Ink TUI 集成

---

### 2.2 Agent System

**职责**: Agent 定义、加载、切换。

**关键类**:
- `AgentDefinition` — Pydantic 模型定义 Agent 配置
- `AgentLoader` — 三层加载：内置 → 用户定义 → 插件
- `ToolRegistry` — 工具注册与查找

**参考来源**:
- **OpenHarness** (`coordinator/agent_definitions.py`) — YAML Frontmatter 定义 Agent
- **Claude Code** (`utils/model/agent.ts`) — Agent 模型选择与管理

---

### 2.3 Tool System

**职责**: 工具抽象、注册、执行。

**内置工具**:
| 工具 | 功能 | 来源 |
|------|------|------|
| `Read` | 文件读取 | OpenHarness |
| `Write` | 文件写入 | OpenHarness |
| `Edit` | 文件编辑 | OpenHarness |
| `Bash` | Shell 命令 | Claude Code |
| `Glob` | 文件匹配 | Claude Code |
| `Grep` | 代码搜索 | Claude Code |

**参考来源**:
- **Claude Code** (`tools/`) — 30+ 专业工具设计，工具即插件
- **OpenHarness** (`tools/base.py`) — 抽象基类 + Pydantic 输入验证

---

## 3. 五大子系统

### 3.1 Workspace 系统

**定位**: Agent 的"家"，持久化存储所有配置和状态。

**目录结构**:
```
~/.myagent/
├── soul.md              # Agent 灵魂/人格
├── user.md              # 用户画像
├── identity.md          # Agent 身份
├── memory/              # 持久化记忆
├── skills/              # 技能目录
├── projects/            # 项目工作空间
├── sessions/            # 对话历史
└── logs/                # 日志
```

**参考来源**:
- **OpenHarness** (`memory/`, `config/paths.py`) — `SOUL.md` + `user.md` + `IDENTITY.md`
- **Claude Code** (`memory/types.ts`) — MEMORY.md 索引 + 分类记忆文件

**详细文档**: [02-workspace.md](02-workspace.md)

---

### 3.2 Memory 系统

**定位**: 让 Agent 记住用户，越用越懂。

**四种记忆类型**:
| 类型 | 用途 | 示例 |
|------|------|------|
| `user` | 用户画像 | 技术背景、偏好 |
| `feedback` | 反馈指导 | 喜欢简洁、不要总结 |
| `project` | 项目上下文 | 当前目标、决策 |
| `reference` | 外部引用 | 文档链接、系统信息 |

**存储格式**: Markdown + YAML Frontmatter

**参考来源**:
- **Claude Code** — MEMORY.md 索引（200 行/25KB 上限），Frontmatter 格式
- **OpenHarness** — `memory/manager.py` 文件级记忆，原子写入

**详细文档**: [03-memory.md](03-memory.md)

---

### 3.3 Task Engine (Plan→Execute→Review)

**定位**: 复杂任务分解、执行、审查的闭环工作流。

**状态机**:
```
User Request → Planning → Planned → Executing → Executed → Reviewing → Done
                    ↑___________________________________________|
                    (循环直到通过审查)
```

**参考来源**:
- **Hermes Agent** — Plan → Execute → Review 工作流
- **OpenHarness** — `tool_metadata` 中的 `task_focus_state`

**详细文档**: [04-task-engine.md](04-task-engine.md)

---

### 3.4 Agent Teams

**定位**: 多 Agent 并行协作，角色分工。

**默认团队**:
| 角色 | Agent | 职责 |
|------|-------|------|
| Planner | `plan` | 创建执行计划 |
| Explorer | `explore` | 调查代码库 |
| Executor | `worker` | 实现功能 |
| Reviewer | `reviewer` | 审查代码 |

**参考来源**:
- **Hermes Agent** — Agent Teams 协作模式
- **Claude Code** (`coordinator/`) — 协调器模式、Swarm 团队

**详细文档**: [05-agent-teams.md](05-agent-teams.md)

---

### 3.5 Codebase 理解

**定位**: 自动扫描、索引、搜索代码库。

**功能**:
- 自动扫描 25+ 种语言
- 生成 `code