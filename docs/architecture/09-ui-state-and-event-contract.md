# UI 状态与事件契约（Phase 0 基线）

本文档定义 MyAgent 在 `Web UI`、`Gateway` 与核心引擎之间当前必须保持一致的最小事件契约。

目标不是一次性覆盖所有未来字段，而是先把 `权限审批`、`工具执行`、`会话持久化` 三条高风险链路固定下来，避免前后端继续各自漂移。

---

## 1. 设计目标

Phase 0 需要解决的核心问题有三个：

1. Web 聊天流与恢复流发送的事件字段不一致
2. Gateway 权限恢复时没有稳定使用 `tool_use_id`
3. 会话更新接口存在“返回成功但未真正持久化”的旧链路

因此，本契约文档只关注以下对象：

- WebSocket 出站事件
- WebSocket 入站动作
- Gateway 审批恢复调用
- Session 持久化规则

---

## 2. 统一原则

### 2.1 `tool_use_id` 是权限审批链路的主键

只要事件与工具执行有关，就必须透传 `tool_use_id`。

适用事件：

- `tool_call`
- `tool_result`
- `permission_request`

适用恢复入口：

- WebSocket `approve_permission`
- Gateway `continue_with_permission()`

### 2.2 同一种语义只能有一套字段名

禁止出现以下分叉：

- Web 端叫 `tool_use_id`，Gateway 端改从 `arguments.tool_use_id` 取
- 初次流式消息不带字段，恢复消息才带字段
- 服务端内部对象与对外消息结构不一致

### 2.3 会话修改必须通过 `SessionStore.update()`

`Session.save()` 当前不是可信持久化入口。

所有会修改会话内容的 Web 路由，必须：

1. 修改 `session`
2. 更新 `session.updated_at`
3. 调用 `store.update(session)`

---

## 3. WebSocket 出站事件

## 3.1 `tool_call`

表示工具开始执行。

```json
{
  "type": "tool_call",
  "tool_name": "bash",
  "tool_use_id": "tool-123",
  "arguments": {
    "command": "pwd"
  }
}
```

字段说明：

- `type`: 固定为 `tool_call`
- `tool_name`: 工具名
- `tool_use_id`: 本次工具执行的唯一标识
- `arguments`: 工具调用参数

## 3.2 `tool_result`

表示工具执行结束。

```json
{
  "type": "tool_result",
  "tool_use_id": "tool-123",
  "result": "done",
  "is_error": false
}
```

字段说明：

- `type`: 固定为 `tool_result`
- `tool_use_id`: 与 `tool_call` 对应
- `result`: 工具输出
- `is_error`: 是否为错误结果

## 3.3 `permission_request`

表示工具执行被权限系统拦截，等待用户决策。

```json
{
  "type": "permission_request",
  "tool_name": "bash",
  "tool_use_id": "tool-123",
  "arguments": {
    "command": "rm -rf ."
  },
  "reason": "需要危险命令审批"
}
```

字段说明：

- `type`: 固定为 `permission_request`
- `tool_name`: 被拦截的工具名
- `tool_use_id`: 审批恢复必须使用的主键
- `arguments`: 原始工具参数
- `reason`: 审批原因

---

## 4. WebSocket 入站动作

## 4.1 `approve_permission`

前端用户点击允许或拒绝后，通过 WebSocket 发送：

```json
{
  "action": "approve_permission",
  "tool_use_id": "tool-123",
  "approved": true
}
```

处理规则：

1. 服务端读取 `tool_use_id`
2. 调用 `engine.continue_with_permission(tool_use_id, approved)`
3. 后续流式事件继续走统一出站契约

---

## 5. Gateway 审批恢复契约

Gateway 适配器只负责向用户发审批请求并返回布尔值：

- `True` 表示允许
- `False` 表示拒绝

真正恢复执行时，必须使用 `PermissionRequestEvent.tool_use_id`：

```python
async for event in engine.continue_with_permission(
    permission_event.tool_use_id,
    approved=True,
):
    ...
```

禁止再从 `permission_event.arguments` 中回推 `tool_use_id`。

原因：

- `tool_use_id` 属于事件元数据，不属于工具参数
- 把它塞进 `arguments` 会污染工具输入语义

---

## 6. Session 持久化契约

以下 Web 路由修改会话后，必须持久化：

- `PATCH /api/sessions/{session_id}`
- `PATCH /api/sessions/{session_id}/system-prompt`
- `POST /api/sessions/{session_id}/import`

统一规则：

```python
session.updated_at = datetime.now()
store.update(session)
```

禁止只调用：

```python
session.save()
```

除非未来 `Session.save()` 被重新实现并显式绑定到 `SessionStore`。

---

## 7. Phase 0 验证范围

当前最小回归覆盖以下场景：

1. Web `process_message()` 出站事件透传 `tool_use_id`
2. Gateway 权限恢复使用事件上的 `tool_use_id`
3. `system-prompt` 更新后持久化到磁盘
4. `import messages` 后持久化到磁盘
5. 文件 API 仅允许 `cwd/workspace` 范围
6. Memory 测试与当前实现契约一致

对应 smoke 测试集：

- `tests/test_web.py`
- `tests/test_web_files.py`
- `tests/test_memory.py`
- `tests/test_gateway_bot.py`

---

## 8. 后续演进建议

Phase 1 以后，建议继续把以下对象也收敛成统一 schema：

- TUI 事件模型
- Task 进度事件
- Review 结果对象
- Session 配置视图模型
- Agent / Team 面板状态对象

Phase 0 先把这份最小契约收稳，再进入体验层重构。
