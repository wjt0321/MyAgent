# Phase 3: HermesAgent Gateway 完整实现

> **审查基础**: PROJECT_REVIEW.md (2026-04-23)
> **预计工期**: 3-4 周
> **目标**: 验证 Gateway 实现、GitHub App 集成、Web UI 多用户支持

---

## 一、Gateway 实现验证

### Task 3.1: Telegram 适配器端到端测试

**现状**: `gateway/adapters/telegram.py` 已存在，但完整度存疑。

**文件**:
- 检查: `src/myagent/gateway/adapters/telegram.py`
- 检查: `src/myagent/gateway/bot.py`
- 检查: `src/myagent/gateway/manager.py`

**实现步骤**:

1. **审查现有 Telegram 适配器代码**
   - 消息接收是否正常
   - 消息格式转换是否正确
   - 会话绑定逻辑是否完整
   - 权限审批在 IM 内如何交互

2. **补充缺失的功能**
```python
# 如果缺失，添加以下功能：

class TelegramAdapter(BaseAdapter):
    """Telegram Bot Adapter for MyAgent."""
    
    async def send_message(self, session_id: str, text: str) -> None:
        """Send a text message to Telegram chat."""
        # Implementation
    
    async def send_permission_request(
        self, 
        session_id: str, 
        tool_name: str, 
        arguments: dict,
        reason: str,
    ) -> bool:
        """Send permission request with inline keyboard."""
        # Show Allow/Deny buttons in Telegram
        # Wait for user response
        # Return True/False
    
    async def handle_update(self, update: dict) -> None:
        """Handle incoming Telegram update."""
        # Extract message text
        # Find or create session
        # Forward to QueryEngine
        # Send response back
```

3. **创建测试机器人**
   - 通过 @BotFather 创建测试 bot
   - 设置 `TELEGRAM_BOT_TOKEN`
   - 运行 `myagent gateway` 并测试

**测试清单**:
- [ ] 发送文本消息，Agent 正确回复
- [ ] 触发工具调用，收到权限请求
- [ ] 点击 Allow，工具执行并返回结果
- [ ] 点击 Deny，收到拒绝提示
- [ ] 多轮对话上下文保持
- [ ] 新用户首次使用时收到配对请求

---

### Task 3.2: Gateway 会话绑定修复

**现状**: 可能存在的问题 — 用户 ID 到会话的映射不明确。

**文件**:
- 修改: `src/myagent/gateway/manager.py`
- 修改: `src/myagent/gateway/base.py`

**实现步骤**:

1. **明确会话绑定策略**
```python
class GatewaySessionManager:
    """Manages sessions for gateway users."""
    
    def __init__(self):
        self._user_sessions: dict[str, str] = {}  # user_id -> session_id
    
    def get_or_create_session(self, user_id: str, platform: str) -> Session:
        """Get existing session or create new one for user."""
        session_id = self._user_sessions.get(user_id)
        if session_id:
            session = self.session_store.get(session_id)
            if session:
                return session
        
        # Create new session
        session = self.session_store.create(agent="general")
        self._user_sessions[user_id] = session.id
        return session
```

2. **持久化用户-会话映射**
   - 保存到 `~/.myagent/gateway_sessions.yaml`
   - 服务重启后恢复

---

## 二、GitHub App 集成

### Task 3.3: GitHub Webhook 处理

**目标**: 监听 PR/Issue/Review 事件，自动分析、回复、创建代码改动。

**文件**:
- 创建: `src/myagent/gateway/adapters/github.py`
- 修改: `src/myagent/gateway/webhook.py`

**实现步骤**:

1. **创建 GitHubAdapter**
```python
"""GitHub App Adapter for MyAgent."""

from myagent.gateway.adapter_base import BaseAdapter

class GitHubAdapter(BaseAdapter):
    """Handle GitHub webhook events."""
    
    supported_events = [
        "pull_request",
        "pull_request_review",
        "issues",
        "issue_comment",
    ]
    
    async def handle_event(self, event_type: str, payload: dict) -> None:
        """Handle GitHub webhook event."""
        if event_type == "pull_request" and payload.get("action") == "opened":
            await self._handle_pr_opened(payload)
        elif event_type == "issues" and payload.get("action") == "opened":
            await self._handle_issue_opened(payload)
        elif event_type == "pull_request_review" and payload.get("action") == "submitted":
            await self._handle_pr_review(payload)
    
    async def _handle_pr_opened(self, payload: dict) -> None:
        """Analyze new PR and post summary comment."""
        pr = payload["pull_request"]
        repo = payload["repository"]
        
        # Clone repo or fetch diff
        diff_url = pr["diff_url"]
        diff = await self._fetch_diff(diff_url)
        
        # Analyze with Agent
        analysis = await self._analyze_diff(diff)
        
        # Post comment
        await self._post_comment(
            repo["full_name"],
            pr["number"],
            f"## AI Analysis\n\n{analysis}",
        )
```

2. **Webhook 路由**
```python
@app.post("/webhook/github")
async def github_webhook(request: Request) -> dict[str, str]:
    """Receive GitHub webhook events."""
    event_type = request.headers.get("X-GitHub-Event", "")
    payload = await request.json()
    
    adapter = GitHubAdapter()
    await adapter.handle_event(event_type, payload)
    
    return {"status": "ok"}
```

3. **GitHub API 集成**
   - 使用 `PyGithub` 或 `httpx` 调用 GitHub API
   - 需要 `GITHUB_APP_ID` 和 `GITHUB_PRIVATE_KEY`

**测试**:
- [ ] PR 创建后自动收到分析评论
- [ ] Issue 创建后自动分类/回复
- [ ] Review 提交后自动处理

---

## 三、Web UI 多用户支持

### Task 3.4: JWT 认证

**目标**: 每个用户独立 session namespace，可选密码保护。

**文件**:
- 创建: `src/myagent/web/auth.py`
- 修改: `src/myagent/web/server.py`
- 修改: `src/myagent/web/session.py`

**实现步骤**:

1. **创建 Auth 模块**
```python
"""Authentication for MyAgent Web UI."""

import jwt
from datetime import datetime, timedelta
from pathlib import Path

SECRET_KEY_PATH = Path.home() / ".myagent" / ".web_secret"

def get_secret_key() -> str:
    """Get or generate JWT secret key."""
    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()
    
    import secrets
    key = secrets.token_urlsafe(32)
    SECRET_KEY_PATH.write_text(key)
    return key

def create_token(user_id: str) -> str:
    """Create JWT token for user."""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7),
    }
    return jwt.encode(payload, get_secret_key(), algorithm="HS256")

def verify_token(token: str) -> str | None:
    """Verify JWT token and return user_id."""
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=["HS256"])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
```

2. **SessionStore 支持多用户**
```python
class SessionStore:
    def __init__(self, storage_dir: Path | None = None):
        # ... existing init ...
        self._user_namespaces: dict[str, str] = {}  # user_id -> namespace
    
    def list_all(self, user_id: str | None = None) -> list[Session]:
        """List sessions for a specific user or all."""
        sessions = list(self._sessions.values())
        if user_id:
            sessions = [s for s in sessions if s.user_id == user_id]
        return sorted(sessions, key=lambda s: s.updated_at, reverse=True)
```

3. **API 路由添加认证**
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user from JWT token."""
    user_id = verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id

@app.get("/api/sessions")
async def list_sessions(user_id: str = Depends(get_current_user)) -> list[dict[str, Any]]:
    """List sessions for current user."""
    store: SessionStore = app.state.session_store
    return [s.to_dict() for s in store.list_all(user_id=user_id)]
```

4. **前端登录页面**
   - 如果未设置密码，自动生成并显示
   - 登录后保存 token 到 localStorage
   - 所有 API 请求携带 Authorization header

**测试**:
- [ ] 未登录访问 API 返回 401
- [ ] 登录后获取 token
- [ ] 携带 token 访问 API 成功
- [ ] 用户 A 看不到用户 B 的会话

---

## 四、测试清单

### Gateway 测试
- [ ] Telegram 文本消息收发正常
- [ ] Telegram 权限审批流程正常
- [ ] 多用户会话隔离
- [ ] 服务重启后会话恢复

### GitHub 测试
- [ ] PR 创建触发分析评论
- [ ] Issue 创建触发自动回复
- [ ] Review 提交触发处理
- [ ] Webhook 签名验证

### 认证测试
- [ ] 未认证访问返回 401
- [ ] 登录获取 JWT token
- [ ] Token 过期后刷新
- [ ] 多用户会话隔离

---

## 五、提交计划

| 提交 | 内容 |
|------|------|
| commit 1 | feat: Telegram Gateway 端到端测试与修复 |
| commit 2 | feat: Gateway 会话绑定持久化 |
| commit 3 | feat: GitHub App Webhook 集成 |
| commit 4 | feat: GitHub PR/Issue 自动分析 |
| commit 5 | feat: Web UI JWT 认证系统 |
| commit 6 | feat: 多用户会话隔离 |

---

*文档版本: v1.0 | 创建时间: 2026-04-23*
