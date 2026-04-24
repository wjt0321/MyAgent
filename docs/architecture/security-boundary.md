# 安全边界文档

本文档明确 MyAgent 各模块的信任边界、安全假设和防护措施。

## 1. Web UI 安全边界

### 1.1 认证机制

- **JWT Token 认证**：所有 Web API 默认需要 JWT 认证
- **白名单开放接口**：`/health`、`/` 等公开接口无需认证
- **WebSocket 认证**：通过 query parameter `token` 传递 JWT token

### 1.2 文件访问限制

**文件 API 路径限制**（`/api/files`、`/api/files/read`）：

- **允许访问的根目录**：
  - 当前工作目录（CWD）
  - Workspace 目录（`~/.myagent/`）
- **实现方式**：`_resolve_allowed_path()` 函数验证目标路径必须在允许根目录下
- **拒绝策略**：路径越界返回 403 Forbidden

```python
def _resolve_allowed_path(path: str) -> Path:
    target = Path(path).resolve()
    cwd = Path.cwd().resolve()
    ws_dir = get_workspace_dir().resolve()

    # Check if target is within allowed roots
    try:
        target.relative_to(cwd)
        return target
    except ValueError:
        pass

    try:
        target.relative_to(ws_dir)
        return target
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Access denied: path outside allowed directories",
        )
```

### 1.3 WebSocket 会话隔离

- **Session Owner 校验**：WebSocket 连接时验证 `user_id` 与 session 所有者匹配
- **Token 校验**：启用 JWT 时，WebSocket 必须携带有效 token
- **会话隔离**：`store.get(session_id, user_id=user_id)` 确保只能访问自己的会话

### 1.4 权限审批链路

- **tool_use_id 透传**：`PermissionRequestEvent` 携带 `tool_use_id`，前端确认/拒绝时回传
- **前后端契约统一**：事件定义、WebSocket 消息、API 接口统一使用 `tool_use_id`

## 2. GitHub Webhook 安全边界

### 2.1 签名验证

**问题**：之前版本从请求体 `payload.get("secret")` 读取密钥，攻击者可自行构造。

**修复后**：

- **密钥来源**：仅从服务端配置（`Settings.github_webhook_secret`）或环境变量（`GITHUB_WEBHOOK_SECRET`）读取
- **生产环境要求**：未配置密钥时显式拒绝请求（返回 401）
- **签名校验失败**：记录警告日志并返回 401

```python
# Webhook secret MUST come from server-side config/env, NEVER from request payload
settings = Settings.load()
webhook_secret = settings.github_webhook_secret or ""
if not webhook_secret:
    webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")

if not webhook_secret:
    return JSONResponse(
        {"status": "error", "message": "Webhook secret not configured"},
        status_code=401,
    )
```

### 2.2 事件处理

- **事件类型验证**：从 `X-GitHub-Event` 请求头读取
- **签名验证**：使用 `X-Hub-Signature-256` 请求头校验 HMAC-SHA256 签名
- **错误日志**：验签失败和事件处理异常记录详细日志

## 3. 工具执行安全边界

### 3.1 Bash 工具

- **权限系统**：根据工具权限级别决定是否执行
  - `ALLOW`：直接执行
  - `DENY`：拒绝执行并记录原因
  - `ASK`：请求用户审批

### 3.2 代码解释器

- **Python 沙箱**：在隔离环境中执行代码
- **资源限制**：限制内存、CPU、执行时间
- **网络访问**：可选限制网络访问

### 3.3 文件编辑工具

- **路径限制**：同 Web UI 文件 API，限制在允许目录下
- **写入权限**：需要用户确认才能执行写操作

## 4. Gateway 平台安全边界

### 4.1 会话隔离

- **按平台隔离**：不同消息平台的会话独立管理
- **按用户/群组隔离**：会话绑定到特定用户或群组
- **持久化绑定**：会话持久化到磁盘，重启后恢复

### 4.2 入站消息处理

- **不可信输入**：所有来自消息平台的消息视为不可信输入
- **配对请求**：未知发送者收到配对请求
- **白名单**：推荐配置允许列表限制访问

## 5. 配置安全

### 5.1 密钥管理

- **环境变量**：API 密钥存储在 `~/.myagent/.env` 或系统环境变量
- **禁止提交**：`.env` 文件被 `.gitignore` 排除
- **配置热重载**：修改配置后自动重新加载，无需重启

### 5.2 日志安全

- **结构化日志**：JSON 格式，便于监控和分析
- **敏感信息过滤**：日志中不记录 API 密钥、token 等敏感信息
- **日志级别**：支持 DEBUG、INFO、WARNING、ERROR

## 6. 已验证场景 / 未验证场景 / 已知限制

### 6.1 已验证场景

- Web UI JWT 认证和会话隔离
- 文件 API 路径限制
- GitHub Webhook 服务端密钥验证
- 权限审批 tool_use_id 透传

### 6.2 未验证场景

- 高并发下的 WebSocket 连接稳定性
- 多用户同时访问文件 API 的竞态条件
- 大规模消息平台的会话持久化性能

### 6.3 已知限制

- Task Engine 批准后执行是异步后台任务，进度未通过 WebSocket 推送
- 前端重置接口已补充后端，但未进行端到端测试
- Session 持久化已修复，但未进行压力测试
