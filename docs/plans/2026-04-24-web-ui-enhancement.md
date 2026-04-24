# Web UI 增强实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 提升 MyAgent Web UI 的用户体验，包括会话侧边栏增强、模型选择器、主题切换、会话导出和移动端适配。

**Architecture:** 纯前端增强，基于现有 HTML/CSS/JS 架构，新增交互组件和响应式优化。

**Tech Stack:** Vanilla JS, CSS3, FastAPI (后端 API 已就绪)

---

## Task 1: 会话侧边栏增强

**Files:**
- Modify: `src/myagent/web/static/app.js:560-609`
- Modify: `src/myagent/web/static/style.css:236-320`

**Step 1: 添加会话重命名功能**

在 `renderSessionList()` 中为每个会话项添加重命名按钮和交互：

```javascript
// 在 session-item-header 中添加重命名按钮
const renameBtn = document.createElement('button');
renameBtn.className = 'session-rename';
renameBtn.title = '重命名';
renameBtn.innerHTML = '...'; // SVG icon
renameBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    this.startRenameSession(session.id);
});
```

**Step 2: 实现重命名交互**

```javascript
startRenameSession(sessionId) {
    const session = this.sessions.find(s => s.id === sessionId);
    if (!session) return;
    const newName = prompt('输入新会话名称:', session.agent);
    if (newName && newName !== session.agent) {
        session.agent = newName;
        this.renderSessionList();
    }
}
```

**Step 3: 更新样式**

在 CSS 中添加重命名按钮样式（与删除按钮类似）。

---

## Task 2: 模型选择器

**Files:**
- Modify: `src/myagent/web/static/index.html:111-114`
- Modify: `src/myagent/web/static/app.js:278-301`

**Step 1: 在 header 中添加模型选择下拉框**

将现有的 `model-badge` 替换为可交互的选择器：

```html
<div class="model-selector">
    <select id="model-select">
        <option value="glm-4">GLM-4</option>
        <option value="glm-4-flash">GLM-4-Flash</option>
        <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
        <option value="gpt-4o">GPT-4o</option>
        <option value="deepseek-chat">DeepSeek Chat</option>
    </select>
</div>
```

**Step 2: 在 app.js 中处理模型切换**

```javascript
async switchModel(modelName) {
    if (!this.currentSessionId) return;
    try {
        const response = await fetch(`/api/sessions/${this.currentSessionId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: modelName }),
        });
        if (response.ok) {
            const session = this.sessions.find(s => s.id === this.currentSessionId);
            if (session) {
                session.model = modelName;
                this.currentModel.textContent = modelName;
            }
        }
    } catch (error) {
        console.error('Failed to switch model:', error);
    }
}
```

---

## Task 3: 主题切换完善

**Files:**
- Modify: `src/myagent/web/static/app.js:27-58`
- Modify: `src/myagent/web/static/style.css:71-107`

**Step 1: 完善亮色主题样式**

当前亮色主题已存在但需微调对比度。

**Step 2: 添加跟随系统主题功能**

```javascript
initTheme() {
    let theme = this.currentTheme;
    if (theme === 'auto') {
        theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    document.body.className = `theme-${theme}`;
    this.updateHLJSTheme();
}
```

**Step 3: 监听系统主题变化**

```javascript
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (this.currentTheme === 'auto') {
        const theme = e.matches ? 'dark' : 'light';
        document.body.className = `theme-${theme}`;
        this.updateHLJSTheme();
    }
});
```

---

## Task 4: 会话导出功能

**Files:**
- Modify: `src/myagent/web/static/app.js:1520-1564`
- Modify: `src/myagent/web/static/index.html:74-92`

**Step 1: 添加导出按钮**

在 sidebar-footer 或设置面板中添加导出选项。

**Step 2: 实现导出逻辑**

```javascript
exportSession(format) {
    const session = this.sessions.find(s => s.id === this.currentSessionId);
    if (!session) return;

    let content, filename, mimeType;

    if (format === 'markdown') {
        content = this.sessionToMarkdown(session);
        filename = `session-${session.id}.md`;
        mimeType = 'text/markdown';
    } else {
        content = JSON.stringify(session, null, 2);
        filename = `session-${session.id}.json`;
        mimeType = 'application/json';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

sessionToMarkdown(session) {
    let md = `# Session: ${session.agent}\n\n`;
    md += `Model: ${session.model}\n`;
    md += `Created: ${session.created_at}\n\n`;
    md += `---\n\n`;
    session.messages.forEach(msg => {
        const role = msg.role === 'user' ? 'User' : 'Assistant';
        md += `## ${role}\n\n${msg.content}\n\n`;
    });
    return md;
}
```

---

## Task 5: 移动端响应式适配

**Files:**
- Modify: `src/myagent/web/static/style.css:1716-1801`

**Step 1: 优化小屏幕布局**

- 调整消息气泡宽度
- 优化输入框高度
- 确保侧边栏可正常滑动

**Step 2: 添加触摸反馈**

```css
@media (max-width: 768px) {
    .session-item:active {
        background: var(--bg-active);
    }

    .quick-card:active {
        transform: scale(0.98);
    }
}
```

**Step 3: 优化横屏模式**

```css
@media (max-height: 500px) and (orientation: landscape) {
    .chat-header {
        height: 44px;
    }

    .composer {
        padding: 8px 14px;
    }
}
```

---

## 测试清单

- [ ] 会话重命名正常工作
- [ ] 模型切换更新后端和前端显示
- [ ] 主题切换（暗色/亮色/自动）正常工作
- [ ] 会话导出 Markdown/JSON 文件内容正确
- [ ] 移动端侧边栏滑动正常
- [ ] 小屏幕消息显示完整

---

## 提交

```bash
git add -A
git commit -m "feat:WebUI增强-会话管理、模型选择、主题切换、导出功能"
git push origin master
```
