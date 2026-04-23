# Plan→Execute→Review 工作流设计

> Task Engine 是复杂任务分解、执行、审查的闭环工作流。
> 灵感来源: Hermes Agent (`agent/agent_loop.py`) + OpenHarness (`engine/query.py`)

---

## 1. 设计目标

1. **任务分解**: 将复杂请求拆分为可执行的子任务
2. **用户审批**: 计划生成后需用户批准才执行
3. **执行追踪**: 实时显示每个子任务的进度
4. **质量审查**: 执行完成后自动审查结果

---

## 2. 状态机

```
┌─────────┐    plan     ┌──────────┐   approve   ┌───────────┐
│ PENDING │ ──────────→ │ PLANNING │ ──────────→ │  PLANNED  │
└─────────┘             └──────────┘             └─────┬─────┘
                                                       │
                                                       │ execute
                                                       ↓
┌─────────┐   review    ┌───────────┐   execute   ┌───────────┐
│   DONE  │ ←────────── │ REVIEWING │ ←────────── │ EXECUTING │
└─────────┘             └───────────┘             └─────┬─────┘
    ↑                                                   │
    │              fail                                 │
    └───────────────────────────────────────────────────┘

┌─────────┐
│ FAILED  │ ←── 任何阶段失败
└─────────┘

┌───────────┐
│ CANCELLED │ ←── 用户取消
└───────────┘
```

---

## 3. 核心类

### 3.1 Task

```python
@dataclass
class Task:
    id: str
    title: str
    description: str
    status: TaskStatus
    subtasks: list[SubTask]
    result: TaskResult | None
    plan_approved: bool
    review_passed: bool
```

### 3.2 SubTask

```python
@dataclass
class SubTask:
    id: str
    description: str
    status: TaskStatus
    agent: str          # 执行 Agent
    result: str
    error: str | None
```

### 3.3 TaskResult

```python
@dataclass
class TaskResult:
    success: bool
    summary: str
    deliverables: list[str]
    issues: list[str]
    suggestions: list[str]
```

### 3.4 TaskEngine

```python
class TaskEngine:
    def __init__(self, engine_manager: WebEngineManager):
        self.engine_manager = engine_manager

    async def create_plan(self, request: str) -> Task:
        # 使用 LLM 生成任务计划

    async def execute_task(self, task: Task) -> AsyncIterator[dict]:
        # 执行所有子任务，流式输出进度

    async def review_task(self, task: Task) -> TaskResult:
        # 审查执行结果
```

---

## 4. 工作流详解

### 4.1 Plan 阶段

1. 用户输入 `/plan <请求>`
2. LLM 分析请求，生成 JSON 格式的计划
3. 计划包含 3-10 个子任务
4. 每个子任务指定执行 Agent

**Prompt 设计**:
```
分析用户请求并创建详细执行计划。
输出 JSON:
{
  "title": "任务标题",
  "subtasks": [
    {"description": "步骤描述", "agent": "worker"}
  ]
}
```

### 4.2 Execute 阶段

1. 用户批准计划
2. 按顺序执行每个子任务
3. 每个子任务使用指定 Agent 的 QueryEngine
4. 流式输出执行进度

### 4.3 Review 阶段

1. 所有子任务完成后
2. LLM 审查执行结果
3. 输出质量报告
4. 如果失败，返回 Execute 阶段重试

---

## 5. 与参考项目的对比

| 维度 | MyAgent | Hermes Agent | OpenHarness |
|------|---------|--------------|-------------|
| 工作流 | Plan→Execute→Review | Plan→Execute→Review | Task Focus State |
| 状态机 | 9 状态 | 简单状态 | tool_metadata |
| 用户审批 | 计划批准后执行 | 无明确审批 | 无 |
| 子任务 | 3-10 个 | 未明确 | task_focus_state |
| 审查 | LLM 自动审查 | 人工审查 | 自动验证 |
| Web UI | 任务面板 + 审批 Modal | 无 | 无 |

---

## 6. 使用方式

### 6.1 Web UI

输入 `/plan <请求>` 触发任务规划：
1. 显示计划步骤列表
2. 用户点击"批准并执行"
3. 实时显示执行进度
4. 完成后显示审查结果

### 6.2 Python API

```python
from myagent.tasks.engine import TaskEngine
from myagent.web.engine_manager import WebEngineManager

em = WebEngineManager()
te = TaskEngine(em)

# 创建计划
task = await te.create_plan("实现用户认证功能")

# 执行
async for event in te.execute_task(task):
    print(event)

# 审查
result = await te.review_task(task)
```
