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
};
