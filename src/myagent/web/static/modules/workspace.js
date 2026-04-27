export default (Base) => class WorkspaceMixin extends Base {
    // ========== Setup & Workspace ==========

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

        this.workspaceInfo.querySelectorAll('.workspace-memory-items').forEach(item => {
            item.addEventListener('click', () => {
                const filename = item.dataset.filename;
                if (filename) {
                    this.showMemoryPreview(filename);
                }
            });
        });

        this.renderWorkspaceOverview();
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

    async _getWorkspacePath() {
        try {
            const response = await fetch('/api/workspace');
            const data = await response.json();
            return data.path;
        } catch (error) {
            return null;
        }
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
        if (!this.fileTree) return;
        this.fileTree.innerHTML = '';
        this.fileEntries = entries;
        this._fileTreeData = { entries, parentPath };

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
                this.previewContent.innerHTML = window.marked.parse(data.content);
                this.previewContent.className = 'markdown-preview';
            } else {
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
        this.detailSidebar?.classList.remove('show', 'show-mobile');

        const overlay = document.getElementById('detail-sidebar-overlay');
        if (overlay) overlay.classList.remove('show');

        if (this.previewContent) {
            this.previewContent.textContent = '';
            this.previewContent.className = '';
        }
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
        this.previewFilename.textContent = payload.title || '详情';
        this.detailSidebarMeta.textContent = payload.meta || kind;

        const bodyHtml = this.escapeHtml(payload.body || '').replace(/\n/g, '<br>');
        this.detailSidebarContent.innerHTML = `
            <div class="detail-card">
                <div class="detail-card-title">${this.escapeHtml(payload.title || '详情')}</div>
                <div class="detail-card-body">${bodyHtml || '暂无详情'}</div>
            </div>
        `;
        this.detailSidebar.classList.add('show');

        const isMobile = window.innerWidth <= 768;
        this.detailSidebar.classList.toggle('show-mobile', isMobile);

        if (isMobile) {
            let overlay = document.getElementById('detail-sidebar-overlay');
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = 'detail-sidebar-overlay';
                overlay.className = 'detail-sidebar-overlay';
                overlay.addEventListener('click', () => this.hideFilePreview());
                document.body.appendChild(overlay);
            }
            overlay.classList.add('show');
        }
    }

    initDetailSidebarResize() {
        if (!this.detailSidebarResize) return;

        let isResizing = false;
        let startX = 0;
        let startWidth = 0;
        const minWidth = 300;
        const maxWidthRatio = 0.5;

        const onMouseDown = (e) => {
            isResizing = true;
            startX = e.clientX;
            startWidth = this.detailSidebar.offsetWidth;
            this.detailSidebarResize.classList.add('active');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            e.preventDefault();
        };

        const onMouseMove = (e) => {
            if (!isResizing) return;
            const delta = startX - e.clientX;
            const newWidth = Math.max(minWidth, Math.min(startWidth + delta, window.innerWidth * maxWidthRatio));
            this.detailSidebar.style.width = `${newWidth}px`;
        };

        const onMouseUp = () => {
            if (!isResizing) return;
            isResizing = false;
            this.detailSidebarResize.classList.remove('active');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };

        this.detailSidebarResize.addEventListener('mousedown', onMouseDown);
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    }

    // ========== Models ==========

    async loadAvailableModels() {
        try {
            const response = await fetch('/api/models');
            if (response.ok) {
                const models = await response.json();
                this.availableModels = models.map(m => m.name);
                this.availableModelDetails = models;
            }
        } catch (error) {
            console.warn('Failed to load models from API, using defaults:', error);
        }
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
};
