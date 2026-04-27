export default (Base) => class SessionMixin extends Base {
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

        const rect = anchorBtn.getBoundingClientRect();
        menu.style.position = 'fixed';
        menu.style.top = `${rect.bottom + 4}px`;
        menu.style.left = `${rect.left}px`;
        menu.style.zIndex = '1000';

        document.body.appendChild(menu);

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

        const chatArea = document.querySelector('.chat-area');
        if (chatArea) {
            chatArea.classList.remove('session-transitioning');
            void chatArea.offsetWidth;
            chatArea.classList.add('session-transitioning');
            setTimeout(() => chatArea.classList.remove('session-transitioning'), 300);
        }

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

    // ========== Session Import ==========

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

            if (data.messages.length > 0) {
                const importResponse = await fetch(`/api/sessions/${session.id}/import`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages: data.messages }),
                });

                if (!importResponse.ok) throw new Error('导入消息失败');
            }

            await this.loadSessions();
            this.selectSession(session.id);
            this.showToast(`会话 "${data.agent}" 导入成功`, 'success');
        } catch (error) {
            console.error('Failed to import session:', error);
            this.showToast('导入失败: ' + error.message, 'error');
        }
    }
};
