# 交互模式与命令规范

> 本文档定义 MyAgent 的所有交互模式和命令规范。

---

## 1. 命令体系

### 1.1 CLI 命令

```bash
myagent init              # 初始化 Workspace
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
| `/agent <name>` | 切换 Agent |
| `/provider <name>` | 切换 Provider |
| `/model <name>` | 切换模型 |
| `/memory` | 查看记忆 |
| `/plan <request>` | 创建任务计划 |

### 1.3 Web UI 命令

| 命令 | 功能 |
|------|------|
| `/plan <request>` | 创建任务计划 |

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

### 2.3 权限审批模式

```
Agent: I need to write to src/main.py. Approve?
[Approve] [Reject]
```

### 2.4 任务工作流模式

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

---

## 3. 状态指示

### 3.1 Agent 状态

| 状态 | 指示 |
|------|------|
| Idle | 等待输入 |
| Thinking | 处理中... |
| Tool Call | 调用工具... |
| Permission | 等待审批 |

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

### 3.3 团队成员状态

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
