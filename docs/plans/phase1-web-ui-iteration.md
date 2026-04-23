# Phase 1: Web UI 紧急修复与视觉升级

> **审查基础**: PROJECT_REVIEW.md (2026-04-23)
> **预计工期**: 1 周（全职）/ 2 周（兼职）
> **目标**: 修复紧急 Bug + 核心视觉升级，用户体验质的飞跃

---

## 一、紧急 Bug 修复（必须先做）

### Task 1.1: 修复模型硬编码问题

**问题**: `server.py:260` 创建会话时模型写死为 `anthropic/claude-3.5-sonnet`，且 WebSocket 连接时错误提示写死为 `ZHIPU_API_KEY`。

**文件**:
- 修改: `src/myagent/web/server.py:260`
- 修改: `src/myagent/web/server.py:368`
- 修改: `src/myagent/web/static/app.js`（模型选择器相关）

**实现步骤**:

1. **后端**: `server.py` 的 `create_session` 中，从配置读取默认模型
```python
from myagent.config.settings import get_settings

settings = get_settings()
default_model = request.get("model") or settings.default_model or "anthropic/claude-3.5-sonnet"
```

2. **后端**: `server.py` 的 WebSocket 错误提示改为通用提示
```python
message = "LLM provider not configured. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or other provider environment variable."
```

3. **前端**: `app.js` 的 `saveSettings()` 中，保存模型选择后发送 PATCH 请求更新会话模型

**测试**: 创建新会话，验证模型字段正确传递

---

### Task 1.2: 修复权限弹窗传参

**问题**: `app.js:831` 的 `handlePermission()` 中，`tool_use_id` 需要从 `_pendingPermission` 中正确获取。

**文件**:
- 修改: `src/myagent/web/static/app.js:792-836`
- 检查: `src/myagent/engine/query_engine.py`（确认后端接收字段）

**实现步骤**:

1. 确认 `query_engine.py` 的 `continue_with_permission` 方法接收的参数名
2. 确认前端 `sendPermissionResponse` 发送的 `tool_use_id` 与后端一致
3. 如果后端使用 `tool_name` 而非 `tool_use_id`，统一修改为 `tool_use_id`

**测试**: 触发需要权限的工具调用，验证 Allow/Deny 后流程正常恢复

---

### Task 1.3: 修复文件树 XSS 漏洞

**问题**: `app.js` 中 `entry.name` 直接通过 `innerHTML` 插入，存在 XSS 风险。

**文件**:
- 修改: `src/myagent/web/static/app.js`（文件树渲染部分）

**实现步骤**:

1. 创建 `escapeHtml()` 工具函数
```javascript
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
```

2. 将所有文件树中 `innerHTML` 插入 `entry.name` 的地方改为先转义

**测试**: 创建含 `<script>alert('xss')</script>` 文件名的文件，验证不会执行

---

### Task 1.4: 修复 MaxTurnsExceeded 异常处理

**问题**: `query_engine.py:73` 抛出 `MaxTurnsExceeded` 但 WebSocket 层没有 catch，导致连接异常断开。

**文件**:
- 修改: `src/myagent/web/server.py:405-421`
- 修改: `src/myagent/engine/query_engine.py:73`

**实现步骤**:

1. 在 `query_engine.py` 中将 `MaxTurnsExceeded` 改为 yield ErrorEvent
```python
if self._turn_count >= self.max_turns:
    yield ErrorEvent(
        error=MaxTurnsExceeded(f"Maximum turns ({self.max_turns}) exceeded."),
        recoverable=False,
    )
    return
```

2. 在 `server.py` 的 WebSocket 处理中添加通用异常 catch
```python
try:
    # ... message processing ...
except Exception as e:
    await websocket.send_json({
        "type": "error",
        "message": f"Internal error: {str(e)}"
    })
```

**测试**: 设置 `max_turns=1`，验证超过后返回错误消息而非断开连接

---

## 二、前端视觉升级

### Task 1.5: 工具调用可折叠面板

**问题**: 工具调用结果直接展开，长输出导致消息区拥挤。

**文件**:
- 修改: `src/myagent/web/static/app.js:734-740`
- 修改: `src/myagent/web/static/style.css`

**实现步骤**:

1. **JS**: 修改 `handleWebSocketMessage` 中 `tool_call` 和 `tool_result` 的处理
```javascript
case 'tool_call':
    this.addToolCall(data.tool_name, data.arguments);
    break;
case 'tool_result':
    this.addToolResult(data.result, data.is_error);
    break;
```

2. **JS**: 新增 `addToolCall` 和 `addToolResult` 方法，生成可折叠 HTML
```javascript
addToolCall(toolName, args) {
    const div = document.createElement('div');
    div.className = 'tool-call-collapsible';
    div.innerHTML = `
        <div class="tool-call-header" onclick="this.parentElement.classList.toggle('expanded')">
            <span class="tool-icon">🔧</span>
            <span class="tool-name">${escapeHtml(toolName)}</span>
            <span class="tool-toggle">▶</span>
        </div>
        <pre class="tool-args"><code>${escapeHtml(JSON.stringify(args, null, 2))}</code></pre>
    `;
    this.messagesContainer.appendChild(div);
}
```

3. **CSS**: 添加折叠样式
```css
.tool-call-collapsible .tool-args { display: none; }
.tool-call-collapsible.expanded .tool-args { display: block; }
.tool-call-collapsible.expanded .tool-toggle { transform: rotate(90deg); }
```

**测试**: 触发工具调用，验证默认收起、点击展开、再次点击收起

---

### Task 1.6: 代码块 Copy 按钮

**问题**: 代码块缺少 Copy 按钮，高频需求。

**文件**:
- 修改: `src/myagent/web/static/app.js`（消息渲染部分）
- 修改: `src/myagent/web/static/style.css`

**实现步骤**:

1. **JS**: 在渲染 Markdown 代码块时，为每个 `pre > code` 添加 Copy 按钮
```javascript
addCopyButtons() {
    document.querySelectorAll('pre code').forEach(block => {
        if (block.parentElement.querySelector('.copy-btn')) return;
        const btn = document.createElement('button');
        btn.className = 'copy-btn';
        btn.textContent = 'Copy';
        btn.onclick = () => {
            navigator.clipboard.writeText(block.textContent);
            btn.textContent = 'Copied!';
            setTimeout(() => btn.textContent = 'Copy', 2000);
        };
        block.parentElement.style.position = 'relative';
        block.parentElement.appendChild(btn);
    });
}
```

2. **CSS**: 添加 Copy 按钮样式（右上角悬浮）
```css
.copy-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    padding: 4px 8px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.2s;
}
pre:hover .copy-btn { opacity: 1; }
```

**测试**: 发送含代码块的回复，验证鼠标悬停显示 Copy 按钮，点击后复制内容

---

### Task 1.7: 欢迎页面快捷指令卡片

**问题**: 欢迎页面仅有 Logo + 一行文字，缺乏引导。

**文件**:
- 修改: `src/myagent/web/static/index.html`
- 修改: `src/myagent/web/static/style.css`
- 修改: `src/myagent/web/static/app.js`

**实现步骤**:

1. **HTML**: 在欢迎页面添加快捷卡片区域
```html
<div id="welcome-screen">
    <div class="welcome-logo">...</div>
    <div class="welcome-subtitle">...</div>
    <div class="quick-actions">
        <div class="quick-card" data-prompt="/plan 分析当前代码库结构">
            <div class="quick-icon">📊</div>
            <div class="quick-title">分析代码库</div>
            <div class="quick-desc">了解项目结构和关键文件</div>
        </div>
        <div class="quick-card" data-prompt="帮我写一个 Python 函数">
            <div class="quick-icon">✨</div>
            <div class="quick-title">编写代码</div>
            <div class="quick-desc">根据需求生成代码实现</div>
        </div>
        <div class="quick-card" data-prompt="解释这个项目的架构">
            <div class="quick-icon">🏗️</div>
            <div class="quick-title">解释架构</div>
            <div class="quick-desc">深入理解系统设计</div>
        </div>
    </div>
</div>
```

2. **JS**: 绑定卡片点击事件
```javascript
bindQuickCards() {
    document.querySelectorAll('.quick-card').forEach(card => {
        card.addEventListener('click', () => {
            const prompt = card.dataset.prompt;
            this.messageInput.value = prompt;
            this.sendMessage();
        });
    });
}
```

3. **CSS**: 添加卡片样式（glassmorphism 风格）

**测试**: 刷新页面，验证卡片显示，点击后正确发送消息

---

### Task 1.8: 消息时间戳

**问题**: 消息气泡内没有时间戳。

**文件**:
- 修改: `src/myagent/web/static/app.js`（addMessage 方法）
- 修改: `src/myagent/web/static/style.css`

**实现步骤**:

1. **JS**: 在 `addMessage` 中添加时间戳
```javascript
addMessage(role, content, isDelta = false) {
    // ... existing code ...
    const timestamp = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    // 在消息气泡底部添加时间戳元素
}
```

2. **CSS**: 时间戳样式（小字、灰色、右下角）
```css
.message-timestamp {
    font-size: 11px;
    color: var(--text-muted);
    text-align: right;
    margin-top: 4px;
}
```

**测试**: 发送消息，验证时间戳显示正确

---

### Task 1.9: Settings 弹窗 Esc 快捷键

**问题**: Settings 弹窗没有 Esc 快捷键关闭。

**文件**:
- 修改: `src/myagent/web/static/app.js`

**实现步骤**:

1. 在 `bindEvents()` 中添加键盘监听
```javascript
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        this.closeSettings();
        this.closeSidebar();
    }
});
```

**测试**: 打开 Settings，按 Esc 验证关闭

---

### Task 1.10: 成本 Token 展示（可选）

**问题**: 用户无法感知 Token 消耗。

**文件**:
- 修改: `src/myagent/web/static/app.js`
- 修改: `src/myagent/web/static/index.html`
- 修改: `src/myagent/web/server.py`（WebSocket 消息中添加 token 信息）

**实现步骤**:

1. **后端**: `query_engine.py` 在 `AssistantTurnComplete` 事件中添加 token 消耗
2. **前端**: 在消息区域右上角显示本次对话的 token 消耗角标

**注**: 如果 Token 计数实现复杂，可延后到 Phase 2。

---

## 三、测试清单

### 功能测试
- [ ] 创建会话时模型正确传递
- [ ] 切换 Agent 后 PATCH 请求成功
- [ ] 权限弹窗 Allow/Deny 后流程正常
- [ ] XSS 文件名安全显示
- [ ] 超过 max_turns 后返回错误而非断连
- [ ] 工具调用默认折叠，点击展开
- [ ] 代码块 Copy 按钮工作正常
- [ ] 欢迎页快捷卡片点击发送消息
- [ ] 消息显示时间戳
- [ ] Esc 关闭 Settings 弹窗

### 回归测试
- [ ] 现有会话列表正常加载
- [ ] WebSocket 连接和消息收发正常
- [ ] 文件树浏览正常
- [ ] 主题切换正常
- [ ] 移动端侧边栏正常

---

## 四、提交计划

| 提交 | 内容 |
|------|------|
| commit 1 | fix: 修复模型硬编码和错误提示 |
| commit 2 | fix: 修复权限弹窗传参和 MaxTurnsExceeded 处理 |
| commit 3 | fix: 修复文件树 XSS 漏洞 |
| commit 4 | feat: 工具调用可折叠面板 |
| commit 5 | feat: 代码块 Copy 按钮 |
| commit 6 | feat: 欢迎页面快捷指令卡片 |
| commit 7 | feat: 消息时间戳和 Esc 快捷键 |

---

*文档版本: v1.0 | 创建时间: 2026-04-23*
