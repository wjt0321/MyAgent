# Phase 2: OpenClaw 核心能力对齐

> **审查基础**: PROJECT_REVIEW.md (2026-04-23)
> **预计工期**: 3-4 周
> **目标**: 上线上下文压缩、Git 工具、插件热加载、工具超时与沙箱

---

## 一、上下文压缩真正上线

### Task 2.1: 在 QueryEngine 中集成 AutoCompactor

**现状**: `engine/context_compression.py` 已完整实现，但 `QueryEngine` 的 `auto_compact_threshold` 参数未实际使用。

**文件**:
- 修改: `src/myagent/engine/query_engine.py:69-76`
- 已有: `src/myagent/engine/context_compression.py`

**实现步骤**:

1. **QueryEngine 初始化时创建 AutoCompactor**
```python
from myagent.engine.context_compression import AutoCompactor, ContextCompressor

class QueryEngine:
    def __init__(self, ..., auto_compact_threshold: float | None = None):
        # ... existing init ...
        self.auto_compactor = None
        if auto_compact_threshold:
            compressor = ContextCompressor(max_tokens=8000)
            self.auto_compactor = AutoCompactor(
                compressor=compressor,
                threshold_ratio=auto_compact_threshold,
            )
```

2. **_run_loop 每轮检查并触发压缩**
```python
async def _run_loop(self):
    while True:
        # Check auto-compaction before each turn
        if self.auto_compactor and self.auto_compactor.should_compact(self.messages):
            result = self.auto_compactor.compact(self.messages)
            if result.strategy_used != "none":
                self.messages = result.messages
                logger.info(
                    f"Auto-compacted: {result.tokens_before} -> {result.tokens_after} "
                    f"tokens (strategy: {result.strategy_used})"
                )
                yield AssistantTextDelta(
                    text=f"\n[Context auto-compacted: {result.tokens_before} -> {result.tokens_after} tokens]\n"
                )
        
        # ... rest of loop ...
```

3. **Web UI 配置暴露**
- `server.py` 的 `create_session` 接收 `auto_compact_threshold` 参数
- `app.js` 的 Settings 中添加滑块配置

**测试**:
```python
def test_auto_compaction_triggers():
    engine = QueryEngine(..., auto_compact_threshold=0.5, max_turns=10)
    # Add many messages to exceed threshold
    # Verify compaction event is yielded
```

---

## 二、Git 工具

### Task 2.2: 实现 GitTool

**现状**: 完全缺失，是代码 Agent 的核心能力。

**文件**:
- 创建: `src/myagent/tools/git.py`
- 修改: `src/myagent/tools/registry.py`
- 测试: `tests/test_tools_git.py`

**实现步骤**:

1. **定义 GitTool 类**
```python
"""Git operations tool for MyAgent."""

from pathlib import Path
from typing import Any

from myagent.tools.base import BaseTool, ToolResult


class GitTool(BaseTool):
    """Execute git commands in the workspace."""

    name = "git"
    description = """Execute git operations: status, diff, log, add, commit, push, branch, checkout.
    
    Commands:
    - status: Show working tree status
    - diff: Show changes between commits, commit and working tree, etc.
    - log: Show commit logs (limit optional)
    - add: Add file contents to the index
    - commit: Record changes to the repository (requires message)
    - push: Update remote refs along with associated objects
    - branch: List, create, or delete branches
    - checkout: Switch branches or restore working tree files
    """

    parameters = {
        "command": {
            "type": "string",
            "enum": ["status", "diff", "log", "add", "commit", "push", "branch", "checkout"],
            "description": "Git subcommand to execute",
        },
        "args": {
            "type": "string",
            "description": "Additional arguments for the git command",
            "default": "",
        },
        "path": {
            "type": "string",
            "description": "Working directory for git command",
            "default": ".",
        },
    }

    required_parameters = ["command"]

    async def execute(self, command: str, args: str = "", path: str = ".") -> ToolResult:
        """Execute a git command."""
        import subprocess
        
        work_dir = Path(path).resolve()
        
        # Security: prevent escaping work_dir
        if not self._is_safe_path(work_dir):
            return ToolResult(
                content="Error: Path is outside allowed workspace",
                is_error=True,
            )
        
        # Build command
        cmd = ["git", command]
        if args:
            cmd.extend(args.split())
        
        try:
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            
            return ToolResult(
                content=output,
                is_error=result.returncode != 0,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                content="Error: Git command timed out after 30 seconds",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(
                content=f"Error: {str(e)}",
                is_error=True,
            )
    
    def _is_safe_path(self, path: Path) -> bool:
        """Check if path is within allowed workspace."""
        workspace = Path.home() / ".myagent" / "workspace"
        try:
            path.relative_to(workspace)
            return True
        except ValueError:
            return path == Path(".").resolve()
```

2. **注册到 ToolRegistry**
```python
from myagent.tools.git import GitTool

# In registry initialization:
self.register(GitTool())
```

3. **添加权限控制**
- `commit` 和 `push` 操作需要 ASK 权限级别
- 其他操作为 ALLOW

**测试**:
```python
async def test_git_status():
    tool = GitTool()
    result = await tool.execute(command="status", path=".")
    assert not result.is_error
    assert "On branch" in result.content or "not a git repository" in result.content

async def test_git_log():
    tool = GitTool()
    result = await tool.execute(command="log", args="--oneline -5", path=".")
    assert not result.is_error
```

---

## 三、工具超时与沙箱

### Task 2.3: Bash 工具超时保护

**现状**: `bash.py` 中长跑命令会永久阻塞。

**文件**:
- 修改: `src/myagent/tools/bash.py`
- 修改: `src/myagent/tools/base.py`（添加 timeout 参数）

**实现步骤**:

1. **BashTool 添加超时**
```python
import asyncio

class BashTool(BaseTool):
    parameters = {
        # ... existing params ...
        "timeout": {
            "type": "integer",
            "description": "Timeout in seconds (default: 60)",
            "default": 60,
        },
    }

    async def execute(self, command: str, timeout: int = 60) -> ToolResult:
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )
            # ... process output ...
        except asyncio.TimeoutError:
            proc.kill()
            return ToolResult(
                content=f"Command timed out after {timeout} seconds",
                is_error=True,
            )
```

**测试**:
```python
async def test_bash_timeout():
    tool = BashTool()
    result = await tool.execute(command="sleep 100", timeout=1)
    assert result.is_error
    assert "timed out" in result.content
```

---

### Task 2.4: WebFetch SSRF 防护

**现状**: `web_fetch.py` 可能访问内网地址。

**文件**:
- 修改: `src/myagent/tools/web_fetch.py`

**实现步骤**:

1. **添加 URL 安全检查**
```python
import ipaddress
from urllib.parse import urlparse

BLOCKED_HOSTS = [
    "localhost", "127.0.0.1", "0.0.0.0",
    "::1", "10.", "172.16.", "192.168.",
]

def is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    
    # Check blocked hosts
    for blocked in BLOCKED_HOSTS:
        if hostname.startswith(blocked) or hostname == blocked:
            return False
    
    # Check IP addresses
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback:
            return False
    except ValueError:
        pass
    
    return True
```

2. **在 execute 中调用检查**
```python
async def execute(self, url: str) -> ToolResult:
    if not is_safe_url(url):
        return ToolResult(
            content="Error: Access to internal/private addresses is blocked",
            is_error=True,
        )
    # ... existing fetch logic ...
```

**测试**:
```python
async def test_ssrf_blocked():
    tool = WebFetchTool()
    result = await tool.execute(url="http://localhost:8000/admin")
    assert result.is_error
    assert "blocked" in result.content.lower()
```

---

## 四、插件热加载 UI

### Task 2.5: 插件管理 API

**现状**: `plugins/` 模块存在但无 UI 管理接口。

**文件**:
- 修改: `src/myagent/web/server.py`
- 已有: `src/myagent/plugins/discovery.py`, `loader.py`, `registry.py`

**实现步骤**:

1. **添加插件管理路由**
```python
@app.get("/api/plugins")
async def list_plugins() -> list[dict[str, Any]]:
    """List all installed plugins."""
    registry = PluginRegistry()
    return [
        {
            "name": p.name,
            "version": p.version,
            "enabled": p.enabled,
            "description": p.description,
        }
        for p in registry.list_plugins()
    ]

@app.post("/api/plugins/install")
async def install_plugin(request: dict[str, Any]) -> dict[str, str]:
    """Install a plugin from git URL or local path."""
    source = request.get("source", "")
    # Use PluginLoader to install
    # Return status

@app.post("/api/plugins/{name}/enable")
async def enable_plugin(name: str) -> dict[str, str]:
    """Enable a plugin."""
    # ...

@app.post("/api/plugins/{name}/disable")
async def disable_plugin(name: str) -> dict[str, str]:
    """Disable a plugin."""
    # ...
```

2. **Web UI 添加插件 Tab**
- 在 Settings 中添加"插件"标签页
- 显示已安装插件列表
- 支持从 git URL 安装

**测试**:
```python
def test_list_plugins():
    response = client.get("/api/plugins")
    assert response.status_code == 200
```

---

## 五、测试清单

### 功能测试
- [ ] 长对话超过 token 阈值后自动压缩
- [ ] 压缩策略正确（先 truncate_tools，再 summarize，最后 sliding_window）
- [ ] Git status/diff/log/add/commit/push 正常工作
- [ ] Git 命令超时保护（30秒）
- [ ] Bash 命令超时保护（默认60秒）
- [ ] SSRF 内网地址被拦截
- [ ] 插件列表 API 返回正确
- [ ] 插件安装/启用/禁用正常工作

### 安全测试
- [ ] Git 命令无法访问工作区外路径
- [ ] Bash 命令无法执行 `rm -rf /`
- [ ] WebFetch 无法访问 192.168.x.x
- [ ] WebFetch 无法访问 10.x.x.x

---

## 六、提交计划

| 提交 | 内容 |
|------|------|
| commit 1 | feat: 在 QueryEngine 中集成 AutoCompactor 上下文压缩 |
| commit 2 | feat: 添加 Git 工具（status/diff/log/add/commit/push） |
| commit 3 | feat: Bash 工具添加超时保护 |
| commit 4 | feat: WebFetch 添加 SSRF 防护 |
| commit 5 | feat: 插件管理 API（列表/安装/启用/禁用） |
| commit 6 | feat: Web UI 添加插件管理标签页 |

---

*文档版本: v1.0 | 创建时间: 2026-04-23*
