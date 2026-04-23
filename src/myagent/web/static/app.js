/**
 * MyAgent Web UI - Frontend Application
 * Modern, polished interaction layer
 */

class MyAgentWebApp {
    constructor() {
        this.ws = null;
        this.currentSessionId = null;
        this.sessions = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.isSending = false;
        this.searchQuery = '';
        this.currentTheme = localStorage.getItem('myagent-theme') || 'dark';

        this.initTheme();
        this.initElements();
        this.bindEvents();
        this.loadSessions();
        this.loadFileTree('.');
    }

    // ========== Theme ==========

    initTheme() {
        document.body.className = `theme-${this.currentTheme}`;
        this.updateHLJSTheme();
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        document.body.className = `theme-${this.currentTheme}`;
        localStorage.setItem('myagent-theme', this.currentTheme);
        this.updateHLJSTheme();
        this.updateThemeIcon();
    }

    updateHLJSTheme() {
        const link = document.getElementById('hljs-theme');
        if (link) {
            const theme = this.currentTheme === 'dark' ? 'atom-one-dark' : 'github';
            link.href = `https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/${theme}.min.css`;
        }
    }

    updateThemeIcon() {
        const icon = document.getElementById('theme-icon');
        if (!icon) return;
        if (this.currentTheme === 'dark') {
            icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
        } else {
            icon.innerHTML = '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>';
        }
    }

    // ========== Elements ==========

    initElements() {
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.messagesContainer = document.getElementById('messages');
        this.welcomeScreen = document.getElementById('welcome-screen');
        this.sessionList = document.getElementById('session-list');
        this.newSessionBtn = document.getElementById('new-session-btn');
        this.statusIndicator = document.getElementById('status-indicator');
        this.statusDot = document.getElementById('status-dot');
        this.currentAgent = document.getElementById('current-agent');
        this.currentModel = document.getElementById('current-model');
        this.fileTree = document.getElementById('file-tree');
        this.filePreviewPanel = document.getElementById('file-preview-panel');
        this.previewFilename = document.getElementById('preview-filename');
        this.previewContent = document.getElementById('preview-content');
        this.closePreviewBtn = document.getElementById('close-preview');
        this.themeToggle = document.getElementById('theme-toggle');
        this.mobileSidebarToggle = document.getElementById('mobile-sidebar-toggle');
        this.sidebar = document.getElementById('sidebar');
        this.sidebarOverlay = document.getElementById('sidebar-overlay');
        this.agentSelect = document.getElementById('agent-select');
        this.searchToggle = document.getElementById('search-toggle');
        this.searchBar = document.getElementById('search-bar');
        this.searchInput = document.getElementById('search-input');
        this.searchClose = document.getElementById('search-close');

        // Settings modal
        this.settingsBtn = document.getElementById('settings-btn');
        this.settingsModal = document.getElementById('settings-modal');
        this.closeSettingsBtn = document.getElementById('close-settings');
        this.saveSettingsBtn = document.getElementById('save-settings-btn');
        this.settingsAgentSelect = document.getElementById('settings-agent-select');
        this.settingsSystemPrompt = document.getElementById('settings-system-prompt');
        this.settingsThemeSelect = document.getElementById('settings-theme-select');
        this.settingsSessionCount = document.getElementById('settings-session-count');
        this.settingsMessageCount = document.getElementById('settings-message-count');

        // Reset modal
        this.resetModal = document.getElementById('reset-modal');
        this.resetMessage = document.getElementById('reset-message');
        this.resetConfirmBtn = document.getElementById('reset-confirm');
        this.resetCancelBtn = document.getElementById('reset-cancel');
        this.resetConversationBtn = document.getElementById('reset-conversation-btn');
        this.resetAllSessionsBtn = document.getElementById('reset-all-sessions-btn');
        this.resetConfigBtn = document.getElementById('reset-config-btn');

        // Settings tabs
        this.tabBtns = document.querySelectorAll('.tab-btn');
        this.tabContents = document.querySelectorAll('.tab-content');

        this.updateThemeIcon();
    }

    // ========== Events ==========

    bindEvents() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());

        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 200) + 'px';
        });

        this.newSessionBtn.addEventListener('click', () => this.createSession());
        this.closePreviewBtn.addEventListener('click', () => this.hideFilePreview());
        this.themeToggle.addEventListener('click', () => this.toggleTheme());

        // Mobile sidebar
        this.mobileSidebarToggle.addEventListener('click', () => this.openSidebar());
        this.sidebarOverlay.addEventListener('click', () => this.closeSidebar());

        // Agent select
        this.agentSelect.addEventListener('change', (e) => this.switchAgent(e.target.value));

        // Search
        this.searchToggle.addEventListener('click', () => this.toggleSearch());
        this.searchClose.addEventListener('click', () => this.toggleSearch());
        this.searchInput.addEventListener('input', (e) => this.performSearch(e.target.value));

        // Settings
        this.settingsBtn.addEventListener('click', () => this.openSettings());
        this.closeSettingsBtn.addEventListener('click', () => this.closeSettings());
        this.saveSettingsBtn.addEventListener('click', () => this.saveSettings());
        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) this.closeSettings();
        });

        // Settings tabs
        this.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });

        // Theme in settings
        this.settingsThemeSelect.addEventListener('change', (e) => {
            const val = e.target.value;
            this.currentTheme = val === 'auto' ? 'dark' : val;
            document.body.className = `theme-${this.currentTheme}`;
            localStorage.setItem('myagent-theme', this.currentTheme);
            this.updateHLJSTheme();
            this.updateThemeIcon();
        });

        // Reset buttons
        this.resetConversationBtn.addEventListener('click', () => this.showResetConfirm('conversation'));
        this.resetAllSessionsBtn.addEventListener('click', () => this.showResetConfirm('all'));
        this.resetConfigBtn.addEventListener('click', () => this.showResetConfirm('config'));
        this.resetCancelBtn.addEventListener('click', () => this.hideResetModal());
        this.resetConfirmBtn.addEventListener('click', () => this.executeReset());
        this.resetModal.addEventListener('click', (e) => {
            if (e.target === this.resetModal) this.hideResetModal();
        });
    }

    // ========== Tabs ==========

    switchTab(tabName) {
        this.tabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        this.tabContents.forEach(content => {
            content.classList.toggle('active', content.dataset.tab === tabName);
        });
    }

    // ========== Sidebar Mobile ==========

    openSidebar() {
        this.sidebar.classList.add('show');
        this.sidebarOverlay.classList.add('show');
    }

    closeSidebar() {
        this.sidebar.classList.remove('show');
        this.sidebarOverlay.classList.remove('show');
    }

    // ========== Agent Switch ==========

    async switchAgent(agentName) {
        if (!this.currentSessionId) return;

        try {
            const response = await fetch(`/api/sessions/${this.currentSessionId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent: agentName }),
            });

            if (response.ok) {
                const session = this.sessions.find(s => s.id === this.currentSessionId);
                if (session) {
                    session.agent = agentName;
                    this.currentAgent.textContent = agentName;
                    this.renderSessionList();
                }
                this.connectWebSocket(this.currentSessionId);
                this.addMessage('assistant', `已切换到 agent: **${agentName}**`, false);
            }
        } catch (error) {
            console.error('Failed to switch agent:', error);
        }
    }

    // ========== Search ==========

    toggleSearch() {
        const isVisible = this.searchBar.classList.contains('show');
        this.searchBar.classList.toggle('show', !isVisible);
        if (!isVisible) {
            this.searchInput.focus();
        } else {
            this.searchInput.value = '';
            this.clearSearchHighlights();
        }
    }

    performSearch(query) {
        this.clearSearchHighlights();
        if (!query.trim()) return;

        const messages = this.messagesContainer.querySelectorAll('.message');
        const lowerQuery = query.toLowerCase();

        messages.forEach(msg => {
            const content = msg.querySelector('.content');
            if (content && content.textContent.toLowerCase().includes(lowerQuery)) {
                msg.classList.add('highlighted');
                msg.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    }

    clearSearchHighlights() {
        this.messagesContainer.querySelectorAll('.message.highlighted')
            .forEach(msg => msg.classList.remove('highlighted'));
    }

    // ========== File Browser ==========

    async loadFileTree(path) {
        try {
            const response = await fetch(`/api/files?path=${encodeURIComponent(path)}`);
            const data = await response.json();
            this.renderFileTree(data.entries, path);
        } catch (error) {
            console.error('Failed to load file tree:', error);
        }
    }

    renderFileTree(entries, parentPath) {
        this.fileTree.innerHTML = '';

        if (parentPath !== '.') {
            const upItem = document.createElement('div');
            upItem.className = 'file-tree-item dir';
            upItem.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" opacity="0.5"><path d="M15 18l-6-6 6-6"/></svg>
                <span class="name">..</span>
            `;
            upItem.addEventListener('click', () => {
                const parent = parentPath.split('\\').slice(0, -1).join('\\') || '.';
                this.loadFileTree(parent);
            });
            this.fileTree.appendChild(upItem);
        }

        entries.forEach(entry => {
            const item = document.createElement('div');
            item.className = `file-tree-item ${entry.is_dir ? 'dir' : ''}`;

            const iconSvg = entry.is_dir
                ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>'
                : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>';

            item.innerHTML = `
                <span class="icon">${iconSvg}</span>
                <span class="name">${entry.name}</span>
            `;

            if (entry.is_dir) {
                item.addEventListener('click', () => this.loadFileTree(entry.path));
            } else {
                item.addEventListener('click', () => this.showFilePreview(entry.path, entry.name));
            }

            this.fileTree.appendChild(item);
        });
    }

    async showFilePreview(path, name) {
        try {
            const response = await fetch(`/api/files/read?path=${encodeURIComponent(path)}`);
            const data = await response.json();

            this.previewFilename.textContent = name;
            this.previewContent.textContent = data.content;

            const ext = name.split('.').pop().toLowerCase();
            this.previewContent.className = ext;
            if (window.hljs) {
                window.hljs.highlightElement(this.previewContent);
            }

            this.filePreviewPanel.classList.add('show');
            this.closeSidebar();
        } catch (error) {
            console.error('Failed to load file:', error);
        }
    }

    hideFilePreview() {
        this.filePreviewPanel.classList.remove('show');
    }

    // ========== Sessions ==========

    async loadSessions() {
        try {
            const response = await fetch('/api/sessions');
            this.sessions = await response.json();
            this.renderSessionList();

            if (this.sessions.length > 0 && !this.currentSessionId) {
                this.selectSession(this.sessions[0].id);
            }
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    }

    renderSessionList() {
        this.sessionList.innerHTML = '';

        this.sessions.forEach(session => {
            const item = document.createElement('div');
            item.className = `session-item ${session.id === this.currentSessionId ? 'active' : ''}`;
            item.innerHTML = `
                <div class="session-title">${session.agent}</div>
                <div class="session-meta">${this.formatDate(session.updated_at)}</div>
            `;
            item.addEventListener('click', () => {
                this.selectSession(session.id);
                this.closeSidebar();
            });
            this.sessionList.appendChild(item);
        });
    }

    formatDate(isoString) {
        const date = new Date(isoString);
        return date.toLocaleString('zh-CN', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    async createSession() {
        try {
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent: 'general', model: 'glm-4.7' })
            });

            const session = await response.json();
            this.sessions.unshift(session);
            this.renderSessionList();
            this.selectSession(session.id);
            this.closeSidebar();
        } catch (error) {
            console.error('Failed to create session:', error);
            this.addMessage('error', '创建会话失败');
        }
    }

    selectSession(sessionId) {
        this.currentSessionId = sessionId;
        this.renderSessionList();
        this.messagesContainer.innerHTML = '';
        this.clearSearchHighlights();

        const session = this.sessions.find(s => s.id === sessionId);
        if (session) {
            this.welcomeScreen.style.display = 'none';
            this.currentAgent.textContent = session.agent;
            this.currentModel.textContent = session.model;
            this.agentSelect.value = session.agent;

            session.messages.forEach(msg => {
                this.addMessage(msg.role, msg.content, false);
            });
        } else {
            this.welcomeScreen.style.display = 'flex';
        }

        this.connectWebSocket(sessionId);
    }

    // ========== WebSocket ==========

    connectWebSocket(sessionId) {
        if (this.ws) {
            this.ws.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.setStatus('connected');
            this.reconnectAttempts = 0;
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onclose = (event) => {
            this.setStatus('disconnected');
            // Only reconnect if it was not a clean close due to server-side error
            // (code 1000 = normal, 1001 = going away, 1005 = no status)
            // Code 1006 = abnormal closure (server error, network issue)
            if (event.code === 1006 || event.code === 1011) {
                // Server error - show error once and stop reconnecting
                if (this.reconnectAttempts === 0) {
                    this.addMessage('error', '连接失败：服务器配置错误，请检查 LLM API Key 设置。', false);
                }
                this.reconnectAttempts = this.maxReconnectAttempts; // Prevent further reconnects
                return;
            }
            this.attemptReconnect(sessionId);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.setStatus('disconnected');
        };
    }

    attemptReconnect(sessionId) {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                this.connectWebSocket(sessionId);
            }, 2000 * this.reconnectAttempts);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'user':
                this.addMessage('user', data.message, false);
                break;

            case 'assistant_start':
                this.showTypingIndicator();
                this.setSending(true);
                break;

            case 'assistant_delta':
                this.hideTypingIndicator();
                this.addMessage('assistant', data.text, true);
                break;

            case 'assistant_done':
                this.hideTypingIndicator();
                this.setSending(false);
                break;

            case 'tool_call':
                this.addMessage('tool-call', `Tool: ${data.tool_name}\n${JSON.stringify(data.arguments, null, 2)}`, false);
                break;

            case 'tool_result':
                this.addMessage('tool-result', data.result, false);
                break;

            case 'error':
                this.addMessage('error', data.message, false);
                this.setSending(false);
                break;

            case 'permission_request':
                this.showPermissionModal(data);
                break;

            case 'permission_result':
                const status = data.approved ? 'approved' : 'denied';
                this.addMessage('tool-result', `Permission ${status}: ${data.reason}`, false);
                break;
        }
    }

    // ========== Sending State ==========

    setSending(sending) {
        this.isSending = sending;
        this.sendBtn.disabled = sending;
        this.sendBtn.style.opacity = sending ? '0.5' : '1';
    }

    sendMessage() {
        const text = this.messageInput.value.trim();
        if (!text || !this.ws || this.ws.readyState !== WebSocket.OPEN || this.isSending) {
            return;
        }

        this.ws.send(JSON.stringify({ message: text }));
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.setSending(true);
    }

    sendPermissionResponse(toolUseId, approved) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                action: 'approve_permission',
                tool_use_id: toolUseId,
                approved: approved,
            }));
        }
    }

    showPermissionModal(data) {
        const modal = document.createElement('div');
        modal.className = 'permission-modal';

        const argsHtml = Object.entries(data.arguments)
            .map(([k, v]) => `<div class="perm-arg"><strong>${k}:</strong> ${v}</div>`)
            .join('');

        modal.innerHTML = `
            <div class="permission-dialog">
                <h3>Permission Required</h3>
                <p class="perm-reason">${data.reason}</p>
                <div class="perm-details">
                    <div><strong>Tool:</strong> ${data.tool_name}</div>
                    ${argsHtml}
                </div>
                <div class="perm-buttons">
                    <button class="btn-deny" onclick="window.myAgentApp.handlePermission(false)">Deny</button>
                    <button class="btn-allow" onclick="window.myAgentApp.handlePermission(true)">Allow</button>
                </div>
            </div>
        `;

        this._pendingPermission = data;
        document.body.appendChild(modal);
    }

    handlePermission(approved) {
        if (this._pendingPermission) {
            this.sendPermissionResponse(this._pendingPermission.tool_name, approved);
            this._pendingPermission = null;
        }
        const modal = document.querySelector('.permission-modal');
        if (modal) modal.remove();
    }

    // ========== Messages ==========

    addMessage(role, content, append = false) {
        if (append) {
            const lastMessage = this.messagesContainer.lastElementChild;
            if (lastMessage && lastMessage.classList.contains(role)) {
                const contentEl = lastMessage.querySelector('.content');
                if (role === 'assistant') {
                    contentEl.innerHTML = this.renderMarkdown(contentEl.textContent + content);
                } else {
                    contentEl.textContent += content;
                }
                this.scrollToBottom();
                return;
            }
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const roleLabels = {
            'user': 'You',
            'assistant': 'Agent',
            'tool-call': 'Tool',
            'tool-result': 'Result',
            'error': 'Error'
        };

        let contentHtml;
        if (role === 'assistant') {
            contentHtml = this.renderMarkdown(content);
        } else {
            contentHtml = this.escapeHtml(content);
        }

        messageDiv.innerHTML = `
            <div class="role-label">${roleLabels[role] || role}</div>
            <div class="content">${contentHtml}</div>
        `;

        if (role === 'assistant' && window.hljs) {
            messageDiv.querySelectorAll('pre code').forEach((block) => {
                window.hljs.highlightElement(block);
            });
        }

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    renderMarkdown(text) {
        if (window.marked) {
            return window.marked.parse(text);
        }
        return this.escapeHtml(text).replace(/\n/g, '<br>');
    }

    showTypingIndicator() {
        if (document.querySelector('.typing-indicator')) return;

        const indicator = document.createElement('div');
        indicator.className = 'message assistant typing-indicator';
        indicator.innerHTML = '<span></span><span></span><span></span>';
        this.messagesContainer.appendChild(indicator);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const indicator = document.querySelector('.typing-indicator');
        if (indicator) indicator.remove();
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    setStatus(status) {
        const isConnected = status === 'connected';
        this.statusIndicator.textContent = isConnected ? '已连接' : '未连接';
        this.statusDot.classList.toggle('connected', isConnected);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ========== Settings ==========

    openSettings() {
        const session = this.sessions.find(s => s.id === this.currentSessionId);
        if (session) {
            this.settingsAgentSelect.value = session.agent || 'general';
        }
        this.settingsThemeSelect.value = this.currentTheme;

        this.settingsSessionCount.textContent = this.sessions.length;
        const totalMessages = this.sessions.reduce((sum, s) => sum + (s.messages ? s.messages.length : 0), 0);
        this.settingsMessageCount.textContent = totalMessages;

        this.settingsModal.classList.add('show');
    }

    closeSettings() {
        this.settingsModal.classList.remove('show');
    }

    async saveSettings() {
        const agent = this.settingsAgentSelect.value;

        if (this.currentSessionId) {
            try {
                const response = await fetch(`/api/sessions/${this.currentSessionId}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ agent }),
                });

                if (response.ok) {
                    const session = this.sessions.find(s => s.id === this.currentSessionId);
                    if (session) {
                        session.agent = agent;
                        this.currentAgent.textContent = agent;
                        this.agentSelect.value = agent;
                        this.renderSessionList();
                    }
                    this.connectWebSocket(this.currentSessionId);
                }
            } catch (error) {
                console.error('Failed to save settings:', error);
            }
        }

        this.closeSettings();
        this.addMessage('assistant', '设置已保存', false);
    }

    // ========== Reset ==========

    showResetConfirm(type) {
        this._resetType = type;
        const messages = {
            conversation: '确定要重置当前对话吗？所有消息将被清空。',
            all: '确定要重置所有会话吗？所有会话数据将被删除。',
            config: '确定要重置配置吗？配置将恢复为默认值（API Key 不会被清除）。',
        };
        this.resetMessage.textContent = messages[type] || '确定要执行此操作吗？此操作不可撤销。';
        this.resetModal.classList.add('show');
    }

    hideResetModal() {
        this.resetModal.classList.remove('show');
        this._resetType = null;
    }

    async executeReset() {
        const type = this._resetType;
        if (!type) return;

        try {
            switch (type) {
                case 'conversation':
                    if (this.currentSessionId) {
                        await fetch(`/api/sessions/${this.currentSessionId}/messages`, { method: 'DELETE' });
                        this.messagesContainer.innerHTML = '';
                        const session = this.sessions.find(s => s.id === this.currentSessionId);
                        if (session) session.messages = [];
                        this.addMessage('assistant', '对话已重置', false);
                    }
                    break;

                case 'all':
                    await fetch('/api/sessions', { method: 'DELETE' });
                    this.sessions = [];
                    this.currentSessionId = null;
                    this.messagesContainer.innerHTML = '';
                    this.welcomeScreen.style.display = 'flex';
                    this.renderSessionList();
                    this.addMessage('assistant', '所有会话已重置', false);
                    break;

                case 'config':
                    await fetch('/api/config', { method: 'DELETE' });
                    this.addMessage('assistant', '配置已重置为默认值', false);
                    break;
            }
        } catch (error) {
            console.error('Reset failed:', error);
            this.addMessage('error', '重置失败: ' + error.message, false);
        }

        this.hideResetModal();
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.myAgentApp = new MyAgentWebApp();
});
