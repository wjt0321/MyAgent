/**
 * MyAgent Web UI - Frontend Application
 * Modern, polished interaction layer
 */

class MyAgentWebApp {
    constructor() {
        this.ws = null;
        this.currentSessionId = null;
        this.sessions = [];
        this.memories = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.isSending = false;
        this.setupReady = true;
        this.setupStatus = null;
        this.searchQuery = '';
        this.currentTheme = localStorage.getItem('myagent-theme') || 'dark';
        this.activeView = 'chat';
        this.workspaceData = null;
        this.teamData = null;
        this.fileEntries = [];
        this.commandPaletteItems = [];
        this.commandPaletteIndex = 0;
        this.taskPollingTimer = null;

        this.initTheme();
        this.initElements();
        this.bindEvents();
        this.loadSetupStatus();
        this.renderCommandPalette();
        this.renderDetailSidebar('overview', {
            title: '工作台详情',
            meta: '准备就绪',
            body: '选择一个会话、任务、文件或工具卡片查看更详细的信息。',
        });
        this.loadSessions();
        this.loadFileTree('.');
        this.loadWorkspace();
        this.loadCurrentTask();
        this.loadTeam();
    }

    // ========== Theme ==========

    getEffectiveTheme() {
        if (this.currentTheme === 'auto') {
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        return this.currentTheme;
    }

    initTheme() {
        const effective = this.getEffectiveTheme();
        document.body.className = `theme-${effective}`;
        this.updateHLJSTheme();
        this.updateThemeIcon();
    }

    toggleTheme() {
        // Cycle: dark -> light -> auto -> dark
        const themes = ['dark', 'light', 'auto'];
        const idx = themes.indexOf(this.currentTheme);
        this.currentTheme = themes[(idx + 1) % themes.length];
        this.applyTheme();
    }

    applyTheme() {
        const effective = this.getEffectiveTheme();
        document.body.className = `theme-${effective}`;
        localStorage.setItem('myagent-theme', this.currentTheme);
        this.updateHLJSTheme();
        this.updateThemeIcon();

        // Update settings panel buttons
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === this.currentTheme);
        });
    }

    updateHLJSTheme() {
        const effective = this.getEffectiveTheme();
        const link = document.getElementById('hljs-theme');
        if (link) {
            const theme = effective === 'dark' ? 'atom-one-dark' : 'github';
            link.href = `https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/${theme}.min.css`;
        }
    }

    updateThemeIcon() {
        const icon = document.getElementById('theme-icon');
        if (!icon) return;
        const effective = this.getEffectiveTheme();
        if (effective === 'dark') {
            icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>';
        } else {
            icon.innerHTML = '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>';
        }
    }

    setupSystemThemeListener() {
        const media = window.matchMedia('(prefers-color-scheme: dark)');
        media.addEventListener('change', () => {
            if (this.currentTheme === 'auto') {
                this.applyTheme();
            }
        });
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
        this.modelSelect = document.getElementById('model-select');
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
        this.workbenchNav = document.getElementById('workbench-nav');
        this.workbenchNavBtns = document.querySelectorAll('.workbench-nav-btn');
        this.workbenchViews = document.querySelectorAll('.workbench-view');
        this.sessionStatusChip = document.getElementById('session-status-chip');
        this.sessionStatusLabel = document.getElementById('session-status-label');
        this.commandPaletteBtn = document.getElementById('command-palette-btn');
        this.commandPaletteModal = document.getElementById('command-palette-modal');
        this.commandPaletteInput = document.getElementById('command-palette-input');
        this.commandPaletteList = document.getElementById('command-palette-list');
        this.closeCommandPaletteBtn = document.getElementById('close-command-palette');
        this.recentSessions = document.getElementById('welcome-recent-sessions');
        this.taskStream = document.getElementById('task-stream');
        this.fileBrowserView = document.getElementById('file-browser-view');
        this.workspaceOverview = document.getElementById('workspace-overview');
        this.teamOverview = document.getElementById('team-overview');
        this.detailSidebar = document.getElementById('detail-sidebar');
        this.detailSidebarMeta = document.getElementById('detail-sidebar-meta');
        this.detailSidebarContent = document.getElementById('detail-sidebar-content');
        this.filePreviewPanel = this.filePreviewPanel || this.detailSidebar;

        // Settings modal
        this.settingsBtn = document.getElementById('settings-btn');
        this.settingsModal = document.getElementById('settings-modal');
        this.closeSettingsBtn = document.getElementById('close-settings');
        this.saveSettingsBtn = document.getElementById('save-settings-btn');
        this.settingsAgentSelect = document.getElementById('settings-agent-select');
        this.settingsSystemPrompt = document.getElementById('settings-system-prompt');
        this.settingsThemeSelect = document.getElementById('settings-theme-select');
        // Theme buttons in settings panel (new theme selector)
        this.settingsThemeBtns = document.querySelectorAll('.theme-btn');
        this.settingsSessionCount = document.getElementById('settings-session-count');
        this.settingsMessageCount = document.getElementById('settings-message-count');
        this.workspaceInfo = document.getElementById('workspace-info');

        // Session import
        this.sessionImportBtn = document.getElementById('session-import-btn');
        this.sessionImportFile = document.getElementById('session-import-file');

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

        // System prompt
        this.saveSystemPromptBtn = document.getElementById('save-system-prompt-btn');

        // Token display
        this.tokenDisplay = document.getElementById('token-display');
        this.tokenCount = document.getElementById('token-count');

        this.updateThemeIcon();
        this.setupSystemThemeListener();
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
                this.hideCommandPalette();
                this.hideFilePreview();
                return;
            }

            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                this.toggleCommandPalette();
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

        // Model select
        if (this.modelSelect) {
            this.modelSelect.addEventListener('change', (e) => this.switchModel(e.target.value));
        }

        // Search
        this.searchToggle.addEventListener('click', () => this.toggleSearch());
        this.searchClose.addEventListener('click', () => this.toggleSearch());
        this.searchInput.addEventListener('input', (e) => this.performSearch(e.target.value));

        this.workbenchNavBtns.forEach(btn => {
            btn.addEventListener('click', () => this.setActiveView(btn.dataset.view));
        });

        if (this.commandPaletteBtn) {
            this.commandPaletteBtn.addEventListener('click', () => this.showCommandPalette());
        }
        if (this.closeCommandPaletteBtn) {
            this.closeCommandPaletteBtn.addEventListener('click', () => this.hideCommandPalette());
        }
        if (this.commandPaletteModal) {
            this.commandPaletteModal.addEventListener('click', (e) => {
                if (e.target === this.commandPaletteModal) {
                    this.hideCommandPalette();
                }
            });
        }
        if (this.commandPaletteInput) {
            this.commandPaletteInput.addEventListener('input', (e) => {
                this.renderCommandPalette(e.target.value);
            });
            this.commandPaletteInput.addEventListener('keydown', (e) => {
                this.handleCommandPaletteKeydown(e);
            });
        }

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
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.currentTheme = btn.dataset.theme;
                this.applyTheme();
            });
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

        // System prompt save
        if (this.saveSystemPromptBtn) {
            this.saveSystemPromptBtn.addEventListener('click', () => this.saveSystemPrompt());
        }

        // Session import
        if (this.sessionImportBtn) {
            this.sessionImportBtn.addEventListener('click', () => this.sessionImportFile.click());
        }
        if (this.sessionImportFile) {
            this.sessionImportFile.addEventListener('change', (e) => this.importSession(e));
        }
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

    setActiveView(viewName) {
        this.activeView = viewName;
        this.workbenchNavBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === viewName);
        });
        this.workbenchViews.forEach(view => {
            view.classList.toggle('active', view.dataset.view === viewName);
        });

        if (viewName === 'chat') {
            this.messageInput?.focus();
        }
        if (viewName === 'tasks') {
            this.renderTaskStream();
            this.startTaskPolling();
        }
        if (viewName === 'files') {
            this.renderFileBrowser();
        }
        if (viewName === 'workspace') {
            this.renderWorkspaceOverview();
        }
        if (viewName === 'team') {
            this.renderTeamOverview();
        }
    }

    getCommandPaletteItems() {
        return [
            {
                id: 'new-session',
                title: '新建会话',
                meta: '创建一个新的 general 会话',
                shortcut: 'Enter',
                handler: () => this.createSession(),
            },
            {
                id: 'focus-chat',
                title: '切换到聊天视图',
                meta: '回到主聊天工作区',
                shortcut: 'chat',
                handler: () => this.setActiveView('chat'),
            },
            {
                id: 'focus-tasks',
                title: '切换到任务视图',
                meta: '查看任务计划与执行状态',
                shortcut: 'tasks',
                handler: () => this.setActiveView('tasks'),
            },
            {
                id: 'focus-files',
                title: '切换到文件视图',
                meta: '浏览当前文件与预览',
                shortcut: 'files',
                handler: () => this.setActiveView('files'),
            },
            {
                id: 'focus-workspace',
                title: '切换到 Workspace 视图',
                meta: '查看用户、记忆与项目信息',
                shortcut: 'workspace',
                handler: () => this.setActiveView('workspace'),
            },
            {
                id: 'focus-team',
                title: '切换到团队视图',
                meta: '查看当前团队状态',
                shortcut: 'team',
                handler: () => this.setActiveView('team'),
            },
            {
                id: 'open-settings',
                title: '打开设置',
                meta: '配置 agent、memory、codebase 和外观',
                shortcut: 'settings',
                handler: () => this.openSettings(),
            },
            {
                id: 'focus-input',
                title: '聚焦输入框',
                meta: '准备发送消息',
                shortcut: 'input',
                handler: () => this.messageInput?.focus(),
            },
            {
                id: 'show-help',
                title: '查看 Slash Commands',
                meta: '展示 /help 中可用的命令',
                shortcut: '/help',
                handler: () => this.executeSlashCommand('/help'),
            },
        ];
    }

    renderCommandPalette(query = '') {
        if (!this.commandPaletteList) return;
        const normalized = query.trim().toLowerCase();
        const items = this.getCommandPaletteItems().filter(item => {
            if (!normalized) return true;
            return `${item.title} ${item.meta} ${item.shortcut}`.toLowerCase().includes(normalized);
        });
        this.commandPaletteItems = items;
        this.commandPaletteIndex = Math.min(this.commandPaletteIndex, Math.max(items.length - 1, 0));

        if (items.length === 0) {
            this.commandPaletteList.innerHTML = '<div class="command-item"><div><div class="command-item-title">未找到命令</div><div class="command-item-meta">试试输入 chat、tasks、settings 或 /help</div></div></div>';
            return;
        }

        this.commandPaletteList.innerHTML = items.map((item, index) => `
            <button class="command-item ${index === this.commandPaletteIndex ? 'active' : ''}" data-command-id="${item.id}">
                <span>
                    <span class="command-item-title">${this.escapeHtml(item.title)}</span>
                    <span class="command-item-meta">${this.escapeHtml(item.meta)}</span>
                </span>
                <span class="command-item-shortcut">${this.escapeHtml(item.shortcut)}</span>
            </button>
        `).join('');

        this.commandPaletteList.querySelectorAll('.command-item').forEach(btn => {
            btn.addEventListener('click', () => {
                this.runCommandPaletteAction(btn.dataset.commandId);
            });
        });
    }

    handleCommandPaletteKeydown(event) {
        if (!this.commandPaletteItems.length) return;

        if (event.key === 'ArrowDown') {
            event.preventDefault();
            this.commandPaletteIndex = (this.commandPaletteIndex + 1) % this.commandPaletteItems.length;
            this.renderCommandPalette(this.commandPaletteInput.value);
            return;
        }

        if (event.key === 'ArrowUp') {
            event.preventDefault();
            this.commandPaletteIndex = (this.commandPaletteIndex - 1 + this.commandPaletteItems.length) % this.commandPaletteItems.length;
            this.renderCommandPalette(this.commandPaletteInput.value);
            return;
        }

        if (event.key === 'Enter') {
            event.preventDefault();
            const item = this.commandPaletteItems[this.commandPaletteIndex];
            if (item) {
                this.runCommandPaletteAction(item.id);
            }
        }
    }

    runCommandPaletteAction(commandId) {
        const item = this.commandPaletteItems.find(entry => entry.id === commandId);
        if (!item) return;
        this.hideCommandPalette();
        item.handler();
    }

    showCommandPalette() {
        if (!this.commandPaletteModal) return;
        this.renderCommandPalette('');
        this.commandPaletteModal.classList.add('show');
        if (this.commandPaletteInput) {
            this.commandPaletteInput.value = '';
            this.commandPaletteInput.focus();
        }
    }

    hideCommandPalette() {
        if (!this.commandPaletteModal) return;
        this.commandPaletteModal.classList.remove('show');
    }

    toggleCommandPalette() {
        if (!this.commandPaletteModal) return;
        const visible = this.commandPaletteModal.classList.contains('show');
        if (visible) {
            this.hideCommandPalette();
        } else {
            this.showCommandPalette();
        }
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
                    this.renderDetailSidebar('session', {
                        title: session.agent,
                        meta: session.model || 'default',
                        body: `会话 ID：${session.id}\n消息数：${session.messages?.length || 0}\n最近更新：${this.formatDate(session.updated_at)}`,
                    });
                }
                this.connectWebSocket(this.currentSessionId);
                this.addMessage('assistant', `已切换到 agent: **${agentName}**`, false);
            }
        } catch (error) {
            console.error('Failed to switch agent:', error);
        }
    }

    // ========== Model Switch ==========

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
                    this.renderSessionList();
                    this.currentModel.textContent = modelName;
                    this.renderDetailSidebar('session', {
                        title: session.agent,
                        meta: session.model || 'default',
                        body: `会话 ID：${session.id}\n消息数：${session.messages?.length || 0}\n最近更新：${this.formatDate(session.updated_at)}`,
                    });
                }
            }
        } catch (error) {
            console.error('Failed to switch model:', error);
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

    async loadSetupStatus() {
        try {
            const response = await fetch('/api/setup/status');
            const data = await response.json();
            this.setupStatus = data;
            this.setupReady = !!data.overall_ready;
            if (!this.setupReady) {
                this.setSending(true);
                this.renderSetupRequired();
            }
        } catch (error) {
            console.error('Failed to load setup status:', error);
        }
    }

    renderSetupRequired() {
        if (!this.welcomeScreen || !this.setupStatus || this.setupReady) return;
        const issues = (this.setupStatus.issues || [])
            .map(issue => `<li>${this.escapeHtml(issue.summary)} - ${this.escapeHtml(issue.fix)}</li>`)
            .join('');
        this.welcomeScreen.style.display = 'flex';
        this.welcomeScreen.innerHTML = `
            <div class="welcome-card">
                <h2>Setup Required</h2>
                <p>当前环境尚未完成初始化，Web 会保留浏览能力，但不会建立聊天会话。</p>
                <p><strong>Next:</strong> <code>${this.escapeHtml(this.setupStatus.next_action)}</code></p>
                <ul>${issues}</ul>
            </div>
        `;
    }

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
            if (this.workspaceOverview) {
                this.workspaceOverview.innerHTML = '<div class="workspace-empty">Workspace 未初始化</div>';
            }
        }
    }

    renderWorkspace(data) {
        if (!this.workspaceInfo) return;
        this.workspaceData = data;

        if (!data.initialized) {
            this.workspaceInfo.innerHTML = `
                <div class="workspace-empty">
                    <div class="workspace-empty-title">Workspace 未初始化</div>
                    <div class="workspace-empty-desc">运行 <code>myagent init</code> 创建 Workspace</div>
                </div>
            `;
            this.renderWorkspaceOverview();
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
                    this.showMemoryPreview(filename);
                }
            });
        });

        this.renderWorkspaceOverview();
    }

    async showMemoryPreview(filename) {
        try {
            const wsPath = await this._getWorkspacePath();
            if (!wsPath) return;
            const memPath = `${wsPath}/memory/${filename}`;
            const response = await fetch(`/api/files/read?path=${encodeURIComponent(memPath)}`);
            if (!response.ok) throw new Error('Failed to load memory');
            const data = await response.json();
            this.previewFilename.textContent = filename;
            this.previewContent.innerHTML = window.marked ? window.marked.parse(data.content) : this.escapeHtml(data.content);
            this.previewContent.className = 'markdown-preview';
            this.renderDetailSidebar('memory', {
                title: filename,
                meta: 'Workspace 记忆',
                body: data.content,
            });
            this.filePreviewPanel.classList.add('show', 'has-preview');
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
        this.fileEntries = entries;
        this._fileTreeData = { entries, parentPath };
        this._renderFileTreeNodes(entries, this.fileTree, parentPath, 0);
        this.renderFileBrowser();
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

            this.renderDetailSidebar('file', {
                title: name,
                meta: path,
                body: `文件类型：${ext || 'text'}\n路径：${path}`,
            });
            this.filePreviewPanel.classList.add('show', 'has-preview');
            this.closeSidebar();
        } catch (error) {
            console.error('Failed to load file:', error);
        }
    }

    hideFilePreview() {
        this.filePreviewPanel.classList.remove('show', 'has-preview');
        if (this.previewContent) {
            this.previewContent.textContent = '';
            this.previewContent.className = '';
        }
    }

    // ========== Sessions ==========

    async loadSessions() {
        try {
            const response = await fetch('/api/sessions');
            this.sessions = await response.json();
            this.renderSessionList();
            this.renderRecentSessions();

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
            item.dataset.sessionId = session.id;
            item.innerHTML = `
                <div class="session-item-header">
                    <div class="session-title">${this.escapeHtml(session.agent)}</div>
                    <div class="session-actions">
                        <button class="session-rename" title="重命名会话" data-session-id="${session.id}">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                            </svg>
                        </button>
                        <button class="session-export" title="导出会话" data-session-id="${session.id}">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="7 10 12 15 17 10"/>
                                <line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                        </button>
                        <button class="session-delete" title="删除会话" data-session-id="${session.id}">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="3 6 5 6 21 6"/>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="session-meta">${this.formatDate(session.updated_at)} · ${this.escapeHtml(session.model || 'default')}</div>
            `;

            // Click on item body selects session
            item.addEventListener('click', (e) => {
                if (e.target.closest('.session-actions')) return;
                this.selectSession(session.id);
                this.closeSidebar();
            });

            // Rename button
            const renameBtn = item.querySelector('.session-rename');
            renameBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.startRenameSession(session.id);
            });

            // Export button
            const exportBtn = item.querySelector('.session-export');
            exportBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showExportMenu(session.id, exportBtn);
            });

            // Delete button
            const deleteBtn = item.querySelector('.session-delete');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showDeleteSessionConfirm(session.id);
            });

            this.sessionList.appendChild(item);
        });

        this.renderRecentSessions();
    }

    startRenameSession(sessionId) {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session) return;

        const newName = prompt('输入新会话名称:', session.agent);
        if (newName && newName.trim() && newName.trim() !== session.agent) {
            const trimmed = newName.trim();
            session.agent = trimmed;
            this.renderSessionList();
            if (this.currentSessionId === sessionId) {
                this.currentAgent.textContent = trimmed;
            }
        }
    }

    showExportMenu(sessionId, anchorBtn) {
        // Remove existing menu
        const existing = document.querySelector('.export-menu');
        if (existing) existing.remove();

        const menu = document.createElement('div');
        menu.className = 'export-menu';
        menu.innerHTML = `
            <div class="export-menu-item" data-format="markdown">导出 Markdown</div>
            <div class="export-menu-item" data-format="json">导出 JSON</div>
        `;

        menu.querySelectorAll('.export-menu-item').forEach(item => {
            item.addEventListener('click', () => {
                this.exportSession(sessionId, item.dataset.format);
                menu.remove();
            });
        });

        // Position near the button
        const rect = anchorBtn.getBoundingClientRect();
        menu.style.position = 'fixed';
        menu.style.top = `${rect.bottom + 4}px`;
        menu.style.left = `${rect.left}px`;
        menu.style.zIndex = '1000';

        document.body.appendChild(menu);

        // Close on outside click
        const closeMenu = (e) => {
            if (!menu.contains(e.target) && e.target !== anchorBtn) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        };
        setTimeout(() => document.addEventListener('click', closeMenu), 0);
    }

    exportSession(sessionId, format) {
        const session = this.sessions.find(s => s.id === sessionId);
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
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    sessionToMarkdown(session) {
        let md = `# Session: ${session.agent}\n\n`;
        md += `- **Model:** ${session.model || 'default'}\n`;
        md += `- **Created:** ${session.created_at}\n`;
        md += `- **Updated:** ${session.updated_at}\n\n`;
        md += `---\n\n`;
        (session.messages || []).forEach(msg => {
            const role = msg.role === 'user' ? 'User' : 'Assistant';
            const time = msg.timestamp ? ` (${msg.timestamp})` : '';
            md += `## ${role}${time}\n\n${msg.content}\n\n`;
        });
        return md;
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

    renderRecentSessions() {
        if (!this.recentSessions) return;

        if (!this.sessions.length) {
            this.recentSessions.innerHTML = '<div class="recent-session-empty">暂无最近会话</div>';
            return;
        }

        this.recentSessions.innerHTML = this.sessions.slice(0, 5).map(session => `
            <button class="recent-session-item" data-session-id="${session.id}">
                <div class="recent-session-title">${this.escapeHtml(session.agent)}</div>
                <div class="recent-session-meta">${this.escapeHtml(session.model || 'default')} · ${this.formatDate(session.updated_at)}</div>
            </button>
        `).join('');

        this.recentSessions.querySelectorAll('.recent-session-item').forEach(button => {
            button.addEventListener('click', () => {
                this.setActiveView('chat');
                this.selectSession(button.dataset.sessionId);
            });
        });
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
            this.currentModel.textContent = session.model || 'default';
            this.agentSelect.value = session.agent;
            if (this.modelSelect && session.model) {
                this.modelSelect.value = session.model;
            }

            session.messages.forEach(msg => {
                this.addMessage(msg.role, msg.content, false);
            });

            this.renderDetailSidebar('session', {
                title: session.agent,
                meta: session.model || 'default',
                body: `会话 ID：${session.id}\n消息数：${session.messages?.length || 0}\n最近更新：${this.formatDate(session.updated_at)}`,
            });
        } else {
            this.welcomeScreen.style.display = 'flex';
        }

        if (!this.setupReady) {
            this.renderSetupRequired();
            this.setStatus('disconnected');
            return;
        }
        this.setActiveView('chat');
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
                this.renderDetailSidebar('permission', {
                    title: data.tool_name || 'Permission Request',
                    meta: data.reason || '需要确认',
                    body: JSON.stringify(data.arguments || {}, null, 2),
                });
                this.showPermissionModal(data);
                break;

            case 'permission_result':
                const status = data.approved ? 'approved' : 'denied';
                this.addMessage('tool-result', `Permission ${status}: ${data.reason}`, false);
                break;

            case 'token_usage':
                this.updateTokenDisplay(data.tokens);
                break;
        }
    }

    updateTokenDisplay(tokens) {
        if (!this.tokenDisplay || !this.tokenCount) return;
        if (tokens > 0) {
            this.tokenDisplay.style.display = 'flex';
            this.tokenCount.textContent = tokens.toLocaleString();
        } else {
            this.tokenDisplay.style.display = 'none';
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

        if (!this.setupReady) {
            this.addMessage('error', `Setup Required：请先执行 ${this.setupStatus?.next_action || 'myagent init --quick'}`, false);
            return;
        }

        if (text.startsWith('/')) {
            this.addMessage('user', text, false);
            this.messageInput.value = '';
            this.messageInput.style.height = 'auto';
            const handled = await this.executeSlashCommand(text);
            if (handled) {
                return;
            }
        }

        if (!this.ws || this.ws.readyState !== WebSocket.OPEN || this.isSending) {
            return;
        }

        this.ws.send(JSON.stringify({ message: text }));
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.setSending(true);
    }

    async executeSlashCommand(text) {
        const [command, ...rest] = text.split(/\s+/);
        const args = rest.join(' ').trim();

        switch (command) {
            case '/plan':
                if (args) {
                    await this.createTaskPlan(args);
                } else {
                    this.addMessage('assistant', '用法：`/plan 任务描述`', false);
                }
                return true;
            case '/help':
                this.addMessage(
                    'assistant',
                    [
                        '可用命令：',
                        '- `/plan <任务>`：创建任务计划',
                        '- `/agent <name>`：切换 agent',
                        '- `/model <name>`：切换 model',
                        '- `/session`：查看当前会话摘要',
                        '- `/setup`：打开设置',
                        '- `/doctor`：查看当前工作台状态',
                    ].join('\n'),
                    false,
                );
                return true;
            case '/setup':
                this.openSettings();
                this.addMessage('assistant', '已打开设置面板。', false);
                return true;
            case '/doctor':
                this.addMessage(
                    'assistant',
                    `当前状态：\n- 会话：${this.currentSessionId ? '已选择' : '未选择'}\n- WebSocket：${this.ws?.readyState === WebSocket.OPEN ? '已连接' : '未连接'}\n- 当前视图：${this.activeView}`,
                    false,
                );
                return true;
            case '/session': {
                const session = this.sessions.find(item => item.id === this.currentSessionId);
                if (!session) {
                    this.addMessage('assistant', '当前没有激活会话。', false);
                } else {
                    this.renderDetailSidebar('session', {
                        title: session.agent,
                        meta: session.model || 'default',
                        body: `会话 ID：${session.id}\n消息数：${session.messages?.length || 0}\n最近更新：${this.formatDate(session.updated_at)}`,
                    });
                    this.addMessage('assistant', `当前会话：**${session.agent}**`, false);
                }
                return true;
            }
            case '/agent':
                if (args) {
                    await this.switchAgent(args);
                } else {
                    this.addMessage('assistant', '用法：`/agent general`', false);
                }
                return true;
            case '/model':
                if (args) {
                    await this.switchModel(args);
                } else {
                    this.addMessage('assistant', '用法：`/model <model-name>`', false);
                }
                return true;
            default:
                this.addMessage('assistant', `未识别命令：\`${command}\``, false);
                return true;
        }
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
                this.startTaskPolling();
                // Show approval message in chat
                this.addMessage('assistant', `任务 "${this.currentTask.title}" 已批准，开始执行...`);
            }
        } catch (error) {
            console.error('Failed to approve task:', error);
        }
    }

    async cancelTask() {
        if (!this.currentTask) return;

        try {
            const response = await fetch(`/api/tasks/${this.currentTask.id}/cancel`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentTask = data.task;
                this.renderTaskPanel();
                this.stopTaskPolling();
                this.addMessage('assistant', `任务 "${this.currentTask.title}" 已取消。`, false);
            }
        } catch (error) {
            console.error('Failed to cancel task:', error);
        }
    }

    async retryTask() {
        if (!this.currentTask) return;

        try {
            const response = await fetch(`/api/tasks/${this.currentTask.id}/retry`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentTask = data.task;
                this.renderTaskPanel();
                this.addMessage('assistant', `任务 "${this.currentTask.title}" 已重置，可重新批准执行。`, false);
            }
        } catch (error) {
            console.error('Failed to retry task:', error);
        }
    }

    async loadCurrentTask() {
        try {
            const response = await fetch('/api/tasks/current');
            if (response.ok) {
                const snapshot = await response.json();
                this.currentTask = snapshot.task;
                this.teamData = snapshot.team || this.teamData;
                this.renderTaskPanel();
                this.renderTeamPanel(this.teamData || {});
                this.syncTaskPollingState();
            }
        } catch (error) {
            console.error('Failed to load current task:', error);
        }
    }

    startTaskPolling() {
        if (this.taskPollingTimer) {
            return;
        }
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
    }

    syncTaskPollingState() {
        const activeStatuses = ['planning', 'planned', 'executing', 'executed', 'reviewing'];
        if (this.currentTask && activeStatuses.includes(this.currentTask.status)) {
            this.startTaskPolling();
            return;
        }
        this.stopTaskPolling();
    }

    renderTaskPanel() {
        if (!this.taskPanel) return;

        if (!this.currentTask) {
            this.taskPanel.innerHTML = '<div class="task-empty">暂无任务</div>';
            this.renderTaskStream();
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
        const reviewSummary = task.result?.summary
            ? `<div class="task-card-summary">${this.escapeHtml(task.result.summary)}</div>`
            : '';
        const teamSummary = this.teamData
            ? `<div class="task-team-summary">Team: ${this.escapeHtml(String(this.teamData.busy_members || 0))} busy / ${this.escapeHtml(String(this.teamData.total_completed || 0))} completed</div>`
            : '';
        const canCancel = ['planning', 'planned', 'executing', 'executed', 'reviewing'].includes(task.status);
        const canRetry = ['failed', 'cancelled'].includes(task.status);

        this.taskPanel.innerHTML = `
            <div class="task-card" data-task-id="${task.id}">
                <div class="task-card-title">${this.escapeHtml(task.title)}</div>
                <span class="task-card-status ${task.status}">${statusLabels[task.status] || task.status}</span>
                <div class="task-progress">
                    <div class="task-progress-bar" style="width: ${progress}%"></div>
                </div>
                ${teamSummary}
                ${reviewSummary}
                ${canCancel ? '<button class="task-cancel-btn">取消任务</button>' : ''}
                ${canRetry ? '<button class="task-retry-btn">重新执行</button>' : ''}
            </div>
        `;

        this.taskPanel.querySelector('.task-card')?.addEventListener('click', () => {
            const resultBody = task.result ? [
                task.result.summary ? `审查摘要：${task.result.summary}` : '',
                (task.result.issues || []).length ? `问题：\n- ${(task.result.issues || []).join('\n- ')}` : '',
                (task.result.suggestions || []).length ? `建议：\n- ${(task.result.suggestions || []).join('\n- ')}` : '',
                (task.result.deliverables || []).length ? `交付物：\n- ${(task.result.deliverables || []).join('\n- ')}` : '',
            ].filter(Boolean).join('\n\n') : '暂无审查结果';
            this.setActiveView('tasks');
            this.renderDetailSidebar('task', {
                title: task.title,
                meta: statusLabels[task.status] || task.status,
                body: `${(task.subtasks || []).map((item, index) => `${index + 1}. ${item.description} [${item.status}]`).join('\n') || '暂无子任务'}\n\n${resultBody}`,
            });
        });
        this.taskPanel.querySelector('.task-cancel-btn')?.addEventListener('click', (event) => {
            event.stopPropagation();
            this.cancelTask();
        });
        this.taskPanel.querySelector('.task-retry-btn')?.addEventListener('click', (event) => {
            event.stopPropagation();
            this.retryTask();
        });

        this.renderTaskStream();
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
        this.teamData = data;

        const team = data.team || {};
        const members = team.members || [];

        if (members.length === 0) {
            this.teamPanel.innerHTML = '<div class="team-empty">暂无团队成员</div>';
            this.renderTeamOverview();
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
        this.renderTeamOverview();
    }

    renderTaskStream() {
        if (!this.taskStream) return;
        if (!this.currentTask) {
            this.taskStream.innerHTML = '<div class="task-empty">暂无任务</div>';
            return;
        }

        const task = this.currentTask;
        const steps = (task.subtasks || []).map((item, index) => `
            <div class="task-step-item">
                <span class="task-step-badge">${index + 1}</span>
                <div>
                    <div class="task-stream-title">${this.escapeHtml(item.description)}</div>
                    <div class="task-stream-meta">状态：${this.escapeHtml(item.status || 'pending')}</div>
                </div>
            </div>
        `).join('');
        const reviewCard = task.result ? `
            <div class="task-review-card">
                <div class="task-stream-title">审查结果</div>
                <div class="task-stream-meta">${this.escapeHtml(task.result.summary || '暂无摘要')}</div>
                ${(task.result.issues || []).length ? `
                    <div class="task-review-section">
                        <strong>问题</strong>
                        <div>${this.escapeHtml(task.result.issues.join(' | '))}</div>
                    </div>
                ` : ''}
                ${(task.result.suggestions || []).length ? `
                    <div class="task-review-section">
                        <strong>建议</strong>
                        <div>${this.escapeHtml(task.result.suggestions.join(' | '))}</div>
                    </div>
                ` : ''}
            </div>
        ` : '';
        const teamSummary = this.teamData ? `
            <div class="task-team-summary">
                Team: ${this.escapeHtml(String(this.teamData.idle_members || 0))} idle /
                ${this.escapeHtml(String(this.teamData.busy_members || 0))} busy /
                ${this.escapeHtml(String(this.teamData.total_completed || 0))} completed
            </div>
        ` : '';
        const canCancel = ['planning', 'planned', 'executing', 'executed', 'reviewing'].includes(task.status);
        const canRetry = ['failed', 'cancelled'].includes(task.status);

        this.taskStream.innerHTML = `
            <div class="task-stream-card">
                <div class="task-stream-title">${this.escapeHtml(task.title)}</div>
                <div class="task-stream-meta">状态：${this.escapeHtml(task.status || 'pending')}</div>
                ${teamSummary}
                ${canCancel ? '<button class="task-cancel-btn">取消任务</button>' : ''}
                ${canRetry ? '<button class="task-retry-btn">重新执行</button>' : ''}
                <div class="task-step-list">${steps || '<div class="task-empty">暂无步骤</div>'}</div>
                ${reviewCard}
            </div>
        `;
        this.taskStream.querySelector('.task-cancel-btn')?.addEventListener('click', () => this.cancelTask());
        this.taskStream.querySelector('.task-retry-btn')?.addEventListener('click', () => this.retryTask());
    }

    renderWorkspaceOverview() {
        if (!this.workspaceOverview) return;
        if (!this.workspaceData || !this.workspaceData.initialized) {
            this.workspaceOverview.innerHTML = '<div class="workspace-empty">Workspace 未初始化</div>';
            return;
        }

        const memories = (this.workspaceData.memories || []).slice(0, 5).map(mem => `
            <button class="workspace-overview-card" data-memory-file="${mem.filename}">
                <div class="workspace-overview-title">${this.escapeHtml(mem.name)}</div>
                <div class="workspace-overview-body">${this.escapeHtml(mem.description || mem.type || 'memory')}</div>
            </button>
        `).join('');

        const projects = (this.workspaceData.projects || []).slice(0, 5).map(project => `
            <div class="workspace-overview-card">
                <div class="workspace-overview-title">${this.escapeHtml(project)}</div>
                <div class="workspace-overview-body">项目上下文已加载</div>
            </div>
        `).join('');

        this.workspaceOverview.innerHTML = `
            <div class="workspace-overview-card">
                <div class="workspace-overview-title">用户资料</div>
                <div class="workspace-overview-body">${this.escapeHtml(this.workspaceData.user || '未设置用户资料')}</div>
            </div>
            ${memories || '<div class="workspace-empty-item">暂无记忆</div>'}
            ${projects || '<div class="workspace-empty-item">暂无项目</div>'}
        `;

        this.workspaceOverview.querySelectorAll('[data-memory-file]').forEach(button => {
            button.addEventListener('click', () => this.showMemoryPreview(button.dataset.memoryFile));
        });
    }

    renderTeamOverview() {
        if (!this.teamOverview) return;
        const members = this.teamData?.team?.members || [];

        if (!members.length) {
            this.teamOverview.innerHTML = '<div class="team-empty">暂无团队成员</div>';
            return;
        }

        this.teamOverview.innerHTML = members.map(member => `
            <div class="detail-card">
                <div class="detail-card-title">${this.escapeHtml(member.name)}</div>
                <div class="detail-card-body">角色：${this.escapeHtml(member.role || 'member')} | 状态：${this.escapeHtml(member.status || 'idle')}</div>
            </div>
        `).join('');
    }

    renderFileBrowser() {
        if (!this.fileBrowserView) return;
        if (!this.fileEntries.length) {
            this.fileBrowserView.innerHTML = '<div class="workspace-empty">暂无文件</div>';
            return;
        }

        this.fileBrowserView.innerHTML = `
            <div class="file-browser-grid">
                ${this.fileEntries.slice(0, 24).map(entry => `
                    <button class="file-entry-card" data-path="${this.escapeHtml(entry.path)}" data-name="${this.escapeHtml(entry.name)}" data-is-dir="${entry.is_dir}">
                        <div class="file-entry-title">${this.escapeHtml(entry.name)}</div>
                        <div class="file-entry-meta">${entry.is_dir ? '目录' : '文件'}</div>
                        <div class="file-entry-path">${this.escapeHtml(entry.path)}</div>
                    </button>
                `).join('')}
            </div>
        `;

        this.fileBrowserView.querySelectorAll('.file-entry-card').forEach(button => {
            button.addEventListener('click', () => {
                if (button.dataset.isDir === 'true') {
                    this.loadFileTree(button.dataset.path);
                    this.renderDetailSidebar('file', {
                        title: button.dataset.name,
                        meta: button.dataset.path,
                        body: '目录已展开，请在左侧文件树继续浏览。',
                    });
                    return;
                }
                this.showFilePreview(button.dataset.path, button.dataset.name);
            });
        });
    }

    renderDetailSidebar(kind, payload) {
        if (!this.detailSidebar || !this.previewFilename || !this.detailSidebarContent) return;
        this.previewFilename.textContent = payload.title || '详情侧栏';
        this.detailSidebarMeta.textContent = payload.meta || kind;

        const bodyHtml = this.escapeHtml(payload.body || '').replace(/\n/g, '<br>');
        this.detailSidebarContent.innerHTML = `
            <div class="detail-card">
                <div class="detail-card-title">${this.escapeHtml(payload.title || '详情')}</div>
                <div class="detail-card-body">${bodyHtml || '暂无详情'}</div>
            </div>
        `;
        this.detailSidebar.classList.add('show');
    }

    // ========== Messages ==========

    addMessage(role, content, append = false) {
        if (this.welcomeScreen) {
            this.welcomeScreen.style.display = 'none';
        }
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
            <div class="message-meta">
                <div class="message-timestamp">${timestamp}</div>
                ${role === 'user' ? `
                <div class="message-actions">
                    <button class="msg-action-btn msg-edit-btn" title="编辑">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                </div>
                ` : ''}
            </div>
        `;

        // Store raw text for streaming append
        if (role === 'assistant') {
            messageDiv.dataset.rawText = content;
        }

        // Bind edit button for user messages
        if (role === 'user') {
            const editBtn = messageDiv.querySelector('.msg-edit-btn');
            if (editBtn) {
                editBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.startEditMessage(messageDiv, content);
                });
            }
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
                <details class="tool-collapsible tool-event-card">
                    <summary>
                        <span class="tool-icon">🔧</span>
                        <span class="tool-name">${this.escapeHtml(toolName)}</span>
                        <span class="tool-toggle">▶</span>
                    </summary>
                    <pre><code>${this.escapeHtml(JSON.stringify(args, null, 2))}</code></pre>
                </details>
            </div>
        `;
        div.addEventListener('click', () => {
            this.renderDetailSidebar('tool', {
                title: toolName,
                meta: 'Tool Call',
                body: JSON.stringify(args, null, 2),
            });
        });
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
                <details class="tool-collapsible tool-event-card">
                    <summary>
                        <span class="tool-icon">${icon}</span>
                        <span class="tool-name">${isError ? 'Execution Failed' : 'Execution Complete'}</span>
                        <span class="tool-toggle">▶</span>
                    </summary>
                    <pre><code>${this.escapeHtml(result)}</code></pre>
                </details>
            </div>
        `;
        div.addEventListener('click', () => {
            this.renderDetailSidebar('tool-result', {
                title: isError ? 'Execution Failed' : 'Execution Complete',
                meta: isError ? '错误结果' : '成功结果',
                body: result,
            });
        });
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
        if (this.sessionStatusChip && this.sessionStatusLabel) {
            this.sessionStatusLabel.textContent = isConnected ? '会话已连接' : '等待连接';
            this.sessionStatusChip.classList.toggle('connected', isConnected);
            this.sessionStatusChip.classList.toggle('disconnected', !isConnected);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text ?? '';
        return div.innerHTML;
    }

    // ========== Message Edit ==========

    startEditMessage(messageDiv, originalContent) {
        const contentEl = messageDiv.querySelector('.content');
        const metaEl = messageDiv.querySelector('.message-meta');

        // Replace content with textarea
        const textarea = document.createElement('textarea');
        textarea.className = 'message-edit-input';
        textarea.value = originalContent;
        textarea.rows = 3;

        contentEl.replaceWith(textarea);
        if (metaEl) metaEl.style.display = 'none';

        // Focus and auto-resize
        textarea.focus();
        textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        this.autoResizeTextarea(textarea);

        // Add action buttons
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-edit-actions';
        actionsDiv.innerHTML = `
            <button class="btn-cancel">取消</button>
            <button class="btn-save">保存</button>
            <button class="btn-resend">保存并重新发送</button>
        `;
        messageDiv.appendChild(actionsDiv);

        const cancelBtn = actionsDiv.querySelector('.btn-cancel');
        const saveBtn = actionsDiv.querySelector('.btn-save');
        const resendBtn = actionsDiv.querySelector('.btn-resend');

        cancelBtn.addEventListener('click', () => {
            this.cancelEditMessage(messageDiv, originalContent);
        });

        saveBtn.addEventListener('click', () => {
            this.saveEditMessage(messageDiv, textarea.value, false);
        });

        resendBtn.addEventListener('click', () => {
            this.saveEditMessage(messageDiv, textarea.value, true);
        });

        // Enter to save, Escape to cancel
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.saveEditMessage(messageDiv, textarea.value, true);
            } else if (e.key === 'Escape') {
                this.cancelEditMessage(messageDiv, originalContent);
            }
        });
    }

    cancelEditMessage(messageDiv, originalContent) {
        const textarea = messageDiv.querySelector('.message-edit-input');
        const actionsDiv = messageDiv.querySelector('.message-edit-actions');

        if (textarea) {
            const contentEl = document.createElement('div');
            contentEl.className = 'content';
            contentEl.textContent = originalContent;
            textarea.replaceWith(contentEl);
        }
        if (actionsDiv) actionsDiv.remove();

        const metaEl = messageDiv.querySelector('.message-meta');
        if (metaEl) metaEl.style.display = '';
    }

    saveEditMessage(messageDiv, newContent, resend) {
        const trimmed = newContent.trim();
        if (!trimmed) return;

        const textarea = messageDiv.querySelector('.message-edit-input');
        const actionsDiv = messageDiv.querySelector('.message-edit-actions');

        if (textarea) {
            const contentEl = document.createElement('div');
            contentEl.className = 'content';
            contentEl.textContent = trimmed;
            textarea.replaceWith(contentEl);
        }
        if (actionsDiv) actionsDiv.remove();

        const metaEl = messageDiv.querySelector('.message-meta');
        if (metaEl) metaEl.style.display = '';

        // Update stored content in dataset
        messageDiv.dataset.rawText = trimmed;

        if (resend) {
            // Remove all messages after this one
            let nextEl = messageDiv.nextElementSibling;
            while (nextEl) {
                const toRemove = nextEl;
                nextEl = nextEl.nextElementSibling;
                toRemove.remove();
            }

            // Send the edited message
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ message: trimmed }));
                this.setSending(true);
            }
        }
    }

    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
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

        // Update theme buttons in settings panel
        this.settingsThemeBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.theme === this.currentTheme);
        });

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

    async saveSystemPrompt() {
        const prompt = this.settingsSystemPrompt.value.trim();
        if (!prompt) {
            alert('系统提示词不能为空');
            return;
        }

        if (!this.currentSessionId) {
            alert('请先选择一个会话');
            return;
        }

        try {
            const response = await fetch(`/api/sessions/${this.currentSessionId}/system-prompt`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ system_prompt: prompt }),
            });

            if (response.ok) {
                // Clear messages and reconnect to apply new system prompt
                this.messagesContainer.innerHTML = '';
                this.addMessage('assistant', '系统提示词已更新，对话上下文已重置', false);
                this.connectWebSocket(this.currentSessionId);
            } else {
                alert('保存失败');
            }
        } catch (error) {
            console.error('Failed to save system prompt:', error);
            alert('保存失败: ' + error.message);
        }
    }

    async importSession(event) {
        const file = event.target.files[0];
        if (!file) return;

        try {
            const text = await file.text();
            const data = JSON.parse(text);

            // Validate imported data
            if (!data.agent || !Array.isArray(data.messages)) {
                alert('无效的会话文件格式');
                return;
            }

            // Create new session with imported data
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    agent: data.agent,
                    model: data.model || 'glm-4',
                }),
            });

            if (!response.ok) throw new Error('创建会话失败');

            const session = await response.json();

            // Import messages
            if (data.messages.length > 0) {
                const importResponse = await fetch(`/api/sessions/${session.id}/import`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages: data.messages }),
                });

                if (!importResponse.ok) throw new Error('导入消息失败');
            }

            // Reload sessions and select the imported one
            await this.loadSessions();
            this.selectSession(session.id);
            this.addMessage('assistant', `会话 "${data.agent}" 导入成功`, false);
        } catch (error) {
            console.error('Failed to import session:', error);
            alert('导入失败: ' + error.message);
        } finally {
            // Reset file input
            event.target.value = '';
        }
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
