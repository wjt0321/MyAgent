# TUI + QueryEngine 完整集成实施计划

> **目标**: 让 TUI 使用 QueryEngine 作为核心循环，实现完整的工具调用、权限审批、成本追踪能力。

**架构**: TUI App 初始化 QueryEngine（包含 ToolRegistry、PermissionChecker、CostTracker），通过事件流处理 AssistantTextDelta、ToolExecutionStarted/Completed 等事件，实现真正的 Agent 能力。

**技术栈**: Textual, QueryEngine, PermissionChecker, CostTracker

---

## Task 1: TUI 集成 QueryEngine（事件流处理）

**Files:**
- Modify: `src/myagent/tui/app.py`
- Test: `tests/test_tui_integration.py`

**Step 1: 编写测试**

创建 `tests/test_tui_integration.py`：
- 测试 QueryEngine 初始化
- 测试事件流正确处理

**Step 2: 修改 TUI App**

在 `MyAgentApp.__init__` 中：
1. 创建 `ToolRegistry` 并注册所有内置工具
2. 创建 `PermissionChecker`
3. 创建 `CostTracker`
4. 创建 `QueryEngine`（替代直接调用 provider）

修改 `_handle_user_message`：
- 使用 `QueryEngine.submit_message()` 替代 `provider.stream_messages()`
- 处理 `AssistantTextDelta` → 流式显示
- 处理 `ToolExecutionStarted` → 显示工具调用
- 处理 `ToolExecutionCompleted` → 显示工具结果
- 处理 `ErrorEvent` → 显示错误

**Step 3: 运行测试**

```bash
pytest tests/test_tui_integration.py -v
```

**Step 4: 运行全部测试**

```bash
pytest tests/ -v --ignore=tests/test_zhipu_live.py
```

**Step 5: 提交**

```bash
git add -A && git commit -m "feat(tui): integrate QueryEngine for full tool loop

- Replace direct provider calls with QueryEngine
- Handle all StreamEvent types in TUI
- Register all built-in tools in ToolRegistry
- 360+ tests passing"
```

---

## Task 2: 权限审批弹窗 ModalScreen

**Files:**
- Create: `src/myagent/tui/screens.py`
- Modify: `src/myagent/tui/app.py`
- Test: `tests/test_tui_screens.py`

**Step 1: 编写测试**

测试 PermissionModalScreen：
- 屏幕创建
- 按钮交互
- 回调触发

**Step 2: 实现 PermissionModalScreen**

创建 `src/myagent/tui/screens.py`：
```python
class PermissionModalScreen(ModalScreen[bool]):
    """Modal screen for permission approval."""
    
    def __init__(self, tool_name: str, arguments: dict, reason: str) -> None:
        ...
    
    def compose(self) -> ComposeResult:
        # 显示工具名、参数、原因
        # Allow / Deny 按钮
```

**Step 3: 在 QueryEngine 中集成权限检查**

修改 `QueryEngine._run_loop`：
- 在工具执行前调用 `PermissionChecker.check()`
- 如果返回 ASK，发送 `PermissionRequestEvent`
- TUI 收到后弹出 ModalScreen

**Step 4: 运行测试**

```bash
pytest tests/test_tui_screens.py -v
```

**Step 5: 提交**

---

## Task 3: 工具调用可视化（可折叠展示）

**Files:**
- Modify: `src/myagent/tui/app.py`
- Test: `tests/test_tui.py`

**Step 1: 增强工具显示**

在 TUI 中：
- `ToolExecutionStarted` → 显示可折叠的工具调用卡片
- `ToolExecutionCompleted` → 展开显示结果
- 使用 Rich 的 Panel/Tree 进行美化

**Step 2: 运行测试**

**Step 3: 提交**

---

## Task 4: Header 增强（成本、回合数显示）

**Files:**
- Modify: `src/myagent/tui/app.py`
- Test: `tests/test_tui.py`

**Step 1: 更新 Header 显示**

```
MyAgent v0.2.0 | Agent: general | Turns: 3 | Cost: $0.012
```

**Step 2: 在事件处理中更新状态**

- `AssistantTurnComplete` → 更新回合数
- 每次 LLM 调用后 → 更新成本

**Step 3: 运行测试**

**Step 4: 提交**

---

## Task 5: 端到端测试与最终提交

**Step 1: 运行全部测试**

```bash
pytest tests/ -v --ignore=tests/test_zhipu_live.py
```

**Step 2: 验证 TUI 可以启动**

```bash
python -m myagent tui --help
```

**Step 3: 提交并打标**

```bash
git add -A && git commit -m "feat(tui): complete QueryEngine integration

- Full tool loop with QueryEngine
- Permission approval modal
- Tool call visualization
- Cost and turn tracking in header
- All tests passing"
git tag v0.3.0-tui-complete
```
