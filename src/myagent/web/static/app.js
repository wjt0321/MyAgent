/**
 * MyAgent Web UI - Frontend Application
 */

class MyAgentWebApp {
    constructor() {
        this.ws = null;
        this.currentSessionId = null;
        this.sessions = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.expandedDirs = new Set();

        this.initElements();
        this.bindEvents();
        this.loadSessions();
        this.loadFileTree('.');
    }

    initElements() {
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.messagesContainer = document.getElementById('messages');
        this.sessionList = document.getElementById('session-list');
        this.newSessionBtn = document.getElementById('new-session-btn');
        this.statusIndicator = document.getElementById('status-indicator');
        this.currentAgent = document.getElementById('current-agent');
        this.currentModel = document.getElementById('current-model');
        this.fileTree = document.getElementById('file-tree');
        this.filePreviewPanel = document.getElementById('file-preview-panel');
        this.previewFilename = document.getElementById('preview-filename');
        this.previewContent = document.getElementById('preview-content');
        this.closePreviewBtn = document.getElementById('close-preview');
    }

    bindEvents() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());

        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.newSessionBtn.addEventListener('click', () => this.createSession());
        this.closePreviewBtn.addEventListener('click', () => this.hideFilePreview());
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
                <span class="file-tree-toggle"></span>
                <span class="icon">📁</span>
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

            const toggle = entry.is_dir ?
                `<span class="file-tree-toggle">▶</span>` :
                '<span class="file-tree-toggle"></span>';
            const icon = entry.is_dir ? '📁' : this.getFileIcon(entry.name);

            item.innerHTML = `
                ${toggle}
                <span class="icon">${icon}</span>
                <span class="name">${entry.name}</span>
            `;

            if (entry.is_dir) {
                item.addEventListener('click', () => {
                    this.loadFileTree(entry.path);
                });
            } else {
                item.addEventListener('click', () => {
                    this.showFilePreview(entry.path, entry.name);
                });
            }

            this.fileTree.appendChild(item);
        });
    }

    getFileIcon(filename) {
        const ext = filename.split('.').pop().toLowerCase();
        const icons = {
            'py': '🐍', 'js': '📜', 'ts': '📘', 'html': '🌐', 'css': '🎨',
            'json': '📋', 'yaml': '📋', 'yml': '📋', 'md': '📝', 'txt': '📄',
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
            'pdf': '📕', 'zip': '📦', 'tar': '📦', 'gz': '📦',
        };
        return icons[ext] || '📄';
    }

    async showFilePreview(path, name) {
        try {
            const response = await fetch(`/api/files/read?path=${encodeURIComponent(path)}`);
            const data = await response.json();

            this.previewFilename.textContent = name;
            this.previewContent.textContent = data.content;

            // Apply syntax highlighting
            const ext = name.split('.').pop().toLowerCase();
            this.previewContent.className = ext;
            if (window.hljs) {
                window.hljs.highlightElement(this.previewContent);
            }

            this.filePreviewPanel.style.display = 'flex';
        } catch (error) {
            console.error('Failed to load file:', error);
        }
    }

    hideFilePreview() {
        this.filePreviewPanel.style.display = 'none';
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
                <div class="session-title">${session.agent} - ${session.id}</div>
                <div class="session-meta">${this.formatDate(session.updated_at)}</div>
            `;
            item.addEventListener('click', () => this.selectSession(session.id));
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
        } catch (error) {
            console.error('Failed to create session:', error);
            this.addMessage('error', '创建会话失败');
        }
    }

    selectSession(sessionId) {
        this.currentSessionId = sessionId;
        this.renderSessionList();
        this.messagesContainer.innerHTML = '';

        const session = this.sessions.find(s => s.id === sessionId);
        if (session) {
            this.currentAgent.textContent = `Agent: ${session.agent}`;
            this.currentModel.textContent = `Model: ${session.model}`;

            session.messages.forEach(msg => {
                this.addMessage(msg.role, msg.content, false);
            });
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

        this.ws.onclose = () => {
            this.setStatus('disconnected');
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
                break;

            case 'assistant_delta':
                this.hideTypingIndicator();
                this.addMessage('assistant', data.text, true);
                break;

            case 'assistant_done':
                this.hideTypingIndicator();
                break;

            case 'tool_call':
                this.addMessage('tool-call', `Tool: ${data.tool_name}\n${JSON.stringify(data.arguments, null, 2)}`, false);
                break;

            case 'tool_result':
                this.addMessage('tool-result', data.result, false);
                break;

            case 'error':
                this.addMessage('error', data.message, false);
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

    sendMessage() {
        const text = this.messageInput.value.trim();
        if (!text || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            return;
        }

        this.ws.send(JSON.stringify({ message: text }));
        this.messageInput.value = '';
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
                contentEl.textContent += content;
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
            // Render Markdown for assistant messages
            contentHtml = this.renderMarkdown(content);
        } else {
            contentHtml = this.escapeHtml(content);
        }

        messageDiv.innerHTML = `
            <div class="role-label">${roleLabels[role] || role}</div>
            <div class="content">${contentHtml}</div>
        `;

        // Apply syntax highlighting to code blocks
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
        // Fallback: simple HTML escape
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
        if (indicator) {
            indicator.remove();
        }
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    setStatus(status) {
        this.statusIndicator.textContent = status === 'connected' ? '已连接' : '未连接';
        this.statusIndicator.className = status === 'connected' ? 'status-connected' : 'status-disconnected';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.myAgentApp = new MyAgentWebApp();
});
