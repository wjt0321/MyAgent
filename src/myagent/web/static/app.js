/**
 * MyAgent Web UI - Frontend Application
 * Modern, polished interaction layer
 */

import ThemeMixin from './modules/theme.js';
import WebSocketMixin from './modules/websocket.js';
import UIMixin from './modules/ui.js';
import SessionMixin from './modules/session.js';
import MessageMixin from './modules/message.js';
import TaskMixin from './modules/task.js';
import WorkspaceMixin from './modules/workspace.js';

const Base = class {};
const MixinBase = WorkspaceMixin(TaskMixin(SessionMixin(MessageMixin(UIMixin(WebSocketMixin(ThemeMixin(Base)))))));

class MyAgentWebApp extends MixinBase {
    constructor() {
        super();
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
        this.loadAvailableModels();
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

        this.settingsBtn = document.getElementById('settings-btn');
        this.settingsModal = document.getElementById('settings-modal');
        this.closeSettingsBtn = document.getElementById('close-settings');
        this.saveSettingsBtn = document.getElementById('save-settings-btn');
        this.settingsAgentSelect = document.getElementById('settings-agent-select');
        this.settingsSystemPrompt = document.getElementById('settings-system-prompt');

        this.settingsThemeBtns = document.querySelectorAll('.theme-btn');
        this.settingsSessionCount = document.getElementById('settings-session-count');
        this.settingsMessageCount = document.getElementById('settings-message-count');
        this.workspaceInfo = document.getElementById('workspace-info');

        this.sessionImportBtn = document.getElementById('session-import-btn');
        this.sessionImportFile = document.getElementById('session-import-file');

        this.toastContainer = document.getElementById('toast-container');

        this.memoryList = document.getElementById('memory-list');
        this.memoryForm = document.getElementById('memory-form');
        this.newMemoryBtn = document.getElementById('new-memory-btn');
        this.memoryName = document.getElementById('memory-name');
        this.memoryDescription = document.getElementById('memory-description');
        this.memoryType = document.getElementById('memory-type');
        this.memoryContent = document.getElementById('memory-content');
        this.memorySaveBtn = document.getElementById('memory-save');
        this.memoryCancelBtn = document.getElementById('memory-cancel');

        this.taskPanel = document.getElementById('task-panel');
        this.taskWorkflowModal = document.getElementById('task-workflow-modal');
        this.taskPlanSteps = document.getElementById('task-plan-steps');
        this.taskApproveBtn = document.getElementById('task-approve');
        this.taskRejectBtn = document.getElementById('task-reject');
        this.closeTaskWorkflowBtn = document.getElementById('close-task-workflow');
        this.currentTask = null;

        this.teamPanel = document.getElementById('team-panel');

        this.rebuildIndexBtn = document.getElementById('rebuild-index-btn');
        this.codebaseSearchInput = document.getElementById('codebase-search-input');
        this.codebaseSearchBtn = document.getElementById('codebase-search-btn');
        this.codebaseStats = document.getElementById('codebase-stats');
        this.codebaseResults = document.getElementById('codebase-results');

        this.resetModal = document.getElementById('reset-modal');
        this.resetMessage = document.getElementById('reset-message');
        this.resetConfirmBtn = document.getElementById('reset-confirm');
        this.resetCancelBtn = document.getElementById('reset-cancel');
        this.resetConversationBtn = document.getElementById('reset-conversation-btn');
        this.resetAllSessionsBtn = document.getElementById('reset-all-sessions-btn');
        this.resetConfigBtn = document.getElementById('reset-config-btn');

        this.tabBtns = document.querySelectorAll('.tab-btn');
        this.tabContents = document.querySelectorAll('.tab-content');

        this.saveSystemPromptBtn = document.getElementById('save-system-prompt-btn');

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

        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 200) + 'px';
        });

        this.newSessionBtn.addEventListener('click', () => this.createSession());
        this.closePreviewBtn.addEventListener('click', () => this.hideFilePreview());
        this.themeToggle?.addEventListener('click', () => this.toggleTheme());

        this.detailSidebar?.addEventListener('click', (e) => {
            if (e.target === this.detailSidebar && window.innerWidth <= 768) {
                this.hideFilePreview();
            }
        });

        this.mobileSidebarToggle?.addEventListener('click', () => this.openSidebar());
        this.sidebarOverlay?.addEventListener('click', () => this.closeSidebar());
        window.addEventListener('resize', () => this.syncResponsiveWorkbenchState());

        this.detailSidebarResize = document.getElementById('detail-sidebar-resize');
        this.initDetailSidebarResize();

        this.searchToggle?.addEventListener('click', () => this.toggleSearch());
        this.searchClose?.addEventListener('click', () => this.toggleSearch());
        this.searchInput.addEventListener('input', (e) => this.performSearch(e.target.value));
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (e.shiftKey) {
                    this.prevSearchResult();
                } else {
                    this.nextSearchResult();
                }
            }
        });
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

        this.settingsBtn?.addEventListener('click', () => this.openSettings());
        this.closeSettingsBtn.addEventListener('click', () => this.closeSettings());
        this.saveSettingsBtn.addEventListener('click', () => this.saveSettings());
        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) this.closeSettings();
        });

        this.bindQuickCards();

        this.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });

        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.currentTheme = btn.dataset.theme;
                this.applyTheme();
            });
        });

        this.newMemoryBtn?.addEventListener('click', () => this.showMemoryForm());
        this.memoryCancelBtn?.addEventListener('click', () => this.hideMemoryForm());
        this.memorySaveBtn?.addEventListener('click', () => this.saveMemory());

        this.closeTaskWorkflowBtn?.addEventListener('click', () => this.hideTaskWorkflow());
        this.taskRejectBtn?.addEventListener('click', () => this.hideTaskWorkflow());
        this.taskApproveBtn?.addEventListener('click', () => this.approveTask());
        this.taskWorkflowModal?.addEventListener('click', (e) => {
            if (e.target === this.taskWorkflowModal) this.hideTaskWorkflow();
        });

        this.rebuildIndexBtn?.addEventListener('click', () => this.rebuildCodebaseIndex());
        this.codebaseSearchBtn?.addEventListener('click', () => this.searchCodebase());
        this.codebaseSearchInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') this.searchCodebase();
        });

        this.resetConversationBtn?.addEventListener('click', () => this.showResetConfirm('conversation'));
        this.resetAllSessionsBtn?.addEventListener('click', () => this.showResetConfirm('all'));
        this.resetConfigBtn?.addEventListener('click', () => this.showResetConfirm('config'));
        this.resetCancelBtn?.addEventListener('click', () => this.hideResetModal());
        this.resetConfirmBtn?.addEventListener('click', () => this.executeReset());
        this.resetModal?.addEventListener('click', (e) => {
            if (e.target === this.resetModal) this.hideResetModal();
        });

        if (this.saveSystemPromptBtn) {
            this.saveSystemPromptBtn.addEventListener('click', () => this.saveSystemPrompt());
        }

        if (this.sessionImportBtn) {
            this.sessionImportBtn.addEventListener('click', () => this.sessionImportFile.click());
        }
        if (this.sessionImportFile) {
            this.sessionImportFile.addEventListener('change', (e) => {
                this.importSession(e);
                e.target.value = '';
            });
        }
    }

    // ========== Welcome & Quick Cards ==========

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

    renderMessages() {
        this.messagesContainer.innerHTML = '';
        this.messages.forEach(msg => {
            this.addMessage(msg.role, msg.content, false);
        });
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

    // ========== Slash Commands ==========

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
}

document.addEventListener('DOMContentLoaded', () => {
    window.myAgentApp = new MyAgentWebApp();
});
