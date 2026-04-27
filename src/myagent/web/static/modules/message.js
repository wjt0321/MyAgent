export default (Base) => class MessageMixin extends Base {
    addMessage(role, content, append = false) {
        if (this.welcomeScreen) {
            this.welcomeScreen.style.display = 'none';
        }
        if (append) {
            const lastMessage = this.messagesContainer.lastElementChild;
            if (lastMessage && lastMessage.classList.contains(role)) {
                const contentEl = lastMessage.querySelector('.content');
                if (role === 'assistant') {
                    const rawText = (lastMessage.dataset.rawText || '') + content;
                    lastMessage.dataset.rawText = rawText;
                    contentEl.innerHTML = this.renderMarkdown(rawText);
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

        if (role === 'assistant') {
            messageDiv.dataset.rawText = content;
        }

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

        const textarea = document.createElement('textarea');
        textarea.className = 'message-edit-input';
        textarea.value = originalContent;
        textarea.rows = 3;

        contentEl.replaceWith(textarea);
        if (metaEl) metaEl.style.display = 'none';

        textarea.focus();
        textarea.setSelectionRange(textarea.value.length, textarea.value.length);
        this.autoResizeTextarea(textarea);

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

        messageDiv.dataset.rawText = trimmed;

        if (resend) {
            let nextEl = messageDiv.nextElementSibling;
            while (nextEl) {
                const toRemove = nextEl;
                nextEl = nextEl.nextElementSibling;
                toRemove.remove();
            }

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

    // ========== Tool Calls ==========

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

    renderToolEventCard({ kind, title, toolUseId = '', summary, payload, icon, statusLabel, statusTone, meta }) {
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
};
