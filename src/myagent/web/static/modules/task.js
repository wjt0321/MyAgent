export default (Base) => class TaskMixin extends Base {
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
};
