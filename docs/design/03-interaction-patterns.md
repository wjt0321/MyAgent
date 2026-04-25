# 交互模式与命令规范

> 本文档定义 MyAgent 的所有交互模式和命令规范。

---

## 1. 命令体系

### 1.1 CLI 命令

```bash
myagent init              # 初始化 Workspace
myagent init --quick      # 生成最小可用配置
myagent web               # 启动 Web UI
myagent gateway           # 启动 Gateway
myagent doctor            # 诊断系统
myagent --tui             # 启动 TUI
myagent --version         # 显示版本
```

### 1.2 TUI 命令

| 命令 | 功能 |
|------|------|
| `/exit` | 退出 |
| `/clear` | 清屏 |
| `/help` | 打开帮助浮层 |
| `/agent <name>` | 切换 Agent |
| `/provider <name>` | 切换 Provider |
| `/model <name>` | 切换模型 |
| `/memory` | 查看记忆 |
| `/plan <request>` | 创建任务计划 |
| `/setup` | 打开 setup handoff 浮层 |
| `/doctor` | 打开 setup 健康摘要浮层 |
| `/session` | 打开当前会话摘要浮层 |

### 1.3 Web UI 命令

| 命令 | 功能 |
|------|------|
| `/plan <request>` | 创建任务计划 |
| `/agent <name>` | 切换 Agent |
| `/model <name>` | 切换模型 |
| `/session` | 查看当前会话摘要 |
| `/setup` | 打开设置面板 |
| `/doctor` | 查看当前 Web 工作台状态 |

### 1.4 Web Command Palette

| 触发方式 | 功能 |
|---------|------|
| `Ctrl+K` | 打开命令面板 |
| `chat/tasks/files/workspace/team` | 切换工作台视图 |
| `settings` | 打开设置 |
| `input` | 聚焦消息输入框 |
| `/help` | 查看支持的 Slash Commands |

---

## 2. 交互模式

### 2.1 对话模式

```
User: Hello
Agent: Hi there! How can I help you today?
```

### 2.2 工具调用模式

```
Agent: I'll read the file for you.
[Tool Call] Read(src/main.py)
[Tool Result] file content...
Agent: Based on the file content...
```

Web 工作台中的对应形态：

1. 聊天流中展示可折叠工具卡片
2. 点击卡片后，在右侧详情侧栏查看参数与结果
3. 长输出保留在详情侧栏中，减少主聊天流噪音

### 2.3 权限审批模式

```
Agent: I need to write to src/main.py. Approve?
[Approve] [Reject]
```

### 2.4 Setup Handoff 模式

```text
App: Setup Required
  - Workspace 尚未初始化
  - 未检测到可用的 API Key
  - Next: myagent init --quick
[Close]
```

### 2.5 Command Palette 模式

```text
Ctrl+K
┌ Command Palette ──────────────────────┐
│ /help     查看帮助与快捷键             │
│ /setup    查看初始化与修复建议         │
│ /session  查看当前会话摘要             │
│ /plan     查看规划入口说明             │
└───────────────────────────────────────┘
```

### 2.6 任务工作流模式

```
User: /plan Implement user authentication
Agent: [Plan generated]
  1. Explore existing auth code
  2. Design auth schema
  3. Implement login endpoint
  4. Add middleware
[Approve] [Reject]
User: [Approve]
Agent: [Executing...]
  [✓] Explore existing auth code
  [✓] Design auth schema
  [✓] Implement login endpoint
  [✓] Add middleware
Agent: [Review] All tasks completed successfully.
```

### 2.5 工作台视图切换

```
User: Click "Tasks" in workbench nav
UI: Main view switches from chat flow to task stream
UI: Detail sidebar remains available for current task / session context
```

### 2.6 会话详情模式

```
User: Click a recent session card
UI: Session becomes active
UI: Header updates agent/model/status
UI: Detail sidebar shows session summary
```

---

## 3. 状态指示

### 3.1 Agent 状态

| 状态 | 指示 |
|------|------|
| Idle | 等待输入 |
| Thinking | 处理中... |
| Tool Call | 调用工具... |
| Permission | 等待审批 |
<<<<<<< HEAD
| Setup Required | 配置未完成，需进入初始化 |
=======
| Connected | WebSocket 已连接 |
| Disconnected | WebSocket 未连接 |
>>>>>>> ddf8ea0 (完成Phase3Web工作台重构)

### 3.2 任务状态

| 状态 | 颜色 |
|------|------|
| Pending | 灰色 |
| Planning | 黄色 |
| Planned | 橙色 |
| Executing | 蓝色 |
| Executed | 紫色 |
| Reviewing | 青色 |
| Done | 绿色 |
| Failed | 红色 |
| Cancelled | 灰色 |

### 3.3 TUI 侧栏状态

| 区域 | 内容 |
|------|------|
| 状态概览 | Agent、Model、Workspace、Setup 状态 |
| 任务状态 | 当前任务状态、最近请求、说明 |
| 活动轨迹 | 最近工具、`tool_use_id`、执行状态、详情摘要 |
| 当前响应 | 最新流式内容 |

### 3.4 团队成员状态

| 状态 | 颜色 |
|------|------|
| Idle | 绿色 |
| Busy | 黄色 |
| Offline | 灰色 |

---

## 4. 错误处理

### 4.1 常见错误

| 错误 | 提示 |
|------|------|
| LLM not configured | 请配置 LLM Provider |
| Session not found | 会话不存在 |
| Tool not found | 工具未注册 |
| Permission denied | 权限不足 |

### 4.2 重连策略

WebSocket 断开后：
1. 检测 close code 1006/1011
2. 显示友好错误信息
3. 停止自动重连
4. 用户手动刷新恢复
