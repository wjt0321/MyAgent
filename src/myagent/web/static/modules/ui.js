export default (Base) => class UIMixin extends Base {
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

    // ========== Views ==========

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

    // ========== Command Palette ==========

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

    // ========== Status ==========

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

    // ========== Agent/Model Switch ==========

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
        this._searchMatchElements = [];

        messages.forEach((msg, msgIndex) => {
            const content = msg.querySelector('.content');
            if (!content) return;

            const text = content.textContent;
            const lowerText = text.toLowerCase();
            const matchStart = lowerText.indexOf(lowerQuery);

            if (matchStart !== -1) {
                msg.classList.add('search-match');
                this._searchMatches.push({ msg, content, matchStart, matchLength: query.length });

                const originalHTML = content.innerHTML;
                const matchEnd = matchStart + query.length;
                const before = text.slice(0, matchStart);
                const match = text.slice(matchStart, matchEnd);
                const after = text.slice(matchEnd);

                content.innerHTML = `${this.escapeHtml(before)}<mark class="search-highlight">${this.escapeHtml(match)}</mark>${this.escapeHtml(after)}`;
                this._searchMatchElements.push(content);
            }
        });

        this._searchIndex = 0;
        this.updateSearchCount(this._searchIndex, this._searchMatches.length);

        if (this._searchMatches.length > 0) {
            this._searchMatches[0].msg.scrollIntoView({ behavior: 'smooth', block: 'center' });
            this.highlightCurrentSearchMatch();
        }
    }

    highlightCurrentSearchMatch() {
        this._searchMatchElements.forEach(el => {
            const mark = el?.querySelector('.search-highlight.current');
            if (mark) mark.classList.remove('current');
        });

        if (this._searchMatches[this._searchIndex]) {
            const content = this._searchMatchElements[this._searchIndex];
            const mark = content?.querySelector('.search-highlight');
            if (mark) mark.classList.add('current');
        }
    }

    scrollToSearchMatch(index) {
        if (!this._searchMatches || this._searchMatches.length === 0) return;
        const clamped = Math.max(0, Math.min(index, this._searchMatches.length - 1));
        this._searchIndex = clamped;
        this.updateSearchCount(this._searchIndex, this._searchMatches.length);
        this._searchMatches[clamped].msg.scrollIntoView({ behavior: 'smooth', block: 'center' });
        this.highlightCurrentSearchMatch();
    }

    updateSearchCount(current, total) {
        const countEl = document.getElementById('search-count');
        if (!countEl) return;
        if (total === 0) {
            countEl.textContent = '无结果';
        } else {
            countEl.textContent = `${current + 1}/${total}`;
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
        this.messagesContainer.querySelectorAll('.search-match').forEach(msg => {
            const content = msg.querySelector('.content');
            if (content) {
                const mark = content.querySelector('.search-highlight');
                if (mark) {
                    const textNode = document.createTextNode(mark.textContent);
                    mark.parentNode.replaceChild(textNode, mark);
                    content.normalize();
                }
            }
            msg.classList.remove('search-match');
        });
        this._searchMatches = [];
        this._searchIndex = 0;
        this.updateSearchCount(0, 0);
    }
};
