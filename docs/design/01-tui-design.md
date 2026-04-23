# TUI 终端界面设计

> MyAgent TUI 基于 Textual 框架构建，提供终端内的 AI Agent 交互体验。
> 灵感来源: OpenHarness (`ui/app.py`) — Textual 框架实现

---

## 1. 设计目标

1. **简洁高效**: 单行输入，流式输出
2. **工具可视化**: 工具调用和结果折叠显示
3. **权限审批**: 写工具/Bash 弹出确认
4. **状态显示**: 实时显示 Agent、成本、回合数

---

## 2. 布局

```
+----------------------------------------------------------+
| MyAgent v0.11.0  [general]  Cost: $0.012  Turns: 3       |
+----------------------------------------------------------+
|                                                          |
|  Transcript (RichLog)                                    |
|  > user: Hello                                           |
|  > assistant: Hi there! How can I help?                  |
|  > tool: Read(src/main.py)                               |
|    [file content...]                                     |
|                                                          |
+----------------------------------------------------------+
| Current Response                                         |
| [bold]Thinking...[/bold]                                 |
+----------------------------------------------------------+
| composer> _                                              |
+----------------------------------------------------------+
| ^L Clear  ^R Refresh  ^P Provider  ^D Exit             |
+----------------------------------------------------------+
```

---

## 3. 组件

| 组件 | 类型 | 功能 |
|------|------|------|
| Header | Header | 版本、Agent、成本、回合数 |
| Transcript | RichLog | 历史对话，支持 Markdown |
| Current Response | Static | 当前流式输出 |
| Composer | Input | 用户输入 |
| Footer | Footer | 快捷键提示 |

---

## 4. 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+L` | 清屏 |
| `Ctrl+R` | 刷新 |
| `Ctrl+P` | 切换 Provider |
| `Ctrl+D` | 退出 |
| `Enter` | 提交输入 |
| `Shift+Enter` | 换行 |

---

## 5. 命令

| 命令 | 功能 |
|------|------|
| `/exit` | 退出 |
| `/clear` | 清屏 |
| `/agent <name>` | 切换 Agent |
| `/provider <name>` | 切换 Provider |
| `/model <name>` | 切换模型 |
| `/memory` | 查看记忆 |
| `/plan <request>` | 创建任务计划 |

---

## 6. 与参考项目的对比

| 维度 | MyAgent | OpenHarness | Claude Code |
|------|---------|-------------|-------------|
| 框架 | Textual | Textual | React Ink |
| 布局 | 三栏 | 三栏 | 单栏 |
| 流式输出 | 支持 | 支持 | 支持 |
| 工具折叠 | 支持 | 支持 | 支持 |
| 权限审批 | ModalScreen | ModalScreen | 确认提示 |
| 代码高亮 | Rich | Rich | 语法高亮 |

---

## 7. 技术栈

- **Textual** — Python TUI 框架
- **Rich** — 文本格式化 (已有依赖)
