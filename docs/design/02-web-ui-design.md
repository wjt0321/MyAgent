# Web UI 设计规范

> MyAgent Web UI 基于 FastAPI + 原生 HTML/JS/CSS 构建，提供浏览器内的 AI Agent 交互体验。

---

## 1. 设计目标

1. **现代美观**: 暗色主题，玻璃拟态效果
2. **响应式**: 适配桌面和移动端
3. **实时通信**: WebSocket 流式消息
4. **功能丰富**: 文件浏览、会话管理、设置面板

---

## 2. 技术栈

- **后端**: FastAPI + WebSocket
- **前端**: 原生 HTML5 + CSS3 + JavaScript (ES6+)
- **样式**: CSS Variables + Glassmorphism
- **图标**: SVG 内联
- **Markdown**: marked.js
- **代码高亮**: Prism.js

---

## 3. 布局

```
+----------------------------------------------------------+
| Logo  MyAgent v0.11.0                    [Settings] [New]|
+----------+-----------------------------------------------+
|          |                                               |
| Sessions |                                               |
|          |              Chat Area                        |
| Workspace|                                               |
|          |                                               |
| Tasks    |                                               |
|          |                                               |
| Team     |                                               |
|          |                                               |
| Files    |                                               |
|          |                                               |
+----------+-----------------------------------------------+
|          |  [Attach] Message input...        [Send]     |
+----------+-----------------------------------------------+
```

---

## 4. 主题系统

### 4.1 CSS Variables

```css
:root {
  --bg-primary: #0f0f1a;
  --bg-secondary: #16162a;
  --bg-tertiary: #1e1e3a;
  --bg-hover: rgba(99, 102, 241, 0.1);
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --accent: #6366f1;
  --accent-hover: #818cf8;
  --accent-soft: rgba(99, 102, 241, 0.15);
  --border-default: rgba(148, 163, 184, 0.15);
  --border-subtle: rgba(148, 163, 184, 0.08);
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
}
```

### 4.2 Glassmorphism

```css
.glass {
  background: rgba(22, 22, 42, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border-default);
}
```

---

## 5. 组件规范

### 5.1 消息气泡

- **用户**: 右侧对齐，渐变背景，圆角
- **助手**: 左侧对齐，深色背景，圆角
- **工具**: 中间对齐，可折叠卡片

### 5.2 侧边栏

- **会话**: 列表，支持删除
- **Workspace**: 用户、记忆、项目
- **任务**: 当前任务卡片 + 进度条
- **团队**: 成员头像 + 状态灯
- **文件**: 可展开目录树

### 5.3 设置面板

- **Agent**: 选择 Agent、系统提示词
- **Memory**: 记忆列表、新建/编辑/删除
- **代码库**: 搜索、重建索引
- **重置**: 重置会话/配置
- **外观**: 主题切换
- **关于**: 版本信息、统计

---

## 6. 交互模式

### 6.1 流式输出

WebSocket 接收 `assistant_delta` 事件，实时追加到消息内容。

### 6.2 Markdown 渲染

使用 marked.js 解析 Markdown，支持：
- 标题、列表、代码块
- 表格、引用
- 任务列表

### 6.3 文件预览

点击文件树中的文件，右侧显示 Markdown 预览。

### 6.4 任务工作流

输入 `/plan <请求>` 触发：
1. 显示计划步骤列表
2. 用户批准
3. 实时显示执行进度

---

## 7. API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/ws` | WebSocket | 实时对话 |
| `/api/sessions` | GET/POST | 会话管理 |
| `/api/memories` | GET/POST/DELETE | 记忆管理 |
| `/api/workspace` | GET | Workspace 信息 |
| `/api/team` | GET | 团队状态 |
| `/api/tasks/plan` | POST | 创建任务计划 |
| `/api/codebase/index` | GET | 代码库索引 |
| `/api/codebase/search` | GET | 代码搜索 |
| `/api/files/tree` | GET | 文件树 |
| `/api/files/read` | GET | 读取文件 |

---

## 8. 与参考项目的对比

| 维度 | MyAgent | OpenClaw | Hermes Agent |
|------|---------|----------|--------------|
| 框架 | FastAPI + 原生 JS | 自研网关 | aiohttp |
| 前端 | 原生 HTML/CSS/JS | 无内置前端 | 无 |
| 主题 | 暗色 + Glassmorphism | 终端主题 | 无 |
| 流式 | WebSocket | WebSocket | 无 |
| 文件浏览 | 侧边栏树 | 无 | 无 |
| 会话管理 | 支持 | 无 | 支持 |
| 代码高亮 | Prism.js | 无 | 无 |
