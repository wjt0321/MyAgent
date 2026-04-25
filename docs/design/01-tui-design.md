# TUI 终端界面设计

> MyAgent TUI 基于 Textual 框架构建，提供终端内的 AI Agent 交互体验。
> 灵感来源: OpenHarness (`ui/app.py`) — Textual 框架实现

---

## 1. 设计目标

1. **高级但不复杂**: 保持单主视图，但把高频状态集中到右侧状态面板
2. **工具可视化**: 工具执行不再只是文本刷屏，而是具备状态、`tool_use_id` 和详情摘要
3. **浮层交互**: 权限审批、Setup Handoff、Session 摘要、帮助与 Command Palette 都通过 ModalScreen 呈现
4. **状态可见**: 首屏即可看到 Agent、Model、Workspace、Setup 状态、任务状态、活动轨迹

---

## 2. 布局

```text
+---------------------------------------------------------------------------------------+
| MyAgent v0.2.0 | Agent: general | Model: glm-4.7 | Turns: 3 | Cost: $0.012 | ...    |
+-----------------------------------------------+---------------------------------------+
| Transcript (RichLog)                           | 状态概览                              |
| > user: Hello                                 | - Agent / Model / Workspace           |
| > assistant: Hi there                         | - Setup: ready / required             |
| > Tool: Read [tool-1]                         |                                       |
| > Result: ...                                 | 任务状态                              |
|                                               | - State: planning / idle              |
|                                               | - Request / Detail                    |
|                                               |                                       |
|                                               | 活动轨迹                              |
|                                               | - Tool / tool_use_id / Status         |
|                                               |                                       |
|                                               | 当前响应                              |
|                                               | - Thinking...                         |
+-----------------------------------------------+---------------------------------------+
| composer> _                                                                            |
+---------------------------------------------------------------------------------------+
| ^L Clear  ^K Palette  ^R Regenerate  ^D Exit                                         |
+---------------------------------------------------------------------------------------+
```

---

## 3. 组件

| 组件 | 类型 | 功能 |
|------|------|------|
| Header | Static | 版本、Agent、Model、成本、回合数 |
| Transcript | RichLog | 历史对话与结构化工具轨迹 |
| Status Panel | Static | 当前 Agent、Model、Workspace、Setup 状态 |
| Task Panel | Static | 当前任务状态与最近请求 |
| Activity Panel | Static | 最近一次工具执行状态、`tool_use_id`、详情摘要 |
| Current Response | Static | 当前流式输出 |
| Composer | TextArea | 多行输入与 Slash Commands |
| Footer | Footer | 快捷键提示 |

---

## 4. 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+L` | 清屏 |
| `Ctrl+K` | 打开 Command Palette |
| `Ctrl+R` | 重新生成上一轮响应 |
| `Ctrl+D` | 退出 |
| `Enter` | 提交输入 |
| `Shift+Enter` | 换行 |

---

## 5. 命令

| 命令 | 功能 |
|------|------|
| `/exit` | 退出 |
| `/clear` | 清屏 |
| `/help` | 通过浮层查看帮助 |
| `/agent <name>` | 切换 Agent |
| `/provider <name>` | 切换 Provider |
| `/model <name>` | 切换模型 |
| `/memory` | 查看记忆 |
| `/plan <request>` | 进入规划模式并记录任务请求 |
| `/setup` | 通过浮层查看 setup handoff |
| `/doctor` | 通过浮层查看 setup 健康摘要 |
| `/session` | 通过浮层查看当前会话摘要 |

---

## 6. 与参考项目的对比

| 维度 | MyAgent | OpenHarness | Claude Code |
|------|---------|-------------|-------------|
| 框架 | Textual | Textual | React Ink |
| 布局 | 单主视图 + 右侧状态面板 | 多区块 | 单栏 |
| 流式输出 | 支持 | 支持 | 支持 |
| 工具轨迹 | 结构化文本 + 状态面板 | 基础文本 | 结构化较强 |
| 权限审批 | ModalScreen | ModalScreen | 确认提示 |
| Setup Handoff | 支持 | 较弱 | 不强调 |

---

## 7. 技术栈

- **Textual** — Python TUI 框架
- **Rich** — 文本格式化 (已有依赖)
