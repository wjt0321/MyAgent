# Agent Teams 多 Agent 协作设计

> Agent Teams 支持多 Agent 并行协作，角色分工。
> 灵感来源: Hermes Agent (Agent Teams) + Claude Code (Swarm)

---

## 1. 设计目标

1. **角色分工**: 不同 Agent 承担不同职责
2. **并行执行**: 多个 Agent 同时工作
3. **结果汇总**: 整合多个 Agent 的输出
4. **状态追踪**: 实时显示团队状态

---

## 2. 团队角色

### 2.1 默认团队

| 角色 | Agent | 职责 | 头像颜色 |
|------|-------|------|----------|
| Planner | `plan` | 创建执行计划 | `#f59e0b` (黄色) |
| Explorer | `explore` | 调查代码库 | `#10b981` (绿色) |
| Executor | `worker` | 实现功能 | `#6366f1` (紫色) |
| Reviewer | `reviewer` | 审查代码 | `#ec4899` (粉色) |

### 2.2 TeamRole 枚举

```python
class TeamRole(Enum):
    LEAD = "lead"           # 负责人
    PLANNER = "planner"     # 规划师
    EXECUTOR = "executor"   # 执行者
    REVIEWER = "reviewer"   # 审查员
    EXPLORER = "explorer"   # 探索者
    SPECIALIST = "specialist" # 专家
```

---

## 3. 核心类

### 3.1 TeamMember

```python
@dataclass
class TeamMember:
    id: str
    name: str              # Agent 名称
    role: TeamRole
    description: str
    status: str            # idle | busy | offline
    current_task: str | None
    completed_tasks: int
    failed_tasks: int
    avatar_color: str
```

### 3.2 Team

```python
@dataclass
class Team:
    id: str
    name: str
    description: str
    members: list[TeamMember]
    active: bool

    def get_available_member(self, role: TeamRole | None = None) -> TeamMember | None:
        # 获取空闲成员

    def update_member_status(self, name: str, status: str, task: str | None):
        # 更新成员状态
```

### 3.3 TeamOrchestrator

```python
class TeamOrchestrator:
    ROLE_AGENT_MAP = {
        TeamRole.PLANNER: "plan",
        TeamRole.EXPLORER: "explore",
        TeamRole.EXECUTOR: "worker",
        TeamRole.REVIEWER: "reviewer",
    }

    def assign_subtask(self, subtask: SubTask) -> TeamMember | None:
        # 根据角色分配子任务

    def release_member(self, member_name: str, success: bool):
        # 任务完成后释放成员

    async def execute_with_team(self, task: Task) -> AsyncIterator[dict]:
        # 使用团队执行任务
```

---

## 4. 协作流程

```
用户请求
    ↓
任务分解 (Plan Agent)
    ↓
┌──────────────────────────────────┐
│     TeamOrchestrator 分配任务     │
├────────┬────────┬────────┬───────┤
│ explore│ worker │ worker │reviewer│
│  探索   │  实现   │  实现   │ 审查   │
├────────┴────────┴────────┴───────┤
│         TeamOrchestrator 汇总       │
└──────────────────────────────────┘
    ↓
结果交付用户
```

---

## 5. 与参考项目的对比

| 维度 | MyAgent | Hermes Agent | Claude Code |
|------|---------|--------------|-------------|
| 团队概念 | Team + TeamMember | Agent Teams | Swarm + teamContext |
| 角色定义 | TeamRole 枚举 | 动态注册 | 子 Agent |
| 任务分配 | TeamOrchestrator | Coordinator | AgentTool |
| 并行执行 | 支持 | 支持 | 支持 |
| 状态追踪 | 实时 | 简单 | 复杂 |
| Web UI | 团队面板 | 无 | tmux/iTerm2 |

---

## 6. 使用方式

### 6.1 Web UI

Sidebar → 团队面板：
- 显示团队成员列表
- 每个成员：头像、名称、角色、状态
- 状态指示灯：绿色(空闲)、黄色(忙碌)、灰色(离线)
- 底部统计：空闲数/忙碌数/完成数

### 6.2 Python API

```python
from myagent.teams.orchestrator import TeamOrchestrator
from myagent.tasks.engine import TaskEngine
from myagent.web.engine_manager import WebEngineManager

em = WebEngineManager()
te = TaskEngine(em)
orchestrator = TeamOrchestrator(te)

# 获取团队状态
status = orchestrator.get_team_status()

# 使用团队执行任务
async for event in orchestrator.execute_with_team(task):
    print(event)
```
