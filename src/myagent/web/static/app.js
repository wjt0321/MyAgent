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
        this.restoreAvailable = false;
        this.toolCallRegistry = new Map();
        this.availableModels = [
            'qwen-max',
            'qwen-plus',
            'qwen-turbo',
            'qwen-coder-plus',
            'glm-4',
            'glm-4-plus',
        ];

        this.initTheme();
        this.initElements();
        this.bindEvents();
        this.syncResponsiveWorkbenchState();
        this.loadSetupStatus();
        this.renderCommandPalette();
        this.renderDetailSidebar('overview', {
            title: '工作台详情',
            meta: '准备就绪',
            body: '选择一个会话、任务、文件或工具卡片查看更详细的信息。',
        });
        this.renderWelcomeLanding();
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
        this.threadTitle = document.getElementById('thread-title');
        this.threadModel = document.getElementById('thread-model');
        this.fileTree = document.getElementById('file-tree');
        this.previewFilename = document.getElementById('preview-filename');
        this.previewContent = document.getElementById('preview-content');
        this.closePreviewBtn = document.getElementById('close-preview');
        this.themeToggle = document.getElementById('theme-toggle');
        this.mobileSidebarToggle = document.getElementById('mobile-sidebar-toggle');
        this.sidebar = document.getElementById('sidebar');
        this.sidebarOverlay = document.getElementById('sidebar-overlay');
        this.searchToggle = document.getElementById('search-toggle');
        this.searchBar = document.getElementById('search-bar');
        this.searchInput = document.getElementById('search-input');
        this.searchClose = document.getElementById('search-close');
        this.workbenchTabBar = document.getElementById('workbench-tab-bar');
        this.workbenchTabBtns = document.querySelectorAll('.tab-bar-btn');
        this.workbenchViews = document.querySelectorAll('.workbench-view');
        this.mobileViewChip = document.getElementById('mobile-view-chip');
        this.sessionControlBar = document.getElementById('session-control-bar');
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
        this.filePreviewPanel = this.detailSidebar;

        // Settings modal
        this.settingsBtn = document.getElementById('settings-btn');
        this.settingsModal = document.getElementById('settings-modal');
        this.closeSettingsBtn = document.getElementById('close-settings');
        this.saveSettingsBtn = document.getElementById('save-settings-btn');
        this.settingsAgentSelect = document.getElementById('settings-agent-select');
        this.settingsSystemPrompt = document.getElementById('settings-system-prompt');

        // Theme buttons in settings panel (new theme selector)
        this.settingsThemeBtns = document.querySelectorAll('.theme-btn');
        this.settingsSessionCount = document.getElementById('settings-session-count');
        this.settingsMessageCount = document.getElementById('settings-message-count');
        this.workspaceInfo = document.getElementById('workspace-info');

        // Session import
        this.sessionImportBtn = document.getElementById('session-import-btn');
        this.sessionImportFile = document.getElementById('session-import-file');

        // Toast notifications
        this.toastContainer = document.getElementById('toast-container');

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

        // Mobile detail sidebar: close when clicking outside
        this.detailSidebar?.addEventListener('click', (e) => {
            if (e.target === this.detailSidebar && window.innerWidth <= 768) {
                this.hideFilePreview();
            }
        });

        // Mobile sidebar
        this.mobileSidebarToggle.addEventListener('click', () => this.openSidebar());
        this.sidebarOverlay.addEventListener('click', () => this.closeSidebar());
        window.addEventListener('resize', () => this.syncResponsiveWorkbenchState());

        // Agent/model select - moved to Settings Modal and Command Palette
        // Model select removed from header in Step 05

        // Search
        this.searchToggle.addEventListener('click', () => this.toggleSearch());
        this.searchClose.addEventListener('click', () => this.toggleSearch());
        this.searchInput.addEventListener('input', (e) => this.performSearch(e.target.value));
        document.getElementById('search-prev')?.addEventListener('click', () => this.prevSearchResult());
        document.getElementById('search-next')?.addEventListener('click', () => this.nextSearchResult());

        this.workbenchTabBtns.forEach(btn => {
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

        this.bindQuickCards();

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
            this.sessionImportFile.addEventListener('change', (e) => {
                this.importSession(e);
                // Reset so the same file can be selected again
                e.target.value = '';
            });
        }
    }

    // ========== Toast Notifications ==========

    showToast(message, type = 'info', duration = 3000) {
        if (!this.toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;

        const icons = {
            success: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
            error: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
            warning: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
            info: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        };

        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-content">${this.escapeHtml(message)}</div>
            <button class="toast-close" title="关闭">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                    <line x1="18" y1="6" x2="6" y2="18"/>
                    <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
            </button>
        `;

        this.toastContainer.appendChild(toast);

        void toast.offsetWidth;
        toast.classList.add('toast-show');

        const closeToast = () => {
            toast.classList.remove('toast-show');
            toast.classList.add('toast-hide');
            setTimeout(() => toast.remove(), 300);
        };

        toast.querySelector('.toast-close').addEventListener('click', closeToast);

        if (duration > 0) {
            setTimeout(closeToast, duration);
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
        this.workbenchTabBtns.forEach(btn => {
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
        this.updateContextHelp(viewName);
        this.updateMobileViewChip(viewName);
        this.scrollActiveWorkbenchNavIntoView();
        if (window.innerWidth <= 768) {
            this.closeSidebar();
        }
    }

    updateContextHelp(viewName) {
        // Removed in Step 05: context-help-strip moved from Header
    }

    updateMobileViewChip(viewName) {
        if (!this.mobileViewChip) return;
        const labels = {
            chat: '聊天',
            tasks: '任务',
            files: '文件',
            workspace: 'Workspace',
            team: '团队',
        };
        this.mobileViewChip.textContent = labels[viewName] || '工作台';
    }

    scrollActiveWorkbenchNavIntoView() {
        const activeButton = this.workbenchNav?.querySelector('.workbench-nav-btn.active');
        activeButton?.scrollIntoView({
            block: 'nearest',
            inline: 'center',
            behavior: 'smooth',
        });
    }

    syncResponsiveWorkbenchState() {
        this.updateMobileViewChip(this.activeView);
        this.scrollActiveWorkbenchNavIntoView();
        if (window.innerWidth > 768) {
            this.closeSidebar();
            this.detailSidebar?.classList.remove('show-mobile');
        }
    }

    getCommandPaletteItems() {
        const modelItems = this.availableModels.map(model => ({
            id: `model-${model}`,
            title: `切换模型: ${model}`,
            meta: `使用 ${model} 模型进行对话`,
            shortcut: 'model',
            handler: () => this.switchModel(model),
        }));

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
                id: 'switch-model',
                title: '切换模型',
                meta: '选择要使用的 AI 模型',
                shortcut: 'model',
                handler: () => this.showModelPicker(),
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
            ...modelItems,
        ];
    }

    showModelPicker() {
        if (!this.commandPaletteModal) return;
        this.renderCommandPalette('model');
        this.commandPaletteModal.classList.add('show');
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

    pulseSessionStatus() {
        if (!this.sessionStatusChip) return;
        this.sessionStatusChip.classList.remove('is-pulsing');
        void this.sessionStatusChip.offsetWidth;
        this.sessionStatusChip.classList.add('is-pulsing');
        window.setTimeout(() => {
            this.sessionStatusChip?.classList.remove('is-pulsing');
        }, 900);
    }

    getCurrentSessionRecord() {
        return this.sessions.find(session => session.id === this.currentSessionId) || null;
    }

    renderSessionSummaryLine(session = null, statusText = '') {
        // Removed in Step 05: session-summary-line removed from Header
    }

    refreshActiveSession(session, statusText = '') {
        if (!session) return;

        const index = this.sessions.findIndex(item => item.id === session.id);
        if (index >= 0) {
            this.sessions[index] = {
                ...this.sessions[index],
                ...session,
            };
        } else {
            this.sessions.unshift(session);
        }

        this.threadTitle.textContent = session.agent || 'general';
        this.threadModel.textContent = session.model || 'default';
        this.renderSessionList();
        this.renderSessionSummaryLine(session, statusText);
        this.renderDetailSidebar('session', {
            title: session.agent || 'general',
            meta: session.model || 'default',
            body: `会话 ID：${session.id}\n消息数：${session.messages?.length || 0}\n最近更新：${this.formatDate(session.updated_at)}`,
        });
    }

    // ========== Agent Switch ==========

    async switchAgent(agentName) {
        if (!this.currentSessionId) return;

        try {
            this.pulseSessionStatus();
            this.setStatus('switching', `正在切换 agent：${agentName}`);
            const response = await fetch(`/api/sessions/${this.currentSessionId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent: agentName }),
            });

            if (response.ok) {
                const session = await response.json();
                this.refreshActiveSession(session, `agent 已切换为 ${agentName}`);
                this.connectWebSocket(this.currentSessionId);
                this.showToast(`已切换到 agent: ${agentName}`, 'success');
            }
        } catch (error) {
            console.error('Failed to switch agent:', error);
            this.setStatus('disconnected');
        }
    }

    // ========== Model Switch ==========

    async switchModel(modelName) {
        if (!this.currentSessionId) return;

        try {
            this.pulseSessionStatus();
            this.setStatus('switching', `正在切换模型：${modelName}`);
            const response = await fetch(`/api/sessions/${this.currentSessionId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: modelName }),
            });

            if (response.ok) {
                const session = await response.json();
                this.refreshActiveSession(session, `模型已切换为 ${modelName}`);
                this.connectWebSocket(this.currentSessionId);
                this.showToast(`已切换到模型: ${modelName}`, 'success');
            }
        } catch (error) {
            console.error('Failed to switch model:', error);
            this.setStatus('disconnected');
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
        if (!query.trim()) {
            this.updateSearchCount(0, 0);
            return;
        }

        const messages = this.messagesContainer.querySelectorAll('.message');
        const lowerQuery = query.toLowerCase();
        this._searchMatches = [];

        messages.forEach(msg => {
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

    clearSearchHighlights() {
        this.messagesContainer.querySelectorAll('.message.highlighted')
            .forEach(msg => msg.classList.remove('highlighted'));
        this._searchMatches = [];
        this._searchIndex = 0;
        this.updateSearchCount(0, 0);
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

    renderWelcomeLanding() {
        // Step 06: Codex-style minimal welcome - hero input + recent threads
        if (!this.welcomeScreen || !this.setupReady) return;
        this.welcomeScreen.style.display = 'flex';
        const sessionCards = this.sessions.slice(0, 8).map((s, i) => `
            <div class="thread-card" data-session-id="${s.id}" style="animation-delay: ${0.05 * i + 0.1}s">
                <div class="thread-card-title">${this.escapeHtml(s.agent || 'general')}</div>
                <div class="thread-card-meta">
                    <span class="thread-card-time">${this.formatDate(s.updated_at)}</span>
                    <span class="thread-card-msgs">${(s.messages || []).length} messages</span>
                </div>
            </div>
        `).join('');

        this.welcomeScreen.innerHTML = `
            <div class="welcome-codex-hero">
                <div class="welcome-codex-brand">MyAgent</div>
                <div class="welcome-codex-slogan">可计划、可执行、可审查的 AI 智能体工作台</div>
                <div class="welcome-codex-input-wrap">
                    <textarea class="welcome-codex-input" id="welcome-input" placeholder="描述你的需求，或按 Enter 创建新线程..." rows="1"></textarea>
                    <button class="welcome-codex-send" id="welcome-send-btn" title="发送">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="welcome-codex-recent">
                <div class="welcome-recent-header">最近线程</div>
                <div class="thread-list" id="welcome-thread-list">
                    ${sessionCards || '<div class="thread-empty">还没有线程，从上方输入框开始吧</div>'}
                </div>
            </div>
        `;

        const input = document.getElementById('welcome-input');
        const sendBtn = document.getElementById('welcome-send-btn');
        const autoResize = () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        };
        input.addEventListener('input', autoResize);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const text = input.value.trim();
                if (text) this.createSessionAndSend(text);
            }
        });
        sendBtn.addEventListener('click', () => {
            const text = input.value.trim();
            if (text) this.createSessionAndSend(text);
        });

        document.querySelectorAll('.thread-card').forEach(card => {
            card.addEventListener('click', () => {
                this.selectSession(card.dataset.sessionId);
            });
        });
    }

    async createSessionAndSend(text) {
        try {
            const res = await fetch('/api/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ agent: 'general', model: 'glm-4' }),
            });
            const session = await res.json();
            this.currentSessionId = session.id;
            this.messages = [];
            this.welcomeScreen.style.display = 'none';
            this.renderMessages();
            this.sendBtn.disabled = true;
            await this.sendMessageToWs(text);
        } catch (error) {
            console.error('Failed to create session and send:', error);
        }
    }

    async sendMessageToWs(text) {
        this.messages.push({ role: 'user', content: text, id: `user-${Date.now()}` });
        this.renderMessages();
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        const token = localStorage.getItem('myagent_token') || '';
        const wsUrl = `ws://${window.location.host}/ws/${this.currentSessionId}?token=${token}`;
        const ws = new WebSocket(wsUrl);
        let assistantMsg = null;
        ws.onopen = () => {
            ws.send(JSON.stringify({ action: 'chat', message: text, session_id: this.currentSessionId }));
        };
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'chunk') {
                if (!assistantMsg) {
                    assistantMsg = { role: 'assistant', content: '', id: `assistant-${Date.now()}` };
                    this.messages.push(assistantMsg);
                }
                assistantMsg.content += data.text;
                this.renderMessages();
                this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
            } else if (data.type === 'done') {
                ws.close();
                this.sendBtn.disabled = false;
                this.messageInput.value = '';
                this.loadSessions();
            } else if (data.type === 'error') {
                ws.close();
                this.sendBtn.disabled = false;
            }
        };
        ws.onclose = () => {
            this.sendBtn.disabled = false;
        };
    }

    async loadWorkspace() {
        if (this.workspaceInfo) {
            this.workspaceInfo.innerHTML = this.renderWorkspaceSkeleton();
        }
        if (this.workspaceOverview) {
            this.workspaceOverview.innerHTML = this.renderWorkspaceSkeleton();
        }
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

    renderWorkspaceSkeleton() {
        return `
            <div class="skeleton-card">
                <div class="skeleton skeleton-card-title"></div>
                <div class="skeleton skeleton-text skeleton-text-long"></div>
                <div class="skeleton skeleton-text skeleton-text-medium"></div>
                <div class="skeleton skeleton-text skeleton-text-short"></div>
            </div>
            <div class="skeleton-icon-row" style="margin-top: 12px;">
                <div class="skeleton skeleton-icon"></div>
                <div class="skeleton skeleton-icon"></div>
                <div class="skeleton skeleton-icon"></div>
            </div>
        `;
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
            <div class="workspace-memory-item" data-filename="${this.escapeHtml(mem.filename)}">
                <div class="memory-name">${this.escapeHtml(mem.name)}</div>
                <div class="memory-desc">${this.escapeHtml(mem.description || mem.type)}</div>
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
        this.detailSidebar?.classList.remove('show-mobile');
        if (this.previewContent) {
            this.previewContent.textContent = '';
            this.previewContent.className = '';
        }
    }

    // ========== Sessions ==========

    async loadSessions() {
        this.renderSessionListSkeleton();
        try {
            const response = await fetch('/api/sessions');
            this.sessions = await response.json();
            this.renderSessionList();
            this.renderRecentSessions();

            if (this.sessions.length > 0 && !this.currentSessionId) {
                this.selectSession(this.sessions[0].id);
            } else if (!this.currentSessionId) {
                this.renderWelcomeLanding();
            }
        } catch (error) {
            console.error('Failed to load sessions:', error);
            this.sessionList.innerHTML = '<div class="thread-empty">加载失败，请刷新重试</div>';
        }
    }

    renderSessionListSkeleton() {
        const skeletonItems = Array(4).fill('').map(() => `
            <div class="skeleton-thread">
                <div class="skeleton skeleton-thread-title"></div>
                <div class="skeleton skeleton-thread-meta"></div>
            </div>
        `).join('');

        this.sessionList.innerHTML = `
            <div class="thread-section">
                <div class="thread-group-header">
                    <span class="thread-group-title">加载中...</span>
                </div>
                <div class="thread-group-list">
                    ${skeletonItems}
                </div>
            </div>
        `;
    }

    renderSessionList() {
        this.sessionList.innerHTML = '';

        const now = new Date();
        const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

        const activeThreads = this.sessions.filter(s => {
            const updatedAt = new Date(s.updated_at);
            return updatedAt >= oneDayAgo;
        });

        const historyThreads = this.sessions.filter(s => {
            const updatedAt = new Date(s.updated_at);
            return updatedAt < oneDayAgo;
        }).sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));

        if (activeThreads.length > 0) {
            const activeSection = document.createElement('div');
            activeSection.className = 'thread-section';
            activeSection.innerHTML = `
                <div class="thread-group-header">
                    <span class="thread-group-title">进行中</span>
                    <span class="thread-group-count">${activeThreads.length}</span>
                </div>
                <div class="thread-group-list">
                    ${activeThreads.map(s => this.renderThreadCard(s)).join('')}
                </div>
            `;
            this.sessionList.appendChild(activeSection);
        }

        if (historyThreads.length > 0) {
            const historySection = document.createElement('div');
            historySection.className = 'thread-section';
            historySection.innerHTML = `
                <div class="thread-group-header">
                    <span class="thread-group-title">历史</span>
                    <span class="thread-group-count">${historyThreads.length}</span>
                </div>
                <div class="thread-group-list">
                    ${historyThreads.map(s => this.renderThreadCard(s)).join('')}
                </div>
            `;
            this.sessionList.appendChild(historySection);
        }

        if (this.sessions.length === 0) {
            this.sessionList.innerHTML = '<div class="thread-empty">还没有线程，点击顶部 + 按钮开始吧</div>';
        }

        this.sessionList.querySelectorAll('.thread-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (e.target.closest('.thread-card-actions')) return;
                this.selectSession(card.dataset.sessionId);
                this.closeSidebar();
            });
        });

        this.sessionList.querySelectorAll('.thread-rename').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.startRenameSession(btn.dataset.sessionId);
            });
        });

        this.sessionList.querySelectorAll('.thread-export').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showExportMenu(btn.dataset.sessionId, btn);
            });
        });

        this.sessionList.querySelectorAll('.thread-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showDeleteSessionConfirm(btn.dataset.sessionId);
            });
        });

        this.renderRecentSessions();
    }

    renderThreadCard(session) {
        const isActive = session.id === this.currentSessionId;
        const updatedAt = new Date(session.updated_at);
        const timeStr = this.formatRelativeTime(updatedAt);
        const msgCount = (session.messages || []).length;
        const hasTask = session.task_status === 'running' || session.task_status === 'pending';

        return `
            <div class="thread-card ${isActive ? 'active' : ''}" data-session-id="${session.id}">
                <div class="thread-card-header">
                    <div class="thread-card-icon">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        </svg>
                    </div>
                    <div class="thread-card-title">${this.escapeHtml(session.agent || 'general')}</div>
                    ${hasTask ? '<div class="thread-card-status-dot" title="任务进行中"></div>' : ''}
                </div>
                <div class="thread-card-body">
                    <div class="thread-card-time">${timeStr}</div>
                    <div class="thread-card-msgs">${msgCount} messages</div>
                </div>
                <div class="thread-card-actions">
                    <button class="thread-rename" data-session-id="${session.id}" title="重命名">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                    </button>
                    <button class="thread-export" data-session-id="${session.id}" title="导出">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                            <polyline points="7 10 12 15 17 10"/>
                            <line x1="12" y1="15" x2="12" y2="3"/>
                        </svg>
                    </button>
                    <button class="thread-delete" data-session-id="${session.id}" title="删除">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }

    formatRelativeTime(date) {
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);

        if (diffSec < 60) return '刚刚';
        if (diffMin < 60) return `${diffMin} 分钟前`;
        if (diffHour < 24) return `${diffHour} 小时前`;
        if (diffDay < 7) return `${diffDay} 天前`;
        return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    }

    async startRenameSession(sessionId) {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session) return;

        const card = this.sessionList.querySelector(`[data-session-id="${sessionId}"]`);
        if (!card) return;

        const titleEl = card.querySelector('.session-card-title') || card.querySelector('.session-title');
        if (!titleEl) return;

        const originalName = titleEl.textContent.trim();

        const input = document.createElement('input');
        input.type = 'text';
        input.value = originalName;
        input.className = 'inline-rename-input';
        input.style.cssText = `
            width: 100%;
            padding: 4px 8px;
            border: 1px solid var(--accent);
            border-radius: var(--radius-sm);
            background: var(--bg-input);
            color: var(--text-primary);
            font-size: inherit;
            font-family: inherit;
            outline: none;
        `;

        const finishEdit = async () => {
            const newName = input.value.trim();
            if (newName && newName !== originalName) {
                try {
                    const response = await fetch(`/api/sessions/${sessionId}`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ agent: newName }),
                    });
                    if (response.ok) {
                        session.agent = newName;
                        this.renderSessionList();
                        if (this.currentSessionId === sessionId) {
                            this.threadTitle.textContent = newName;
                        }
                    }
                } catch (error) {
                    console.error('Failed to rename session:', error);
                }
            } else {
                titleEl.textContent = originalName;
            }
        };

        input.addEventListener('blur', finishEdit);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') input.blur();
            if (e.key === 'Escape') {
                input.value = originalName;
                input.blur();
            }
        });

        titleEl.textContent = '';
        titleEl.appendChild(input);
        input.focus();
        input.select();
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
                body: JSON.stringify({ agent: 'general', model: 'glm-4' })
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
        this.clearSearchHighlights();

        const session = this.sessions.find(s => s.id === sessionId);
        if (session) {
            this.welcomeScreen.style.display = 'none';
            this.messagesContainer.innerHTML = '';
            this.renderMessageLoadingSkeleton();
            this.refreshActiveSession(session, '当前会话正在加载');

            session.messages.forEach(msg => {
                this.addMessage(msg.role, msg.content, false);
            });

            this.refreshActiveSession(session, '当前会话已同步');
        } else {
            this.renderSessionSummaryLine(null, '当前会话尚未加载');
            this.renderWelcomeLanding();
        }

        if (!this.setupReady) {
            this.renderSetupRequired();
            this.setStatus('disconnected');
            return;
        }
        this.setActiveView('chat');
        this.connectWebSocket(sessionId);
    }

    renderMessageLoadingSkeleton() {
        const skeletonMessages = Array(3).fill('').map(() => `
            <div class="skeleton-message">
                <div class="skeleton skeleton-avatar"></div>
                <div class="skeleton-message-body">
                    <div class="skeleton skeleton-text skeleton-text-long"></div>
                    <div class="skeleton skeleton-text skeleton-text-medium"></div>
                    <div class="skeleton skeleton-text skeleton-text-short"></div>
                </div>
            </div>
        `).join('');

        this.messagesContainer.innerHTML = `
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <span>正在加载消息...</span>
            </div>
            ${skeletonMessages}
        `;
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
        this.setStatus('connecting');

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
                // Show error once and try delayed reconnect
                if (this.reconnectAttempts === 0) {
                    this.addMessage('error', '连接失败：服务器配置错误，请检查 LLM API Key 设置。', false);
                }
                this.reconnectAttempts++;
                if (this.reconnectAttempts <= this.maxReconnectAttempts) {
                    setTimeout(() => {
                        this.connectWebSocket(sessionId);
                    }, 5000);
                }
                return;
            }
            // Non-fatal close codes (1001, 1002, 1003, etc.) - attempt reconnect
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
                this.addToolCall(data.tool_name, data.arguments, data.tool_use_id);
                break;

            case 'tool_result':
                this.addToolResult(data.result, data.is_error, data.tool_use_id);
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
                this.addPermissionResult(data.approved, data.reason);
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
                this.showToast('已打开设置面板', 'info');
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
            .map(([k, v]) => `<div class="perm-arg"><strong>${this.escapeHtml(k)}:</strong> ${this.escapeHtml(String(v))}</div>`)
            .join('');

        modal.innerHTML = `
            <div class="permission-dialog">
                <h3>Permission Required</h3>
                <p class="perm-reason">${this.escapeHtml(data.reason)}</p>
                <div class="perm-details">
                    <div><strong>Tool:</strong> ${this.escapeHtml(data.tool_name)}</div>
                    ${argsHtml}
                </div>
                <div class="perm-buttons">
                    <button class="btn-deny" id="perm-deny-btn">Deny</button>
                    <button class="btn-allow" id="perm-allow-btn">Allow</button>
                </div>
            </div>
        `;

        this._pendingPermission = data;
        document.body.appendChild(modal);

        modal.querySelector('#perm-allow-btn').addEventListener('click', () => this.handlePermission(true));
        modal.querySelector('#perm-deny-btn').addEventListener('click', () => this.handlePermission(false));
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
            this.restoreAvailable = true;
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

    async restoreTask() {
        try {
            const response = await fetch('/api/tasks/restore', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentTask = data.task;
                this.restoreAvailable = !!data.task;
                this.renderTaskPanel();
                this.syncTaskPollingState();
                this.addMessage('assistant', `已恢复任务 "${this.currentTask.title}" 的最近快照。`, false);
            }
        } catch (error) {
            console.error('Failed to restore task:', error);
        }
    }

    async loadCurrentTask() {
        try {
            const response = await fetch('/api/tasks/current');
            if (response.ok) {
                const snapshot = await response.json();
                this.currentTask = snapshot.task;
                this.teamData = snapshot.team || this.teamData;
                this.restoreAvailable = !!snapshot.restore_available;
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
            this.taskPanel.innerHTML = this.renderTaskEmptyState();
            this.bindTaskEmptyActions(this.taskPanel);
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
            <div class="task-card surface-card surface-card-strong" data-task-id="${task.id}">
                <div class="surface-eyebrow">Task</div>
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

    renderReviewListSection(sectionClass, title, items) {
        if (!items || items.length === 0) {
            return '';
        }
        const listItems = items
            .map(item => `<li>${this.escapeHtml(item)}</li>`)
            .join('');
        return `
            <div class="task-review-section ${sectionClass}">
                <div class="task-review-heading">${this.escapeHtml(title)}</div>
                <ul>${listItems}</ul>
            </div>
        `;
    }

    renderTaskEmptyState() {
        return `
            <div class="task-empty">
                <div class="task-empty-title">还没有进行中的任务</div>
                <div class="task-empty-desc">你可以先创建一个计划任务，或者把最近一次任务快照恢复回工作台。</div>
                <div class="task-empty-actions">
                    <button class="task-empty-primary">创建计划任务</button>
                    ${this.restoreAvailable ? '<button class="task-restore-btn">恢复最近任务</button>' : ''}
                </div>
            </div>
        `;
    }

    bindTaskEmptyActions(container) {
        container.querySelector('.task-empty-primary')?.addEventListener('click', () => {
            this.setActiveView('chat');
            this.messageInput.value = '/plan ';
            this.messageInput.focus();
        });
        container.querySelector('.task-restore-btn')?.addEventListener('click', () => this.restoreTask());
    }

    renderTaskTimeline(events) {
        if (!events || events.length === 0) {
            return '<div class="task-empty">暂无执行事件</div>';
        }
        const recentEvents = events.slice(-8).reverse();
        return `
            <div class="task-timeline-list">
                ${recentEvents.map(event => `
                    <div class="task-timeline-item">
                        <div class="task-stream-title">${this.escapeHtml(event.message || event.type || 'event')}</div>
                        <div class="task-stream-meta">
                            ${this.escapeHtml(event.type || 'event')}
                            ${event.member ? ` · ${this.escapeHtml(event.member)}` : ''}
                            ${event.status ? ` · ${this.escapeHtml(event.status)}` : ''}
                        </div>
                    </div>
                `).join('')}
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
            this.taskStream.innerHTML = this.renderTaskEmptyState();
            this.bindTaskEmptyActions(this.taskStream);
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
                ${this.renderReviewListSection('task-review-deliverables', '交付物', task.result.deliverables || [])}
                ${this.renderReviewListSection('task-review-issues', '问题', task.result.issues || [])}
                ${this.renderReviewListSection('task-review-suggestions', '建议', task.result.suggestions || [])}
            </div>
        ` : '';
        const timelineCard = `
            <div class="task-review-card">
                <div class="task-stream-title">执行时间线</div>
                ${this.renderTaskTimeline(task.events || [])}
            </div>
        `;
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
                ${timelineCard}
                ${reviewCard}
            </div>
        `;
        this.taskStream.querySelector('.task-cancel-btn')?.addEventListener('click', () => this.cancelTask());
        this.taskStream.querySelector('.task-retry-btn')?.addEventListener('click', () => this.retryTask());
        this.taskStream.querySelector('.task-restore-btn')?.addEventListener('click', () => this.restoreTask());
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
        this.detailSidebar.classList.toggle('show-mobile', window.innerWidth <= 768);
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

    summarizeToolArguments(args) {
        if (!args || Object.keys(args).length === 0) {
            return '无参数';
        }
        if (typeof args.command === 'string' && args.command.trim()) {
            return args.command.trim();
        }
        const firstPair = Object.entries(args)[0];
        if (!firstPair) {
            return '无参数';
        }
        return `${firstPair[0]}: ${String(firstPair[1])}`.slice(0, 96);
    }

    summarizeToolResult(result, isError = false) {
        const text = String(result || '').trim();
        if (!text) {
            return isError ? '工具调用失败，暂无输出。' : '工具调用完成，暂无输出。';
        }
        const firstLine = text.split('\n')[0].trim();
        const summary = firstLine.length > 96 ? `${firstLine.slice(0, 96)}...` : firstLine;
        return summary;
    }

    renderToolEventCard({
        kind,
        title,
        toolUseId = '',
        summary,
        payload,
        icon,
        statusLabel,
        statusTone,
        meta,
    }) {
        const payloadText = typeof payload === 'string'
            ? payload
            : JSON.stringify(payload || {}, null, 2);
        return `
            <details class="tool-collapsible tool-event-card tool-event-card-v2 surface-card surface-card-soft ${statusTone}" ${kind === 'tool-result' ? 'open' : ''}>
                <summary>
                    <span class="tool-icon">${icon}</span>
                    <span class="tool-event-heading">
                        <span class="surface-eyebrow">Tool Event</span>
                        <span class="tool-name">${this.escapeHtml(title)}</span>
                        <span class="tool-event-summary">${this.escapeHtml(summary)}</span>
                    </span>
                    <span class="tool-status-chip ${statusTone}">${this.escapeHtml(statusLabel)}</span>
                    <span class="tool-toggle">▶</span>
                </summary>
                <div class="tool-event-meta">
                    <span>${this.escapeHtml(meta)}</span>
                    ${toolUseId ? `<span>Use ID: ${this.escapeHtml(toolUseId)}</span>` : ''}
                </div>
                <pre><code>${this.escapeHtml(payloadText)}</code></pre>
            </details>
        `;
    }

    animateToolCard(container) {
        const card = container?.querySelector('.tool-event-card-v2');
        if (!card) return;
        card.classList.remove('is-entering');
        void card.offsetWidth;
        card.classList.add('is-entering');
        window.setTimeout(() => {
            card.classList.remove('is-entering');
        }, 520);
    }

    addToolCall(toolName, args, toolUseId = '') {
        if (toolUseId) {
            this.toolCallRegistry.set(toolUseId, {
                toolName,
                arguments: args,
            });
        }
        const div = document.createElement('div');
        div.className = 'message tool-call';
        const summary = this.summarizeToolArguments(args);
        div.innerHTML = `
            <div class="role-label">Tool</div>
            <div class="content">
                ${this.renderToolEventCard({
                    kind: 'tool-call',
                    title: toolName,
                    toolUseId,
                    summary,
                    payload: args,
                    icon: '🔧',
                    statusLabel: '运行中',
                    statusTone: 'pending',
                    meta: 'Tool Call',
                })}
            </div>
        `;
        div.addEventListener('click', () => {
            this.renderDetailSidebar('tool', {
                title: toolName,
                meta: toolUseId ? `Tool Call · ${toolUseId}` : 'Tool Call',
                body: JSON.stringify(args, null, 2),
            });
        });
        this.messagesContainer.appendChild(div);
        this.animateToolCard(div);
        this.scrollToBottom();
    }

    addToolResult(result, isError, toolUseId = '') {
        const div = document.createElement('div');
        div.className = `message tool-result ${isError ? 'error' : ''}`;
        const registry = toolUseId ? this.toolCallRegistry.get(toolUseId) : null;
        const toolName = registry?.toolName || '工具调用';
        const summary = this.summarizeToolResult(result, isError);
        div.innerHTML = `
            <div class="role-label">${isError ? 'Error' : 'Result'}</div>
            <div class="content">
                ${this.renderToolEventCard({
                    kind: 'tool-result',
                    title: toolName,
                    toolUseId,
                    summary,
                    payload: result,
                    icon: isError ? '❌' : '✅',
                    statusLabel: isError ? '失败' : '完成',
                    statusTone: isError ? 'error' : 'success',
                    meta: isError ? 'Tool Result · Error' : 'Tool Result',
                })}
            </div>
        `;
        div.addEventListener('click', () => {
            this.renderDetailSidebar('tool-result', {
                title: toolName,
                meta: isError ? '错误结果' : '成功结果',
                body: String(result),
            });
        });
        this.messagesContainer.appendChild(div);
        this.animateToolCard(div);
        this.scrollToBottom();
    }

    addPermissionResult(approved, reason) {
        const div = document.createElement('div');
        div.className = `message tool-result ${approved ? '' : 'error'}`;
        div.innerHTML = `
            <div class="role-label">Result</div>
            <div class="content">
                ${this.renderToolEventCard({
                    kind: 'permission-result',
                    title: 'Permission Request',
                    summary: reason || (approved ? '已批准执行。' : '已拒绝执行。'),
                    payload: reason || '',
                    icon: approved ? '🟢' : '🛑',
                    statusLabel: approved ? '已批准' : '已拒绝',
                    statusTone: approved ? 'success' : 'error',
                    meta: 'Permission Result',
                })}
            </div>
        `;
        div.addEventListener('click', () => {
            this.renderDetailSidebar('tool-result', {
                title: 'Permission Request',
                meta: approved ? '已批准' : '已拒绝',
                body: reason || '',
            });
        });
        this.messagesContainer.appendChild(div);
        this.animateToolCard(div);
        this.scrollToBottom();
    }

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

    setStatus(status, label = '') {
        const isConnected = status === 'connected';
        const isSwitching = status === 'switching';
        const isConnecting = status === 'connecting';
        this.statusIndicator.textContent = isConnected ? '已连接' : (isSwitching ? '切换中' : (isConnecting ? '连接中' : '未连接'));
        this.statusDot.classList.toggle('connected', isConnected);
        this.statusDot.classList.toggle('connecting', isConnecting);
        if (this.sessionStatusChip && this.sessionStatusLabel) {
            this.sessionStatusLabel.textContent = label || (isConnected ? '会话已连接' : (isSwitching ? '会话切换中' : (isConnecting ? '正在连接...' : '等待连接')));
            this.sessionStatusChip.classList.toggle('connected', isConnected);
            this.sessionStatusChip.classList.toggle('disconnected', !isConnected && !isSwitching && !isConnecting);
            this.sessionStatusChip.classList.toggle('switching', isSwitching);
            this.sessionStatusChip.classList.toggle('connecting', isConnecting);
        }
        if (status === 'connected') {
            this.renderSessionSummaryLine(this.getCurrentSessionRecord(), label || '当前会话已连接');
        } else if (status === 'switching') {
            this.renderSessionSummaryLine(this.getCurrentSessionRecord(), label || '正在同步会话设置');
        } else if (status === 'connecting') {
            this.renderSessionSummaryLine(this.getCurrentSessionRecord(), label || '正在连接服务器...');
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
            <div class="memory-card" data-name="${this.escapeHtml(mem.name)}">
                <div class="memory-card-header">
                    <div class="memory-card-name">${this.escapeHtml(mem.name)}</div>
                    <span class="memory-card-type">${typeLabels[mem.type] || mem.type}</span>
                </div>
                <div class="memory-card-desc">${this.escapeHtml(mem.description || '')}</div>
                <div class="memory-card-content">${this.escapeHtml(mem.content || '').substring(0, 100)}${(mem.content || '').length > 100 ? '...' : ''}</div>
                <div class="memory-card-actions">
                    <button class="memory-btn-edit" data-name="${this.escapeHtml(mem.name)}">编辑</button>
                    <button class="memory-btn-delete" data-name="${this.escapeHtml(mem.name)}">删除</button>
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
            this.showToast('名称和内容不能为空', 'warning');
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
                this.loadWorkspace();
                this.showToast('记忆保存成功', 'success');
            } else {
                this.showToast('保存失败', 'error');
            }
        } catch (error) {
            console.error('Failed to save memory:', error);
            this.showToast('保存失败: ' + error.message, 'error');
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
                this.showToast('记忆已删除', 'success');
            } else {
                this.showToast('删除失败', 'error');
            }
        } catch (error) {
            console.error('Failed to delete memory:', error);
            this.showToast('删除失败: ' + error.message, 'error');
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
                    this.showFilePreview(path, path.split('/').pop());
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
                this.showToast('索引重建完成', 'success');
            }
        } catch (error) {
            console.error('Failed to rebuild index:', error);
            this.showToast('重建失败', 'error');
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
                        this.threadTitle.textContent = agent;
                        this.renderSessionList();
                    }
                    this.connectWebSocket(this.currentSessionId);
                }
            } catch (error) {
                console.error('Failed to save settings:', error);
            }
        }

        this.closeSettings();
        this.showToast('设置已保存', 'success');
    }

    async saveSystemPrompt() {
        const prompt = this.settingsSystemPrompt.value.trim();
        if (!prompt) {
            this.showToast('系统提示词不能为空', 'warning');
            return;
        }

        if (!this.currentSessionId) {
            this.showToast('请先选择一个会话', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/sessions/${this.currentSessionId}/system-prompt`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ system_prompt: prompt }),
            });

            if (response.ok) {
                this.messagesContainer.innerHTML = '';
                this.addMessage('assistant', '系统提示词已更新，对话上下文已重置', false);
                this.connectWebSocket(this.currentSessionId);
                this.showToast('系统提示词已保存', 'success');
            } else {
                this.showToast('保存失败', 'error');
            }
        } catch (error) {
            console.error('Failed to save system prompt:', error);
            this.showToast('保存失败: ' + error.message, 'error');
        }
    }

    async importSession(event) {
        const file = event.target.files[0];
        if (!file) return;

        try {
            const text = await file.text();
            const data = JSON.parse(text);

            if (!data.agent || !Array.isArray(data.messages)) {
                this.showToast('无效的会话文件格式', 'error');
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
            this.showToast(`会话 "${data.agent}" 导入成功`, 'success');
        } catch (error) {
            console.error('Failed to import session:', error);
            this.showToast('导入失败: ' + error.message, 'error');
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
                    this.showToast('配置已重置为默认值', 'info');
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
