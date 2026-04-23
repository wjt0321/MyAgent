# Workspace 架构设计

> Workspace 是 MyAgent 的持久化存储层，为 Agent 提供"家"的概念。
> 灵感来源: OpenHarness (`memory/`, `config/paths.py`)

---

## 1. 设计目标

1. **有状态**: Agent 不再是每次重启就失忆的 Chat Bot
2. **结构化**: 清晰的目录结构，方便人工查看和编辑
3. **可扩展**: 支持多项目、多 Agent、多技能
4. **可移植**: 纯文件系统，无外部依赖

---

## 2. 目录结构

```
~/.myagent/                          # Workspace 根目录
├── soul.md                          # Agent 灵魂/人格 (系统级)
├── user.md                          # 用户画像 (系统级)
├── identity.md                      # Agent 身份 (系统级)
├── MEMORY.md                        # 记忆索引 (系统级)
├── memory/                          # 系统级记忆存储
│   ├── user_role.md
│   ├── feedback_style.md
│   └── project_context.md
├── skills/                          # 技能目录
├── projects/                        # 项目工作空间
│   └── default/                     # 默认项目
│       ├── .myagent/                # 项目级配置
│       │   ├── memory/              # 项目级记忆
│       │   ├── agents/              # 项目级 Agent
│       │   └── tasks/               # 任务历史
│       └── ...                      # 项目文件
├── sessions/                        # 对话历史
├── logs/                            # 日志
└── workspace/                       # 通用工作区
```

---

## 3. 核心文件说明

### 3.1 soul.md

**来源**: OpenHarness `SOUL.md`

定义 Agent 的核心人格和原则。

```markdown
# SOUL.md - Who You Are

You are MyAgent, an autonomous AI assistant.

## Core truths
- Be genuinely helpful, not performatively helpful
- Have judgment and explain your reasons
- Be resourceful before asking
- Earn trust through competence

## Boundaries
- Private things stay private
- When in doubt, ask before acting
```

### 3.2 user.md

**来源**: OpenHarness `user.md` + Claude Code 用户画像

引导式用户画像模板。

```markdown
# user.md - About Your Human

## Profile
- Name:
- Timezone:
- Languages:

## Defaults
- Preferred tone:
- Decision style:

## Ongoing context
- Main projects:
- Tools and platforms:

## Preferences
- What they want more of:
- What tends to annoy them:
```

### 3.3 identity.md

**来源**: OpenHarness `IDENTITY.md`

Agent 身份标识。

```markdown
# identity.md - Agent Identity

## Name
MyAgent

## Version
v0.11.0

## Capabilities
- Code understanding and generation
- Task planning and execution
- Multi-agent collaboration
- Memory persistence
```

### 3.4 MEMORY.md

**来源**: Claude Code MEMORY.md 索引

记忆索引文件，自动维护。

```markdown
# Memory Index

- [User Role](user_role.md) — 用户是后端工程师，专注 Python/Go
- [Feedback Style](feedback_style.md) — 喜欢简洁回答，不要总结
- [Project Context](project_context.md) — 正在开发 MyAgent 项目
```

---

## 4. 核心类

### 4.1 WorkspaceManager

```python
class WorkspaceManager:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = Path(workspace_dir)
        self.memory_dir = get_memory_dir(self.workspace_dir)

    def exists(self) -> bool:
        return self.workspace_dir.exists()

    def read_soul(self) -> str | None:
        path = self.workspace_dir / "soul.md"
        return path.read_text() if path.exists() else None

    def read_user_profile(self) -> str | None:
        path = self.workspace_dir / "user.md"
        return path.read_text() if path.exists() else None

    def get_memory_files(self) -> list[Path]:
        return sorted(self.memory_dir.glob("*.md"))
```

### 4.2 初始化流程

```python
def initialize_workspace(workspace_dir=None, context=None):
    ws = ensure_workspace(workspace_dir)
    for name in TEMPLATES:
        write_template(ws, name, context)
    return ws
```

---

## 5. 与参考项目的对比

| 维度 | MyAgent | OpenHarness | Claude Code |
|------|---------|-------------|-------------|
| 根目录 | `~/.myagent/` | `~/.ohmo/` | `~/.claude/` |
| Agent 灵魂 | `soul.md` | `SOUL.md` | 无独立文件 |
| 用户画像 | `user.md` | `user.md` | `user.md` |
| 记忆索引 | `MEMORY.md` | `MEMORY.md` | `MEMORY.md` |
| 项目空间 | `projects/` | 无 | `projects/<slug>/` |
| 技能目录 | `skills/` | `skills/` | 无 |

---

## 6. 使用方式

### 6.1 CLI

```bash
myagent init  # 初始化 Workspace
```

### 6.2 Python API

```python
from myagent.workspace.manager import WorkspaceManager

wm = WorkspaceManager()
soul = wm.read_soul()
user = wm.read_user_profile()
```

### 6.3 Web UI

Settings → Workspace 面板显示当前 Workspace 信息。
