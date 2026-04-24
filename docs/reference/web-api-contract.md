# Web API 接口契约

本文档定义 MyAgent Web UI 的所有前后端接口、请求/响应格式、鉴权要求和错误码。

## 1. 通用说明

### 1.1 鉴权机制

- **JWT Token 认证**：通过 `Authorization: Bearer <token>` 请求头传递
- **可选密码保护**：通过 `MYAGENT_PASSWORD` 环境变量启用
- **公开接口**：`GET /health`、`GET /`、`GET /static/*` 无需认证

### 1.2 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或认证失败 |
| 403 | 权限不足（如文件路径越界） |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 1.3 通用响应格式

```json
{
  "status": "success|error",
  "message": "错误描述（仅失败时）",
  "data": {}
}
```

## 2. 会话管理

### 2.1 创建会话

**POST** `/api/sessions`

**请求体**：
```json
{
  "agent": "general",
  "model": "anthropic/claude-sonnet-4"
}
```

**响应**：
```json
{
  "id": "abc12345",
  "agent": "general",
  "model": "anthropic/claude-sonnet-4",
  "created_at": "2026-04-24T10:00:00",
  "updated_at": "2026-04-24T10:00:00",
  "messages": [],
  "user_id": "user123"
}
```

**说明**：
- `model` 可选，为空时使用 `Settings.model.default`
- 会话绑定到当前认证用户

### 2.2 列出会话

**GET** `/api/sessions`

**响应**：
```json
[
  {
    "id": "abc12345",
    "agent": "general",
    "model": "anthropic/claude-sonnet-4",
    "created_at": "2026-04-24T10:00:00",
    "updated_at": "2026-04-24T10:00:00",
    "messages": [],
    "user_id": "user123"
  }
]
```

### 2.3 更新会话

**PATCH** `/api/sessions/{session_id}`

**请求体**：
```json
{
  "model": "openai/gpt-4o",
  "agent": "worker",
  "system_prompt": "You are a helpful assistant."
}
```

**响应**：同创建会话响应

**说明**：
- 仅传递需要更新的字段
- 更新后自动持久化到磁盘

### 2.4 删除会话

**DELETE** `/api/sessions/{session_id}`

**响应**：
```json
{
  "status": "deleted"
}
```

### 2.5 清空会话消息

**DELETE** `/api/sessions/{session_id}/messages`

**响应**：
```json
{
  "status": "cleared",
  "session": {
    "id": "abc12345",
    "messages": []
  }
}
```

### 2.6 批量删除会话

**DELETE** `/api/sessions`

**响应**：
```json
{
  "status": "deleted",
  "count": "5"
}
```

**说明**：删除当前用户的所有会话

## 3. 聊天

### 3.1 WebSocket 连接

**WS** `/ws/{session_id}?token=<jwt_token>`

**连接参数**：
- `session_id`：会话 ID（路径参数）
- `token`：JWT token（query parameter）

**消息类型**：

#### 客户端 → 服务端

```json
{
  "type": "message",
  "content": "Hello, world!"
}
```

#### 服务端 → 客户端

**工具执行开始**：
```json
{
  "type": "tool_use",
  "tool_name": "Bash",
  "tool_use_id": "tool_abc123",
  "input": {"command": "ls -la"}
}
```

**工具执行结果**：
```json
{
  "type": "tool_result",
  "tool_name": "Bash",
  "tool_use_id": "tool_abc123",
  "output": "total 0\ndrwxr-xr-x  2 user  staff  64 Apr 24 10:00 ."
}
```

**文本块**：
```json
{
  "type": "text_delta",
  "delta": "Hello! How can I help you today?"
}
```

**权限请求**：
```json
{
  "type": "permission_request",
  "tool_name": "Bash",
  "tool_use_id": "tool_abc123",
  "arguments": {"command": "rm -rf /"},
  "reason": "此命令可能具有破坏性"
}
```

**错误**：
```json
{
  "type": "error",
  "message": "Session not found"
}
```

### 3.2 批准权限

**POST** `/api/permissions/{tool_use_id}/approve`

**响应**：
```json
{
  "status": "approved"
}
```

### 3.3 拒绝权限

**POST** `/api/permissions/{tool_use_id}/reject`

**响应**：
```json
{
  "status": "rejected"
}
```

## 4. 文件管理

### 4.1 列出文件

**GET** `/api/files?path=.`

**查询参数**：
- `path`：目标路径（默认 `.`）

**响应**：
```json
{
  "path": "/app/workspace",
  "entries": [
    {
      "name": "src",
      "path": "/app/workspace/src",
      "is_dir": true,
      "size": 0
    },
    {
      "name": "README.md",
      "path": "/app/workspace/README.md",
      "is_dir": false,
      "size": 1024
    }
  ]
}
```

**限制**：
- 路径必须在 CWD 或 Workspace 目录下
- 路径越界返回 403 Forbidden

### 4.2 读取文件

**GET** `/api/files/read?path=README.md`

**查询参数**：
- `path`：目标文件路径

**响应**：
```json
{
  "path": "/app/workspace/README.md",
  "name": "README.md",
  "content": "# MyAgent\n\n...",
  "size": 1024
}
```

**限制**：同列出文件

## 5. 记忆管理

### 5.1 列出记忆

**GET** `/api/memories?type=user&limit=20&offset=0`

**查询参数**：
- `type`：记忆类型（`user`、`feedback`、`project`、`reference`）
- `limit`：返回数量限制（默认 20）
- `offset`：偏移量（默认 0）

**响应**：
```json
{
  "entries": [
    {
      "id": "mem_abc123",
      "type": "user",
      "tags": ["preference", "coding-style"],
      "created": "2026-04-24",
      "updated": "2026-04-24",
      "content": "User prefers concise responses."
    }
  ],
  "total": 10
}
```

### 5.2 创建记忆

**POST** `/api/memories`

**请求体**：
```json
{
  "type": "user",
  "tags": ["preference"],
  "content": "User prefers concise responses."
}
```

**响应**：同记忆条目

### 5.3 更新记忆

**PUT** `/api/memories/{memory_id}`

**请求体**：
```json
{
  "tags": ["preference", "updated"],
  "content": "User prefers very concise responses."
}
```

**响应**：同记忆条目

### 5.4 删除记忆

**DELETE** `/api/memories/{memory_id}`

**响应**：
```json
{
  "status": "deleted"
}
```

## 6. 任务管理

### 6.1 创建任务

**POST** `/api/tasks`

**请求体**：
```json
{
  "title": "Implement feature X",
  "description": "Add support for..."
}
```

**响应**：
```json
{
  "id": "task_abc123",
  "title": "Implement feature X",
  "description": "Add support for...",
  "status": "pending",
  "plan": null,
  "plan_approved": false,
  "created_at": "2026-04-24T10:00:00"
}
```

### 6.2 获取当前任务

**GET** `/api/tasks/current`

**响应**：同任务条目

### 6.3 批准任务计划

**POST** `/api/tasks/{task_id}/approve`

**响应**：
```json
{
  "status": "approved",
  "task": {
    "id": "task_abc123",
    "plan_approved": true,
    "status": "planned"
  }
}
```

**说明**：
- 批准后自动触发后台执行
- 执行完成后自动进入 review

## 7. 团队管理

### 7.1 创建团队

**POST** `/api/teams`

**请求体**：
```json
{
  "name": "Development Team",
  "agents": ["plan", "explore", "worker"]
}
```

**响应**：
```json
{
  "id": "team_abc123",
  "name": "Development Team",
  "agents": ["plan", "explore", "worker"],
  "created_at": "2026-04-24T10:00:00"
}
```

### 7.2 列出团队

**GET** `/api/teams`

**响应**：
```json
{
  "teams": [
    {
      "id": "team_abc123",
      "name": "Development Team",
      "agents": ["plan", "explore", "worker"]
    }
  ]
}
```

## 8. 配置管理

### 8.1 获取配置

**GET** `/api/config`

**响应**：
```json
{
  "model": "anthropic/claude-sonnet-4",
  "agent": "general",
  "context_max_turns": 50
}
```

### 8.2 更新配置

**PATCH** `/api/config`

**请求体**：
```json
{
  "model": "openai/gpt-4o"
}
```

**响应**：
```json
{
  "status": "updated"
}
```

### 8.3 重置配置

**DELETE** `/api/config`

**响应**：
```json
{
  "status": "reset"
}
```

**说明**：删除 `~/.myagent/config.yaml` 文件

## 9. 健康检查

### 9.1 健康状态

**GET** `/health`

**响应**：
```json
{
  "status": "healthy",
  "version": "0.11.0"
}
```

**说明**：公开接口，无需认证

## 10. 静态文件

### 10.1 访问静态资源

**GET** `/static/{path}`

**说明**：提供 Web UI 前端文件（HTML、CSS、JS）

## 11. GitHub Webhook

### 11.1 接收 GitHub 事件

**POST** `/webhook/github`

**请求头**：
- `X-GitHub-Event`：事件类型（如 `push`、`pull_request`）
- `X-Hub-Signature-256`：HMAC-SHA256 签名

**响应**：
```json
{
  "status": "ok",
  "result": "Event processed"
}
```

**安全要求**：
- 签名验证使用服务端配置的 `GITHUB_WEBHOOK_SECRET`
- 未配置密钥时拒绝请求（401）
- 签名验证失败返回 401
