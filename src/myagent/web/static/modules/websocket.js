export default (Base) => class WebSocketMixin extends Base {
    connectWebSocket(sessionId) {
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
            if (event.code === 1000 || event.code === 1005) {
                return;
            }
            if (event.code === 1006 || event.code === 1011) {
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

    setSending(sending) {
        this.isSending = sending;
        this.sendBtn.disabled = sending;
        this.sendBtn.style.opacity = sending ? '0.5' : '1';
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
        this._pendingPermissions = this._pendingPermissions || [];
        this._pendingPermissions.push(data);
        this._alwaysAllowTools = this._alwaysAllowTools || new Set();

        const toolName = data.tool_name || 'Unknown';
        if (this._alwaysAllowTools.has(toolName)) {
            this.handlePermissionForItem(data, true);
            return;
        }

        this.renderPermissionBanners();
    }

    renderPermissionBanners() {
        let container = document.getElementById('approval-gates-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'approval-gates-container';
            const chatArea = document.querySelector('.chat-area') || document.querySelector('.workbench-view[data-view="chat"]');
            if (chatArea) {
                chatArea.insertBefore(container, chatArea.querySelector('.composer-bar'));
            } else {
                document.body.appendChild(container);
            }
        }

        container.innerHTML = '';

        this._pendingPermissions = this._pendingPermissions || [];
        this._pendingPermissions.forEach((data, index) => {
            const banner = document.createElement('div');
            banner.className = 'approval-gate-banner';
            banner.dataset.toolUseId = data.tool_use_id || '';

            const argsText = Object.entries(data.arguments || {})
                .map(([k, v]) => `${k}: ${String(v)}`)
                .join(', ');

            banner.innerHTML = `
                <div class="approval-gate-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                </div>
                <div class="approval-gate-body">
                    <div class="approval-gate-title">${this.escapeHtml(data.tool_name || 'Permission Required')}</div>
                    <div class="approval-gate-reason">${this.escapeHtml(data.reason || '')}</div>
                    ${argsText ? `<div class="approval-gate-args">${this.escapeHtml(argsText)}</div>` : ''}
                </div>
                <div class="approval-gate-actions">
                    <label class="approval-gate-always-allow">
                        <input type="checkbox" data-tool="${this.escapeHtml(data.tool_name)}" />
                        <span>总是允许</span>
                    </label>
                    <button class="approval-gate-btn approval-gate-deny" data-index="${index}">拒绝</button>
                    <button class="approval-gate-btn approval-gate-approve" data-index="${index}">允许</button>
                </div>
            `;

            container.appendChild(banner);

            void banner.offsetWidth;
            banner.classList.add('slide-in');

            banner.querySelector('.approval-gate-approve').addEventListener('click', () => {
                const alwaysAllow = banner.querySelector('.approval-gate-always-allow input');
                if (alwaysAllow && alwaysAllow.checked) {
                    this._alwaysAllowTools.add(data.tool_name);
                }
                this.handlePermissionForItem(data, true);
            });

            banner.querySelector('.approval-gate-deny').addEventListener('click', () => {
                this.handlePermissionForItem(data, false);
            });
        });
    }

    handlePermissionForItem(data, approved) {
        this.sendPermissionResponse(data.tool_use_id, approved);

        this._pendingPermissions = (this._pendingPermissions || []).filter(
            p => p.tool_use_id !== data.tool_use_id
        );

        const banner = document.querySelector(`.approval-gate-banner[data-tool-use-id="${data.tool_use_id}"]`);
        if (banner) {
            banner.classList.add('approved');
            setTimeout(() => banner.remove(), 600);
        }

        if (this._pendingPermissions.length === 0) {
            const container = document.getElementById('approval-gates-container');
            if (container) container.remove();
        } else {
            this.renderPermissionBanners();
        }
    }

    handlePermission(approved) {
        if (this._pendingPermissions && this._pendingPermissions.length > 0) {
            this.handlePermissionForItem(this._pendingPermissions[0], approved);
        }
    }
};
