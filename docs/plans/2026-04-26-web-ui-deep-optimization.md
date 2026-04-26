# Web UI 深度优化迭代计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 系统性修复 MyAgent Web UI 的已知 Bug、安全隐患和交互缺陷，提升稳定性、安全性和用户体验。

**Architecture:** 基于现有 FastAPI + 原生 HTML/CSS/JS 架构，不引入新框架，通过增量修复和样式补全解决问题。

**Tech Stack:** Vanilla JS, CSS3 Variables, FastAPI, marked.js, highlight.js

---

## Phase 1: P0 紧急 Bug 修复（功能不可用）

### Task 1.1: 修复 `--accent-hover` 颜色值错误

**Files:**
- Modify: `src/myagent/web/static/style.css:62`

**Step 1: 定位错误值**

找到：
```css
--accent-hover: #9b5a2ff;
```

**Step 2: 修复为有效颜色值**

替换为：
```css
--accent-hover: #9b5aff;
```

> 说明：原值 `#9b5a2ff` 有 9 位字符，不是有效的 CSS 颜色。修正为 `#9b5aff`（紫色系，与品牌色调一致）。

**Step 3: 验证**

切换到亮色主题，悬停按钮观察颜色变化是否正常。

---

### Task 1.2: 修复 WebSocket 重连逻辑（移除死代码或启用重连）

**Files:**
- Modify: `src/myagent/web/static/app.js:1524-1589`

**Step 1: 分析当前 onclose 逻辑**

当前 `onclose` 中：
- 1006/1011：显示错误，设置 `reconnectAttempts = maxReconnectAttempts`（阻止重连）
- 其他：同样设置 `reconnectAttempts = maxReconnectAttempts`（阻止重连）
- `attemptReconnect` 方法永远不会被调用

**Step 2: 重写 onclose 逻辑**

将 `onclose` 回调替换为：

```javascript
this.ws.onclose = (event) => {
    this.setStatus('disconnected');
    // 正常关闭 (1000, 1005) 不重连
    if (event.code === 1000 || event.code === 1005) {
        return;
    }
    // 服务器错误 (1006, 1011) 显示错误但不无限重连
    if (event.code === 1006 || event.code === 1011) {
        if (this.reconnectAttempts === 0) {
            this.addMessage('error', '连接失败：服务器配置错误，请检查 LLM API Key 设置。', false);
        }
        this.reconnectAttempts = this.maxReconnectAttempts;
        return;
    }
    // 其他情况尝试重连
    this.attemptReconnect(sessionId);
};
```

**Step 3: 验证**

1. 启动服务器并连接会话
2. 停止服务器模拟断开
3. 观察是否触发重连（应有重连提示）

---

### Task 1.3: 补全消息编辑功能的 CSS 样式

**Files:**
- Modify: `src/myagent/web/static/style.css`（在文件末尾追加）

**Step 1: 添加消息编辑相关样式**

在 `style.css` 末尾追加：

```css
/* ---------- Message Edit ---------- */
.message-edit-input {
  width: 100%;
  background: var(--bg-secondary);
  border: 1px solid var(--accent-glow);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  padding: 10px 14px;
  font-size: 0.92rem;
  line-height: 1.5;
  resize: vertical;
  min-height: 60px;
  font-family: inherit;
  outline: none;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.message-edit-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.message-edit-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  justify-content: flex-end;
}

.message-edit-actions .btn-cancel {
  padding: 6px 14px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  font-size: 0.82rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.message-edit-actions .btn-cancel:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.message-edit-actions .btn-save {
  padding: 6px 14px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #fff;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.message-edit-actions .btn-save:hover {
  background: var(--accent-hover);
}

.message-edit-actions .btn-resend {
  padding: 6px 14px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--success);
  color: #fff;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.message-edit-actions .btn-resend:hover {
  background: #16a34a;
}
```

**Step 2: 验证**

1. 发送一条用户消息
2. 点击消息旁的编辑按钮
3. 确认编辑框和按钮样式正常

---

### Task 1.4: 补全代码块复制按钮的 CSS 样式

**Files:**
- Modify: `src/myagent/web/static/style.css`（在文件末尾追加）

**Step 1: 添加复制按钮样式**

在 `style.css` 末尾追加：

```css
/* ---------- Code Block Copy Button ---------- */
.copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--bg-elevated);
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--transition-fast), background var(--transition-fast), color var(--transition-fast);
  z-index: 5;
}

pre:hover .copy-btn {
  opacity: 1;
}

.copy-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-strong);
}

.copy-btn:active {
  transform: scale(0.92);
}

pre {
  position: relative;
}
```

**Step 2: 验证**

1. 让助手返回包含代码块的消息
2. 鼠标悬停在代码块上
3. 确认右上角出现复制按钮，点击后图标变化

---

## Phase 2: P1 安全与体验修复

### Task 2.1: 修复 Markdown 渲染 XSS 风险

**Files:**
- Modify: `src/myagent/web/static/app.js:2641-2646`
- Modify: `src/myagent/web/static/index.html`（添加 DOMPurify）

**Step 1: 引入 DOMPurify**

在 `index.html` 的 `<head>` 中，在 `marked.min.js` 之后添加：

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/dompurify/3.0.8/purify.min.js"></script>
```

**Step 2: 修改 renderMarkdown 方法**

将 `renderMarkdown` 替换为：

```javascript
renderMarkdown(text) {
    if (window.marked) {
        const rawHtml = window.marked.parse(text);
        if (window.DOMPurify) {
            return window.DOMPurify.sanitize(rawHtml);
        }
        return rawHtml;
    }
    return this.escapeHtml(text).replace(/\n/g, '<br>');
}
```

**Step 3: 验证**

1. 发送消息包含 `<script>alert('xss')</script>`
2. 确认脚本不会执行，输出被转义或过滤

---

### Task 2.2: 修复主题切换闪烁（FOUC）

**Files:**
- Modify: `src/myagent/web/static/index.html:21`

**Step 1: 在 head 中添加内联主题恢复脚本**

在 `<head>` 的最底部（`</head>` 之前）添加：

```html
<script>
  (function() {
    const savedTheme = localStorage.getItem('myagent-theme') || 'dark';
    const effective = savedTheme === 'auto'
      ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : savedTheme;
    document.documentElement.className = 'theme-' + effective;
  })();
</script>
```

**Step 2: 修改 body 的 class 逻辑**

将 `<body class="theme-dark">` 改为：

```html
<body>
```

> 主题由上述内联脚本在页面渲染前设置，避免闪烁。

**Step 3: 修改 app.js 中的 initTheme**

将 `initTheme` 方法改为同步应用已设置的主题类：

```javascript
initTheme() {
    const effective = this.getEffectiveTheme();
    document.body.className = `theme-${effective}`;
    this.updateHLJSTheme();
    this.updateThemeIcon();
}
```

**Step 4: 验证**

1. 切换到亮色主题
2. 刷新页面
3. 确认页面从始至终保持亮色，无暗色闪烁

---

### Task 2.3: 修复移动端详情侧栏无法关闭

**Files:**
- Modify: `src/myagent/web/static/app.js:1251-1258`
- Modify: `src/myagent/web/static/style.css:3545-3553`

**Step 1: 修改 hideFilePreview 方法**

确保移动端侧栏正确关闭：

```javascript
hideFilePreview() {
    this.filePreviewPanel.classList.remove('show', 'has-preview');
    this.detailSidebar?.classList.remove('show-mobile');
    if (this.previewContent) {
        this.previewContent.textContent = '';
        this.previewContent.className = '';
    }
}
```

**Step 2: 添加点击外部关闭逻辑**

在 `bindEvents` 中添加：

```javascript
// Close detail sidebar on mobile when clicking outside
this.detailSidebar?.addEventListener('click', (e) => {
    if (e.target === this.detailSidebar && window.innerWidth <= 768) {
        this.hideFilePreview();
    }
});
```

**Step 3: 验证**

1. 在移动端宽度（<=768px）打开详情侧栏
2. 点击侧栏外部区域确认可以关闭

---

### Task 2.4: 优化任务轮询（页面隐藏时暂停）

**Files:**
- Modify: `src/myagent/web/static/app.js:1951-1975`

**Step 1: 修改 startTaskPolling 和 stopTaskPolling**

添加页面可见性监听：

```javascript
startTaskPolling() {
    if (this.taskPollingTimer) {
        return;
    }
    this._visibilityHandler = () => {
        if (document.hidden) {
            this.stopTaskPolling();
        } else {
            this.loadCurrentTask();
            this.startTaskPolling();
        }
    };
    document.addEventListener('visibilitychange', this._visibilityHandler);
    this.taskPollingTimer = window.setInterval(() => {
        this.loadCurrentTask();
    }, 1500);
}

stopTaskPolling() {
    if (!this.taskPollingTimer) {
        return;
    }
    window.clearInterval(this.taskPollingTimer);
    this.taskPollingTimer = null;
    if (this._visibilityHandler) {
        document.removeEventListener('visibilitychange', this._visibilityHandler);
        this._visibilityHandler = null;
    }
}
```

**Step 2: 验证**

1. 打开任务视图
2. 切换到其他浏览器标签页
3. 观察网络面板，确认轮询请求停止
4. 切回标签页，确认轮询恢复

---

## Phase 3: P2 交互优化

### Task 3.1: 为文件树添加"返回上级"功能

**Files:**
- Modify: `src/myagent/web/static/app.js:1138-1144`
- Modify: `src/myagent/web/static/style.css:381-439`

**Step 1: 修改 renderFileTree 方法**

在渲染根目录时添加返回上级按钮（非根目录时）：

```javascript
renderFileTree(entries, parentPath) {
    this.fileTree.innerHTML = '';
    this.fileEntries = entries;
    this._fileTreeData = { entries, parentPath };

    // Add "go to parent" button if not at root
    if (parentPath && parentPath !== '.') {
        const parentItem = document.createElement('div');
        parentItem.className = 'file-tree-node';
        parentItem.innerHTML = `
            <div class="file-tree-item" style="padding-left: 12px">
                <span class="icon">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M19 12H5M12 19l-7-7 7-7"/>
                    </svg>
                </span>
                <span class="name">..</span>
            </div>
        `;
        parentItem.querySelector('.file-tree-item').addEventListener('click', () => {
            const parent = parentPath.split('/').slice(0, -1).join('/') || '.';
            this.loadFileTree(parent);
        });
        this.fileTree.appendChild(parentItem);
    }

    this._renderFileTreeNodes(entries, this.fileTree, parentPath, 0);
    this.renderFileBrowser();
}
```

**Step 2: 验证**

1. 进入某个子目录
2. 确认文件树顶部出现 ".." 返回按钮
3. 点击后返回上级目录

---

### Task 3.2: 为搜索添加上一个/下一个导航按钮

**Files:**
- Modify: `src/myagent/web/static/app.js:762-792`
- Modify: `src/myagent/web/static/index.html:322-337`

**Step 1: 修改搜索栏 HTML**

在 `search-bar` 中添加导航按钮：

```html
<div class="search-bar" id="search-bar">
    <div class="search-input-wrap">
        <!-- existing svg and input -->
        <input type="text" id="search-input" placeholder="搜索消息...">
    </div>
    <div class="search-nav">
        <button class="icon-btn" id="search-prev" title="上一个">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="15 18 9 12 15 6"/>
            </svg>
        </button>
        <span id="search-count" class="search-count"></span>
        <button class="icon-btn" id="search-next" title="下一个">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="9 18 15 12 9 6"/>
            </svg>
        </button>
    </div>
    <button class="icon-btn" id="search-close">
        <!-- existing close svg -->
    </button>
</div>
```

**Step 2: 添加搜索导航样式**

在 `style.css` 中追加：

```css
.search-nav {
  display: flex;
  align-items: center;
  gap: 4px;
}

.search-count {
  font-size: 0.78rem;
  color: var(--text-muted);
  min-width: 40px;
  text-align: center;
}
```

**Step 3: 修改 performSearch 和添加导航逻辑**

```javascript
performSearch(query) {
    this.clearSearchHighlights();
    if (!query.trim()) {
        this.updateSearchCount(0, 0);
        return;
    }

    const messages = this.messagesContainer.querySelectorAll('.message');
    const lowerQuery = query.toLowerCase();
    this._searchMatches = [];

    messages.forEach((msg, index) => {
        const content = msg.querySelector('.content');
        if (content && content.textContent.toLowerCase().includes(lowerQuery)) {
            msg.classList.add('highlighted');
            this._searchMatches.push(msg);
        }
    });

    this._searchIndex = 0;
    this.updateSearchCount(this._searchMatches.length);
    this.scrollToSearchMatch(0);
}

scrollToSearchMatch(index) {
    if (!this._searchMatches || this._searchMatches.length === 0) return;
    const clamped = Math.max(0, Math.min(index, this._searchMatches.length - 1));
    this._searchIndex = clamped;
    this._searchMatches[clamped].scrollIntoView({ behavior: 'smooth', block: 'center' });
    this.updateSearchCount(this._searchMatches.length);
}

updateSearchCount(total) {
    const countEl = document.getElementById('search-count');
    if (!countEl) return;
    if (total === 0) {
        countEl.textContent = '无结果';
    } else {
        countEl.textContent = `${this._searchIndex + 1} / ${total}`;
    }
}

nextSearchResult() {
    if (!this._searchMatches || this._searchMatches.length === 0) return;
    this.scrollToSearchMatch(this._searchIndex + 1);
}

prevSearchResult() {
    if (!this._searchMatches || this._searchMatches.length === 0) return;
    this.scrollToSearchMatch(this._searchIndex - 1);
}
```

**Step 4: 绑定导航按钮事件**

在 `bindEvents` 中添加：

```javascript
document.getElementById('search-prev')?.addEventListener('click', () => this.prevSearchResult());
document.getElementById('search-next')?.addEventListener('click', () => this.nextSearchResult());
```

**Step 5: 验证**

1. 打开搜索栏，输入关键词
2. 确认显示匹配数量（如 "2 / 5"）
3. 点击上下按钮导航到不同匹配项

---

### Task 3.3: 清理无效代码引用

**Files:**
- Modify: `src/myagent/web/static/app.js:129-164`

**Step 1: 移除对不存在元素的引用**

在 `initElements` 中，将：

```javascript
this.filePreviewPanel = document.getElementById('file-preview-panel');
```

改为：

```javascript
// file-preview-panel element does not exist in HTML; use detailSidebar as fallback
this.filePreviewPanel = this.detailSidebar;
```

同时移除：

```javascript
this.filePreviewPanel = this.filePreviewPanel || this.detailSidebar;
```

因为上面已经直接赋值了。

**Step 2: 移除 settingsThemeSelect 引用**

在 `initElements` 中删除：

```javascript
this.settingsThemeSelect = document.getElementById('settings-theme-select');
```

**Step 3: 验证**

1. 打开浏览器开发者工具
2. 确认控制台没有 "Cannot read properties of null" 错误

---

### Task 3.4: 修复会话导入重复文件问题

**Files:**
- Modify: `src/myagent/web/static/app.js:378-384`

**Step 1: 修改导入按钮事件绑定**

将：

```javascript
if (this.sessionImportFile) {
    this.sessionImportFile.addEventListener('change', (e) => this.importSession(e));
}
```

替换为：

```javascript
if (this.sessionImportFile) {
    this.sessionImportFile.addEventListener('change', (e) => {
        this.importSession(e);
        // Reset so the same file can be selected again
        e.target.value = '';
    });
}
```

**Step 2: 移除 finally 块中的重复重置**

在 `importSession` 方法的 `finally` 块中删除：

```javascript
event.target.value = '';
```

因为已经在事件监听器中处理了。

**Step 3: 验证**

1. 导入一个会话文件
2. 再次点击导入按钮，选择同一个文件
3. 确认可以正常触发导入

---

## Phase 4: 代码质量与可维护性

### Task 4.1: 为 Welcome Landing 事件绑定添加清理机制

**Files:**
- Modify: `src/myagent/web/static/app.js:827-868`

**Step 1: 使用事件委托替代直接绑定**

将 `bindQuickCards`、`bindDemoPathCards`、`bindDocsEntryCards` 改为事件委托：

```javascript
bindQuickCards() {
    this.welcomeScreen?.addEventListener('click', (e) => {
        const card = e.target.closest('.quick-card[data-prompt]');
        if (card) {
            const prompt = card.dataset.prompt;
            if (prompt) {
                this.messageInput.value = prompt;
                this.sendMessage();
            }
        }
    });
}

bindDemoPathCards() {
    this.welcomeScreen?.addEventListener('click', (e) => {
        const card = e.target.closest('.demo-path-card');
        if (card) {
            const viewName = card.dataset.demoView;
            const prompt = card.dataset.demoPrompt;
            if (viewName) {
                this.setActiveView(viewName);
            }
            if (prompt && this.messageInput) {
                this.messageInput.value = prompt;
                if (viewName === 'chat') {
                    this.messageInput.focus();
                }
            }
        }
    });
}

bindDocsEntryCards() {
    this.welcomeScreen?.addEventListener('click', (e) => {
        const card = e.target.closest('.docs-entry-card[data-doc-path]');
        if (card) {
            const docPath = card.dataset.docPath;
            const docName = card.dataset.docName || docPath || '文档';
            if (!docPath) return;
            this.setActiveView('files');
            this.loadFileTree('.');
            this.showFilePreview(docPath, docName);
        }
    });
}
```

**Step 2: 验证**

1. 刷新页面进入 Welcome 界面
2. 点击各个卡片确认功能正常
3. 多次切换视图后返回，确认无内存泄漏

---

## 测试清单

- [ ] 亮色主题悬停按钮颜色正常
- [ ] WebSocket 断开后自动重连
- [ ] 消息编辑框样式正常，保存/取消/重新发送功能正常
- [ ] 代码块复制按钮悬停显示，点击后图标变化
- [ ] Markdown 中的 `<script>` 标签被过滤，不执行
- [ ] 亮色主题刷新页面无闪烁
- [ ] 移动端详情侧栏可点击外部关闭
- [ ] 切换标签页后任务轮询暂停，返回后恢复
- [ ] 文件树进入子目录后可返回上级
- [ ] 搜索消息支持上一个/下一个导航
- [ ] 控制台无 null 引用错误
- [ ] 同一个会话文件可重复导入
- [ ] Welcome 卡片点击功能正常

---

## 提交

```bash
git add -A
git commit -m "fix(web-ui): 修复 P0 Bug、XSS 风险、主题闪烁和交互缺陷

- 修复 --accent-hover 无效颜色值
- 修复 WebSocket 重连逻辑
- 补全消息编辑和代码复制按钮样式
- 添加 DOMPurify 防止 XSS
- 修复主题切换 FOUC 闪烁
- 优化移动端侧栏关闭体验
- 页面隐藏时暂停任务轮询
- 文件树添加返回上级功能
- 搜索添加上一个/下一个导航
- 清理无效代码引用"
```
