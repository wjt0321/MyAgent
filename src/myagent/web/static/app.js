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
        this.loadWorkspace();
        this.loadCurrentTask();
        this.loadTeam();
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
        this.workspaceInfo = document.getElementById('workspace-info');

        // Memory management
        this.memoryList = document.getElementById('memory-list');
        this.memoryForm = document.getElementById('memory-form');
        this.newMemoryBtn = document.getElementById('new-memory-btn');
        this.memoryName = document.getElementById('memory-name');
        this.memoryDescription = document.getElementById('memory-description');
        this.memoryType = document.getElementById('memory-type');
        this.memoryContent = document.getElementById('memory-content');
        this.memorySaveBtn = document.getElementById('memory-save');
        this.memoryCancelBtn = document.getElementById('memory-cancel');

        // Task workflow
        this.taskPanel = document.getElementById('task-panel');
        this.taskWorkflowModal = document.getElementById('task-workflow-modal');
        this.taskPlanSteps = document.getElementById('task-plan-steps');
        this.taskApproveBtn = document.getElementById('task-approve');
        this.taskRejectBtn = document.getElementById('task-reject');
        this.closeTaskWorkflowBtn = document.getElementById('close-task-workflow');
        this.currentTask = null;

        // Team panel
        this.teamPanel = document.getElementById('team-panel');

        // Codebase panel
        this.rebuildIndexBtn = document.getElementById('rebuild-index-btn');
        this.codebaseSearchInput = document.getElementById('codebase-search-input');
        this.codebaseSearchBtn = document.getElementById('codebase-search-btn');
        this.codebaseStats = document.getElementById('codebase-stats');
        this.codebaseResults = document.getElementById('codebase-results');

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

        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeSettings();
                this.closeSidebar();
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

        // Quick action cards
        document.querySelectorAll('.quick-card').forEach(card => {
            card.addEventListener('click', () => {
                const prompt = card.dataset.prompt;
                if (prompt) {
                    this.messageInput.value = prompt;
                    this.sendMessage();
                }
            });
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

        // Memory management
        this.newMemoryBtn.addEventListener('click', () => this.showMemoryForm());
        this.memoryCancelBtn.addEventListener('click', () => this.hideMemoryForm());
        this.memorySaveBtn.addEventListener('click', () => this.saveMemory());

        // Task workflow
        this.closeTaskWorkflowBtn.addEventListener('click', () => this.hideTaskWorkflow());
        this.taskRejectBtn.addEventListener('click', () => this.hideTaskWorkflow());
        this.taskApproveBtn.addEventListener('click', () => this.approveTask());
        this.taskWorkflowModal.addEventListener('click', (e) => {
            if (e.target === this.taskWorkflowModal) this.hideTaskWorkflow();
        });

        // Codebase panel
        this.rebuildIndexBtn.addEventListener('click', () => this.rebuildCodebaseIndex());
        this.codebaseSearchBtn.addEventListener('click', () => this.searchCodebase());
        this.codebaseSearchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.searchCodebase();
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

    // ========== Workspace ==========

    async loadWorkspace() {
        try {
            const response = await fetch('/api/workspace');
            const data = await response.json();
            this.renderWorkspace(data);
        } catch (error) {
            console.error('Failed to load workspace:', error);
            if (this.workspaceInfo) {
                this.workspaceInfo.innerHTML = '<div class="workspace-empty">Workspace 未初始化</div>';
            }
        }
    }

    renderWorkspace(data) {
        if (!this.workspaceInfo) return;

        if (!data.initialized) {
            this.workspaceInfo.innerHTML = `
                <div class="workspace-empty">
                    <div class="workspace-empty-title">Workspace 未初始化</div>
                    <div class="workspace-empty-desc">运行 <code>myagent init</code> 创建 Workspace</div>
                </div>
            `;
            return;
        }

        const memoryItems = (data.memories || []).map(mem => `
            <div class="workspace-memory-item" data-filename="${mem.filename}">
                <div class="memory-name">${mem.name}</div>
                <div class="memory-desc">${mem.description || mem.type}</div>
            </div>
        `).join('');

        const projectItems = (data.projects || []).map(proj => `
            <div class="workspace-project-item">${proj}</div>
        `).join('');

        this.workspaceInfo.innerHTML = `
            <div class="workspace-section">
                <div class="workspace-section-title">用户</div>
                <div class="workspace-user-preview">${data.user ? this.escapeHtml(data.user.split('\n').slice(0, 3).join('\n')) : '未设置用户资料'}</div>
            </div>
            <div class="workspace-section">
                <div class="workspace-section-title">记忆 (${data.memories?.length || 0})</div>
                <div class="workspace-memory-list">
                    ${memoryItems || '<div class="workspace-empty-item">暂无记忆</div>'}
                </div>
            </div>
            <div class="workspace-section">
                <div class="workspace-section-title">项目 (${data.projects?.length || 0})</div>
                <div class="workspace-project-list">
                    ${projectItems || '<div class="workspace-empty-item">暂无项目</div>'}
                </div>
            </div>
        `;

        // Add click handlers for memory items to preview
        this.workspaceInfo.querySelectorAll('.workspace-memory-item').forEach(item => {
            item.addEventListener('click', () => {
                const filename = item.dataset.filename;
                if (filename) {
                    // Memory files are in ~/.myagent/memory/
                    // We'll use a dedicated endpoint or construct path
                    this.showMemoryPreview(filename);
                }
            });
        });
    }

    async showMemoryPreview(filename) {
        try {
            // Try to read from workspace memory directory via files API
            const wsPath = await this._getWorkspacePath();
            if (!wsPath) return;
            const memPath = `${wsPath}/memory/${filename}`;
            const response = await fetch(`/api/files/read?path=${encodeURIComponent(memPath)}`);
            if (!response.ok) throw new Error('Failed to load memory');
            const data = await response.json();
            this.previewFilename.textContent = filename;
            this.previewContent.innerHTML = window.marked ? window.marked.parse(data.content) : this.escapeHtml(data.content);
            this.previewContent.className = 'markdown-preview';
            this.filePreviewPanel.classList.add('show');
        } catch (error) {
            console.error('Failed to load memory preview:', error);
        }
    }

    async _getWorkspacePath() {
        try {
            const response = await fetch('/api/workspace');
            const data = await response.json();
            return data.path;
        } catch (error) {
            return null;
        }
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
        this._fileTreeData = { entries, parentPath };
        this._renderFileTreeNodes(entries, this.fileTree, parentPath, 0);
    }

    _renderFileTreeNodes(entries, container, parentPath, depth) {
        entries.forEach(entry => {
            const item = document.createElement('div');
            item.className = 'file-tree-node';

            const indent = depth * 14;

            if (entry.is_dir) {
                // Directory with expand/collapse
                item.innerHTML = `
                    <div class="file-tree-item dir" style="padding-left: ${12 + indent}px">
                        <span class="expand-icon">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="9 18 15 12 9 6"/>
                            </svg>
                        </span>
                        <span class="icon">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                            </svg>
                        </span>
                        <span class="name">${this.escapeHtml(entry.name)}</span>
                    </div>
                    <div class="file-tree-children" style="display: none;"></div>
                `;

                const header = item.querySelector('.file-tree-item');
                const childrenContainer = item.querySelector('.file-tree-children');
                const expandIcon = item.querySelector('.expand-icon');
                let loaded = false;

                header.addEventListener('click', async () => {
                    const isExpanded = childrenContainer.style.display !== 'none';
                    if (isExpanded) {
                        childrenContainer.style.display = 'none';
                        expandIcon.style.transform = 'rotate(0deg)';
                    } else {
                        childrenContainer.style.display = 'block';
                        expandIcon.style.transform = 'rotate(90deg)';
                        if (!loaded) {
                            try {
                                const response = await fetch(`/api/files?path=${encodeURIComponent(entry.path)}`);
                                const data = await response.json();
                                this._renderFileTreeNodes(data.entries, childrenContainer, entry.path, depth + 1);
                                loaded = true;
                            } catch (error) {
                                console.error('Failed to load directory:', error);
                            }
                        }
                    }
                });
            } else {
                // File
                const iconSvg = entry.name.endsWith('.md')
                    ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>'
                    : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>';

                item.innerHTML = `
                    <div class="file-tree-item" style="padding-left: ${12 + indent + 18}px">
                        <span class="icon">${iconSvg}</span>
                        <span class="name">${this.escapeHtml(entry.name)}</span>
                    </div>
                `;

                const header = item.querySelector('.file-tree-item');
                header.addEventListener('click', () => this.showFilePreview(entry.path, entry.name));
            }

            container.appendChild(item);
        });
    }

    async showFilePreview(path, name) {
        try {
            const response = await fetch(`/api/files/read?path=${encodeURIComponent(path)}`);
            const data = await response.json();

            this.previewFilename.textContent = name;
            const ext = name.split('.').pop().toLowerCase();

            if (ext === 'md' && window.marked) {
                // Render Markdown
                this.previewContent.innerHTML = window.marked.parse(data.content);
                this.previewContent.className = 'markdown-preview';
            } else {
                // Code/text preview
                this.previewContent.textContent = data.content;
                this.previewContent.className = ext;
                if (window.hljs) {
                    window.hljs.highlightElement(this.previewContent);
                }
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
                <div class="session-item-header">
                    <div class="session-title">${session.agent}</div>
                    <button class="session-delete" title="删除会话" data-session-id="${session.id}">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                    </button>
                </div>
                <div class="session-meta">${this.formatDate(session.updated_at)}</div>
            `;

            // Click on item body selects session
            item.addEventListener('click', (e) => {
                if (e.target.closest('.session-delete')) return;
                this.selectSession(session.id);
                this.closeSidebar();
            });

            // Click on delete button
            const deleteBtn = item.querySelector('.session-delete');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showDeleteSessionConfirm(session.id);
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
        // Don't connect if no session is selected
        if (!sessionId) {
            if (this.ws) {
                this.ws.close();
                this.ws = null;
            }
            this.setStatus('disconnected');
            return;
        }

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
            // Don't reconnect if this was an intentional close (code 1000 or 1005)
            if (event.code === 1000 || event.code === 1005) {
                return;
            }
            // Server-side error (code 1006 = abnormal, 1011 = server error)
            if (event.code === 1006 || event.code === 1011) {
                // Show error once and stop reconnecting
                if (this.reconnectAttempts === 0) {
                    this.addMessage('error', '连接失败：服务器配置错误，请检查 LLM API Key 设置。', false);
                }
                this.reconnectAttempts = this.maxReconnectAttempts;
                return;
            }
            // Session not found or other errors - show once and stop
            if (this.reconnectAttempts === 0) {
                this.addMessage('error', '会话不存在或已过期，请创建新会话。', false);
            }
            this.reconnectAttempts = this.maxReconnectAttempts;
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
                this.addToolCall(data.tool_name, data.arguments);
                break;

            case 'tool_result':
                this.addToolResult(data.result, data.is_error);
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

    async sendMessage() {
        const text = this.messageInput.value.trim();
        if (!text) return;

        // Check for /plan command
        if (text.startsWith('/plan ')) {
            const request = text.slice(6).trim();
            if (request) {
                this.addMessage('user', text, false);
                this.messageInput.value = '';
                this.messageInput.style.height = 'auto';
                await this.createTaskPlan(request);
            }
            return;
        }

        if (!this.ws || this.ws.readyState !== WebSocket.OPEN || this.isSending) {
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
            this.sendPermissionResponse(this._pendingPermission.tool_use_id, approved);
            this._pendingPermission = null;
        }
        const modal = document.querySelector('.permission-modal');
        if (modal) modal.remove();
    }

    // ========== Task Workflow ==========

    async createTaskPlan(request) {
        try {
            const response = await fetch('/api/tasks/plan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ request })
            });

            if (!response.ok) throw new Error('Failed to create plan');

            const task = await response.json();
            this.currentTask = task;
            this.showTaskWorkflow(task);
            this.renderTaskPanel();
            return task;
        } catch (error) {
            console.error('Failed to create task plan:', error);
            return null;
        }
    }

    showTaskWorkflow(task) {
        if (!this.taskPlanSteps) return;

        const steps = (task.subtasks || []).map((subtask, index) => `
            <div class="task-plan-step">
                <div class="task-plan-step-num">${index + 1}</div>
                <div class="task-plan-step-text">${this.escapeHtml(subtask.description)}</div>
            </div>
        `).join('');

        this.taskPlanSteps.innerHTML = steps || '<div class="task-empty">暂无步骤</div>';
        this.taskWorkflowModal.classList.add('show');
    }

    hideTaskWorkflow() {
        this.taskWorkflowModal.classList.remove('show');
    }

    async approveTask() {
        if (!this.currentTask) return;

        try {
            const response = await fetch(`/api/tasks/${this.currentTask.id}/approve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                this.hideTaskWorkflow();
                this.currentTask.plan_approved = true;
                this.renderTaskPanel();
                // Show approval message in chat
                this.addMessage('assistant', `任务 "${this.currentTask.title}" 已批准，开始执行...`);
            }
        } catch (error) {
            console.error('Failed to approve task:', error);
        }
    }

    async loadCurrentTask() {
        try {
            const response = await fetch('/api/tasks/current');
            if (response.ok) {
                const task = await response.json();
                this.currentTask = task;
                this.renderTaskPanel();
            }
        } catch (error) {
            console.error('Failed to load current task:', error);
        }
    }

    renderTaskPanel() {
        if (!this.taskPanel) return;

        if (!this.currentTask) {
            this.taskPanel.innerHTML = '<div class="task-empty">暂无任务</div>';
            return;
        }

        const task = this.currentTask;
        const statusLabels = {
            'pending': '待处理',
            'planning': '规划中',
            'planned': '待批准',
            'executing': '执行中',
            'executed': '待审查',
            'reviewing': '审查中',
            'done': '已完成',
            'failed': '失败',
            'cancelled': '已取消'
        };

        const completed = (task.subtasks || []).filter(s =>
            ['done', 'failed'].includes(s.status)
        ).length;
        const total = (task.subtasks || []).length;
        const progress = total > 0 ? (completed / total * 100) : 0;

        this.taskPanel.innerHTML = `
            <div class="task-card" data-task-id="${task.id}">
                <div class="task-card-title">${this.escapeHtml(task.title)}</div>
                <span class="task-card-status ${task.status}">${statusLabels[task.status] || task.status}</span>
                <div class="task-progress">
                    <div class="task-progress-bar" style="width: ${progress}%"></div>
                </div>
            </div>
        `;
    }

    // ========== Team Panel ==========

    async loadTeam() {
        try {
            const response = await fetch('/api/team');
            if (response.ok) {
                const data = await response.json();
                this.renderTeamPanel(data);
            }
        } catch (error) {
            console.error('Failed to load team:', error);
            if (this.teamPanel) {
                this.teamPanel.innerHTML = '<div class="team-empty">加载失败</div>';
            }
        }
    }

    renderTeamPanel(data) {
        if (!this.teamPanel) return;

        const team = data.team || {};
        const members = team.members || [];

        if (members.length === 0) {
            this.teamPanel.innerHTML = '<div class="team-empty">暂无团队成员</div>';
            return;
        }

        const roleLabels = {
            'lead': '负责人',
            'planner': '规划师',
            'executor': '执行者',
            'reviewer': '审查员',
            'explorer': '探索者',
            'specialist': '专家'
        };

        const memberItems = members.map(member => {
            const initials = member.name.substring(0, 2).toUpperCase();
            const statusClass = member.status || 'idle';
            return `
                <div class="team-member">
                    <div class="team-member-avatar" style="background: ${member.avatar_color || '#6366f1'}">${initials}</div>
                    <div class="team-member-info">
                        <div class="team-member-name">${member.name}</div>
                        <div class="team-member-role">${roleLabels[member.role] || member.role}</div>
                    </div>
                    <div class="team-member-status ${statusClass}"></div>
                </div>
            `;
        }).join('');

        const stats = `
            <div class="team-stats">
                <div class="team-stat">
                    <div class="team-stat-value">${data.idle_members || 0}</div>
                    <div class="team-stat-label">空闲</div>
                </div>
                <div class="team-stat">
                    <div class="team-stat-value">${data.busy_members || 0}</div>
                    <div class="team-stat-label">忙碌</div>
                </div>
                <div class="team-stat">
                    <div class="team-stat-value">${data.total_completed || 0}</div>
                    <div class="team-stat-label">完成</div>
                </div>
            </div>
        `;

        this.teamPanel.innerHTML = memberItems + stats;
    }

    // ========== Messages ==========

    addMessage(role, content, append = false) {
        if (append) {
            const lastMessage = this.messagesContainer.lastElementChild;
            if (lastMessage && lastMessage.classList.contains(role)) {
                const contentEl = lastMessage.querySelector('.content');
                if (role === 'assistant') {
                    // Store raw text in data attribute, render full markdown each time
                    const rawText = (lastMessage.dataset.rawText || '') + content;
                    lastMessage.dataset.rawText = rawText;
                    contentEl.innerHTML = this.renderMarkdown(rawText);
                    // Re-highlight code blocks
                    if (window.hljs) {
                        contentEl.querySelectorAll('pre code').forEach((block) => {
                            window.hljs.highlightElement(block);
                            const pre = block.parentElement;
                            if (!pre.querySelector('.copy-btn')) {
                                const btn = document.createElement('button');
                                btn.className = 'copy-btn icon-btn';
                                btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
                                btn.title = 'Copy';
                                btn.onclick = () => {
                                    navigator.clipboard.writeText(block.innerText);
                                    btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>';
                                    setTimeout(() => btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>', 2000);
                                };
                                pre.appendChild(btn);
                            }
                        });
                    }
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
        } else if (role === 'tool-call' || role === 'tool-result') {
            contentHtml = this.escapeHtml(content);
        } else {
            contentHtml = this.escapeHtml(content);
        }

        const timestamp = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

        messageDiv.innerHTML = `
            <div class="role-label">${roleLabels[role] || role}</div>
            <div class="content">${contentHtml}</div>
            <div class="message-timestamp">${timestamp}</div>
        `;

        // Store raw text for streaming append
        if (role === 'assistant') {
            messageDiv.dataset.rawText = content;
        }

        if (role === 'assistant' && window.hljs) {
            messageDiv.querySelectorAll('pre code').forEach((block) => {
                window.hljs.highlightElement(block);
                const pre = block.parentElement;
                if (!pre.querySelector('.copy-btn')) {
                    const btn = document.createElement('button');
                    btn.className = 'copy-btn icon-btn';
                    btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>';
                    btn.title = 'Copy';
                    btn.onclick = () => {
                        navigator.clipboard.writeText(block.innerText);
                        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>';
                        setTimeout(() => btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>', 2000);
                    };
                    pre.appendChild(btn);
                }
            });
        }

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    addToolCall(toolName, args) {
        const div = document.createElement('div');
        div.className = 'message tool-call';
        div.innerHTML = `
            <div class="role-label">Tool</div>
            <div class="content">
                <details class="tool-collapsible">
                    <summary>
                        <span class="tool-icon">🔧</span>
                        <span class="tool-name">${this.escapeHtml(toolName)}</span>
                        <span class="tool-toggle">▶</span>
                    </summary>
                    <pre><code>${this.escapeHtml(JSON.stringify(args, null, 2))}</code></pre>
                </details>
            </div>
        `;
        this.messagesContainer.appendChild(div);
        this.scrollToBottom();
    }

    addToolResult(result, isError) {
        const div = document.createElement('div');
        div.className = `message tool-result ${isError ? 'error' : ''}`;
        const icon = isError ? '❌' : '✅';
        const label = isError ? 'Error' : 'Result';
        div.innerHTML = `
            <div class="role-label">${label}</div>
            <div class="content">
                <details class="tool-collapsible">
                    <summary>
                        <span class="tool-icon">${icon}</span>
                        <span class="tool-name">${isError ? 'Execution Failed' : 'Execution Complete'}</span>
                        <span class="tool-toggle">▶</span>
                    </summary>
                    <pre><code>${this.escapeHtml(result)}</code></pre>
                </details>
            </div>
        `;
        this.messagesContainer.appendChild(div);
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

    // ========== Memory Management ==========

    async loadMemories() {
        try {
            const response = await fetch('/api/memories');
            this.memories = await response.json();
            this.renderMemoryList();
        } catch (error) {
            console.error('Failed to load memories:', error);
            if (this.memoryList) {
                this.memoryList.innerHTML = '<div class="memory-loading">加载失败</div>';
            }
        }
    }

    renderMemoryList() {
        if (!this.memoryList) return;

        if (!this.memories || this.memories.length === 0) {
            this.memoryList.innerHTML = '<div class="memory-empty">暂无记忆</div>';
            return;
        }

        const typeLabels = {
            'user': '用户',
            'feedback': '反馈',
            'project': '项目',
            'reference': '参考'
        };

        const items = this.memories.map(mem => `
            <div class="memory-card" data-name="${mem.name}">
                <div class="memory-card-header">
                    <div class="memory-card-name">${mem.name}</div>
                    <span class="memory-card-type">${typeLabels[mem.type] || mem.type}</span>
                </div>
                <div class="memory-card-desc">${mem.description || ''}</div>
                <div class="memory-card-content">${this.escapeHtml(mem.content || '').substring(0, 100)}${(mem.content || '').length > 100 ? '...' : ''}</div>
                <div class="memory-card-actions">
                    <button class="memory-btn-edit" data-name="${mem.name}">编辑</button>
                    <button class="memory-btn-delete" data-name="${mem.name}">删除</button>
                </div>
            </div>
        `).join('');

        this.memoryList.innerHTML = items;

        // Bind edit/delete handlers
        this.memoryList.querySelectorAll('.memory-btn-edit').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const name = btn.dataset.name;
                const mem = this.memories.find(m => m.name === name);
                if (mem) this.editMemory(mem);
            });
        });

        this.memoryList.querySelectorAll('.memory-btn-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteMemory(btn.dataset.name);
            });
        });
    }

    showMemoryForm() {
        this.memoryForm.style.display = 'block';
        this.memoryList.style.display = 'none';
        this.newMemoryBtn.style.display = 'none';
        this._editingMemory = null;
        this.memoryName.value = '';
        this.memoryDescription.value = '';
        this.memoryType.value = 'user';
        this.memoryContent.value = '';
        this.memoryName.disabled = false;
    }

    hideMemoryForm() {
        this.memoryForm.style.display = 'none';
        this.memoryList.style.display = 'block';
        this.newMemoryBtn.style.display = 'inline-block';
        this._editingMemory = null;
    }

    editMemory(mem) {
        this._editingMemory = mem.name;
        this.memoryName.value = mem.name;
        this.memoryName.disabled = true;
        this.memoryDescription.value = mem.description || '';
        this.memoryType.value = mem.type || 'user';
        this.memoryContent.value = mem.content || '';
        this.memoryForm.style.display = 'block';
        this.memoryList.style.display = 'none';
        this.newMemoryBtn.style.display = 'none';
    }

    async saveMemory() {
        const name = this.memoryName.value.trim();
        const description = this.memoryDescription.value.trim();
        const type = this.memoryType.value;
        const content = this.memoryContent.value.trim();

        if (!name || !content) {
            alert('名称和内容不能为空');
            return;
        }

        try {
            const response = await fetch('/api/memories', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, description, type, content })
            });

            if (response.ok) {
                this.hideMemoryForm();
                await this.loadMemories();
                // Also refresh workspace sidebar
                this.loadWorkspace();
            } else {
                alert('保存失败');
            }
        } catch (error) {
            console.error('Failed to save memory:', error);
            alert('保存失败: ' + error.message);
        }
    }

    async deleteMemory(name) {
        if (!confirm(`确定要删除记忆 "${name}" 吗？`)) return;

        try {
            const response = await fetch(`/api/memories/${encodeURIComponent(name)}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                await this.loadMemories();
                this.loadWorkspace();
            } else {
                alert('删除失败');
            }
        } catch (error) {
            console.error('Failed to delete memory:', error);
            alert('删除失败: ' + error.message);
        }
    }

    // ========== Codebase Panel ==========

    async loadCodebaseIndex() {
        try {
            const response = await fetch('/api/codebase/index');
            if (response.ok) {
                const data = await response.json();
                this.renderCodebaseStats(data);
            }
        } catch (error) {
            console.error('Failed to load codebase index:', error);
        }
    }

    renderCodebaseStats(data) {
        if (!this.codebaseStats) return;

        const totalFiles = data.total_files || 0;
        const totalLines = data.total_lines || 0;
        const languages = data.languages || {};
        const topLang = Object.entries(languages).sort((a, b) => b[1] - a[1])[0];

        this.codebaseStats.innerHTML = `
            <div class="codebase-stat">
                <div class="codebase-stat-value">${totalFiles}</div>
                <div class="codebase-stat-label">文件</div>
            </div>
            <div class="codebase-stat">
                <div class="codebase-stat-value">${totalLines.toLocaleString()}</div>
                <div class="codebase-stat-label">行数</div>
            </div>
            <div class="codebase-stat">
                <div class="codebase-stat-value">${topLang ? topLang[0] : '-'}</div>
                <div class="codebase-stat-label">主要语言</div>
            </div>
        `;
    }

    async searchCodebase() {
        const query = this.codebaseSearchInput.value.trim();
        if (!query) return;

        try {
            this.codebaseResults.innerHTML = '<div class="codebase-empty">搜索中...</div>';
            const response = await fetch(`/api/codebase/search?q=${encodeURIComponent(query)}&limit=20`);
            if (response.ok) {
                const results = await response.json();
                this.renderCodebaseResults(results);
            }
        } catch (error) {
            console.error('Failed to search codebase:', error);
            this.codebaseResults.innerHTML = '<div class="codebase-empty">搜索失败</div>';
        }
    }

    renderCodebaseResults(results) {
        if (!this.codebaseResults) return;

        if (!results || results.length === 0) {
            this.codebaseResults.innerHTML = '<div class="codebase-empty">未找到结果</div>';
            return;
        }

        const items = results.map(result => `
            <div class="codebase-result-item" data-path="${result.path}" data-line="${result.line_number}">
                <div class="codebase-result-path">${result.path}:${result.line_number}</div>
                <div class="codebase-result-line">${this.escapeHtml(result.content)}</div>
                <div class="codebase-result-meta">${result.language} | 相关度: ${(result.score * 100).toFixed(0)}%</div>
            </div>
        `).join('');

        this.codebaseResults.innerHTML = items;

        // Add click handlers
        this.codebaseResults.querySelectorAll('.codebase-result-item').forEach(item => {
            item.addEventListener('click', () => {
                const path = item.dataset.path;
                if (path) {
                    this.loadFileTree('.');
                    this.previewFile(path);
                }
            });
        });
    }

    async rebuildCodebaseIndex() {
        try {
            this.rebuildIndexBtn.disabled = true;
            this.rebuildIndexBtn.textContent = '重建中...';
            const response = await fetch('/api/codebase/index/rebuild', { method: 'POST' });
            if (response.ok) {
                await this.loadCodebaseIndex();
                alert('索引重建完成');
            }
        } catch (error) {
            console.error('Failed to rebuild index:', error);
            alert('重建失败');
        } finally {
            this.rebuildIndexBtn.disabled = false;
            this.rebuildIndexBtn.textContent = '重建索引';
        }
    }

    // ========== Settings ==========

    openSettings() {
        const session = this.sessions.find(s => s.id === this.currentSessionId);
        if (session) {
            this.settingsAgentSelect.value = session.agent || 'general';
        }
        this.settingsThemeSelect.value = this.currentTheme;

        this.settingsSessionCount.textContent = this.sessions.length;
        this.loadMemories();
        this.loadCodebaseIndex();
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

    // ========== Session Delete ==========

    showDeleteSessionConfirm(sessionId) {
        this._deleteSessionId = sessionId;
        const session = this.sessions.find(s => s.id === sessionId);
        const name = session ? session.agent : '此会话';
        this.resetMessage.textContent = `确定要删除 "${name}" 吗？此操作不可撤销。`;
        this.resetConfirmBtn.textContent = '删除';
        this.resetConfirmBtn.className = 'btn-danger';
        this.resetModal.classList.add('show');
    }

    async executeDeleteSession() {
        const sessionId = this._deleteSessionId;
        if (!sessionId) return;

        try {
            const response = await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
            if (response.ok) {
                this.sessions = this.sessions.filter(s => s.id !== sessionId);

                if (this.currentSessionId === sessionId) {
                    this.currentSessionId = null;
                    this.messagesContainer.innerHTML = '';
                    this.welcomeScreen.style.display = 'flex';
                    if (this.ws) {
                        this.ws.close();
                        this.ws = null;
                    }
                    this.setStatus('disconnected');
                }

                this.renderSessionList();
            } else {
                this.addMessage('error', '删除会话失败', false);
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
            this.addMessage('error', '删除会话失败: ' + error.message, false);
        }

        this.hideResetModal();
        this._deleteSessionId = null;
        this.resetConfirmBtn.textContent = '确认重置';
    }

    // ========== Reset ==========

    showResetConfirm(type) {
        this._resetType = type;
        this._deleteSessionId = null;
        this.resetConfirmBtn.textContent = '确认重置';
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
        this._deleteSessionId = null;
        this.resetConfirmBtn.textContent = '确认重置';
    }

    async executeReset() {
        // If deleting a session
        if (this._deleteSessionId) {
            await this.executeDeleteSession();
            return;
        }

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
