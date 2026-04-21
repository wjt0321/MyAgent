# MyAgent TUI 设计文档

## 参考来源

- **OpenHarness** (`src/openharness/ui/textual_app.py`) — Textual 框架实现，包含：
  - 三栏布局：对话区 | 侧边栏（状态/任务/MCP）
  - 实时流式输出显示
  - 权限审批弹窗（ModalScreen）
  - 快捷键绑定（Ctrl+L 清屏、Ctrl+D 退出等）
  - RichLog 组件显示带格式的文本

- **Claude Code** — 简洁的终端交互体验：
  - 单行输入，流式输出
  - 工具执行结果折叠显示
  - 代码差异高亮

## MyAgent TUI 设计

### 布局

```
+----------------------------------------------------------+
| Header: MyAgent v0.1.0  [general]  Cost: $0.012          |
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
| Footer: ^L Clear  ^R Refresh  ^P Provider  ^D Exit       |
+----------------------------------------------------------+
```

### 组件

1. **Header** — 显示版本、当前 Agent、累计成本
2. **Transcript (RichLog)** — 历史对话记录，支持 markdown/markup
3. **Current Response (Static)** — 当前流式输出缓冲区
4. **Composer (Input)** — 用户输入框
5. **Footer** — 快捷键提示

### 交互

- **流式输出**：LLM 返回的 TextDelta 实时追加到 Current Response
- **工具执行**：显示工具调用和结果，可折叠
- **权限审批**：写工具/Bash 弹出 ModalScreen 确认
- **快捷键**：
  - `Ctrl+L` — 清屏
  - `Ctrl+R` — 刷新
  - `Ctrl+P` — 切换 Provider
  - `Ctrl+D` — 退出
  - `Enter` — 提交输入

### 技术栈

- **Textual** — Python TUI 框架
- **Rich** — 文本格式化（已作为依赖）
